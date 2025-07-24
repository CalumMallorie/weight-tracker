from datetime import datetime, timedelta, UTC
import json
import logging
import plotly
import plotly.express as px
import pandas as pd
from sqlalchemy import text, inspect
from typing import List, Optional, Dict, Any, Tuple

from .models import WeightEntry, WeightCategory, db, format_date

# Set up logger
logger = logging.getLogger(__name__)

def create_tables() -> None:
    """Create database tables if they don't exist"""
    logger.info("Creating database tables if they don't exist")
    try:
        # Create tables
        db.create_all()
        
        # Create default 'Body Mass' category if it doesn't exist
        create_default_category()
        
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        # Continue anyway, as the application might still work with existing tables

def create_default_category() -> WeightCategory:
    """Create default 'Body Mass' category if it doesn't exist"""
    body_mass = WeightCategory.query.filter_by(name="Body Mass").first()
    if not body_mass:
        logger.info("Creating default 'Body Mass' category")
        body_mass = WeightCategory(name="Body Mass", is_body_mass=True)
        db.session.add(body_mass)
        db.session.commit()
        logger.info(f"Default category created with ID: {body_mass.id}")
    return body_mass

def get_or_create_category(name: str, is_body_mass: bool = False) -> WeightCategory:
    """Get an existing category or create a new one"""
    category = WeightCategory.query.filter_by(name=name).first()
    if not category:
        logger.info(f"Creating new category: {name}")
        category = WeightCategory(name=name, is_body_mass=is_body_mass)
        db.session.add(category)
        db.session.commit()
        logger.info(f"Category created with ID: {category.id}")
    return category

def get_all_categories() -> List[WeightCategory]:
    """Get all weight categories ordered by name"""
    logger.info("Retrieving all weight categories")
    categories = WeightCategory.query.order_by(WeightCategory.name).all()
    logger.info(f"Retrieved {len(categories)} categories total")
    return categories

def delete_category(category_id: int) -> bool:
    """Delete a category and all its entries by ID"""
    logger.info(f"Attempting to delete category with ID: {category_id}")
    category = WeightCategory.query.get(category_id)
    if category:
        if category.is_body_mass:
            logger.warning(f"Cannot delete body mass category (ID: {category_id})")
            return False
            
        db.session.delete(category)
        db.session.commit()
        logger.info(f"Category with ID {category_id} and all its entries deleted successfully")
        return True
    logger.warning(f"Category with ID {category_id} not found for deletion")
    return False

