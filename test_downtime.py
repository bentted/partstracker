#!/usr/bin/env python3
"""
Test script for Downtime functionality in Parts Tracker
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add current directory to path to import from the main script
sys.path.insert(0, '.')

# Import functions from the main script with better error handling
try:
    print("Loading main script...")
    with open('pparts tracker.py', 'r', encoding='utf-8', errors='replace') as f:
        exec(f.read())
    print("Main script loaded successfully!")
except Exception as e:
    print(f"Error loading main script: {e}")
    sys.exit(1)

def test_downtime_functions():
    """Test the downtime functions"""
    print("\nTesting Downtime Functions...")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Test downtime validation
    print("\n--- Testing downtime validation ---")
    print(f"validate_downtime_duration(30): {validate_downtime_duration(30)}")  # Should be True
    print(f"validate_downtime_duration(0): {validate_downtime_duration(0)}")    # Should be False
    print(f"validate_downtime_duration(500): {validate_downtime_duration(500)}")  # Should be False
    print(f"validate_downtime_duration('abc'): {validate_downtime_duration('abc')}")  # Should be False
    
    # Check downtime reasons are loaded
    print(f"\nDowntime reasons available: {len(downtime_reasons)}")
    print("Sample reasons:", downtime_reasons[:5])
    
    # Test saving downtime entry (if we have operators)
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Check if we have any operators
    cursor.execute('SELECT COUNT(*) FROM operators')
    operator_count = cursor.fetchone()[0]
    
    print(f"\nFound {operator_count} operators in database")
    
    if operator_count > 0:
        # Get first operator
        cursor.execute('SELECT operator_number FROM operators LIMIT 1')
        first_operator = cursor.fetchone()[0]
        
        print(f"\n--- Testing save_downtime_entry ---")
        try:
            save_downtime_entry(first_operator, "machine breakdown", 45)
            print("✓ Downtime entry saved successfully!")
        except Exception as e:
            print(f"✗ Error saving downtime: {e}")
        
        # Check downtime entries in database
        cursor.execute('SELECT COUNT(*) FROM downtime_entries')
        downtime_count = cursor.fetchone()[0]
        print(f"Total downtime entries in database: {downtime_count}")
    
    conn.close()
    
    # Test analytics with downtime
    print("\n--- Testing analytics with downtime ---")
    try:
        analytics_data = get_operator_analytics()
        print(f"Analytics data retrieved for {len(analytics_data)} operators")
        
        for data in analytics_data[:3]:  # Show first 3 operators
            print(f"Operator {data['operator_number']}: "
                  f"Downtime: {data['total_downtime_hours']:.1f}h, "
                  f"Days with downtime: {data['days_with_downtime']}")
    except Exception as e:
        print(f"Error in analytics with downtime: {e}")
    
    print("\nDowntime functions test completed!")

if __name__ == "__main__":
    test_downtime_functions()