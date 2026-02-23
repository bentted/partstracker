#!/usr/bin/env python3
import sys
import os

print("Python Parts Tracker Test")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    print("Testing imports...")
    import random
    import sqlite3
    from datetime import datetime
    print("✓ Basic imports successful")
    
    import tkinter as tk
    print("✓ Tkinter import successful")
    
    from tkinter import ttk, messagebox, scrolledtext, simpledialog
    print("✓ Tkinter modules import successful")
    
    print("\nTesting database creation...")
    # Test database functionality
    conn = sqlite3.connect('test_parts_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            test_data TEXT
        )
    ''')
    cursor.execute("INSERT INTO test_table (test_data) VALUES ('test')")
    conn.commit()
    conn.close()
    print("✓ Database operations successful")
    
    print("\nAttempting to create simple GUI window...")
    root = tk.Tk()
    root.title("Test GUI")
    root.geometry("200x100")
    
    label = ttk.Label(root, text="GUI Test Successful!")
    label.pack()
    
    # Destroy window after 2 seconds
    root.after(2000, root.destroy)
    root.mainloop()
    print("✓ GUI window created and closed successfully")
    
    print("\nAll tests passed! The application should work correctly.")
    
except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")