def save_weight_entry(
    weight: float, 
    unit: str, 
    category_id_or_notes: Any = None, 
    reps: Optional[int] = None
) -> WeightEntry:
    """Save a new weight entry to the database
    
    For backwards compatibility with tests:
    - If category_id_or_notes is a string, it's treated as deprecated
    - If category_id_or_notes is a number, it's treated as category_id
    """
    # Special handling for tests that pass notes as 3rd parameter
    if isinstance(category_id_or_notes, str):
        category_id = None
    else:
        category_id = category_id_or_notes
    
    if category_id is None:
        # Use default Body Mass category if none provided
        category = create_default_category()
        category_id = category.id
    
    category = WeightCategory.query.get(category_id)
    if not category:
        logger.error(f"Category with ID {category_id} not found")
        raise ValueError(f"Category with ID {category_id} not found")
    
    # Check if 'is_body_weight_exercise' attribute exists to ensure backward compatibility
    is_body_weight_exercise = False
    if hasattr(category, 'is_body_weight_exercise'):
        is_body_weight_exercise = category.is_body_weight_exercise
    
    if category.is_body_mass:
        # Body Mass: ensure no reps
        if reps is not None:
            logger.warning("Body Mass entries should not have reps, ignoring reps value")
            reps = None
    elif is_body_weight_exercise:
        # Body Weight exercise: ensure has reps but use body mass for weight
        if reps is None:
            logger.warning("Body Weight exercises should have reps, defaulting to 1")
            reps = 1
            
        # For body weight exercises, use the most recent body mass entry as the weight
        most_recent_body_mass = get_most_recent_body_mass()
        if most_recent_body_mass:
            weight = most_recent_body_mass.weight
            unit = most_recent_body_mass.unit
            logger.info(f"Using body mass for body weight exercise: {weight}{unit}")
        else:
            # If no body mass entry exists, use the provided weight or default to 0
            logger.warning("No body mass entry found, using provided weight or default")
            if weight <= 0:
                weight = 70.0  # Default weight if none is provided
                unit = 'kg'    # Default unit
    else:
        # Normal exercise: ensure both weight and reps
        if reps is None:
            logger.warning("Normal exercises should have reps, defaulting to 1")
            reps = 1
    
    logger.info(f"Saving new weight entry: {weight}{unit}, category: {category.name}, reps: {reps}")
    logger.debug(f"Weight parameter type: {type(weight)}, value: {weight}")
    
    # Final validation: prevent zero weights for body mass entries
    if category.is_body_mass and weight <= 0:
        logger.error(f"CRITICAL: Attempted to save body mass entry with zero weight! weight={weight}, category={category.name}")
        raise ValueError(f"Body mass entries cannot have zero weight. Received weight: {weight}")
    
    try:
        # Check columns exist using introspection to avoid errors with older database schemas
        inspector = inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("weight_entry")}
        
        # Prepare entry data based on available columns
        current_time = datetime.now(UTC)
        entry_data = {
            'weight': weight,
            'unit': unit,
            'category_id': category_id,
            'created_at': current_time
        }
            
        # Only include reps if column exists
        if 'reps' in columns and reps is not None:
            entry_data['reps'] = reps
            
        # Create entry and save
        entry = WeightEntry(**entry_data)
        db.session.add(entry)
        
        # Update category's last_used_at if the column exists
        try:
            # Check if weight_category table has last_used_at column
            category_columns = {c["name"] for c in inspector.get_columns("weight_category")}
            if "last_used_at" in category_columns:
                category.last_used_at = current_time
            else:
                logger.warning("last_used_at column not found in weight_category table, skipping update")
        except Exception as e:
            logger.warning(f"Error checking or updating last_used_at: {str(e)}")
        
        db.session.commit()
        logger.info(f"Entry saved with ID: {entry.id}")
        return entry
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving weight entry: {str(e)}")
        raise

