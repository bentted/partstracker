#!/usr/bin/env python3
"""
Test script for Analytics functionality in Parts Tracker
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

def test_analytics_functions():
    """Test the analytics functions"""
    print("Testing Analytics Functions...")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Add some test data if needed
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Check if we have any operators
    cursor.execute('SELECT COUNT(*) FROM operators')
    operator_count = cursor.fetchone()[0]
    
    print(f"Found {operator_count} operators in database")
    
    # Check if we have any scrap entries
    cursor.execute('SELECT COUNT(*) FROM scrap_entries')
    scrap_count = cursor.fetchone()[0]
    
    print(f"Found {scrap_count} scrap entries in database")
    
    conn.close()
    
    # Test analytics functions
    print("\n--- Testing get_operator_analytics() ---")
    try:
        analytics_data = get_operator_analytics()
        print(f"Analytics data retrieved for {len(analytics_data)} operators")
        
        for data in analytics_data[:3]:  # Show first 3 operators
            print(f"Operator {data['operator_number']}: "
                  f"Parts: {data['estimated_parts_made']}, "
                  f"Scrap: {data['total_scrap']}, "
                  f"Efficiency: {data['efficiency_percentage']:.1f}%")
    except Exception as e:
        print(f"Error in get_operator_analytics: {e}")
    
    # Test detailed analytics if we have operators
    if operator_count > 0:
        print("\n--- Testing get_detailed_operator_analytics() ---")
        try:
            # Get first operator number
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            cursor.execute('SELECT operator_number FROM operators LIMIT 1')
            first_operator = cursor.fetchone()
            conn.close()
            
            if first_operator:
                detailed_data = get_detailed_operator_analytics(first_operator[0])
                if detailed_data:
                    print(f"Detailed analytics retrieved for operator {first_operator[0]}")
                    print(f"  - Operator ID: {detailed_data['anonymized_name']}")
                    print(f"  - Scrap entries: {len(detailed_data['detailed_entries'])}")
                    print(f"  - Daily stats: {len(detailed_data['daily_stats'])}")
                else:
                    print("No detailed analytics data available")
        except Exception as e:
            print(f"Error in get_detailed_operator_analytics: {e}")
    
    print("\nAnalytics functions test completed!")

if __name__ == "__main__":
    test_analytics_functions()