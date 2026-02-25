#!/usr/bin/env python3
"""
Test script for SMC (Sheet Moulding Compound) Scrap functionality in Parts Tracker
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

def test_smc_scrap_functions():
    """Test the SMC (Sheet Moulding Compound) scrap functions"""
    print("\nTesting SMC (Sheet Moulding Compound) Scrap Functions...")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Test SMC scrap validation
    print("\n--- Testing SMC scrap validation ---")
    print(f"validate_smc_scrap_count(50): {validate_smc_scrap_count(50)}")  # Should be True
    print(f"validate_smc_scrap_count(-5): {validate_smc_scrap_count(-5)}")  # Should be False
    print(f"validate_smc_scrap_count(1000000): {validate_smc_scrap_count(1000000)}")  # Should be False
    print(f"validate_smc_scrap_count('abc'): {validate_smc_scrap_count('abc')}")  # Should be False
    
    # Check SMC scrap reasons are loaded
    print(f"\nSMC scrap reasons available: {len(smc_scrap_reasons)}")
    print("Sample SMC scrap reasons:", smc_scrap_reasons[:5])
    
    # Test saving SMC scrap entry (if we have operators)
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
        
        print(f"\n--- Testing save_smc_scrap_entry ---")
        try:
            save_smc_scrap_entry(first_operator, "Hood-Panel-001", "incomplete fill", 15)
            print("✓ SMC scrap entry saved successfully!")
        except Exception as e:
            print(f"✗ Error saving SMC scrap: {e}")
        
        # Check SMC scrap entries in database
        cursor.execute('SELECT COUNT(*) FROM smc_scrap_entries')
        smc_scrap_count = cursor.fetchone()[0]
        print(f"Total SMC scrap entries in database: {smc_scrap_count}")
    
    conn.close()
    
    # Test analytics with SMC scrap
    print("\n--- Testing analytics with SMC scrap ---")
    try:
        analytics_data = get_operator_analytics()
        print(f"Analytics data retrieved for {len(analytics_data)} operators")
        
        for data in analytics_data[:3]:  # Show first 3 operators
            print(f"Operator {data['operator_number']}: "
                  f"SMC Scrap: {data['total_smc_scrap']}, "
                  f"Part types: {data['part_types_worked']}")
    except Exception as e:
        print(f"Error in analytics with SMC scrap: {e}")
    
    # Test detailed analytics
    if operator_count > 0:
        print("\n--- Testing detailed analytics with SMC scrap ---")
        try:
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            cursor.execute('SELECT operator_number FROM operators LIMIT 1')
            first_operator = cursor.fetchone()[0]
            conn.close()
            
            detailed_data = get_detailed_operator_analytics(first_operator)
            if detailed_data and 'smc_scrap_entries' in detailed_data:
                print(f"Detailed SMC scrap data retrieved for operator {first_operator}")
                print(f"  - SMC scrap entries: {len(detailed_data['smc_scrap_entries'])}")
                print(f"  - Daily SMC scrap stats: {len(detailed_data['daily_smc_scrap_stats'])}")
            else:
                print("No SMC scrap detailed data available")
        except Exception as e:
            print(f"Error in detailed analytics with SMC scrap: {e}")
    
    print("\nSMC (Sheet Moulding Compound) scrap functions test completed!")

if __name__ == "__main__":
    test_smc_scrap_functions()