def delete_entry(entry_id: int) -> bool:
    """Delete an entry by ID"""
    logger.info(f"Attempting to delete entry with ID: {entry_id}")
    entry = WeightEntry.query.get(entry_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        logger.info(f"Entry with ID {entry_id} deleted successfully")
        return True
    logger.warning(f"Entry with ID {entry_id} not found for deletion")
    return False

def update_entry(
    entry_id: int,
    weight: float,
    unit: str,
    category_id: int,
    reps: Optional[int] = None
) -> Optional[WeightEntry]:
    """Update an existing weight entry
    
    Args:
        entry_id: ID of the entry to update
        weight: New weight value
        unit: Weight unit ('kg' or 'lb')
        category_id: ID of the category to assign
        reps: Number of repetitions (None for body mass entries)
        
    Returns:
        Updated entry or None if entry not found
    """
    logger.info(f"Attempting to update entry {entry_id} with weight={weight}{unit}, category_id={category_id}, reps={reps}")
    
    entry = WeightEntry.query.get(entry_id)
    if not entry:
        logger.warning(f"Entry {entry_id} not found for update")
        return None
    
    category = WeightCategory.query.get(category_id)
    if not category:
        logger.error(f"Category with ID {category_id} not found")
        raise ValueError(f"Category with ID {category_id} not found")
    
    # Check if 'is_body_weight_exercise' attribute exists to ensure backward compatibility
    is_body_weight_exercise = False
    if hasattr(category, 'is_body_weight_exercise'):
        is_body_weight_exercise = category.is_body_weight_exercise
    
    if category.is_body_mass:
        # Body Mass: ensure no reps
        if reps is not None:
            logger.warning("Body Mass entries should not have reps, ignoring reps value")
            reps = None
    elif is_body_weight_exercise:
        # Body Weight exercise: ensure has reps but use body mass for weight
        if reps is None:
            logger.warning("Body Weight exercises should have reps, defaulting to 1")
            reps = 1
            
        # For body weight exercises, use the most recent body mass entry as the weight
        most_recent_body_mass = get_most_recent_body_mass()
        if most_recent_body_mass:
            weight = most_recent_body_mass.weight
            unit = most_recent_body_mass.unit
            logger.info(f"Using body mass for body weight exercise: {weight}{unit}")
        else:
            # If no body mass entry exists, use the provided weight or default to 0
            logger.warning("No body mass entry found, using provided weight or default")
            if weight <= 0:
                weight = 70.0  # Default weight if none is provided
                unit = 'kg'    # Default unit
    else:
        # Normal exercise: ensure both weight and reps
        if reps is None:
            logger.warning("Normal exercises should have reps, defaulting to 1")
            reps = 1
    
    # Update entry values
    entry.weight = weight
    entry.unit = unit
    entry.category_id = category_id
    
    # Only update reps if the column exists
    if hasattr(entry, 'reps'):
        entry.reps = reps
    
    try:
        # Update category's last_used_at if the column exists
        if hasattr(category, 'last_used_at'):
            category.last_used_at = datetime.now(UTC)
        
        db.session.commit()
        logger.info(f"Entry {entry_id} updated successfully")
        return entry
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating entry: {str(e)}")
        raise

def get_entries_by_time_window(
    time_window: str, 
    category_id: Optional[int] = None
) -> List[WeightEntry]:
    """Get entries based on time window (week, month, year, all) and optional category"""
    logger.info(f"Retrieving entries for time window: {time_window}, category_id: {category_id}")
    try:
        now = datetime.now(UTC)
        
        # Handle potential schema issues by using a safer approach with raw SQL
        inspector = inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("weight_entry")}
        
        # Build query dynamically based on available columns
        column_list = ["id", "weight", "unit", "category_id", "created_at"]
        if "reps" in columns:
            column_list.append("reps")
            
        # Create column string for SQL
        columns_sql = ", ".join(f"weight_entry.{col}" for col in column_list)
        
        # Build base query
        query_parts = [f"SELECT {columns_sql} FROM weight_entry"]
        params = {}
        
        # Add category filter if provided
        where_clauses = []
        if category_id is not None:
            where_clauses.append("weight_entry.category_id = :category_id")
            params["category_id"] = category_id
        
        # Add time window filter
        if time_window == 'week':
            start_date = now - timedelta(days=7)
            where_clauses.append("weight_entry.created_at >= :start_date")
            params["start_date"] = start_date
        elif time_window == 'month':
            start_date = now - timedelta(days=30)
            where_clauses.append("weight_entry.created_at >= :start_date")
            params["start_date"] = start_date
        elif time_window == 'year':
            start_date = now - timedelta(days=365)
            where_clauses.append("weight_entry.created_at >= :start_date")
            params["start_date"] = start_date
        
        # Add WHERE clause if needed
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # Add ORDER BY
        query_parts.append("ORDER BY weight_entry.created_at DESC")
        
        # Execute query
        query = text(" ".join(query_parts))
        result = db.session.execute(query, params)
        
        # Convert to WeightEntry objects
        entries = []
        for row in result:
            entry_data = dict(zip(column_list, row))
            entry = WeightEntry(**entry_data)
            entry.category = WeightCategory.query.get(entry.category_id)
            entries.append(entry)
        
        logger.info(f"Retrieved {len(entries)} entries")
        return entries
    except Exception as e:
        logger.error(f"Error retrieving entries: {str(e)}")
        return []

