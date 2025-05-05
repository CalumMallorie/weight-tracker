from datetime import datetime, timedelta, UTC
import json
import logging
import plotly
import plotly.express as px
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple

from .models import WeightEntry, WeightCategory, db

# Set up logger
logger = logging.getLogger(__name__)

def create_tables() -> None:
    """Create database tables if they don't exist"""
    logger.info("Creating database tables if they don't exist")
    db.create_all()
    
    # Create default 'Body Mass' category if it doesn't exist
    create_default_category()
    
    logger.info("Database tables created/verified")

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
    category_id: int = None, 
    reps: Optional[int] = None
) -> WeightEntry:
    """Save a new weight entry to the database"""
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
    
    logger.info(f"Saving new weight entry: {weight}{unit}, category: {category.name}, reps: {reps}")
    entry = WeightEntry(
        weight=weight, 
        unit=unit, 
        category_id=category_id,
        reps=reps
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

def get_all_entries(category_id: Optional[int] = None) -> List[WeightEntry]:
    """Get all entries ordered by created date, optionally filtered by category"""
    logger.info(f"Retrieving all weight entries for category_id: {category_id}")
    
    query = WeightEntry.query
    if category_id is not None:
        query = query.filter(WeightEntry.category_id == category_id)
    
    entries = query.order_by(WeightEntry.created_at).all()
    logger.info(f"Retrieved {len(entries)} entries total")
    return entries

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
    if not entries:
        logger.info("No entries to plot, returning None")
        return None
    
    # Prepare data
    data = []
    for entry in entries:
        weight_kg = convert_to_kg(entry.weight, entry.unit)
        item = {
            'date': entry.created_at,
            'weight_kg': weight_kg,
            'weight_original': entry.weight,
            'unit': entry.unit,
            'category': entry.category.name,
            'reps': entry.reps
        }
        
        # Add calculated values if processing type is specified
        if processing_type == 'volume' and entry.reps is not None:
            item['processed_value'] = entry.calculate_volume()
            y_axis_label = 'Volume (weight × reps)'
        elif processing_type == 'estimated_1rm' and entry.reps is not None:
            item['processed_value'] = entry.calculate_estimated_1rm()
            y_axis_label = 'Estimated 1RM'
        else:
            item['processed_value'] = entry.weight
            y_axis_label = 'Weight'
            
        data.append(item)
    
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
    if processing_type and not df.iloc[0].category.is_body_mass:
        hovertemplate += f'{y_axis_label}: %{{y:.1f}}<br>'
        hovertemplate += 'Weight: %{customdata[0]:.1f} %{customdata[1]}<br>'
        hovertemplate += 'Reps: %{customdata[2]}'
        fig.update_traces(
            customdata=df[['weight_original', 'unit', 'reps']],
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
    
    # Get or create Body Mass category
    body_mass = create_default_category()
    
    # Look for entries with null category_id
    entries_to_migrate = WeightEntry.query.filter(WeightEntry.category_id.is_(None)).all()
    count = len(entries_to_migrate)
    
    if count > 0:
        logger.info(f"Found {count} entries to migrate to Body Mass category")
        for entry in entries_to_migrate:
            entry.category_id = body_mass.id
            logger.debug(f"Migrated entry ID: {entry.id} to Body Mass category")
        
        db.session.commit()
        logger.info(f"Successfully migrated {count} entries to Body Mass category")
    else:
        logger.info("No entries found that need migration") 