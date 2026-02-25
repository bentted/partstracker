#!/usr/bin/env python3

import random
import sqlite3
from datetime import datetime, timedelta
import hashlib
import time
import re
import sys

# Fix console encoding issues on Windows
if sys.platform.startswith('win'):
    try:
        # Try to set UTF-8 encoding for console output  
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        # If that fails, just continue with default encoding
        pass

# Updated scrap reasons
scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]

# Downtime reasons for operator logging
downtime_reasons = [
    "mechanical issue", "material shortage", "quality hold", "maintenance", 
    "setup/changeover", "training", "meeting", "break", "lunch", 
    "waiting for work", "tooling issue", "power outage", "other"
]

# SMC (Sheet Moulding Compound) scrap reasons
smc_scrap_reasons = [
    "incomplete fill", "flash/excess material", "air bubbles/voids", "surface defects", 
    "dimensional out of spec", "fiber showing", "delamination", "warp/distortion", 
    "contamination", "cure issues", "tool marks", "gelcoat defects", 
    "resin starved areas", "overpacking", "sink marks", "cracking"
]

# Security configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
MIN_LOGIN_DELAY_SECONDS = 1

# Input validation limits
MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_LENGTH = 128
MAX_OPERATOR_NAME_LENGTH = 100
MAX_MIX_LENGTH = 10


def sanitize_input(input_string, max_length=None, input_type='general'):
    """Sanitize user input to prevent injection attacks"""
    if input_string is None:
        return ""
    
    # Convert to string and strip whitespace
    sanitized = str(input_string).strip()
    
    # Apply length limit if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Apply different sanitization based on input type
    if input_type == 'operator_name':
        # More permissive for operator names - allow letters, numbers, spaces, apostrophes, hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9\s\'\-\.]', '', sanitized)
    elif input_type == 'numeric':
        # For numeric inputs, only allow digits
        sanitized = re.sub(r'[^0-9]', '', sanitized)
    else:
        # Default sanitization - allow alphanumeric, spaces, and safe special characters
        sanitized = re.sub(r'[^\w\s\-\.\@\!\?]', '', sanitized)
    
    return sanitized


def validate_operator_number(op_number):
    """Validate operator number input"""
    try:
        num = int(op_number)
        return 0 <= num <= 9999
    except (ValueError, TypeError):
        return False


def validate_parts_count(parts_count):
    """Validate parts count input"""
    try:
        count = int(parts_count)
        return 0 <= count <= 999999  # Reasonable upper limit
    except (ValueError, TypeError):
        return False


def validate_downtime_duration(duration_minutes):
    """Validate downtime duration input"""
    try:
        minutes = int(duration_minutes)
        return 1 <= minutes <= 480  # 1 minute to 8 hours (1 shift)
    except (ValueError, TypeError):
        return False


def validate_smc_scrap_count(smc_count):
    """Validate SMC scrap count input"""
    try:
        count = int(smc_count)
        return 0 <= count <= 999999  # Reasonable upper limit
    except (ValueError, TypeError):
        return False


def authenticate_admin(username, password):
    """Secure admin authentication with brute force protection"""
    
    # Input validation and sanitization
    if not username or not password:
        return False
    
    username = sanitize_input(username, MAX_USERNAME_LENGTH)
    password = sanitize_input(password, MAX_PASSWORD_LENGTH)
    
    if not username or not password:
        return False
    
    # Check for account lockout
    if is_account_locked(username):
        print("Account temporarily locked due to too many failed attempts. Try again later.")
        return False
    
    # Add minimum delay to prevent rapid brute force attempts
    time.sleep(MIN_LOGIN_DELAY_SECONDS)
    
    # Check credentials against database
    is_valid = verify_admin_credentials(username, password)
    
    # Log the attempt
    log_login_attempt(username, is_valid, 'admin')
    
    return is_valid


