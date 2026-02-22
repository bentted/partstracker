#!/usr/bin/env python3

import random
import sqlite3
from datetime import datetime

scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]

# Admin credentials
ADMIN_CREDENTIALS = {
    "admin": "admin123",
    "supervisor": "super456"
}

def authenticate_admin(username, password):
    return ADMIN_CREDENTIALS.get(username) == password

def init_database():
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrap_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_number INTEGER NOT NULL,
            part_number TEXT NOT NULL,
            order_number INTEGER NOT NULL,
            scrap_reason TEXT NOT NULL,
            scrap_count INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_scrap_entry(operator_number, part_number, order_number, scrap_reason, scrap_count):
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO scrap_entries 
        (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp))
    
    conn.commit()
    conn.close()

class Order:
    _next_order_number = 1

    def __init__(self, part_number, parts_per_order):
        self.order_number = Order._next_order_number
        Order._next_order_number += 1
        self.part_number = part_number
        self.parts_per_order = parts_per_order

def main():
    print("\n=== PARTS TRACKER - COMMAND LINE VERSION ===")
    print("This is a command-line version of the Parts Tracker application.")
    print("Available admin credentials:")
    print("  Username: admin, Password: admin123")
    print("  Username: supervisor, Password: super456")
    
    # Initialize database
    init_database()
    print("Database initialized successfully.")
    
    # Simple login
    print("\nLogin:")
    user_type = input("Enter 'admin' for administrator or 'operator' for operator: ").lower().strip()
    
    if user_type == "admin":
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        if authenticate_admin(username, password):
            print(f"Welcome, Administrator {username}!")
            admin_interface()
        else:
            print("Invalid credentials!")
            return
    else:
        try:
            operator_input = input("Enter operator number (0-9999): ").strip()
            operator_num = int(operator_input)
            if 0 <= operator_num <= 9999:
                print(f"Welcome, Operator {operator_num}!")
                operator_interface(operator_num)
            else:
                print("Invalid operator number!")
                return
        except ValueError:
            print("Invalid operator number!")
            return

def admin_interface():
    """Command-line interface for administrators"""
    while True:
        print("\n=== ADMIN MENU ===")
        print("1. Create new order")
        print("2. View recent scrap entries")
        print("3. Exit")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            create_order()
        elif choice == "2":
            view_scrap_entries()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

def operator_interface(operator_num):
    """Command-line interface for operators"""
    while True:
        print(f"\n=== OPERATOR MENU (Operator {operator_num}) ===")
        print("1. Track scrap for existing order")
        print("2. View my recent scrap entries")
        print("3. Exit")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            track_scrap(operator_num)
        elif choice == "2":
            view_operator_scrap_entries(operator_num)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

def create_order():
    """Command-line order creation"""
    print("\n=== CREATE NEW ORDER ===")
    
    print("Available part numbers:", ", ".join(part_numbers))
    part_number = input("Enter part number: ").strip()
    
    if part_number not in part_numbers:
        print("Invalid part number!")
        return
    
    mix_number = input("Enter mix number: ").strip()
    if not mix_number:
        print("Mix number is required!")
        return
        
    part_number_full = part_number + mix_number
    
    order_quantity = random.randint(110, 5000)
    order = Order(part_number_full, order_quantity)
    
    print(f"\nOrder created successfully!")
    print(f"Order Number: {order.order_number}")
    print(f"Part: {part_number_full}")
    print(f"Quantity: {order_quantity}")

def track_scrap(operator_num):
    """Command-line scrap tracking"""
    print("\n=== TRACK SCRAP ===")
    
    try:
        order_number = int(input("Enter order number: ").strip())
        parts_made = int(input("Enter parts made: ").strip())
        
        if parts_made < 0:
            print("Parts made cannot be negative!")
            return
            
    except ValueError:
        print("Invalid input! Please enter numbers only.")
        return
    
    print(f"\nAvailable scrap reasons: {', '.join(scrap_reasons)}")
    
    total_scrap = 0
    scrap_entries = []
    
    while True:
        reason = input("\nEnter scrap reason (or 'done' to finish): ").strip()
        
        if reason.lower() == 'done':
            break
            
        if reason not in scrap_reasons:
            print("Invalid scrap reason!")
            continue
        
        try:
            count = int(input(f"Enter scrap count for '{reason}': ").strip())
            if count < 0:
                print("Scrap count cannot be negative!")
                continue
                
            if total_scrap + count > parts_made:
                print(f"Total scrap ({total_scrap + count}) cannot exceed parts made ({parts_made})!")
                continue
                
            total_scrap += count
            scrap_entries.append((reason, count))
            
            # Save to database
            save_scrap_entry(operator_num, f"Order{order_number}", order_number, reason, count)
            print(f"✓ Added {count} parts for '{reason}'. Total scrap so far: {total_scrap}")
            
        except ValueError:
            print("Invalid count! Please enter a number.")
    
    good_parts = parts_made - total_scrap
    
    print(f"\n=== SCRAP SUMMARY ===")
    print(f"Order Number: {order_number}")
    print(f"Parts Made: {parts_made}")
    print("Scrap Breakdown:")
    for reason, count in scrap_entries:
        print(f"  {reason}: {count} parts")
    print(f"Total Scrap: {total_scrap}")
    print(f"Good Parts: {good_parts}")
    print("✓ All data saved to database.")

def view_scrap_entries():
    """View recent scrap entries (admin)"""
    print("\n=== RECENT SCRAP ENTRIES ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp
        FROM scrap_entries
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        for entry in entries:
            op_num, part, order, reason, count, timestamp = entry
            print(f"{timestamp} | Operator {op_num} | Order {order} | Part {part} | {reason}: {count} parts")
    else:
        print("No scrap entries found.")

def view_operator_scrap_entries(operator_num):
    """View scrap entries for specific operator"""
    print(f"\n=== YOUR RECENT SCRAP ENTRIES (Operator {operator_num}) ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT part_number, order_number, scrap_reason, scrap_count, timestamp
        FROM scrap_entries
        WHERE operator_number = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (operator_num,))
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        for entry in entries:
            part, order, reason, count, timestamp = entry
            print(f"{timestamp} | Order {order} | Part {part} | {reason}: {count} parts")
    else:
        print("No scrap entries found for your operator number.")

if __name__ == "__main__":
    main()