def get_all_entries(category_id: Optional[int] = None) -> List[WeightEntry]:
    """Get all entries, optionally filtered by category"""
    logger.info(f"Retrieving all entries, category_id: {category_id}")
    try:
        query = WeightEntry.query.order_by(WeightEntry.created_at.desc())
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        entries = query.all()
        logger.info(f"Retrieved {len(entries)} entries")
        return entries
    except Exception as e:
        logger.error(f"Error retrieving entries: {str(e)}")
        return []

def convert_to_kg(weight: float, unit: str) -> float:
    """Convert weight to kg if needed"""
    if unit.lower() == 'lb':
        return weight * 0.45359237
    return weight

def create_weight_plot(
    entries: List[WeightEntry], 
    time_window: str, 
    processing_type: Optional[str] = None
) -> str:
    """Create a plotly plot of weight entries"""
    try:
        if not entries:
            logger.info("No entries to plot - creating informative empty plot")
            # Create a more informative empty plot
            fig = px.line()
            fig.add_annotation(
                text="No data available for the selected time period<br>Try selecting a different time range or add some entries",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="#7f8c8d")
            )
            fig.update_layout(
                plot_bgcolor='rgba(240,240,240,0.9)',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif", size=14),
                margin=dict(l=40, r=20, t=20, b=50),
                height=400,
                autosize=True,
                title=None,
                xaxis=dict(title="Date", showgrid=False, showticklabels=False),
                yaxis=dict(title="Weight", showgrid=False, showticklabels=False),
                showlegend=False
            )
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
        # Get category from first entry
        category = entries[0].category if entries[0].category else None
        category_name = category.name if category and hasattr(category, 'name') and category.name else "Unknown Exercise"
        
        # Determine if this is body mass or body weight exercise
        is_body_mass = False
        is_body_weight_exercise = False
        
        if category:
            is_body_mass = category.is_body_mass if hasattr(category, 'is_body_mass') else False
            if hasattr(category, 'is_body_weight_exercise'):
                is_body_weight_exercise = category.is_body_weight_exercise
        
        # Convert entries to pandas DataFrame
        data = []
        for entry in entries:
            row = {
                'date': entry.created_at,
                'weight_original': entry.weight,
                'unit': entry.unit,
                'weight_kg': convert_to_kg(entry.weight, entry.unit)
            }
            
            # Add reps if available
            if hasattr(entry, 'reps') and entry.reps is not None:
                row['reps'] = entry.reps
            
            data.append(row)
            
        df = pd.DataFrame(data)
        
        # Sort by date
        df = df.sort_values('date')
        
        # Determine default unit based on most common unit
        default_unit = df['unit'].mode().iloc[0]
        
        # Create more specific y-axis label based on the category and processing type
        if is_body_mass:
            y_axis_label = f'Body Weight ({default_unit})'
        elif is_body_weight_exercise:
            if processing_type == 'volume':
                y_axis_label = f'{category_name} Volume (Body Weight × Reps)'
            elif processing_type == 'estimated_1rm':
                y_axis_label = f'{category_name} Est. 1RM (Body Weight)'
            elif processing_type == 'reps':
                y_axis_label = f'{category_name} Reps'
            else:
                y_axis_label = f'{category_name} (Body Weight Exercise)'
        elif category_name:
            if processing_type == 'volume':
                y_axis_label = f'{category_name} Volume ({default_unit}·reps)'
            elif processing_type == 'estimated_1rm':
                y_axis_label = f'{category_name} Est. 1RM ({default_unit})'
            elif processing_type == 'reps':
                y_axis_label = f'{category_name} Reps'
            else:
                y_axis_label = f'{category_name} Weight ({default_unit})'
        else:
            # Default label if no category information is available
            y_axis_label = f'Weight ({default_unit})'
        
        # Convert all weights to the default unit
        if default_unit == 'kg':
            df['processed_value'] = df['weight_kg']
        else:  # lb
            df['processed_value'] = df['weight_kg'] * 2.20462
        
        # Apply processing if requested
        if processing_type == 'volume' and 'reps' in df.columns:
            df['processed_value'] = df['processed_value'] * df['reps']
        elif processing_type == 'estimated_1rm' and 'reps' in df.columns:
            # Brzycki formula: 1RM = weight × (36 / (37 - reps))
            # Handle negative or very large reps that could cause division by zero or negative results
            df['safe_reps'] = df['reps'].apply(lambda x: min(max(x, 0), 36))
            df['processed_value'] = df['processed_value'] * (36 / (37 - df['safe_reps']))
        elif processing_type == 'reps' and 'reps' in df.columns:
            # Plot raw reps instead of weight
            df['processed_value'] = df['reps']
        
        # If there's only one data point, duplicate it slightly offset to show a line
        if len(df) == 1:
            new_row = df.iloc[0].copy()
            # Ensure date is a datetime object before adding timedelta
            if isinstance(new_row['date'], str):
                new_row['date'] = pd.to_datetime(new_row['date'])
            new_row['date'] = new_row['date'] + timedelta(hours=1)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Y-axis value based on processing type
        y_value = 'processed_value'
        
        # Create plot
        fig = px.line(
            df, 
            x='date', 
            y=y_value,
            markers=True,
            labels={y_value: y_axis_label, 'date': 'Date'},
        )
        
        # Add enhanced trendlines using daily aggregated values (mean, max, min)
        if len(df) > 1:
            # Group by date and calculate daily aggregates
            df['date_only'] = df['date'].dt.date
            daily_stats = df.groupby('date_only')['processed_value'].agg(['mean', 'min', 'max']).reset_index()
            daily_stats['date_only'] = pd.to_datetime(daily_stats['date_only'])
            
            if len(daily_stats) > 1:
                # Create trendlines using linear regression
                try:
                    from scipy.stats import linregress
                    
                    # Convert dates to numeric values for regression
                    x_numeric = (daily_stats['date_only'] - daily_stats['date_only'].min()).dt.days
                    
                    # Mean trendline (clear/prominent)
                    slope_mean, intercept_mean, r_value_mean, _, _ = linregress(x_numeric, daily_stats['mean'])
                    trend_mean = slope_mean * x_numeric + intercept_mean
                    
                    fig.add_scatter(
                        x=daily_stats['date_only'],
                        y=trend_mean,
                        mode='lines',
                        name='Mean Trend',
                        line=dict(color='rgba(231, 76, 60, 0.8)', width=3, dash='dash'),
                        hovertemplate='Mean Trend: %{y:.1f}<br>Date: %{x|%Y-%m-%d}<extra></extra>'
                    )
                    
                    # Min trendline (faint/transparent)
                    slope_min, intercept_min, r_value_min, _, _ = linregress(x_numeric, daily_stats['min'])
                    trend_min = slope_min * x_numeric + intercept_min
                    
                    fig.add_scatter(
                        x=daily_stats['date_only'],
                        y=trend_min,
                        mode='lines',
                        name='Min Trend',
                        line=dict(color='rgba(52, 152, 219, 0.3)', width=1, dash='dot'),
                        hovertemplate='Min Trend: %{y:.1f}<br>Date: %{x|%Y-%m-%d}<extra></extra>'
                    )
                    
                    # Max trendline (faint/transparent)
                    slope_max, intercept_max, r_value_max, _, _ = linregress(x_numeric, daily_stats['max'])
                    trend_max = slope_max * x_numeric + intercept_max
                    
                    fig.add_scatter(
                        x=daily_stats['date_only'],
                        y=trend_max,
                        mode='lines',
                        name='Max Trend',
                        line=dict(color='rgba(46, 204, 113, 0.3)', width=1, dash='dot'),
                        hovertemplate='Max Trend: %{y:.1f}<br>Date: %{x|%Y-%m-%d}<extra></extra>'
                    )
                    
                    logger.info(f"Added trendlines: Mean(slope={slope_mean:.3f}, R²={r_value_mean**2:.3f}), Min(slope={slope_min:.3f}), Max(slope={slope_max:.3f})")
                    
                except ImportError:
                    logger.warning("scipy not available, skipping trendline calculation")
                except Exception as e:
                    logger.warning(f"Could not calculate trendlines: {str(e)}")
        
        # Enhanced hover information - always show comprehensive data
        # Format date in hover template to be more readable
        hovertemplate = 'Date: %{x|%Y-%m-%d}<br>'
        
        # Always show the plotted value first
        if processing_type in ('volume', 'estimated_1rm', 'reps'):
            hovertemplate += f'{y_axis_label}: %{{y:.1f}}<br>'
        
        # Always include weight and reps information when available
        customdata_cols = []
        
        if is_body_weight_exercise:
            # For body weight exercises, always show body weight and reps
            hovertemplate += 'Body Weight: %{customdata[0]:.1f} %{customdata[1]}<br>'
            customdata_cols = ['weight_original', 'unit']
            
            if 'reps' in df.columns:
                hovertemplate += 'Reps: %{customdata[2]}'
                customdata_cols.append('reps')
                
        elif is_body_mass:
            # For body mass, just show the weight (no reps)
            if processing_type not in ('volume', 'estimated_1rm', 'reps'):
                hovertemplate += 'Body Weight: %{y:.1f} %{text}'
            else:
                hovertemplate += 'Body Weight: %{customdata[0]:.1f} %{customdata[1]}'
                customdata_cols = ['weight_original', 'unit']
                
        else:
            # For regular exercises, always show both weight and reps
            hovertemplate += 'Weight: %{customdata[0]:.1f} %{customdata[1]}'
            customdata_cols = ['weight_original', 'unit']
            
            if 'reps' in df.columns:
                hovertemplate += '<br>Reps: %{customdata[2]}'
                customdata_cols.append('reps')
        
        # Apply the hover template
        if customdata_cols:
            fig.update_traces(
                customdata=df[customdata_cols],
                hovertemplate=hovertemplate + '<extra></extra>'
            )
        else:
            # Fallback for body mass when not using processed values
            fig.update_traces(
                text=df['unit'], 
                hovertemplate=hovertemplate + '<extra></extra>'
            )
        
        # Enhance plot markers for better visibility and interaction
        fig.update_traces(
            marker=dict(
                size=8,  # Larger markers for better touch/click targets
                line=dict(width=2, color='DarkSlateGrey'),  # Border around markers
                opacity=0.8
            ),
            line=dict(width=2),  # Thicker line
            hoverinfo='none',  # Use custom hovertemplate only
        )
        
        # Customize appearance for better mobile experience and hover interaction
        fig.update_layout(
            plot_bgcolor='rgba(240,240,240,0.9)',
            font=dict(family="Arial, sans-serif", size=12),  # Reduce font size for mobile
            hoverlabel=dict(
                bgcolor="white", 
                font_size=12,
                bordercolor="darkgray",
                align="left"
            ),
            margin=dict(l=40, r=20, t=20, b=50),  # Increase margins, especially bottom
            height=400,
            autosize=True,
            showlegend=False,  # Remove legend to save space
            hovermode='closest',  # Always show closest point info
            title=None,  # Explicitly remove title
        )
        
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            gridcolor='rgba(200,200,200,0.3)',
            title_font=dict(size=11),  # Smaller axis title font
            tickfont=dict(size=10),    # Smaller tick font
            automargin=True,
            fixedrange=True,  # Prevents x-axis zoom on mobile
            title_standoff=15    # Add space between title and axis
        )
        
        fig.update_yaxes(
            gridcolor='rgba(200,200,200,0.3)',
            title_font=dict(size=11),  # Smaller axis title font  
            tickfont=dict(size=10),    # Smaller tick font
            automargin=True,
            fixedrange=True,  # Prevents y-axis zoom on mobile
            title_standoff=15,   # Add space between title and axis
            side='left'          # Ensure y-axis title is on the left
        )
        
        # Convert to JSON for embedding in HTML
        logger.info("Plot created successfully")
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return plot_json
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return a fallback empty plot instead of None
        fig = px.line()
        fig.add_annotation(
            text=f"Error creating plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=14, color="#e74c3c")
        )
        fig.update_layout(
            plot_bgcolor='rgba(240,240,240,0.9)',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=14),
            margin=dict(l=40, r=20, t=20, b=50),
            height=400,
            autosize=True,
            title=None,
            xaxis=dict(title="Date", showgrid=False, showticklabels=False),
            yaxis=dict(title="Weight", showgrid=False, showticklabels=False),
            showlegend=False
        )
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_available_processing_types() -> List[Dict[str, str]]:
    """Get available processing options for weight entries"""
    return [
        {'id': 'none', 'name': 'Raw Weight'},
        {'id': 'reps', 'name': 'Raw Reps'},
        {'id': 'volume', 'name': 'Volume (Weight × Reps)'},
        {'id': 'estimated_1rm', 'name': 'Estimated 1RM'}
    ]

