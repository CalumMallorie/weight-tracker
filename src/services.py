from datetime import datetime, timedelta, UTC
import json
import logging
import plotly
import plotly.express as px
import pandas as pd
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Tuple

from .models import WeightEntry, WeightCategory, db

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
    reps: Optional[int] = None,
    notes: Optional[str] = None
) -> WeightEntry:
    """Save a new weight entry to the database
    
    For backwards compatibility with tests:
    - If category_id_or_notes is a string, it's treated as notes
    - If category_id_or_notes is a number, it's treated as category_id
    """
    # Special handling for tests that pass notes as 3rd parameter
    if isinstance(category_id_or_notes, str) and notes is None:
        notes = category_id_or_notes
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
    
    # Validate reps based on category
    if category.is_body_mass and reps is not None:
        logger.warning("Body Mass entries should not have reps, ignoring reps value")
        reps = None
    elif not category.is_body_mass and reps is None:
        logger.warning("Non-Body Mass entries should have reps, defaulting to 1")
        reps = 1
    
    logger.info(f"Saving new weight entry: {weight}{unit}, category: {category.name}, reps: {reps}, notes: {notes}")
    entry = WeightEntry(
        weight=weight, 
        unit=unit, 
        category_id=category_id,
        reps=reps,
        notes=notes
    )
    db.session.add(entry)
    db.session.commit()
    logger.info(f"Entry saved with ID: {entry.id}")
    return entry

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

def get_entries_by_time_window(
    time_window: str, 
    category_id: Optional[int] = None
) -> List[WeightEntry]:
    """Get entries based on time window (week, month, year, all) and optional category"""
    logger.info(f"Retrieving entries for time window: {time_window}, category_id: {category_id}")
    try:
        now = datetime.now(UTC)
        
        # Base query
        query = WeightEntry.query
        
        # Add category filter if provided
        if category_id is not None:
            query = query.filter(WeightEntry.category_id == category_id)
        
        # Add time window filter
        if time_window == 'week':
            start_date = now - timedelta(days=7)
            query = query.filter(WeightEntry.created_at >= start_date)
        elif time_window == 'month':
            start_date = now - timedelta(days=30)
            query = query.filter(WeightEntry.created_at >= start_date)
        elif time_window == 'year':
            start_date = now - timedelta(days=365)
            query = query.filter(WeightEntry.created_at >= start_date)
        
        # Execute query
        entries = query.order_by(WeightEntry.created_at).all()
        logger.info(f"Retrieved {len(entries)} entries")
        return entries
    except Exception as e:
        logger.error(f"Error retrieving entries: {str(e)}")
        # Return empty list if database hasn't been set up yet
        return []

def get_all_entries(category_id: Optional[int] = None) -> List[WeightEntry]:
    """Get all entries ordered by created date, optionally filtered by category"""
    logger.info(f"Retrieving all weight entries for category_id: {category_id}")
    
    try:
        query = WeightEntry.query
        if category_id is not None:
            query = query.filter(WeightEntry.category_id == category_id)
        
        entries = query.order_by(WeightEntry.created_at).all()
        logger.info(f"Retrieved {len(entries)} entries total")
        return entries
    except Exception as e:
        logger.error(f"Error retrieving all entries: {str(e)}")
        return []

def convert_to_kg(weight: float, unit: str) -> float:
    """Convert weight to kg if in lb"""
    if unit.lower() == 'lb':
        result = weight * 0.45359237
        logger.debug(f"Converted {weight}{unit} to {result:.2f}kg")
        return result
    return weight

