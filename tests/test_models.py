import pytest
from datetime import datetime, UTC
from src.models import WeightEntry

def test_weight_entry_creation():
    """Test creating a WeightEntry instance"""
    # Create the entry with explicit created_at to avoid default function
    test_date = datetime.now(UTC)
    entry = WeightEntry(weight=75.5, unit='kg', created_at=test_date)
    
    assert entry.weight == 75.5
    assert entry.unit == 'kg'
    assert entry.created_at == test_date

def test_weight_entry_representation():
    """Test the string representation of WeightEntry"""
    entry = WeightEntry(id=1, weight=75.5, unit='kg', created_at=datetime(2023, 1, 1, 12, 0, 0))
    
    # Check for partial match since the exact format may vary
    assert "WeightEntry(id=1, weight=75.5kg" in str(entry)
    assert "created_at=2023-01-01" in str(entry)

def test_weight_entry_to_dict():
    """Test the to_dict method of WeightEntry"""
    test_date = datetime(2023, 1, 1, 12, 0, 0)
    entry = WeightEntry(id=1, weight=75.5, unit='kg', created_at=test_date)
    
    entry_dict = entry.to_dict()
    
    assert entry_dict['id'] == 1
    assert entry_dict['weight'] == 75.5
    assert entry_dict['unit'] == 'kg'
    assert entry_dict['created_at'] == '2023-01-01' 