def verify_admin_credentials(username, password):
    """Verify admin credentials against database"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Hash the username and password
    hashed_username = hashlib.sha256(username.encode()).hexdigest()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('''
        SELECT COUNT(*) FROM admin_credentials 
        WHERE username_hash = ? AND password_hash = ?
    ''', (hashed_username, hashed_password))
    
    is_valid = cursor.fetchone()[0] > 0
    conn.close()
    
    return is_valid


def is_account_locked(username):
    """Check if account is currently locked due to failed attempts"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Get recent failed attempts
    lockout_time = datetime.now() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    cursor.execute('''
        SELECT COUNT(*) FROM login_attempts 
        WHERE username = ? AND success = 0 AND attempt_time > ?
    ''', (username, lockout_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    failed_attempts = cursor.fetchone()[0]
    conn.close()
    
    return failed_attempts >= MAX_LOGIN_ATTEMPTS


def log_login_attempt(username, success, user_type):
    """Log login attempt for security monitoring"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO login_attempts (username, success, user_type, attempt_time)
        VALUES (?, ?, ?, ?)
    ''', (username, 1 if success else 0, user_type, timestamp))
    
    conn.commit()
    conn.close()


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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            operator_number INTEGER PRIMARY KEY,
            operator_name_hash TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_number INTEGER PRIMARY KEY,
            part_number TEXT NOT NULL,
            parts_per_order INTEGER NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            success INTEGER NOT NULL,
            user_type TEXT NOT NULL,
            attempt_time TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username_hash TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downtime_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_number INTEGER NOT NULL,
            downtime_reason TEXT NOT NULL,
            downtime_duration_minutes INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            shift_date TEXT NOT NULL,
            FOREIGN KEY (operator_number) REFERENCES operators(operator_number)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS smc_scrap_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_number INTEGER NOT NULL,
            part_type TEXT NOT NULL,
            smc_scrap_reason TEXT NOT NULL,
            smc_scrap_count INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            shift_date TEXT NOT NULL,
            FOREIGN KEY (operator_number) REFERENCES operators(operator_number)
        )
    ''')
    
    # Create index for performance on login attempts
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_login_attempts_username_time 
        ON login_attempts(username, attempt_time)
    ''')
    
    # Initialize default admin accounts if none exist
    cursor.execute('SELECT COUNT(*) FROM admin_credentials')
    if cursor.fetchone()[0] == 0:
        # Add default admin accounts
        default_admins = [
            ("FeuerWasser", "Jennifer124!"),
            ("supervisor", "super456")
        ]
        
        for username, password in default_admins:
            hashed_username = hashlib.sha256(username.encode()).hexdigest()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO admin_credentials (username_hash, password_hash, created_date)
                VALUES (?, ?, ?)
            ''', (hashed_username, hashed_password, timestamp))
    
    conn.commit()
    conn.close()


def save_scrap_entry(operator_number, part_number, order_number, scrap_reason, scrap_count):
    """Save scrap entry with input validation"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_operator_number(operator_number):
        conn.close()
        raise ValueError("Invalid operator number")
    
    if not validate_parts_count(scrap_count):
        conn.close()
        raise ValueError("Invalid scrap count")
    
    # Sanitize text inputs
    part_number = sanitize_input(part_number, 50)
    scrap_reason = sanitize_input(scrap_reason, 50)
    
    # Validate scrap reason is in allowed list
    if scrap_reason not in scrap_reasons:
        conn.close()
        raise ValueError("Invalid scrap reason")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO scrap_entries 
        (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp))
    
    conn.commit()
    conn.close()
    print(f"Scrap entry saved: {scrap_count} parts for reason '{scrap_reason}'")


def save_downtime_entry(operator_number, downtime_reason, duration_minutes):
    """Save downtime entry with input validation"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_operator_number(operator_number):
        conn.close()
        raise ValueError("Invalid operator number")
    
    if not validate_downtime_duration(duration_minutes):
        conn.close()
        raise ValueError("Invalid downtime duration (must be 1-480 minutes)")
    
    # Sanitize downtime reason
    downtime_reason = sanitize_input(downtime_reason, 50)
    
    # Validate downtime reason is in allowed list
    if downtime_reason not in downtime_reasons:
        conn.close()
        raise ValueError("Invalid downtime reason")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    shift_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        INSERT INTO downtime_entries 
        (operator_number, downtime_reason, downtime_duration_minutes, timestamp, shift_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (operator_number, downtime_reason, duration_minutes, timestamp, shift_date))
    
    conn.commit()
    conn.close()
    print(f"Downtime entry saved: {duration_minutes} minutes for '{downtime_reason}'") 


def save_smc_scrap_entry(operator_number, part_type, smc_scrap_reason, smc_scrap_count):
    """Save SMC (Sheet Moulding Compound) scrap entry with input validation"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_operator_number(operator_number):
        conn.close()
        raise ValueError("Invalid operator number")
    
    if not validate_smc_scrap_count(smc_scrap_count):
        conn.close()
        raise ValueError("Invalid SMC scrap count")
    
    # Sanitize text inputs
    part_type = sanitize_input(part_type, 50)
    smc_scrap_reason = sanitize_input(smc_scrap_reason, 50)
    
    # Validate SMC scrap reason is in allowed list
    if smc_scrap_reason not in smc_scrap_reasons:
        conn.close()
        raise ValueError("Invalid SMC scrap reason")
    
    if not part_type or len(part_type.strip()) == 0:
        conn.close()
        raise ValueError("Part type cannot be empty")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    shift_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        INSERT INTO smc_scrap_entries 
        (operator_number, part_type, smc_scrap_reason, smc_scrap_count, timestamp, shift_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (operator_number, part_type, smc_scrap_reason, smc_scrap_count, timestamp, shift_date))
    
    conn.commit()
    conn.close()
    print(f"SMC scrap entry saved: {smc_scrap_count} parts for reason '{smc_scrap_reason}' on part '{part_type}'") 


def add_operator(operator_number, operator_name):
    """Add operator with hashed name for privacy protection"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_operator_number(operator_number):
        conn.close()
        return False
    
    # Sanitize operator name
    operator_name = sanitize_input(operator_name, MAX_OPERATOR_NAME_LENGTH, 'operator_name')
    if not operator_name or len(operator_name.strip()) == 0:
        conn.close()
        return False
    
    # Hash the operator name for privacy protection
    operator_name_hash = hashlib.sha256(operator_name.encode()).hexdigest()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute('''
            INSERT INTO operators (operator_number, operator_name_hash, created_date)
            VALUES (?, ?, ?)
        ''', (operator_number, operator_name_hash, timestamp))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def remove_operator(operator_number):
    """Remove operator with validation"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate input
    if not validate_operator_number(operator_number):
        conn.close()
        return False
    
    cursor.execute('DELETE FROM operators WHERE operator_number = ?', (operator_number,))
    rows_affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    return rows_affected > 0


def get_operator_analytics():
    """Get comprehensive analytics for all operators"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Get all operators with their anonymized names
    cursor.execute('SELECT operator_number, operator_name_hash, created_date FROM operators ORDER BY operator_number')
    operators = cursor.fetchall()
    
    analytics_data = []
    
    for op_number, name_hash, created_date in operators:
        # Get scrap data for this operator
        cursor.execute('''
            SELECT COUNT(*) as total_entries,
                   SUM(scrap_count) as total_scrap,
                   COUNT(DISTINCT order_number) as orders_worked
            FROM scrap_entries WHERE operator_number = ?
        ''', (op_number,))
        
        scrap_stats = cursor.fetchone()
        total_entries = scrap_stats[0] if scrap_stats[0] else 0
        total_scrap = scrap_stats[1] if scrap_stats[1] else 0
        orders_worked = scrap_stats[2] if scrap_stats[2] else 0
        
        # Get downtime data for this operator
        cursor.execute('''
            SELECT COUNT(*) as downtime_entries,
                   SUM(downtime_duration_minutes) as total_downtime_minutes,
                   COUNT(DISTINCT shift_date) as days_with_downtime
            FROM downtime_entries WHERE operator_number = ?
        ''', (op_number,))
        
        downtime_stats = cursor.fetchone()
        downtime_entries = downtime_stats[0] if downtime_stats[0] else 0
        total_downtime_minutes = downtime_stats[1] if downtime_stats[1] else 0
        days_with_downtime = downtime_stats[2] if downtime_stats[2] else 0
        
        # Get SMC scrap data for this operator
        cursor.execute('''
            SELECT COUNT(*) as smc_scrap_entries,
                   SUM(smc_scrap_count) as total_smc_scrap,
                   COUNT(DISTINCT part_type) as part_types_worked,
                   COUNT(DISTINCT shift_date) as days_with_smc_scrap
            FROM smc_scrap_entries WHERE operator_number = ?
        ''', (op_number,))
        
        smc_scrap_stats = cursor.fetchone()
        smc_scrap_entries = smc_scrap_stats[0] if smc_scrap_stats[0] else 0
        total_smc_scrap = smc_scrap_stats[1] if smc_scrap_stats[1] else 0
        part_types_worked = smc_scrap_stats[2] if smc_scrap_stats[2] else 0
        days_with_smc_scrap = smc_scrap_stats[3] if smc_scrap_stats[3] else 0
        
        # Calculate scrap rate
        scrap_rate_percentage = 0
        if total_entries > 0:
            scrap_rate_percentage = (total_scrap / total_entries) * 100
        
        # Anonymize name for display
        anonymized_name = f"User_{name_hash[:8]}..."
        
        analytics_data.append({
            'operator_number': op_number,
            'anonymized_name': anonymized_name,
            'total_entries': total_entries,
            'total_scrap': total_scrap,
            'orders_worked': orders_worked,
            'scrap_rate_percentage': round(scrap_rate_percentage, 2),
            'downtime_entries': downtime_entries,
            'total_downtime_minutes': total_downtime_minutes,
            'total_downtime_hours': round(total_downtime_minutes / 60, 2),
            'days_with_downtime': days_with_downtime,
            'avg_downtime_per_day': round(total_downtime_minutes / max(days_with_downtime, 1), 1),
            'smc_scrap_entries': smc_scrap_entries,
            'total_smc_scrap': total_smc_scrap,
            'part_types_worked': part_types_worked,
            'days_with_smc_scrap': days_with_smc_scrap,
            'avg_smc_scrap_per_day': round(total_smc_scrap / max(days_with_smc_scrap, 1), 1) if days_with_smc_scrap > 0 else 0,
            'created_date': created_date
        })
    
    conn.close()
    return analytics_data


def get_detailed_operator_analytics(operator_number):
    """Get detailed analytics for a specific operator"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Get operator basic info
    cursor.execute('SELECT operator_name_hash, created_date FROM operators WHERE operator_number = ?', (operator_number,))
    operator_info = cursor.fetchone()
    
    if not operator_info:
        conn.close()
        return None
    
    name_hash, created_date = operator_info
    
    # Get detailed scrap entries
    cursor.execute('''
        SELECT timestamp, part_number, order_number, scrap_reason, scrap_count
        FROM scrap_entries 
        WHERE operator_number = ?
        ORDER BY timestamp DESC
    ''', (operator_number,))
    
    scrap_entries = cursor.fetchall()
    
    # Get detailed downtime entries
    cursor.execute('''
        SELECT timestamp, downtime_reason, downtime_duration_minutes, shift_date
        FROM downtime_entries 
        WHERE operator_number = ?
        ORDER BY timestamp DESC
    ''', (operator_number,))
    
    downtime_entries = cursor.fetchall()
    
    # Get detailed SMC scrap entries
    cursor.execute('''
        SELECT timestamp, part_type, smc_scrap_reason, smc_scrap_count, shift_date
        FROM smc_scrap_entries
        WHERE operator_number = ?
        ORDER BY timestamp DESC
    ''', (operator_number,))
    
    smc_scrap_entries = cursor.fetchall()
    
    conn.close()
    
    return {
        'operator_number': operator_number,
        'anonymized_name': f"User_{name_hash[:8]}...",
        'created_date': created_date,
        'scrap_entries': scrap_entries,
        'downtime_entries': downtime_entries,
        'smc_scrap_entries': smc_scrap_entries
    }


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
    print("Features: Scrap tracking, SMC (Sheet Moulding Compound) scrap, Downtime tracking, Analytics")
    print("Available admin credentials:")
    print("  Username: FeuerWasser, Password: Jennifer124!")
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
            if validate_operator_number(operator_num):
                print(f"Welcome, Operator {operator_num}!")
                operator_interface(operator_num)
            else:
                print("Invalid operator number! Must be between 0-9999.")
                return
        except ValueError:
            print("Invalid operator number! Please enter a valid number.")
            return


def admin_interface():
    """Command-line interface for administrators"""
    while True:
        print("\n=== ADMIN MENU ===")
        print("1. Create new order")
        print("2. View recent scrap entries")
        print("3. View operator analytics")
        print("4. View detailed operator analytics")
        print("5. Manage operators")
        print("6. View downtime entries")
        print("7. View SMC (Sheet Moulding Compound) scrap entries")
        print("8. Exit")
        
        choice = input("Select option (1-8): ").strip()
        
        if choice == "1":
            create_order()
        elif choice == "2":
            view_scrap_entries()
        elif choice == "3":
            view_operator_analytics()
        elif choice == "4":
            view_detailed_operator_analytics()
        elif choice == "5":
            manage_operators()
        elif choice == "6":
            view_downtime_entries()
        elif choice == "7":
            view_smc_scrap_entries()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


def operator_interface(operator_num):
    """Command-line interface for operators"""
    while True:
        print(f"\n=== OPERATOR MENU (Operator {operator_num}) ===")
        print("1. Track scrap for existing order")
        print("2. Track downtime")
        print("3. Track SMC (Sheet Moulding Compound) scrap")
        print("4. View my recent scrap entries")
        print("5. View my downtime entries")
        print("6. View my SMC scrap entries")
        print("7. Exit")
        
        choice = input("Select option (1-7): ").strip()
        
        if choice == "1":
            track_scrap(operator_num)
        elif choice == "2":
            track_downtime(operator_num)
        elif choice == "3":
            track_smc_scrap(operator_num)
        elif choice == "4":
            view_operator_scrap_entries(operator_num)
        elif choice == "5":
            view_operator_downtime_entries(operator_num)
        elif choice == "6":
            view_operator_smc_scrap_entries(operator_num)
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


def track_downtime(operator_num):
    """Track operator downtime"""
    print("\n=== TRACK DOWNTIME ===")
    print("Available downtime reasons:", ", ".join(downtime_reasons))
    
    reason = input("\nEnter downtime reason: ").strip()
    if reason not in downtime_reasons:
        print("Invalid downtime reason!")
        return
    
    try:
        duration = int(input("Enter duration in minutes (1-480): ").strip())
        if not validate_downtime_duration(duration):
            print("Invalid duration! Must be between 1-480 minutes.")
            return
        
        save_downtime_entry(operator_num, reason, duration)
        print("✓ Downtime entry saved successfully.")
        
    except ValueError:
        print("Invalid duration! Please enter a number.")


def track_smc_scrap(operator_num):
    """Track SMC (Sheet Moulding Compound) scrap"""
    print("\n=== TRACK SMC (SHEET MOULDING COMPOUND) SCRAP ===")
    
    part_type = input("Enter part type (e.g., 'Hood-Panel-001'): ").strip()
    if not part_type:
        print("Part type cannot be empty!")
        return
    
    print("\nAvailable SMC scrap reasons:", ", ".join(smc_scrap_reasons))
    
    reason = input("\nEnter SMC scrap reason: ").strip()
    if reason not in smc_scrap_reasons:
        print("Invalid SMC scrap reason!")
        return
    
    try:
        count = int(input("Enter SMC scrap count: ").strip())
        if not validate_smc_scrap_count(count):
            print("Invalid count! Must be between 0-999999.")
            return
        
        save_smc_scrap_entry(operator_num, part_type, reason, count)
        print("✓ SMC scrap entry saved successfully.")
        
    except ValueError:
        print("Invalid count! Please enter a number.")


def view_operator_analytics():
    """View comprehensive operator analytics"""
    print("\n=== OPERATOR ANALYTICS ===")
    
    analytics = get_operator_analytics()
    
    if not analytics:
        print("No operators found with analytics data.")
        return
    
    print(f"{'Op#':<6} {'Name':<15} {'Scrap':<8} {'Orders':<8} {'Downtime':<10} {'SMC Scrap':<10} {'Part Types':<12}")
    print("-" * 75)
    
    for data in analytics:
        print(f"{data['operator_number']:<6} {data['anonymized_name']:<15} "
              f"{data['total_scrap']:<8} {data['orders_worked']:<8} "
              f"{data['total_downtime_hours']:<10.1f}h {data['total_smc_scrap']:<10} "
              f"{data['part_types_worked']:<12}")


def view_detailed_operator_analytics():
    """View detailed analytics for specific operator"""
    print("\n=== DETAILED OPERATOR ANALYTICS ===")
    
    try:
        op_num = int(input("Enter operator number: ").strip())
        if not validate_operator_number(op_num):
            print("Invalid operator number!")
            return
        
        details = get_detailed_operator_analytics(op_num)
        
        if not details:
            print(f"No data found for operator {op_num}")
            return
        
        print(f"\n--- OPERATOR {op_num} ({details['anonymized_name']}) ---")
        print(f"Created: {details['created_date']}")
        
        print(f"\nSCRAP ENTRIES ({len(details['scrap_entries'])}):")
        for entry in details['scrap_entries'][:10]:  # Show last 10
            timestamp, part_number, order_number, scrap_reason, scrap_count = entry
            print(f"  {timestamp} | Order {order_number} | {scrap_reason}: {scrap_count} parts")
        
        print(f"\nDOWNTIME ENTRIES ({len(details['downtime_entries'])}):")
        for entry in details['downtime_entries'][:10]:  # Show last 10
            timestamp, downtime_reason, duration_minutes, shift_date = entry
            print(f"  {timestamp} | {downtime_reason}: {duration_minutes} minutes")
        
        print(f"\nSMC SCRAP ENTRIES ({len(details['smc_scrap_entries'])}):")
        for entry in details['smc_scrap_entries'][:10]:  # Show last 10
            timestamp, part_type, smc_scrap_reason, smc_scrap_count, shift_date = entry
            print(f"  {timestamp} | {part_type} | {smc_scrap_reason}: {smc_scrap_count} parts")
        
    except ValueError:
        print("Invalid operator number! Please enter a number.")


def manage_operators():
    """Manage operators (add/remove)"""
    print("\n=== MANAGE OPERATORS ===")
    print("1. Add operator")
    print("2. Remove operator")
    print("3. List all operators")
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        try:
            op_num = int(input("Enter operator number (0-9999): ").strip())
            if not validate_operator_number(op_num):
                print("Invalid operator number!")
                return
            
            op_name = input("Enter operator name: ").strip()
            if not op_name:
                print("Operator name cannot be empty!")
                return
            
            if add_operator(op_num, op_name):
                print(f"✓ Operator {op_num} added successfully.")
            else:
                print(f"✗ Failed to add operator {op_num} (may already exist).")
            
        except ValueError:
            print("Invalid operator number! Please enter a number.")
    
    elif choice == "2":
        try:
            op_num = int(input("Enter operator number to remove: ").strip())
            if not validate_operator_number(op_num):
                print("Invalid operator number!")
                return
            
            if remove_operator(op_num):
                print(f"✓ Operator {op_num} removed successfully.")
            else:
                print(f"✗ Operator {op_num} not found.")
            
        except ValueError:
            print("Invalid operator number! Please enter a number.")
    
    elif choice == "3":
        # List operators using analytics data
        analytics = get_operator_analytics()
        if analytics:
            print("\nRegistered Operators:")
            print(f"{'Operator #':<12} {'Anonymized Name':<18} {'Created Date':<20}")
            print("-" * 50)
            for data in analytics:
                print(f"{data['operator_number']:<12} {data['anonymized_name']:<18} {data['created_date']:<20}")
        else:
            print("No operators found.")
    else:
        print("Invalid choice!")


def view_downtime_entries():
    """View recent downtime entries (admin)"""
    print("\n=== RECENT DOWNTIME ENTRIES ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT operator_number, downtime_reason, downtime_duration_minutes, timestamp, shift_date
        FROM downtime_entries
        ORDER BY timestamp DESC
        LIMIT 15
    ''')
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        for entry in entries:
            op_num, reason, duration, timestamp, shift_date = entry
            print(f"{timestamp} | Operator {op_num} | {reason}: {duration} minutes | Shift: {shift_date}")
    else:
        print("No downtime entries found.")


def view_smc_scrap_entries():
    """View recent SMC scrap entries (admin)"""
    print("\n=== RECENT SMC (SHEET MOULDING COMPOUND) SCRAP ENTRIES ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT operator_number, part_type, smc_scrap_reason, smc_scrap_count, timestamp, shift_date
        FROM smc_scrap_entries
        ORDER BY timestamp DESC
        LIMIT 15
    ''')
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        for entry in entries:
            op_num, part_type, reason, count, timestamp, shift_date = entry
            print(f"{timestamp} | Operator {op_num} | {part_type} | {reason}: {count} parts | Shift: {shift_date}")
    else:
        print("No SMC scrap entries found.")


def view_operator_downtime_entries(operator_num):
    """View downtime entries for specific operator"""
    print(f"\n=== YOUR DOWNTIME ENTRIES (Operator {operator_num}) ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT downtime_reason, downtime_duration_minutes, timestamp, shift_date
        FROM downtime_entries
        WHERE operator_number = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (operator_num,))
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        total_minutes = 0
        for entry in entries:
            reason, duration, timestamp, shift_date = entry
            print(f"{timestamp} | {reason}: {duration} minutes | Shift: {shift_date}")
            total_minutes += duration
        print(f"\nTotal downtime in last 10 entries: {total_minutes} minutes ({total_minutes/60:.1f} hours)")
    else:
        print("No downtime entries found for your operator number.")


def view_operator_smc_scrap_entries(operator_num):
    """View SMC scrap entries for specific operator"""
    print(f"\n=== YOUR SMC SCRAP ENTRIES (Operator {operator_num}) ===")
    
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT part_type, smc_scrap_reason, smc_scrap_count, timestamp, shift_date
        FROM smc_scrap_entries
        WHERE operator_number = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (operator_num,))
    
    entries = cursor.fetchall()
    conn.close()
    
    if entries:
        total_smc_scrap = 0
        for entry in entries:
            part_type, reason, count, timestamp, shift_date = entry
            print(f"{timestamp} | {part_type} | {reason}: {count} parts | Shift: {shift_date}")
            total_smc_scrap += count
        print(f"\nTotal SMC scrap in last 10 entries: {total_smc_scrap} parts")
    else:
        print("No SMC scrap entries found for your operator number.")


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