def create_weight_plot(
    entries: List[WeightEntry], 
    time_window: str, 
    processing_type: Optional[str] = None
) -> Optional[str]:
    """Create a plotly plot for weight entries with optional processing"""
    logger.info(f"Creating weight plot for {len(entries)} entries in {time_window} window")
    try:
        if not entries:
            logger.info("No entries to plot, returning None")
            return None
        
        # Prepare data
        data = []
        for entry in entries:
            try:
                weight_kg = convert_to_kg(entry.weight, entry.unit)
                item = {
                    'date': entry.created_at,
                    'weight_kg': weight_kg,
                    'weight_original': entry.weight,
                    'unit': entry.unit,
                    'category': entry.category.name if hasattr(entry, 'category') and entry.category else "Unknown",
                }
                
                # Add reps field if it exists
                if hasattr(entry, 'reps'):
                    item['reps'] = entry.reps
                
                # Add calculated values if processing type is specified and reps exists
                has_reps = hasattr(entry, 'reps') and entry.reps is not None
                if processing_type == 'volume' and has_reps:
                    item['processed_value'] = entry.calculate_volume()
                    y_axis_label = 'Volume (weight × reps)'
                elif processing_type == 'estimated_1rm' and has_reps:
                    item['processed_value'] = entry.calculate_estimated_1rm()
                    y_axis_label = 'Estimated 1RM'
                else:
                    item['processed_value'] = entry.weight
                    y_axis_label = 'Weight'
                    
                data.append(item)
            except Exception as e:
                logger.error(f"Error processing entry {entry.id}: {str(e)}")
                continue
        
        if not data:
            logger.info("No valid data points to plot after processing, returning None")
            return None
            
        df = pd.DataFrame(data)
        
        if len(df) < 2:
            # Add a duplicate point slightly offset if only one point
            # This ensures a line can be drawn
            if len(df) == 1:
                logger.info("Only one data point, adding offset duplicate for line plot")
                new_row = df.iloc[0].copy()
                new_row['date'] = new_row['date'] + timedelta(hours=1)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Y-axis value based on processing type
        y_value = 'processed_value' if 'processed_value' in df.columns else 'weight_original'
        
        # Create plot
        fig = px.line(
            df, 
            x='date', 
            y=y_value,
            markers=True,
            labels={y_value: y_axis_label, 'date': 'Date'},
        )
        
        # Add custom hover text
        hovertemplate = 'Date: %{x}<br>'
        
        is_body_mass = True
        if 'category' in df.columns and len(df) > 0:
            category_val = df.iloc[0].get('category', '')
            is_body_mass = category_val == 'Body Mass'
        
        if processing_type and not is_body_mass and 'reps' in df.columns:
            hovertemplate += f'{y_axis_label}: %{{y:.1f}}<br>'
            hovertemplate += 'Weight: %{customdata[0]:.1f} %{customdata[1]}<br>'
            hovertemplate += 'Reps: %{customdata[2]}'
            customdata_cols = ['weight_original', 'unit']
            if 'reps' in df.columns:
                customdata_cols.append('reps')
            fig.update_traces(
                customdata=df[customdata_cols],
                hovertemplate=hovertemplate + '<extra></extra>'
            )
        else:
            hovertemplate += 'Weight: %{y:.1f} %{text}'
            fig.update_traces(
                text=df['unit'], 
                hovertemplate=hovertemplate + '<extra></extra>'
            )
        
        # Customize appearance for better mobile experience
        fig.update_layout(
            plot_bgcolor='rgba(240,240,240,0.9)',
            font=dict(family="Arial, sans-serif", size=14),
            hoverlabel=dict(bgcolor="white", font_size=14),
            margin=dict(l=10, r=10, t=10, b=10),
            height=400,
            autosize=True,
            hovermode='closest',
            title=None,
        )
        
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            gridcolor='rgba(200,200,200,0.3)',
            title_font=dict(size=14),
            automargin=True,
            fixedrange=True  # Prevents x-axis zoom on mobile
        )
        
        fig.update_yaxes(
            gridcolor='rgba(200,200,200,0.3)',
            title_font=dict(size=14),
            automargin=True,
            fixedrange=True  # Prevents y-axis zoom on mobile
        )
        
        # Convert to JSON for embedding in HTML
        logger.info("Plot created successfully")
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}")
        return None

def get_available_processing_types() -> List[Dict[str, str]]:
    """Get available processing options for weight entries"""
    return [
        {'id': 'none', 'name': 'None (Raw Weight)'},
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