def migrate_old_entries_to_body_mass() -> None:
    """Migrate old entries without category to Body Mass category"""
    logger.info("Checking for entries without category to migrate")
    
    try:
        # Get or create Body Mass category
        body_mass = create_default_category()
        
        # Use raw SQL to check for the existence of the category_id column
        # to avoid accessing columns that might not exist yet
        
        # Check if entries table exists
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='weight_entry'"))
        if not result.fetchone():
            logger.info("weight_entry table doesn't exist yet, skipping migration")
            return
            
        # Check if category_id column exists
        result = db.session.execute(text("PRAGMA table_info(weight_entry)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'category_id' not in columns:
            logger.info("category_id column doesn't exist yet, skipping migration")
            return
            
        # Get entries without category_id using raw SQL to avoid ORM issues
        result = db.session.execute(text("SELECT id FROM weight_entry WHERE category_id IS NULL"))
        entry_ids = [row[0] for row in result.fetchall()]
        
        count = len(entry_ids)
        
        if count > 0:
            logger.info(f"Found {count} entries to migrate to Body Mass category")
            # Update entries in batches
            for i in range(0, count, 100):
                batch = entry_ids[i:i+100]
                id_list = ','.join(str(id) for id in batch)
                db.session.execute(text(f"UPDATE weight_entry SET category_id = {body_mass.id} WHERE id IN ({id_list})"))
            
            db.session.commit()
            logger.info(f"Successfully migrated {count} entries to Body Mass category")
        else:
            logger.info("No entries found that need migration")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        logger.info("Continuing with application startup despite migration error")

def get_most_recent_body_mass() -> Optional[WeightEntry]:
    """Get the most recent body mass entry for use in body weight exercises"""
    logger.info("Retrieving most recent body mass entry")
    
    # Find the body mass category
    body_mass_category = WeightCategory.query.filter_by(is_body_mass=True).first()
    if not body_mass_category:
        logger.warning("Body mass category not found")
        return None
    
    # Find the most recent entry
    most_recent = WeightEntry.query.filter_by(category_id=body_mass_category.id).order_by(WeightEntry.created_at.desc()).first()
    
    if most_recent:
        logger.info(f"Found most recent body mass entry: {most_recent.weight}{most_recent.unit} ({format_date(most_recent.created_at)})")
    else:
        logger.info("No body mass entries found")
    
    return most_recent 