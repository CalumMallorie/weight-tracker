"""
Tests for x-axis tick formatting and spacing behavior
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from src.models import WeightEntry, WeightCategory, db
from src.services import create_weight_plot

pytestmark = pytest.mark.unit


class TestXAxisTickFormatting:
    """Test x-axis tick formatting and spacing"""
    
    def test_short_range_tick_formatting(self, app, default_user):
        """Test tick formatting for short date ranges (≤90 days)"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create entries spanning 30 days
            entries = []
            base_date = datetime(2024, 1, 1, 12, 0)
            for i in range(5):  # 5 entries over 28 days
                entry = WeightEntry(
                    weight=70.0 + i,
                    unit='kg',
                    category_id=category.id,
                    user_id=default_user.id,
                    created_at=base_date + timedelta(days=i * 7)  # Weekly entries
                )
                entries.append(entry)
                db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot(entries, 'month')
            plot_data = json.loads(plot_json)
            
            # Verify formatting for short ranges
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should use array mode with limited number of ticks
            assert xaxis.get('tickmode') == 'array'
            assert 'tickvals' in xaxis
            assert 'ticktext' in xaxis
            
            # Should have reasonable number of ticks (≤10)
            tick_count = len(xaxis.get('tickvals', []))
            assert tick_count <= 10
            assert tick_count >= 1
            
    def test_medium_range_tick_formatting(self, app, default_user):
        """Test tick formatting for medium date ranges (90-150 days)"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create entries spanning 120 days
            entries = []
            base_date = datetime(2024, 1, 1, 12, 0)
            for i in range(8):  # 8 entries over 119 days
                entry = WeightEntry(
                    weight=70.0 + i,
                    unit='kg',
                    category_id=category.id,
                    user_id=default_user.id,
                    created_at=base_date + timedelta(days=i * 17)  # Every ~2.5 weeks
                )
                entries.append(entry)
                db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot(entries, 'all')
            plot_data = json.loads(plot_json)
            
            # Verify formatting for medium ranges
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should use array mode with limited number of ticks
            assert xaxis.get('tickmode') == 'array'
            tick_count = len(xaxis.get('tickvals', []))
            assert tick_count <= 10
            assert tick_count >= 1
            
    def test_long_range_tick_formatting(self, app, default_user):
        """Test tick formatting for long date ranges (150-365 days)"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create entries spanning 10 months
            entries = []
            base_date = datetime(2024, 1, 1, 12, 0)
            for i in range(10):  # 10 monthly entries
                entry = WeightEntry(
                    weight=70.0 + i,
                    unit='kg',
                    category_id=category.id,
                    user_id=default_user.id,
                    created_at=base_date + timedelta(days=i * 30)  # Monthly entries
                )
                entries.append(entry)
                db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot(entries, 'all')
            plot_data = json.loads(plot_json)
            
            # Verify formatting for long ranges
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should use array mode with limited ticks for long range
            assert xaxis.get('tickmode') == 'array'
            tick_count = len(xaxis.get('tickvals', []))
            assert tick_count <= 10
            assert tick_count >= 1
            
    def test_very_long_range_tick_formatting(self, app, default_user):
        """Test tick formatting for very long date ranges (>365 days)"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create entries spanning 2 years
            entries = []
            base_date = datetime(2022, 1, 1, 12, 0)
            for i in range(8):  # 8 quarterly entries over 2 years
                entry = WeightEntry(
                    weight=70.0 + i,
                    unit='kg',
                    category_id=category.id,
                    user_id=default_user.id,
                    created_at=base_date + timedelta(days=i * 90)  # Quarterly entries
                )
                entries.append(entry)
                db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot(entries, 'all')
            plot_data = json.loads(plot_json)
            
            # Verify formatting for very long ranges
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should use array mode with limited ticks for 2-year range
            assert xaxis.get('tickmode') == 'array'
            tick_count = len(xaxis.get('tickvals', []))
            assert tick_count <= 10
            assert tick_count >= 1
    
    def test_tick_overlap_prevention(self, app, default_user):
        """Test that tick configuration prevents overlapping"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create many entries over short period to test density
            entries = []
            base_date = datetime(2024, 1, 1, 12, 0)
            for i in range(15):  # 15 entries over 14 days (high density)
                entry = WeightEntry(
                    weight=70.0 + i * 0.1,
                    unit='kg',
                    category_id=category.id,
                    user_id=default_user.id,
                    created_at=base_date + timedelta(days=i)  # Daily entries
                )
                entries.append(entry)
                db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot(entries, 'all')
            plot_data = json.loads(plot_json)
            
            # Verify tick spacing prevents overlapping
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should use array mode with limited ticks to prevent overlapping
            assert xaxis.get('tickmode') == 'array'
            tick_count = len(xaxis.get('tickvals', []))
            assert tick_count <= 10
            assert tick_count >= 1
            
            # Should have auto margins and appropriate angle
            assert xaxis.get('automargin') is True
            assert isinstance(xaxis.get('tickangle'), (int, float))  # Should be numeric angle
    
    def test_optimal_tick_count(self, app, default_user):
        """Test that tick count stays within optimal range"""
        with app.app_context():
            # Create test category
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            # Test various date ranges to ensure reasonable tick counts
            test_cases = [
                (7, 'week'),      # 1 week
                (30, 'month'),    # 1 month  
                (90, 'all'),      # 3 months
                (180, 'all'),     # 6 months
                (365, 'year'),    # 1 year
                (730, 'all'),     # 2 years
            ]
            
            for days, time_window in test_cases:
                # Clear previous entries
                WeightEntry.query.filter_by(category_id=category.id).delete()
                db.session.commit()
                
                # Create entries for this test case
                entries = []
                base_date = datetime(2024, 1, 1, 12, 0)
                num_entries = max(5, days // 7)  # At least 5 entries, roughly weekly
                
                for i in range(num_entries):
                    entry = WeightEntry(
                        weight=70.0 + i * 0.1,
                        unit='kg',
                        category_id=category.id,
                        user_id=default_user.id,
                        created_at=base_date + timedelta(days=(i * days) // num_entries)
                    )
                    entries.append(entry)
                    db.session.add(entry)
                db.session.commit()
                
                plot_json = create_weight_plot(entries, time_window)
                plot_data = json.loads(plot_json)
                
                # Verify reasonable configuration
                layout = plot_data['layout']
                xaxis = layout['xaxis']
                
                # All plots should have these anti-overlap properties
                assert xaxis.get('automargin') is True
                assert isinstance(xaxis.get('tickangle'), (int, float))  # Should be numeric angle
                
                # Should use array mode with hard tick limit
                assert xaxis.get('tickmode') == 'array'
                tick_count = len(xaxis.get('tickvals', []))
                assert tick_count <= 10
                assert tick_count >= 1
    
    def test_mobile_responsive_settings(self, app, default_user):
        """Test that x-axis settings are mobile-responsive"""
        with app.app_context():
            # Create test category and entry
            category = WeightCategory(name="Test Exercise", user_id=default_user.id)
            db.session.add(category)
            db.session.commit()
            
            entry = WeightEntry(
                weight=70.0,
                unit='kg',
                category_id=category.id,
                user_id=default_user.id
            )
            db.session.add(entry)
            db.session.commit()
            
            plot_json = create_weight_plot([entry], 'all')
            plot_data = json.loads(plot_json)
            
            # Verify mobile-friendly settings
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should have mobile-responsive properties
            assert xaxis.get('automargin') is True
            assert xaxis.get('fixedrange') is True  # Prevents zoom on mobile
            assert isinstance(xaxis.get('tickangle'), (int, float))  # Should be a numeric angle
            
            # Font sizes should be appropriate for mobile
            assert xaxis.get('tickfont', {}).get('size') == 10
            # Check title font configuration - it might be under different key
            title_font = xaxis.get('title_font') or xaxis.get('titlefont', {})
            if title_font:
                assert title_font.get('size') == 11

    def test_empty_data_x_axis_handling(self, app):
        """Test x-axis behavior with empty data"""
        with app.app_context():
            plot_json = create_weight_plot([], 'all')
            plot_data = json.loads(plot_json)
            
            # Should still have proper x-axis configuration
            layout = plot_data['layout']
            xaxis = layout['xaxis']
            
            # Should have basic mobile-friendly settings even with no data
            assert 'title' in xaxis
            assert xaxis.get('showgrid') is False
            assert xaxis.get('tickcolor') == '#e0e0e0'  # Dark mode colors
            assert xaxis.get('linecolor') == '#e0e0e0'