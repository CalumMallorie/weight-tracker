from datetime import datetime, timedelta, UTC
import json
import plotly
import plotly.express as px
import pandas as pd
from typing import List, Optional, Dict, Any

from models import WeightEntry, db

def create_tables() -> None:
    """Create database tables if they don't exist"""
    db.create_all()

def save_weight_entry(weight: float, unit: str, notes: str = None) -> WeightEntry:
    """Save a new weight entry to the database"""
    entry = WeightEntry(weight=weight, unit=unit, notes=notes)
    db.session.add(entry)
    db.session.commit()
    return entry

def delete_entry(entry_id: int) -> bool:
    """Delete an entry by ID"""
    entry = WeightEntry.query.get(entry_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return True
    return False

def get_entries_by_time_window(time_window: str) -> List[WeightEntry]:
    """Get entries based on time window (week, month, year, all)"""
    now = datetime.now(UTC)
    
    if time_window == 'week':
        start_date = now - timedelta(days=7)
    elif time_window == 'month':
        start_date = now - timedelta(days=30)
    elif time_window == 'year':
        start_date = now - timedelta(days=365)
    else:  # 'all' or any other value
        return WeightEntry.query.order_by(WeightEntry.created_at).all()
    
    return WeightEntry.query.filter(
        WeightEntry.created_at >= start_date
    ).order_by(WeightEntry.created_at).all()

def get_all_entries() -> List[WeightEntry]:
    """Get all entries ordered by created date"""
    return WeightEntry.query.order_by(WeightEntry.created_at).all()

def convert_to_kg(weight: float, unit: str) -> float:
    """Convert weight to kg if in lb"""
    if unit.lower() == 'lb':
        return weight * 0.45359237
    return weight

def create_weight_plot(entries: List[WeightEntry], time_window: str) -> Optional[str]:
    """Create a plotly plot for weight entries"""
    if not entries:
        return None
    
    # Prepare data
    data = []
    for entry in entries:
        weight_kg = convert_to_kg(entry.weight, entry.unit)
        data.append({
            'date': entry.created_at,
            'weight_kg': weight_kg,
            'weight_original': entry.weight,
            'unit': entry.unit
        })
    
    df = pd.DataFrame(data)
    
    if len(df) < 2:
        # Add a duplicate point slightly offset if only one point
        # This ensures a line can be drawn
        if len(df) == 1:
            new_row = df.iloc[0].copy()
            new_row['date'] = new_row['date'] + timedelta(hours=1)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Create plot with both units
    fig = px.line(
        df, 
        x='date', 
        y='weight_original',
        markers=True,
        labels={'weight_original': 'Weight', 'date': 'Date'},
    )
    
    # Add custom hover text with original units
    hovertemplate = 'Date: %{x}<br>Weight: %{y:.1f} %{text}<extra></extra>'
    fig.update_traces(text=df['unit'], hovertemplate=hovertemplate)
    
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
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) 