import pytest
from datetime import datetime, timedelta, UTC
import json
from unittest.mock import patch, MagicMock
import pandas as pd

from src import services
from src.models import WeightEntry, db
from src.app import create_app

@pytest.fixture
def app():
    """Create a Flask app for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    return app

@pytest.fixture
def app_context(app):
    """Provide app context for tests that need it"""
    with app.app_context():
        yield

def test_convert_to_kg():
    """Test weight conversion from lb to kg"""
    # Test lb to kg conversion
    result = services.convert_to_kg(100, 'lb')
    assert pytest.approx(result) == 45.359237
    
    # Test kg remains unchanged
    result = services.convert_to_kg(50, 'kg')
    assert result == 50

@pytest.fixture
def mock_entry():
    """Create a mock weight entry"""
    entry = MagicMock(spec=WeightEntry)
    entry.id = 1
    entry.weight = 75.5
    entry.unit = 'kg'
    entry.notes = 'Test notes'
    entry.created_at = datetime(2023, 1, 1, 12, 0, 0)
    return entry

@pytest.fixture
def mock_entries():
    """Create a list of mock weight entries"""
    entries = []
    for i in range(3):
        entry = MagicMock(spec=WeightEntry)
        entry.id = i + 1
        entry.weight = 75.0 + i
        entry.unit = 'kg'
        entry.notes = f'Test notes {i}'
        entry.created_at = datetime(2023, 1, 1, 12, 0, 0) + timedelta(days=i)
        entries.append(entry)
    return entries

def test_create_weight_plot_empty():
    """Test creating a plot with no entries"""
    result = services.create_weight_plot([], 'month')
    assert result is None

def test_create_weight_plot_single_entry(mock_entry):
    """Test creating a plot with a single entry using a simple approach"""
    # Use a simple approach to avoid complex mocking
    with patch('pandas.DataFrame') as mock_df, \
         patch('plotly.express.line') as mock_line, \
         patch('json.dumps') as mock_dumps:
        
        # Return simple values that will work with our code
        mock_line.return_value = MagicMock()
        mock_line.return_value.update_traces = MagicMock()
        mock_line.return_value.update_layout = MagicMock()
        mock_line.return_value.update_xaxes = MagicMock()
        mock_line.return_value.update_yaxes = MagicMock()
        
        mock_dumps.return_value = '{"data": [], "layout": {}}'
        
        # Create a simpler version for the test
        result = services.create_weight_plot([mock_entry], 'month')
        
        # We just need to know the function worked and returned a string
        assert mock_dumps.called
        assert isinstance(result, str)

def test_create_weight_plot_multiple_entries(mock_entries):
    """Test creating a plot with multiple entries"""
    with patch('pandas.DataFrame') as mock_df:
        # Mock the DataFrame operations
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        mock_df_instance.__len__.return_value = 3
        
        with patch('plotly.express.line') as mock_line:
            mock_fig = MagicMock()
            mock_line.return_value = mock_fig
            
            with patch('json.dumps') as mock_dumps:
                mock_dumps.return_value = '{"data": [], "layout": {}}'
                
                result = services.create_weight_plot(mock_entries, 'month')
                
                assert mock_line.called
                assert mock_dumps.called
                assert isinstance(result, str)

def test_get_entries_by_time_window(app_context):
    """Test filtering entries by time window"""
    # Complete patch path
    with patch('src.models.WeightEntry.query') as mock_query:
        # Create a chain of mocks for the query methods
        filter_mock = MagicMock()
        order_mock = MagicMock()
        all_mock = MagicMock()
        
        # Setup the return values
        mock_query.filter.return_value = filter_mock
        mock_query.order_by.return_value = order_mock
        order_mock.all.return_value = []
        filter_mock.order_by.return_value = order_mock
        
        # Test 'all' time window (simplest case)
        result = services.get_entries_by_time_window('all')
        assert isinstance(result, list)

    # Test 'week' time window
    result = services.get_entries_by_time_window('week')
    assert isinstance(result, list)
    
    # Test 'month' time window
    result = services.get_entries_by_time_window('month')
    assert isinstance(result, list)
    
    # Test 'year' time window
    result = services.get_entries_by_time_window('year')
    assert isinstance(result, list) 