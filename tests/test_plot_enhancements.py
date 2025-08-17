"""
Tests for plot enhancement features including persistence and enhanced hover information.
"""

import pytest
import json
from src.services import create_weight_plot, save_weight_entry, get_or_create_category
from src.models import WeightEntry, WeightCategory
from datetime import datetime, timedelta


def test_enhanced_hover_information_regular_exercise(app, default_user):
    """Test that regular exercises show weight, reps, and date in hover"""
    with app.app_context():
        # Create a regular exercise category
        category = get_or_create_category("Bench Press", user_id=default_user.id, is_body_mass=False)
        
        # Add a test entry
        save_weight_entry(100.0, "kg", category.id, 10, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check that hover template includes date, weight, and reps
        hover_template = plot_data['data'][0]['hovertemplate']
        assert 'Date: %{x|%Y-%m-%d}' in hover_template
        assert 'Weight: %{customdata[0]:.1f} %{customdata[1]}' in hover_template
        assert 'Reps: %{customdata[2]}' in hover_template


def test_enhanced_hover_information_body_weight_exercise(app, default_user):
    """Test that body weight exercises show body weight, reps, and date in hover"""
    with app.app_context():
        # Create body mass category first
        body_mass = get_or_create_category("Body Mass", user_id=default_user.id, is_body_mass=True)
        save_weight_entry(75.0, "kg", body_mass.id, None, user_id=default_user.id)
        
        # Create a body weight exercise category
        category = get_or_create_category("Push-ups", user_id=default_user.id, is_body_mass=False)
        if hasattr(category, 'is_body_weight_exercise'):
            category.is_body_weight_exercise = True
            from src import services
            services.db.session.commit()
        
        # Add a test entry (will use body mass for weight)
        save_weight_entry(0, "kg", category.id, 15, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check that hover template includes date, body weight, and reps
        hover_template = plot_data['data'][0]['hovertemplate']
        assert 'Date: %{x|%Y-%m-%d}' in hover_template
        assert 'Body Weight: %{customdata[0]:.1f} %{customdata[1]}' in hover_template
        assert 'Reps: %{customdata[2]}' in hover_template


def test_enhanced_hover_information_body_mass(app, default_user):
    """Test that body mass entries show date and weight in hover"""
    with app.app_context():
        # Create body mass category
        category = get_or_create_category("Body Mass", user_id=default_user.id, is_body_mass=True)
        
        # Add a test entry
        save_weight_entry(75.0, "kg", category.id, None, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check that hover template includes date and weight (no reps)
        hover_template = plot_data['data'][0]['hovertemplate']
        assert 'Date: %{x|%Y-%m-%d}' in hover_template
        assert 'Body Weight: %{y:.1f} %{text}' in hover_template
        assert 'Reps:' not in hover_template  # Should not show reps for body mass


def test_enhanced_hover_with_volume_processing(app, default_user):
    """Test that volume processing shows the calculated value plus original data"""
    with app.app_context():
        # Create a regular exercise category
        category = get_or_create_category("Deadlift", user_id=default_user.id, is_body_mass=False)
        
        # Add a test entry
        save_weight_entry(150.0, "kg", category.id, 8, user_id=default_user.id)
        
        # Get entries and create plot with volume processing
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'volume')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check that hover template shows volume value and original data
        hover_template = plot_data['data'][0]['hovertemplate']
        assert 'Date: %{x|%Y-%m-%d}' in hover_template
        assert 'Volume' in hover_template  # Should show volume in the y-axis label
        assert 'Weight: %{customdata[0]:.1f} %{customdata[1]}' in hover_template
        assert 'Reps: %{customdata[2]}' in hover_template


def test_plot_marker_enhancement(app, default_user):
    """Test that plot markers are enhanced for better visibility"""
    with app.app_context():
        # Create a test category and entry
        category = get_or_create_category("Test Exercise", user_id=default_user.id, is_body_mass=False)
        save_weight_entry(50.0, "kg", category.id, 5, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check marker properties
        trace = plot_data['data'][0]
        assert 'marker' in trace
        assert trace['marker']['size'] == 8  # Larger markers
        assert trace['marker']['line']['width'] == 2  # Border around markers
        assert trace['marker']['opacity'] == 0.8
        
        # Check line properties
        assert trace['line']['width'] == 2  # Thicker line
        
        # Check hover settings
        assert trace['hoverinfo'] == 'none'  # Custom template only


def test_hover_date_formatting(app, default_user):
    """Test that dates are properly formatted in hover"""
    with app.app_context():
        # Create a test category and entry
        category = get_or_create_category("Test Exercise", user_id=default_user.id, is_body_mass=False)
        save_weight_entry(50.0, "kg", category.id, 5, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check that date formatting uses the proper format string
        hover_template = plot_data['data'][0]['hovertemplate']
        assert '%{x|%Y-%m-%d}' in hover_template  # Should format date as YYYY-MM-DD


def test_hover_layout_settings(app, default_user):
    """Test that hover layout settings are properly configured"""
    with app.app_context():
        # Create a test category and entry
        category = get_or_create_category("Test Exercise", user_id=default_user.id, is_body_mass=False)
        save_weight_entry(50.0, "kg", category.id, 5, user_id=default_user.id)
        
        # Get entries and create plot
        entries = WeightEntry.query.filter_by(category_id=category.id, user_id=default_user.id).all()
        plot_json = create_weight_plot(entries, 'all', 'none')
        
        # Parse the plot JSON
        plot_data = json.loads(plot_json)
        
        # Check hover label settings
        layout = plot_data['layout']
        assert 'hoverlabel' in layout
        assert layout['hoverlabel']['bgcolor'] == '#3a3a3a'
        # Check font settings (plotly may use 'font' dict instead of 'font_size')
        if 'font_size' in layout['hoverlabel']:
            assert layout['hoverlabel']['font_size'] == 12
        elif 'font' in layout['hoverlabel']:
            assert layout['hoverlabel']['font']['size'] == 12
        assert layout['hoverlabel']['bordercolor'] == '#555'
        assert layout['hoverlabel']['align'] == 'left'
        
        # Check hovermode
        assert layout['hovermode'] == 'closest' 