import random
import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import sys
import os
import hashlib
import re
import time

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

scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]

# Downtime reasons for operator logging
downtime_reasons = [
    "machine breakdown", "material shortage", "quality hold", "maintenance", 
    "setup/changeover", "training", "meeting", "break", "lunch", 
    "waiting for work", "tooling issue", "power outage", "other"
]

# SMC (Sheet Moulding Compound) scrap reasons
smc_scrap_reasons = [
    "incomplete fill", "flash/excess material", "air bubbles/voids", "surface defects", 
    "dimensional out of spec", "fiber showing", "delamination", "warp/distortion", 
    "gel coat defects", "contamination", "burn marks", "under cure", 
    "over cure", "crack/split", "poor surface finish", "other"
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


def add_admin_credential(username, password):
    """Add admin credential to database"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    hashed_username = hashlib.sha256(username.encode()).hexdigest()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute('''
            INSERT INTO admin_credentials (username_hash, password_hash, created_date)
            VALUES (?, ?, ?)
        ''', (hashed_username, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


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
    
    # Check if we need to migrate the operators table from old schema
    cursor.execute("PRAGMA table_info(operators)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'operator_name' in columns and 'operator_name_hash' not in columns:
        print("Migrating operators table to new schema...")
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE operators_new (
                operator_number INTEGER PRIMARY KEY,
                operator_name_hash TEXT NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        
        # Migrate existing data by hashing operator names
        cursor.execute('SELECT operator_number, operator_name, created_date FROM operators')
        existing_operators = cursor.fetchall()
        
        for op_number, op_name, created_date in existing_operators:
            # Hash the existing operator name
            op_name_hash = hashlib.sha256(op_name.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO operators_new (operator_number, operator_name_hash, created_date)
                VALUES (?, ?, ?)
            ''', (op_number, op_name_hash, created_date))
        
        # Replace old table with new table
        cursor.execute('DROP TABLE operators')
        cursor.execute('ALTER TABLE operators_new RENAME TO operators')
        print("Operators table migration completed.")
    
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
            shift_date TEXT NOT NULL
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
            shift_date TEXT NOT NULL
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


def validate_downtime_duration(duration_minutes):
    """Validate downtime duration input"""
    try:
        minutes = int(duration_minutes)
        return 1 <= minutes <= 480  # 1 minute to 8 hours (1 shift)
    except (ValueError, TypeError):
        return False


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


def validate_smc_scrap_count(smc_count):
    """Validate SMC scrap count input"""
    try:
        count = int(smc_count)
        return 0 <= count <= 999999  # Reasonable upper limit
    except (ValueError, TypeError):
        return False


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


def get_all_operators():
    """Get all operators with anonymized names for display"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT operator_number, operator_name_hash, created_date FROM operators ORDER BY operator_number')
    operators = cursor.fetchall()
    
    # Convert to display format with anonymized names
    display_operators = []
    for op_number, name_hash, created_date in operators:
        # Show first 8 characters of hash for identification while maintaining privacy
        anonymized_name = f"User_{name_hash[:8]}..."
        display_operators.append((op_number, anonymized_name, created_date))
    
    conn.close()
    return display_operators


def verify_operator_exists(operator_number):
    """Verify if operator number exists in database"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM operators WHERE operator_number = ?', (operator_number,))
    exists = cursor.fetchone()[0] > 0
    
    conn.close()
    return exists


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
        
        # Calculate estimated parts made (this is an approximation based on scrap entries)
        # We'll estimate parts made as total_scrap + estimated good parts
        # Using average scrap rate to estimate total production
        cursor.execute('''
            SELECT se.order_number, se.scrap_count, o.parts_per_order
            FROM scrap_entries se
            JOIN orders o ON se.order_number = o.order_number
            WHERE se.operator_number = ?
        ''', (op_number,))
        
        order_details = cursor.fetchall()
        
        estimated_parts_made = 0
        total_expected_parts = 0
        good_parts_estimate = 0
        
        if order_details:
            # Group by order to avoid counting same order multiple times
            orders_processed = {}
            for order_num, scrap_count, parts_per_order in order_details:
                if order_num not in orders_processed:
                    orders_processed[order_num] = {'scrap': 0, 'total': parts_per_order}
                orders_processed[order_num]['scrap'] += scrap_count
            
            for order_data in orders_processed.values():
                # Estimate that operator made at least the parts they scrapped plus some good parts
                # Conservative estimate: assume 5% scrap rate, so if they made X scrap, total production = X / 0.05
                scrap_for_order = order_data['scrap']
                if scrap_for_order > 0:
                    estimated_production = min(scrap_for_order * 20, order_data['total'])  # Cap at order total
                    estimated_parts_made += estimated_production
                    good_parts_estimate += (estimated_production - scrap_for_order)
                    total_expected_parts += estimated_production
        
        # Calculate efficiency based on expected rate (248 parts/hour)
        # Assume 8 hour shifts for efficiency calculation
        expected_rate_per_shift = 248 * 8  # 1984 parts per shift
        efficiency_percentage = 0
        if total_expected_parts > 0 and estimated_parts_made > 0:
            # Calculate actual good parts vs expected rate
            efficiency_percentage = (good_parts_estimate / (orders_worked * expected_rate_per_shift)) * 100
            efficiency_percentage = min(efficiency_percentage, 100)  # Cap at 100%
        
        # Calculate scrap rate
        scrap_rate_percentage = 0
        if estimated_parts_made > 0:
            scrap_rate_percentage = (total_scrap / estimated_parts_made) * 100
        
        # Anonymize name for display
        anonymized_name = f"User_{name_hash[:8]}..."
        
        analytics_data.append({
            'operator_number': op_number,
            'anonymized_name': anonymized_name,
            'total_entries': total_entries,
            'estimated_parts_made': estimated_parts_made,
            'total_scrap': total_scrap,
            'good_parts_estimate': good_parts_estimate,
            'orders_worked': orders_worked,
            'efficiency_percentage': round(efficiency_percentage, 2),
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
        SELECT se.timestamp, se.part_number, se.order_number, se.scrap_reason, 
               se.scrap_count, o.parts_per_order
        FROM scrap_entries se
        LEFT JOIN orders o ON se.order_number = o.order_number
        WHERE se.operator_number = ?
        ORDER BY se.timestamp DESC
    ''', (operator_number,))
    
    detailed_entries = cursor.fetchall()
    
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
    
    # Calculate daily/weekly trends
    cursor.execute('''
        SELECT DATE(timestamp) as date, 
               SUM(scrap_count) as daily_scrap,
               COUNT(DISTINCT order_number) as orders_worked_daily
        FROM scrap_entries 
        WHERE operator_number = ?
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 30
    ''', (operator_number,))
    
    daily_stats = cursor.fetchall()
    
    # Calculate daily downtime trends
    cursor.execute('''
        SELECT shift_date,
               SUM(downtime_duration_minutes) as daily_downtime_minutes,
               COUNT(*) as downtime_events
        FROM downtime_entries
        WHERE operator_number = ?
        GROUP BY shift_date
        ORDER BY shift_date DESC
        LIMIT 30
    ''', (operator_number,))
    
    daily_downtime_stats = cursor.fetchall()
    
    # Calculate daily SMC scrap trends
    cursor.execute('''
        SELECT shift_date,
               SUM(smc_scrap_count) as daily_smc_scrap,
               COUNT(*) as smc_scrap_events,
               COUNT(DISTINCT part_type) as part_types_per_day
        FROM smc_scrap_entries
        WHERE operator_number = ?
        GROUP BY shift_date
        ORDER BY shift_date DESC
        LIMIT 30
    ''', (operator_number,))
    
    daily_smc_scrap_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'operator_number': operator_number,
        'anonymized_name': f"User_{name_hash[:8]}...",
        'created_date': created_date,
        'detailed_entries': detailed_entries,
        'downtime_entries': downtime_entries,
        'smc_scrap_entries': smc_scrap_entries,
        'daily_stats': daily_stats,
        'daily_downtime_stats': daily_downtime_stats,
        'daily_smc_scrap_stats': daily_smc_scrap_stats
    }


def save_order(part_number, parts_per_order):
    """Save order with input validation"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_parts_count(parts_per_order):
        conn.close()
        raise ValueError("Invalid parts per order count")
    
    # Sanitize part number
    part_number = sanitize_input(part_number, 50)
    if not part_number:
        conn.close()
        raise ValueError("Invalid part number")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO orders (part_number, parts_per_order, created_date)
        VALUES (?, ?, ?)
    ''', (part_number, parts_per_order, timestamp))
    
    order_number = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_number


class Part:
    expected_rate = 248

    def __init__(self, part_number):
        self.part_number = part_number

    def rate_percentage(self, made_parts):
        if self.expected_rate <= 0:
            return 0.0
        return (made_parts / self.expected_rate) * 100


class Order:
    _next_order_number = 1

    def __init__(self, part_number, parts_per_order):
        self.order_number = Order._next_order_number
        Order._next_order_number += 1
        self.part_number = part_number
        self.parts_per_order = parts_per_order

    def summary(self):
        return (
            "Order "
            + str(self.order_number)
            + ": Part "
            + self.part_number
            + ", Parts per order: "
            + str(self.parts_per_order)
        )


def part_selection():
    while True:
        part_number = input("Enter part number: ")
        if part_number in part_numbers:
            break
        print("Invalid part number. Please enter a valid part number from the list: " + ", ".join(part_numbers))

    mix = input("Enter mix number: ")
    part_number = part_number + mix
    order_quantity = random.randint(110, 5000)
    print("Part number: " + part_number + ", Order quantity: " + str(order_quantity) + " (randomly generated)")
    
    while True:
        try:
            parts_made = int(input("Enter number of parts you have made: "))
            if parts_made < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for parts made.")
    
    return part_number, order_quantity, parts_made


def scrap_tracking(parts_made, part_number, order_number):
    while True:
        try:
            operator_number = int(input("Enter operator number (max 4 digits): "))
            if operator_number < 0 or operator_number > 9999:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid 4-digit integer (0-9999).")
    
    total_scrap = 0
    scrap_details = []
    
    print(f"\nTracking scrap for {parts_made} parts made")
    print("Enter each scrap reason and count. Enter 'done' when finished.")
    
    while True:
        reason_input = input("\nEnter scrap reason (or 'done' to finish): ").strip()
        
        if reason_input.lower() == 'done':
            break
            
        if reason_input not in scrap_reasons:
            print("Invalid scrap reason. Please enter a valid reason from the list: " + ", ".join(scrap_reasons))
            continue
        
        while True:
            try:
                scrap_count = int(input(f"Enter number of parts scrapped for '{reason_input}': "))
                if scrap_count < 0:
                    raise ValueError
                if total_scrap + scrap_count > parts_made:
                    print(f"Total scrap ({total_scrap + scrap_count}) cannot exceed parts made ({parts_made})")
                    continue
                break
            except ValueError:
                print("Please enter a valid non-negative integer.")
        
        if scrap_count > 0:
            total_scrap += scrap_count
            scrap_details.append((reason_input, scrap_count))
            save_scrap_entry(operator_number, part_number, order_number, reason_input, scrap_count)
            print(f"Recorded: {scrap_count} parts for '{reason_input}'. Total scrap so far: {total_scrap}")
    
    good_parts_made = parts_made - total_scrap
    
    print(f"\nScrap Summary:")
    for reason, count in scrap_details:
        print(f"  {reason}: {count} parts")
    print(f"Total scrap: {total_scrap}")
    print(f"Good parts made: {good_parts_made}")
    
    return good_parts_made, total_scrap


class LoginWindow:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.is_admin = False
        self.username = ""
        
        self.create_login_window()
    
    def create_login_window(self):
        try:
            print("Creating login window...")
            # Create login window
            self.login_window = tk.Toplevel(self.root)
            self.login_window.title("Parts Tracker - Login")
            self.login_window.geometry("400x400")
            self.login_window.resizable(False, False)
            
            # Make it modal
            self.login_window.transient(self.root)
            self.login_window.grab_set()
            
            # Handle window close event
            self.login_window.protocol("WM_DELETE_WINDOW", self.on_login_close)
            
            # Force window to center and display
            self.login_window.update_idletasks()
            
            # Get screen dimensions
            screen_width = self.login_window.winfo_screenwidth()
            screen_height = self.login_window.winfo_screenheight()
            
            # Calculate center position
            x = (screen_width // 2) - (400 // 2)
            y = (screen_height // 2) - (400 // 2)
            
            # Ensure window is not off-screen
            x = max(0, min(x, screen_width - 400))
            y = max(0, min(y, screen_height - 400))
            
            self.login_window.geometry(f"400x400+{x}+{y}")
            
            # Force window to be visible and on top
            self.login_window.deiconify()
            self.login_window.lift()
            self.login_window.focus_force()
            self.login_window.attributes('-topmost', True)
            self.login_window.update()
            
            print("Login window created and positioned successfully")
            
        except Exception as e:
            print(f"Error creating login window: {e}")
            # Fall back to command line if login window fails
            messagebox.showerror("Error", f"Failed to create login window: {e}")
            self.root.destroy()
            run_command_line_mode()
            return
        
        main_frame = ttk.Frame(self.login_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Parts Tracker Login", font=("", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Login type selection
        ttk.Label(main_frame, text="Login as:").pack(anchor=tk.W)
        
        self.login_type = tk.StringVar(value="operator")
        
        operator_rb = ttk.Radiobutton(main_frame, text="Operator", variable=self.login_type, value="operator")
        operator_rb.pack(anchor=tk.W, pady=(5, 0))
        
        admin_rb = ttk.Radiobutton(main_frame, text="Administrator", variable=self.login_type, value="admin")
        admin_rb.pack(anchor=tk.W, pady=(5, 15))
        
        # Username field (only shown for admin)
        self.username_frame = ttk.Frame(main_frame)
        self.username_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.username_frame, text="Username:").pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.username_frame, textvariable=self.username_var)
        self.username_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Password field (only shown for admin)
        self.password_frame = ttk.Frame(main_frame)
        self.password_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.password_frame, text="Password:").pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.password_frame, textvariable=self.password_var, show="*")
        self.password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Operator number field (only shown for operator)
        self.operator_frame = ttk.Frame(main_frame)
        self.operator_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(self.operator_frame, text="Operator Number:").pack(anchor=tk.W)
        self.operator_var = tk.StringVar()
        self.operator_entry = ttk.Entry(self.operator_frame, textvariable=self.operator_var)
        self.operator_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Initially hide admin fields
        self.toggle_admin_fields()
        
        # Bind radio button changes
        operator_rb.config(command=self.toggle_admin_fields)
        admin_rb.config(command=self.toggle_admin_fields)
        
        # Add spacer frame to push buttons to bottom
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label 
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="red")
        self.status_label.pack(pady=(10, 5))
        
        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Login button (primary action, on top)
        login_btn = ttk.Button(button_frame, text="Login", command=self.login)
        login_btn.pack(pady=(0, 5))
        
        # Close button  
        close_btn = ttk.Button(button_frame, text="Close Application", command=self.close_application)
        close_btn.pack(pady=(0, 0))
    
    def toggle_admin_fields(self):
        if self.login_type.get() == "admin":
            self.operator_frame.pack_forget()
            # Use status_label for positioning only if it exists
            if hasattr(self, 'status_label'):
                self.username_frame.pack(fill=tk.X, pady=(0, 10), before=self.status_label)
                self.password_frame.pack(fill=tk.X, pady=(0, 10), before=self.status_label)
            else:
                self.username_frame.pack(fill=tk.X, pady=(0, 10))
                self.password_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.username_frame.pack_forget()
            self.password_frame.pack_forget()
            # Use status_label for positioning only if it exists
            if hasattr(self, 'status_label'):
                self.operator_frame.pack(fill=tk.X, pady=(0, 20), before=self.status_label)
            else:
                self.operator_frame.pack(fill=tk.X, pady=(0, 20))
    
    def login(self):
        print("Processing login...")
        
        if self.login_type.get() == "admin":
            username = sanitize_input(self.username_var.get(), MAX_USERNAME_LENGTH)
            password = self.password_var.get()  # Don't sanitize password (may contain special chars)
            
            if not username or not password:
                self.status_var.set("Please enter username and password")
                return
            
            # Check for account lockout before attempting authentication
            if is_account_locked(username):
                self.status_var.set(f"Account locked. Try again in {LOCKOUT_DURATION_MINUTES} minutes.")
                print(f"Admin login blocked: Account {username} is locked")
                return
            
            if authenticate_admin(username, password):
                print(f"Admin login successful: {username}")
                self.is_admin = True
                self.username = username
                self.login_window.destroy()
                self.callback(self.is_admin, self.username)
            else:
                # Check if account is now locked after this failed attempt
                if is_account_locked(username):
                    self.status_var.set(f"Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes.")
                else:
                    remaining_attempts = MAX_LOGIN_ATTEMPTS - self.get_recent_failed_attempts(username)
                    self.status_var.set(f"Invalid credentials. {remaining_attempts} attempts remaining.")
                print("Admin login failed: Invalid credentials")
        else:
            # Operator login
            operator_input = sanitize_input(self.operator_var.get(), 10, 'numeric')
            
            if not operator_input:
                self.status_var.set("Please enter operator number")
                return
            
            if not validate_operator_number(operator_input):
                self.status_var.set("Please enter a valid 4-digit operator number (0-9999)")
                print("Operator login failed: Invalid operator number format")
                return
            
            operator_num = int(operator_input)
            
            # Verify operator exists in the system (optional - can be removed if not required)
            # if not verify_operator_exists(operator_num):
            #     self.status_var.set("Operator number not found in system. Contact administrator.")
            #     print(f"Operator login failed: Operator {operator_num} not registered")
            #     return
            
            # Log operator login attempt
            log_login_attempt(f"operator_{operator_num}", True, 'operator')
            
            print(f"Operator login successful: {operator_num}")
            self.is_admin = False
            self.username = f"Operator {operator_num}"
            self.login_window.destroy()
            self.callback(self.is_admin, self.username, operator_num)
    
    def get_recent_failed_attempts(self, username):
        """Get count of recent failed attempts for display purposes"""
        conn = sqlite3.connect('parts_tracker.db')
        cursor = conn.cursor()
        
        lockout_time = datetime.now() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE username = ? AND success = 0 AND attempt_time > ?
        ''', (username, lockout_time.strftime('%Y-%m-%d %H:%M:%S')))
        
        failed_attempts = cursor.fetchone()[0]
        conn.close()
        
        return failed_attempts
    
    def close_application(self):
        """Close the application cleanly"""
        try:
            result = messagebox.askyesno("Exit Application", 
                                       "Are you sure you want to exit the Parts Tracker application?")
            if result:
                print("Application closing by user request")
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            print(f"Error during application close: {e}")
            import sys
            sys.exit(0)
    
    def on_login_close(self):
        """Handle login window close event"""
        self.close_application()


class PartsTrackerGUI:
    def __init__(self, root):
        try:
            print("Initializing PartsTrackerGUI...")
            self.root = root
            self.root.title("Parts Tracker")
            self.root.geometry("800x600")
            
            # Ensure window is visible and on top
            self.root.lift()
            self.root.attributes('-topmost', True)
            
            # Center the window on screen
            self.center_window()
            
            print("Initializing database...")
            # Initialize database
            init_database()
            print("Database initialized successfully")
            
            # Variables
            self.order = None
            self.scrap_entries = []
            self.is_admin = False
            self.current_user = ""
            self.operator_number = None
            
            print("Starting login process...")
            # Start with login
            self.show_login()
            
        except Exception as e:
            print(f"Error in PartsTrackerGUI.__init__: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {e}")
            try:
                self.root.destroy()
            except:
                pass
            raise
    
    def center_window(self):
        """Center the main window on the screen"""
        self.root.update_idletasks()
        width = 800
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_login(self):
        LoginWindow(self.root, self.on_login_complete)
    
    def on_login_complete(self, is_admin, username, operator_num=None):
        print(f"Login completed. User: {username}, Admin: {is_admin}")
        self.is_admin = is_admin
        self.current_user = username
        self.operator_number = operator_num
        
        try:
            # Show main window
            print("Showing main window...")
            self.root.deiconify()
            self.root.update_idletasks()
            
            # Force main window to be visible and on top
            self.root.lift()
            self.root.focus_force()
            self.root.attributes('-topmost', True)
            
            # Brief delay to ensure window is ready
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
            
            # Create the main interface
            print("Creating main interface...")
            self.create_widgets()
            
            # Update title with user info
            user_type = "Administrator" if is_admin else "Operator"
            self.root.title(f"Parts Tracker - {user_type}: {username}")
            
            # Final visibility ensure
            self.root.update()
            
            print(f"Application ready: {user_type} {username}")
            
        except Exception as e:
            print(f"Error showing main window: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to initialize main window: {e}")
            self.root.quit()
        
    def create_widgets(self):
        try:
            # Clear any existing widgets
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # Configure root window
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            
            # Main frame
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            main_frame.columnconfigure(0, weight=1)
            
            # User info frame
            user_frame = ttk.Frame(main_frame)
            user_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            
            user_type = "Administrator" if self.is_admin else "Operator"
            ttk.Label(user_frame, text=f"Logged in as: {user_type} - {self.current_user}", 
                     font=("", 10, "bold")).pack(side=tk.LEFT)
            
            # Button frame for logout and close
            button_frame = ttk.Frame(user_frame)
            button_frame.pack(side=tk.RIGHT)
            
            logout_btn = ttk.Button(button_frame, text="Logout", command=self.logout)
            logout_btn.pack(side=tk.RIGHT, padx=(0, 5))
            
            close_btn = ttk.Button(button_frame, text="Close Application", command=self.close_application)
            close_btn.pack(side=tk.RIGHT)
            
            if self.is_admin:
                self.create_admin_widgets(main_frame)
            else:
                self.create_operator_widgets(main_frame)
                
        except Exception as e:
            print(f"Error creating widgets: {e}")
            messagebox.showerror("Error", f"Failed to create interface: {e}")
    
    def create_admin_widgets(self, main_frame):
        # Admin-specific widgets
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Orders Tab
        orders_tab = ttk.Frame(notebook)
        notebook.add(orders_tab, text="Orders")
        
        # Part Selection Section
        part_frame = ttk.LabelFrame(orders_tab, text="Create New Order", padding="10")
        part_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(part_frame, text="Part Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.part_var = tk.StringVar()
        self.part_combo = ttk.Combobox(part_frame, textvariable=self.part_var, values=part_numbers, state="readonly")
        self.part_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(part_frame, text="Mix Number:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.mix_var = tk.StringVar()
        self.mix_entry = ttk.Entry(part_frame, textvariable=self.mix_var, width=10)
        self.mix_entry.grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(part_frame, text="Parts per Order:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.parts_per_order_var = tk.StringVar()
        self.parts_per_order_entry = ttk.Entry(part_frame, textvariable=self.parts_per_order_var, width=10)
        self.parts_per_order_entry.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))
        
        self.create_order_btn = ttk.Button(part_frame, text="Create New Order", command=self.create_order)
        self.create_order_btn.grid(row=1, column=2, columnspan=2, pady=(10, 0))
        
        # Current Orders Section
        orders_frame = ttk.LabelFrame(orders_tab, text="Current Orders", padding="10")
        orders_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.orders_text = scrolledtext.ScrolledText(orders_frame, height=15, width=80)
        self.orders_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        refresh_btn = ttk.Button(orders_frame, text="Refresh Orders", command=self.refresh_orders)
        refresh_btn.grid(row=1, column=0, pady=(10, 0))
        
        # Analytics Tab
        analytics_tab = ttk.Frame(notebook)
        notebook.add(analytics_tab, text="Analytics")
        
        # Operators Tab
        operators_tab = ttk.Frame(notebook)
        notebook.add(operators_tab, text="Operators")
        
        # Add Operator Section
        add_op_frame = ttk.LabelFrame(operators_tab, text="Add New Operator", padding="10")
        add_op_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(add_op_frame, text="Operator Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.new_op_number_var = tk.StringVar()
        self.new_op_number_entry = ttk.Entry(add_op_frame, textvariable=self.new_op_number_var, width=10)
        self.new_op_number_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(add_op_frame, text="Operator Name:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.new_op_name_var = tk.StringVar()
        self.new_op_name_entry = ttk.Entry(add_op_frame, textvariable=self.new_op_name_var, width=20)
        self.new_op_name_entry.grid(row=0, column=3, padx=(0, 20))
        
        self.add_op_btn = ttk.Button(add_op_frame, text="Add Operator", command=self.add_operator)
        self.add_op_btn.grid(row=0, column=4)
        
        # Operator List Section
        op_list_frame = ttk.LabelFrame(operators_tab, text="Current Operators", padding="10")
        op_list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Create treeview for operators
        columns = ('Number', 'Anonymized ID', 'Created Date')
        self.operators_tree = ttk.Treeview(op_list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.operators_tree.heading(col, text=col)
            if col == 'Number':
                self.operators_tree.column(col, width=100)
            elif col == 'Anonymized ID':
                self.operators_tree.column(col, width=200)
            else:
                self.operators_tree.column(col, width=150)
        
        self.operators_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(op_list_frame, orient=tk.VERTICAL, command=self.operators_tree.yview)
        tree_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.operators_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Remove operator button
        self.remove_op_btn = ttk.Button(op_list_frame, text="Remove Selected Operator", command=self.remove_operator)
        self.remove_op_btn.grid(row=1, column=0, pady=(10, 0))
        
        # Refresh operators button
        self.refresh_op_btn = ttk.Button(op_list_frame, text="Refresh Operators", command=self.refresh_operators)
        self.refresh_op_btn.grid(row=1, column=1, pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        orders_tab.columnconfigure(0, weight=1)
        orders_tab.rowconfigure(1, weight=1)
        orders_frame.columnconfigure(0, weight=1)
        orders_frame.rowconfigure(0, weight=1)
        operators_tab.columnconfigure(0, weight=1)
        operators_tab.rowconfigure(1, weight=1)
        op_list_frame.columnconfigure(0, weight=1)
        op_list_frame.rowconfigure(0, weight=1)
        
        self.refresh_orders()
        self.refresh_operators()
        self.create_analytics_widgets(analytics_tab)
    
    def create_operator_widgets(self, main_frame):
        # Operator-specific widgets (scrap tracking only)
        
        # Instructions
        info_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        instruction_text = "Operators can only track scrap for existing orders. Contact an administrator to create new orders."
        ttk.Label(info_frame, text=instruction_text, wraplength=600).grid(row=0, column=0)
        
        # Order Selection for Scrap Tracking
        order_frame = ttk.LabelFrame(main_frame, text="Select Order for Scrap Tracking", padding="10")
        order_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(order_frame, text="Available Orders:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.order_selection_var = tk.StringVar()
        self.order_selection_combo = ttk.Combobox(order_frame, textvariable=self.order_selection_var, 
                                                 state="readonly", width=40)
        self.order_selection_combo.grid(row=0, column=1, padx=(0, 10))
        
        # Refresh orders button
        refresh_orders_btn = ttk.Button(order_frame, text="Refresh Orders", 
                                       command=self.refresh_available_orders)
        refresh_orders_btn.grid(row=0, column=2, padx=(0, 20))
        
        ttk.Label(order_frame, text="Parts Made:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.parts_made_var = tk.StringVar()
        self.parts_made_entry = ttk.Entry(order_frame, textvariable=self.parts_made_var, width=10)
        self.parts_made_entry.grid(row=1, column=1, padx=(0, 10), pady=(10, 0), sticky=tk.W)
        
        self.select_order_btn = ttk.Button(order_frame, text="Select Order", command=self.select_order_for_scrap)
        self.select_order_btn.grid(row=1, column=2, pady=(10, 0))
        
        # Order Information Section
        order_info_frame = ttk.LabelFrame(main_frame, text="Selected Order Information", padding="10")
        order_info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.order_info_var = tk.StringVar(value="No order selected")
        self.order_info_label = ttk.Label(order_info_frame, textvariable=self.order_info_var, font=("Arial", 10, "bold"))
        self.order_info_label.grid(row=0, column=0)
        
        self.create_operator_scrap_widgets(main_frame)
    
    def create_operator_scrap_widgets(self, main_frame):
        # Scrap Tracking Section
        scrap_frame = ttk.LabelFrame(main_frame, text="Scrap Tracking", padding="10")
        scrap_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrap Entry
        ttk.Label(scrap_frame, text="Scrap Reason:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.scrap_reason_var = tk.StringVar()
        self.scrap_reason_combo = ttk.Combobox(scrap_frame, textvariable=self.scrap_reason_var, values=scrap_reasons, state="readonly")
        self.scrap_reason_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(scrap_frame, text="Scrap Count:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.scrap_count_var = tk.StringVar()
        self.scrap_count_entry = ttk.Entry(scrap_frame, textvariable=self.scrap_count_var, width=10)
        self.scrap_count_entry.grid(row=0, column=3, padx=(0, 20))
        
        self.add_scrap_btn = ttk.Button(scrap_frame, text="Add Scrap", command=self.add_scrap_entry)
        self.add_scrap_btn.grid(row=0, column=4)
        
        # Scrap List
        ttk.Label(scrap_frame, text="Scrap Entries:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        self.scrap_listbox = tk.Listbox(scrap_frame, height=6)
        self.scrap_listbox.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.remove_scrap_btn = ttk.Button(scrap_frame, text="Remove Selected", command=self.remove_scrap_entry)
        self.remove_scrap_btn.grid(row=2, column=4, sticky=tk.N)
        
        self.finish_btn = ttk.Button(scrap_frame, text="Finish & Calculate", command=self.finish_tracking)
        self.finish_btn.grid(row=3, column=0, columnspan=5, pady=(10, 0))
        
        # Downtime Tracking Section
        downtime_frame = ttk.LabelFrame(main_frame, text="Downtime Tracking", padding="10")
        downtime_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Downtime Entry
        ttk.Label(downtime_frame, text="Downtime Reason:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.downtime_reason_var = tk.StringVar()
        self.downtime_reason_combo = ttk.Combobox(downtime_frame, textvariable=self.downtime_reason_var, 
                                                values=downtime_reasons, state="readonly")
        self.downtime_reason_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(downtime_frame, text="Duration (minutes):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.downtime_duration_var = tk.StringVar()
        self.downtime_duration_entry = ttk.Entry(downtime_frame, textvariable=self.downtime_duration_var, width=10)
        self.downtime_duration_entry.grid(row=0, column=3, padx=(0, 20))
        
        self.add_downtime_btn = ttk.Button(downtime_frame, text="Log Downtime", command=self.log_downtime)
        self.add_downtime_btn.grid(row=0, column=4)
        
        # Recent downtime entries display
        ttk.Label(downtime_frame, text="Recent Downtime Entries:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        self.downtime_listbox = tk.Listbox(downtime_frame, height=4)
        self.downtime_listbox.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Load recent downtime entries button
        self.refresh_downtime_btn = ttk.Button(downtime_frame, text="Refresh Downtime", command=self.refresh_downtime_entries)
        self.refresh_downtime_btn.grid(row=2, column=4, sticky=tk.N)
        
        # SMC Scrap Tracking Section
        smc_scrap_frame = ttk.LabelFrame(main_frame, text="SMC (Sheet Moulding Compound) Scrap Tracking", padding="10")
        smc_scrap_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # SMC Scrap Entry
        ttk.Label(smc_scrap_frame, text="Part Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.smc_part_type_var = tk.StringVar()
        self.smc_part_type_entry = ttk.Entry(smc_scrap_frame, textvariable=self.smc_part_type_var, width=15)
        self.smc_part_type_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(smc_scrap_frame, text="SMC Scrap Reason:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.smc_scrap_reason_var = tk.StringVar()
        self.smc_scrap_reason_combo = ttk.Combobox(smc_scrap_frame, textvariable=self.smc_scrap_reason_var, 
                                                  values=smc_scrap_reasons, state="readonly", width=18)
        self.smc_scrap_reason_combo.grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(smc_scrap_frame, text="SMC Count:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.smc_scrap_count_var = tk.StringVar()
        self.smc_scrap_count_entry = ttk.Entry(smc_scrap_frame, textvariable=self.smc_scrap_count_var, width=10)
        self.smc_scrap_count_entry.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))
        
        self.log_smc_scrap_btn = ttk.Button(smc_scrap_frame, text="Log SMC Scrap", command=self.log_smc_scrap)
        self.log_smc_scrap_btn.grid(row=1, column=2, pady=(10, 0))
        
        # Recent SMC scrap entries display
        ttk.Label(smc_scrap_frame, text="Recent SMC Scrap Entries:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        self.smc_scrap_listbox = tk.Listbox(smc_scrap_frame, height=4)
        self.smc_scrap_listbox.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Refresh SMC scrap entries button
        self.refresh_smc_scrap_btn = ttk.Button(smc_scrap_frame, text="Refresh SMC Scrap", command=self.refresh_smc_scrap_entries)
        self.refresh_smc_scrap_btn.grid(row=3, column=3, sticky=tk.N)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)  # Updated to row 7 for results
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Initially disable scrap tracking until order is selected
        self.toggle_scrap_tracking(False)
        
        # Load available orders (with retry for robustness)
        try:
            self.refresh_available_orders()
        except Exception as e:
            print(f"Initial order refresh failed: {e}")
            # Set fallback message
            if hasattr(self, 'order_selection_combo'):
                self.order_selection_combo['values'] = ["Failed to load orders - click Refresh"]
                self.order_selection_combo.set("Failed to load orders - click Refresh")
        
        # Load initial downtime entries for operator
        self.refresh_downtime_entries()
        
        # Load initial SMC scrap entries for operator
        self.refresh_smc_scrap_entries()
        
        # Start automatic refresh timer for operator interface (refresh every 30 seconds)
        self.start_auto_refresh()
    
    def refresh_available_orders(self):
        """Refresh the list of available orders for operator selection"""
        try:
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            
            # Get active orders
            cursor.execute('''
                SELECT order_number, part_number, parts_per_order, created_date, status 
                FROM orders 
                WHERE status = 'Active' 
                ORDER BY order_number DESC
            ''')
            orders = cursor.fetchall()
            conn.close()
            
            # Create display strings for combobox
            order_options = []
            self.order_data = {}  # Store order details for lookup
            
            for order_num, part_num, parts_per_order, created_date, status in orders:
                display_text = f"Order {order_num}: {part_num} (Qty: {parts_per_order})"
                order_options.append(display_text)
                self.order_data[display_text] = {
                    'order_number': order_num,
                    'part_number': part_num,
                    'parts_per_order': parts_per_order,
                    'created_date': created_date
                }
            
            # Update combobox
            if hasattr(self, 'order_selection_combo'):
                self.order_selection_combo['values'] = order_options
                if not order_options:
                    self.order_selection_combo.set("No active orders available")
                else:
                    self.order_selection_combo.set("")  # Clear current selection
                    
        except Exception as e:
            print(f"Error refreshing orders: {e}")
            messagebox.showerror("Error", f"Failed to refresh orders: {str(e)}")
    
    def start_auto_refresh(self):
        """Start automatic refresh of available orders for operator interface"""
        try:
            if not self.is_admin and hasattr(self, 'order_selection_combo'):
                self.refresh_available_orders()
                # Schedule next refresh in 30 seconds
                self.root.after(30000, self.start_auto_refresh)
        except Exception as e:
            print(f"Error in auto-refresh: {e}")
            # Still schedule next refresh even if current one failed
            try:
                if not self.is_admin and hasattr(self, 'order_selection_combo'):
                    self.root.after(30000, self.start_auto_refresh)
            except:
                pass
    
    def toggle_scrap_tracking(self, enabled):
        state = "normal" if enabled else "disabled"
        
        # Order selection widgets should always remain enabled for operators
        # Only disable actual scrap tracking widgets until order is selected
        
        # Keep order selection widgets enabled (don't disable these)
        # - order_selection_combo should stay as "readonly"
        # - parts_made_entry should stay enabled 
        # - select_order_btn should stay enabled
        
        # Only disable scrap tracking widgets until order is selected
        if hasattr(self, 'scrap_reason_combo'):
            self.scrap_reason_combo.config(state=state)
        if hasattr(self, 'scrap_count_entry'):
            self.scrap_count_entry.config(state=state)
        if hasattr(self, 'add_scrap_btn'):
            self.add_scrap_btn.config(state=state)
        if hasattr(self, 'remove_scrap_btn'):
            self.remove_scrap_btn.config(state=state)
        if hasattr(self, 'finish_btn'):
            self.finish_btn.config(state=state)
    
    def logout(self):
        # Clear all widgets from main window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Reset user state
        self.is_admin = False
        self.current_user = ""
        self.operator_number = None
        self.order = None
        self.scrap_entries = []
        
        # Reset window title
        self.root.title("Parts Tracker")
        
        # Show login screen again
        self.show_login()
    
    def close_application(self):
        """Close the application cleanly"""
        try:
            result = messagebox.askyesno("Exit Application", 
                                       "Are you sure you want to exit the Parts Tracker application?")
            if result:
                print("Application closing by user request")
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            print(f"Error during application close: {e}")
            import sys
            sys.exit(0)
    
    def refresh_orders(self):
        if not hasattr(self, 'orders_text'):
            return
        
        # Get orders from database (same query as operator to ensure consistency)
        conn = sqlite3.connect('parts_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT order_number, part_number, parts_per_order, created_date, status FROM orders WHERE status = \'Active\' ORDER BY order_number DESC')
        orders = cursor.fetchall()
        conn.close()
        
        # Display orders
        orders_info = "=== ACTIVE ORDERS ===\n\n"
        
        if orders:
            for order_num, part_num, parts_per_order, created_date, status in orders:
                orders_info += f"Order #{order_num}: Part {part_num}, Quantity: {parts_per_order}, Status: {status}\n"
                orders_info += f"  Created: {created_date}\n\n"
        else:
            orders_info += "No active orders found in database.\n"
        
        self.orders_text.delete(1.0, tk.END)
        self.orders_text.insert(1.0, orders_info)
    
    def add_operator(self):
        # Check if user is admin
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can manage operators")
            return
            
        # Validate inputs with enhanced security
        op_number_input = sanitize_input(self.new_op_number_var.get(), 10, 'numeric')
        op_name_input = sanitize_input(self.new_op_name_var.get(), MAX_OPERATOR_NAME_LENGTH, 'operator_name')
        
        if not op_number_input or not op_name_input:
            messagebox.showerror("Error", "Please fill in both Operator Number and Name")
            return
        
        if not validate_operator_number(op_number_input):
            messagebox.showerror("Error", "Operator Number must be between 0 and 9999")
            return
        
        op_number = int(op_number_input)
        op_name = op_name_input.strip()
        
        if not op_name:
            messagebox.showerror("Error", "Operator Name cannot be empty")
            return
        
        try:
            if add_operator(op_number, op_name):
                messagebox.showinfo("Success", f"Operator {op_number} ({op_name}) added successfully!")
                self.new_op_number_var.set("")
                self.new_op_name_var.set("")
                self.refresh_operators()
            else:
                messagebox.showerror("Error", f"Operator number {op_number} already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add operator: {str(e)}")
    
    def remove_operator(self):
        # Check if user is admin
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can manage operators")
            return
            
        selection = self.operators_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an operator to remove")
            return
        
        item = self.operators_tree.item(selection[0])
        op_number = int(item['values'][0])
        anonymized_id = item['values'][1]
        
        result = messagebox.askyesno("Confirm", f"Are you sure you want to remove Operator {op_number} ({anonymized_id})?")
        
        if result:
            if remove_operator(op_number):
                messagebox.showinfo("Success", f"Operator {op_number} removed successfully!")
                self.refresh_operators()
            else:
                messagebox.showerror("Error", f"Failed to remove operator {op_number}")
    
    def refresh_operators(self):
        if not hasattr(self, 'operators_tree'):
            return
        
        # Clear existing items
        for item in self.operators_tree.get_children():
            self.operators_tree.delete(item)
        
        # Get operators from database
        operators = get_all_operators()
        
        # Insert operators into treeview
        for op_number, anonymized_name, created_date in operators:
            self.operators_tree.insert('', tk.END, values=(op_number, anonymized_name, created_date))
    
    def create_analytics_widgets(self, analytics_tab):
        """Create analytics interface for admin"""
        # Analytics Overview Section
        overview_frame = ttk.LabelFrame(analytics_tab, text="Operator Performance Overview", padding="10")
        overview_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Analytics table
        analytics_columns = ('Op#', 'Operator ID', 'Parts Made', 'Scrap Total', 'Good Parts', 
                           'Orders', 'Efficiency %', 'Scrap Rate %', 'Downtime (hrs)', 'SMC Scrap', 'Part Types')
        self.analytics_tree = ttk.Treeview(overview_frame, columns=analytics_columns, show='headings', height=12)
        
        # Configure column widths and headings
        column_widths = {'Op#': 50, 'Operator ID': 100, 'Parts Made': 80, 'Scrap Total': 80, 
                        'Good Parts': 80, 'Orders': 60, 'Efficiency %': 80, 
                        'Scrap Rate %': 80, 'Downtime (hrs)': 90, 'SMC Scrap': 80, 'Part Types': 80}
        
        for col in analytics_columns:
            self.analytics_tree.heading(col, text=col)
            width = column_widths.get(col, 80)
            self.analytics_tree.column(col, width=width, anchor='center')
        
        self.analytics_tree.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for analytics table
        analytics_scrollbar = ttk.Scrollbar(overview_frame, orient=tk.VERTICAL, command=self.analytics_tree.yview)
        analytics_scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.analytics_tree.configure(yscrollcommand=analytics_scrollbar.set)
        
        # Analytics Control Buttons
        analytics_button_frame = ttk.Frame(overview_frame)
        analytics_button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        refresh_analytics_btn = ttk.Button(analytics_button_frame, text="Refresh Analytics", 
                                         command=self.refresh_analytics)
        refresh_analytics_btn.grid(row=0, column=0, padx=(0, 10))
        
        detailed_analytics_btn = ttk.Button(analytics_button_frame, text="View Detailed Analytics", 
                                          command=self.show_detailed_analytics)
        detailed_analytics_btn.grid(row=0, column=1, padx=(0, 10))
        
        export_analytics_btn = ttk.Button(analytics_button_frame, text="Export Analytics", 
                                         command=self.export_analytics)
        export_analytics_btn.grid(row=0, column=2)
        
        # Summary Statistics Section
        summary_frame = ttk.LabelFrame(analytics_tab, text="Summary Statistics", padding="10")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=8, width=80)
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for analytics tab
        analytics_tab.columnconfigure(0, weight=1)
        analytics_tab.rowconfigure(0, weight=3)  # Give more space to the table
        analytics_tab.rowconfigure(1, weight=1)  # Less space to summary
        overview_frame.columnconfigure(0, weight=1)
        overview_frame.rowconfigure(0, weight=1)
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        
        # Load initial analytics data
        self.refresh_analytics()
    
    def refresh_analytics(self):
        """Refresh analytics data display"""
        if not hasattr(self, 'analytics_tree'):
            return
        
        try:
            # Clear existing analytics data
            for item in self.analytics_tree.get_children():
                self.analytics_tree.delete(item)
            
            # Get analytics data
            analytics_data = get_operator_analytics()
            
            # Populate analytics table
            total_operators = len(analytics_data)
            total_parts_made = sum(data['estimated_parts_made'] for data in analytics_data)
            total_scrap = sum(data['total_scrap'] for data in analytics_data)
            total_good_parts = sum(data['good_parts_estimate'] for data in analytics_data)
            total_downtime_hours = sum(data['total_downtime_hours'] for data in analytics_data)
            total_smc_scrap = sum(data['total_smc_scrap'] for data in analytics_data)
            avg_efficiency = sum(data['efficiency_percentage'] for data in analytics_data) / max(total_operators, 1)
            avg_scrap_rate = sum(data['scrap_rate_percentage'] for data in analytics_data) / max(total_operators, 1)
            avg_downtime_hours = total_downtime_hours / max(total_operators, 1)
            avg_smc_scrap = total_smc_scrap / max(total_operators, 1)
            
            for data in analytics_data:
                values = (
                    data['operator_number'],
                    data['anonymized_name'],
                    data['estimated_parts_made'],
                    data['total_scrap'],
                    data['good_parts_estimate'],
                    data['orders_worked'],
                    f"{data['efficiency_percentage']:.1f}%",
                    f"{data['scrap_rate_percentage']:.1f}%",
                    f"{data['total_downtime_hours']:.1f}",
                    data['total_smc_scrap'],
                    data['part_types_worked']
                )
                self.analytics_tree.insert('', tk.END, values=values)
            
            # Update summary statistics
            summary_text = "=== OPERATOR PERFORMANCE SUMMARY ===\n\n"
            summary_text += f"Total Operators: {total_operators}\n"
            summary_text += f"Total Estimated Parts Made: {total_parts_made:,}\n"
            summary_text += f"Total Scrap Parts: {total_scrap:,}\n"
            summary_text += f"Total Good Parts: {total_good_parts:,}\n"
            summary_text += f"Total Downtime Hours: {total_downtime_hours:.1f}\n"
            summary_text += f"Total SMC Scrap: {total_smc_scrap:,}\n"
            summary_text += f"Overall Scrap Rate: {(total_scrap / max(total_parts_made, 1)) * 100:.2f}%\n"
            summary_text += f"Average Operator Efficiency: {avg_efficiency:.2f}%\n"
            summary_text += f"Average Scrap Rate: {avg_scrap_rate:.2f}%\n"
            summary_text += f"Average Downtime per Operator: {avg_downtime_hours:.1f} hours\n"
            summary_text += f"Average SMC Scrap per Operator: {avg_smc_scrap:.1f}\n\n"
            
            # Top/Bottom performers
            if analytics_data:
                sorted_by_efficiency = sorted(analytics_data, key=lambda x: x['efficiency_percentage'], reverse=True)
                sorted_by_scrap = sorted(analytics_data, key=lambda x: x['scrap_rate_percentage'])
                
                summary_text += "=== TOP PERFORMERS (by Efficiency) ===\n"
                for i, data in enumerate(sorted_by_efficiency[:3]):
                    summary_text += f"{i+1}. Operator {data['operator_number']} ({data['anonymized_name']}): {data['efficiency_percentage']:.1f}% efficiency\n"
                
                summary_text += "\n=== LOWEST SCRAP RATES ===\n"
                for i, data in enumerate(sorted_by_scrap[:3]):
                    summary_text += f"{i+1}. Operator {data['operator_number']} ({data['anonymized_name']}): {data['scrap_rate_percentage']:.1f}% scrap rate\n"
                
                # Alert for high scrap rates
                high_scrap_operators = [d for d in analytics_data if d['scrap_rate_percentage'] > 10]
                if high_scrap_operators:
                    summary_text += "\n*** HIGH SCRAP RATE ALERTS (>10%) ***\n"
                    for data in high_scrap_operators:
                        summary_text += f"* Operator {data['operator_number']}: {data['scrap_rate_percentage']:.1f}% scrap rate\n"
                
                # Alert for high downtime
                high_downtime_operators = [d for d in analytics_data if d['total_downtime_hours'] > 8]
                if high_downtime_operators:
                    summary_text += "\n*** HIGH DOWNTIME ALERTS (>8 hours) ***\n"
                    for data in high_downtime_operators:
                        summary_text += f"* Operator {data['operator_number']}: {data['total_downtime_hours']:.1f} hours downtime\n"
                
                # Alert for high SMC scrap
                high_smc_scrap_operators = [d for d in analytics_data if d['total_smc_scrap'] > 50]
                if high_smc_scrap_operators:
                    summary_text += "\n*** HIGH SMC SCRAP ALERTS (>50 SMCs) ***\n"
                    for data in high_smc_scrap_operators:
                        summary_text += f"* Operator {data['operator_number']}: {data['total_smc_scrap']} SMC scrap\n"
            
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, summary_text)
            
            print(f"Analytics refreshed: {total_operators} operators analyzed")
            
        except Exception as e:
            print(f"Error refreshing analytics: {e}") 
            messagebox.showerror("Error", f"Failed to refresh analytics: {str(e)}")
    
    def show_detailed_analytics(self):
        """Show detailed analytics for selected operator"""
        selection = self.analytics_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an operator to view detailed analytics")
            return
        
        item = self.analytics_tree.item(selection[0])
        operator_number = int(item['values'][0])
        
        # Get detailed analytics
        detailed_data = get_detailed_operator_analytics(operator_number)
        if not detailed_data:
            messagebox.showerror("Error", "Could not retrieve detailed analytics for this operator")
            return
        
        # Create detailed analytics window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Detailed Analytics - Operator {operator_number}")
        detail_window.geometry("900x700")
        detail_window.transient(self.root)
        
        # Main frame
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Operator info
        info_frame = ttk.LabelFrame(main_frame, text="Operator Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Operator Number: {detailed_data['operator_number']}", 
                 font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=f"Anonymized ID: {detailed_data['anonymized_name']}", 
                 font=("Arial", 10)).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Label(info_frame, text=f"Created: {detailed_data['created_date']}", 
                 font=("Arial", 10)).grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        
        # Recent activity
        activity_frame = ttk.LabelFrame(main_frame, text="Recent Activity", padding="10")
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create notebook for scrap, downtime, and SMC scrap tabs
        activity_notebook = ttk.Notebook(activity_frame)
        activity_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Scrap entries tab
        scrap_tab = ttk.Frame(activity_notebook)
        activity_notebook.add(scrap_tab, text="Production Scrap")
        
        # Activity table for scrap
        activity_columns = ('Date/Time', 'Part Number', 'Order #', 'Scrap Reason', 'Count', 'Order Qty')
        activity_tree = ttk.Treeview(scrap_tab, columns=activity_columns, show='headings', height=12)
        
        for col in activity_columns:
            activity_tree.heading(col, text=col)
            if col == 'Date/Time':
                activity_tree.column(col, width=140)
            elif col in ['Count', 'Order #', 'Order Qty']:
                activity_tree.column(col, width=80, anchor='center')
            else:
                activity_tree.column(col, width=120)
        
        activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Activity scrollbar
        activity_scroll = ttk.Scrollbar(scrap_tab, orient=tk.VERTICAL, command=activity_tree.yview)
        activity_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        activity_tree.configure(yscrollcommand=activity_scroll.set)
        
        # Populate activity data
        for entry in detailed_data['detailed_entries']:
            timestamp, part_num, order_num, scrap_reason, scrap_count, parts_per_order = entry
            values = (
                timestamp,
                part_num or 'N/A',
                order_num or 'N/A',
                scrap_reason,
                scrap_count,
                parts_per_order or 'N/A'
            )
            activity_tree.insert('', tk.END, values=values)
        
        # Downtime entries tab
        downtime_tab = ttk.Frame(activity_notebook)
        activity_notebook.add(downtime_tab, text="Downtime")
        
        # Downtime table
        downtime_columns = ('Date/Time', 'Downtime Reason', 'Duration (min)', 'Duration (hrs)')
        downtime_tree = ttk.Treeview(downtime_tab, columns=downtime_columns, show='headings', height=12)
        
        for col in downtime_columns:
            downtime_tree.heading(col, text=col)
            if col == 'Date/Time':
                downtime_tree.column(col, width=140)
            elif col in ['Duration (min)', 'Duration (hrs)']:
                downtime_tree.column(col, width=100, anchor='center')
            else:
                downtime_tree.column(col, width=200)
        
        downtime_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Downtime scrollbar
        downtime_scroll = ttk.Scrollbar(downtime_tab, orient=tk.VERTICAL, command=downtime_tree.yview)
        downtime_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        downtime_tree.configure(yscrollcommand=downtime_scroll.set)
        
        # Populate downtime data
        for entry in detailed_data['downtime_entries']:
            timestamp, reason, duration_minutes, shift_date = entry
            duration_hours = duration_minutes / 60
            values = (
                timestamp,
                reason,
                duration_minutes,
                f"{duration_hours:.2f}"
            )
            downtime_tree.insert('', tk.END, values=values)
        
        # SMC Scrap entries tab
        smc_scrap_tab = ttk.Frame(activity_notebook)
        activity_notebook.add(smc_scrap_tab, text="SMC Scrap")
        
        # SMC Scrap table
        smc_scrap_columns = ('Date/Time', 'Part Type', 'SMC Scrap Reason', 'SMC Count')
        smc_scrap_tree = ttk.Treeview(smc_scrap_tab, columns=smc_scrap_columns, show='headings', height=12)
        
        for col in smc_scrap_columns:
            smc_scrap_tree.heading(col, text=col)
            if col == 'Date/Time':
                smc_scrap_tree.column(col, width=140)
            elif col == 'SMC Count':
                smc_scrap_tree.column(col, width=100, anchor='center')
            else:
                smc_scrap_tree.column(col, width=150)
        
        smc_scrap_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # SMC Scrap scrollbar
        smc_scrap_scroll = ttk.Scrollbar(smc_scrap_tab, orient=tk.VERTICAL, command=smc_scrap_tree.yview)
        smc_scrap_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        smc_scrap_tree.configure(yscrollcommand=smc_scrap_scroll.set)
        
        # Populate SMC scrap data
        for entry in detailed_data['smc_scrap_entries']:
            timestamp, part_type, smc_reason, smc_count, shift_date = entry
            values = (
                timestamp,
                part_type,
                smc_reason,
                smc_count
            )
            smc_scrap_tree.insert('', tk.END, values=values)
        
        # Daily trends
        trends_frame = ttk.LabelFrame(main_frame, text="Daily Performance Trends (Last 30 Days)", padding="10")
        trends_frame.pack(fill=tk.X)
        
        # Create notebook for scrap, downtime, and SMC scrap trends
        trends_notebook = ttk.Notebook(trends_frame)
        trends_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Scrap trends tab
        scrap_trends_tab = ttk.Frame(trends_notebook)
        trends_notebook.add(scrap_trends_tab, text="Production Scrap")
        
        scrap_trends_text = scrolledtext.ScrolledText(scrap_trends_tab, height=6)
        scrap_trends_text.pack(fill=tk.BOTH, expand=True)
        
        scrap_trends_content = "Date\t\tDaily Scrap\tOrders Worked\n"
        scrap_trends_content += "-" * 50 + "\n"
        
        for date, daily_scrap, orders_worked in detailed_data['daily_stats']:
            scrap_trends_content += f"{date}\t\t{daily_scrap}\t\t{orders_worked}\n"
        
        if not detailed_data['daily_stats']:
            scrap_trends_content += "No daily production scrap activity data available.\n"
        
        scrap_trends_text.insert(1.0, scrap_trends_content)
        scrap_trends_text.config(state=tk.DISABLED)
        
        # Downtime trends tab
        downtime_trends_tab = ttk.Frame(trends_notebook)
        trends_notebook.add(downtime_trends_tab, text="Downtime")
        
        downtime_trends_text = scrolledtext.ScrolledText(downtime_trends_tab, height=6)
        downtime_trends_text.pack(fill=tk.BOTH, expand=True)
        
        downtime_trends_content = "Date\t\tDowntime (min)\tDowntime Events\tDowntime (hrs)\n"
        downtime_trends_content += "-" * 70 + "\n"
        
        for date, downtime_minutes, events in detailed_data['daily_downtime_stats']:
            downtime_hours = downtime_minutes / 60
            downtime_trends_content += f"{date}\t\t{downtime_minutes}\t\t{events}\t\t{downtime_hours:.2f}\n"
        
        if not detailed_data['daily_downtime_stats']:
            downtime_trends_content += "No daily downtime activity data available.\n"
        
        downtime_trends_text.insert(1.0, downtime_trends_content)
        downtime_trends_text.config(state=tk.DISABLED)
        
        # SMC Scrap trends tab
        smc_scrap_trends_tab = ttk.Frame(trends_notebook)
        trends_notebook.add(smc_scrap_trends_tab, text="SMC Scrap")
        
        smc_scrap_trends_text = scrolledtext.ScrolledText(smc_scrap_trends_tab, height=6)
        smc_scrap_trends_text.pack(fill=tk.BOTH, expand=True)
        
        smc_scrap_trends_content = "Date\t\tSMC Scrap\tSMC Events\tPart Types\n"
        smc_scrap_trends_content += "-" * 60 + "\n"
        
        for date, smc_scrap, events, part_types in detailed_data['daily_smc_scrap_stats']:
            smc_scrap_trends_content += f"{date}\t\t{smc_scrap}\t\t{events}\t\t{part_types}\n"
        
        if not detailed_data['daily_smc_scrap_stats']:
            smc_scrap_trends_content += "No daily SMC scrap activity data available.\n"
        
        smc_scrap_trends_text.insert(1.0, smc_scrap_trends_content)
        smc_scrap_trends_text.config(state=tk.DISABLED)
    
    def export_analytics(self):
        """Export analytics data to CSV format"""
        try:
            analytics_data = get_operator_analytics()
            
            # Create export content
            export_content = "Operator_Number,Anonymized_ID,Estimated_Parts_Made,Total_Scrap,Good_Parts,Orders_Worked,Efficiency_Percent,Scrap_Rate_Percent,Downtime_Hours,SMC_Scrap_Total,Part_Types_Worked,Avg_SMC_Scrap_Per_Day,Created_Date\n"
            
            for data in analytics_data:
                export_content += f"{data['operator_number']},{data['anonymized_name']},{data['estimated_parts_made']},{data['total_scrap']},{data['good_parts_estimate']},{data['orders_worked']},{data['efficiency_percentage']},{data['scrap_rate_percentage']},{data['total_downtime_hours']},{data['total_smc_scrap']},{data['part_types_worked']},{data['avg_smc_scrap_per_day']},\n"
            
            # Show export data in a new window
            export_window = tk.Toplevel(self.root)
            export_window.title("Analytics Export Data")
            export_window.geometry("800x600")
            export_window.transient(self.root)
            
            export_frame = ttk.Frame(export_window, padding="10")
            export_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(export_frame, text="Analytics Data (CSV Format) - Copy and save to .csv file:", 
                     font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
            
            export_text = scrolledtext.ScrolledText(export_frame, wrap=tk.NONE)
            export_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            export_text.insert(1.0, export_content)
            export_text.config(state=tk.NORMAL)  # Allow copying
            
            ttk.Button(export_frame, text="Close", command=export_window.destroy).pack()
            
            messagebox.showinfo("Export Ready", "Analytics data is ready for export. Copy the content and save as .csv file.")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export analytics: {str(e)}")
    
    def select_order_for_scrap(self):
        # Validate order selection
        selected_order = self.order_selection_var.get()
        parts_input = sanitize_input(self.parts_made_var.get(), 10, 'numeric')
        
        if not selected_order or selected_order == "No active orders available":
            messagebox.showerror("Error", "Please select an order from the dropdown")
            return
        
        if not parts_input:
            messagebox.showerror("Error", "Please enter parts made count")
            return
        
        if not validate_parts_count(parts_input):
            messagebox.showerror("Error", "Please enter a valid parts made count")
            return
        
        parts_made = int(parts_input)
        
        if parts_made <= 0:
            messagebox.showerror("Error", "Parts made must be greater than 0")
            return
        
        # Get order details from selection
        if selected_order not in self.order_data:
            messagebox.showerror("Error", "Invalid order selection")
            return
            
        order_details = self.order_data[selected_order]
        
        # Create order object with actual database data
        self.order = type('Order', (), {
            'order_number': order_details['order_number'],
            'part_number': order_details['part_number'], 
            'parts_per_order': order_details['parts_per_order']
        })()
        
        self.parts_made = parts_made
        
        # Update display
        self.order_info_var.set(f"Order {self.order.order_number}: {self.order.part_number}, "
                               f"Quantity: {self.order.parts_per_order}, Parts Made: {parts_made}")
        
        # Enable scrap tracking
        self.toggle_scrap_tracking(True)
        
        # Clear previous results
        if hasattr(self, 'results_text'):
            self.results_text.delete(1.0, tk.END)
        self.scrap_entries.clear()
        if hasattr(self, 'scrap_listbox'):
            self.scrap_listbox.delete(0, tk.END)
        
        messagebox.showinfo("Order Selected", 
                           f"Order {self.order.order_number} selected for scrap tracking\n"
                           f"Part: {self.order.part_number}\n"
                           f"Order Quantity: {self.order.parts_per_order}\n"
                           f"Parts Made: {parts_made}")
    
    def create_order(self):
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can create orders")
            return
            
        # Validate and sanitize inputs
        part_number = self.part_var.get()
        mix_number = sanitize_input(self.mix_var.get(), MAX_MIX_LENGTH)
        parts_input = sanitize_input(self.parts_per_order_var.get(), 10, 'numeric')
        
        if not part_number:
            messagebox.showerror("Error", "Please select a part number")
            return
        
        if not mix_number:
            messagebox.showerror("Error", "Please enter a mix number")
            return
        
        if not parts_input:
            messagebox.showerror("Error", "Please enter parts per order")
            return
        
        if not validate_parts_count(parts_input):
            messagebox.showerror("Error", "Parts per order must be a positive integer (max 999999)")
            return
        
        parts_per_order = int(parts_input)
        
        # Validate part number is in allowed list
        if part_number not in part_numbers:
            messagebox.showerror("Error", "Invalid part number selected")
            return
        
        # Create order
        full_part_number = part_number + mix_number
        
        try:
            # Save order to database and get order number
            order_number = save_order(full_part_number, parts_per_order)
            
            self.order = Order(full_part_number, parts_per_order)
            self.order.order_number = order_number
            
            # Show success message
            messagebox.showinfo("Order Created", 
                               f"Order {order_number} created successfully!\n"
                               f"Part: {full_part_number}\n"
                               f"Quantity: {parts_per_order}")
            
            # Clear inputs
            self.part_var.set("")
            self.mix_var.set("")
            self.parts_per_order_var.set("")
            
            # Refresh orders display
            self.refresh_orders()
            
            # Also refresh operator available orders if they exist
            if hasattr(self, 'refresh_available_orders'):
                self.refresh_available_orders()
            
            # Refresh analytics if admin
            if self.is_admin and hasattr(self, 'analytics_tree'):
                self.refresh_analytics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")
    
    def add_scrap_entry(self):
        # Get operator number
        if self.is_admin:
            # Admin needs to specify operator number
            try:
                operator_number = int(tk.simpledialog.askstring("Operator Number", 
                                    "Enter operator number for this scrap entry (0-9999):"))
                if operator_number < 0 or operator_number > 9999:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Please enter a valid 4-digit operator number (0-9999)")
                return
        else:
            # Use logged-in operator number
            operator_number = self.operator_number
        
        # Validate scrap reason
        if not self.scrap_reason_var.get():
            messagebox.showerror("Error", "Please select a scrap reason")
            return
        
        # Validate scrap count
        try:
            scrap_count = int(self.scrap_count_var.get())
            if scrap_count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for scrap count")
            return
        
        # Check if total scrap would exceed parts made
        total_scrap = sum(entry[1] for entry in self.scrap_entries) + scrap_count
        if total_scrap > self.parts_made:
            messagebox.showerror("Error", f"Total scrap ({total_scrap}) cannot exceed parts made ({self.parts_made})")
            return
        
        # Add scrap entry
        scrap_entry = (self.scrap_reason_var.get(), scrap_count, operator_number)
        self.scrap_entries.append(scrap_entry)
        
        # Update listbox
        self.scrap_listbox.insert(tk.END, f"{self.scrap_reason_var.get()}: {scrap_count} parts")
        
        # Clear inputs
        self.scrap_reason_var.set("")
        self.scrap_count_var.set("")
    
    def remove_scrap_entry(self):
        selection = self.scrap_listbox.curselection()
        if selection:
            index = selection[0]
            self.scrap_entries.pop(index)
            self.scrap_listbox.delete(index)
    
    def log_downtime(self):
        """Log downtime entry for operator"""
        if not self.operator_number:
            messagebox.showerror("Error", "No operator logged in")
            return
        
        # Validate downtime reason
        if not self.downtime_reason_var.get():
            messagebox.showerror("Error", "Please select a downtime reason")
            return
        
        # Validate downtime duration
        duration_input = sanitize_input(self.downtime_duration_var.get(), 10, 'numeric')
        
        if not duration_input:
            messagebox.showerror("Error", "Please enter downtime duration in minutes")
            return
        
        if not validate_downtime_duration(duration_input):
            messagebox.showerror("Error", "Duration must be between 1 and 480 minutes (1-8 hours)")
            return
        
        duration = int(duration_input)
        
        try:
            # Save downtime entry
            save_downtime_entry(self.operator_number, self.downtime_reason_var.get(), duration)
            
            # Clear inputs
            self.downtime_reason_var.set("")
            self.downtime_duration_var.set("")
            
            # Refresh downtime display
            self.refresh_downtime_entries()
            
            # Show success message
            hours = duration // 60
            mins = duration % 60
            duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            
            messagebox.showinfo("Downtime Logged", 
                               f"Downtime logged successfully:\n"
                               f"Reason: {self.downtime_reason_var.get()}\n"
                               f"Duration: {duration_str}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to log downtime: {str(e)}")
    
    def refresh_downtime_entries(self):
        """Refresh recent downtime entries for current operator"""
        if not hasattr(self, 'downtime_listbox') or not self.operator_number:
            return
        
        try:
            # Clear existing entries
            self.downtime_listbox.delete(0, tk.END)
            
            # Get recent downtime entries
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, downtime_reason, downtime_duration_minutes
                FROM downtime_entries
                WHERE operator_number = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (self.operator_number,))
            
            downtime_entries = cursor.fetchall()
            conn.close()
            
            # Display entries
            if downtime_entries:
                for timestamp, reason, duration in downtime_entries:
                    # Format duration
                    hours = duration // 60
                    mins = duration % 60
                    duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    
                    # Format timestamp 
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    time_str = dt.strftime('%m/%d %H:%M')
                    
                    display_text = f"{time_str} - {reason} ({duration_str})"
                    self.downtime_listbox.insert(tk.END, display_text)
            else:
                self.downtime_listbox.insert(tk.END, "No downtime entries found")
                
        except Exception as e:
            print(f"Error refreshing downtime entries: {e}")
    
    def log_smc_scrap(self):
        """Log SMC (Sheet Moulding Compound) scrap entry for operator"""
        if not self.operator_number:
            messagebox.showerror("Error", "No operator logged in")
            return
        
        # Validate part type
        part_type = sanitize_input(self.smc_part_type_var.get(), 50)
        if not part_type:
            messagebox.showerror("Error", "Please enter a part type")
            return
        
        # Validate SMC scrap reason
        if not self.smc_scrap_reason_var.get():
            messagebox.showerror("Error", "Please select an SMC scrap reason")
            return
        
        # Validate SMC scrap count
        count_input = sanitize_input(self.smc_scrap_count_var.get(), 10, 'numeric')
        
        if not count_input:
            messagebox.showerror("Error", "Please enter SMC scrap count")
            return
        
        if not validate_smc_scrap_count(count_input):
            messagebox.showerror("Error", "SMC count must be between 0 and 999999")
            return
        
        smc_count = int(count_input)
        
        if smc_count <= 0:
            messagebox.showerror("Error", "SMC scrap count must be greater than 0")
            return
        
        try:
            # Save SMC scrap entry
            save_smc_scrap_entry(self.operator_number, part_type, 
                                self.smc_scrap_reason_var.get(), smc_count)
            
            # Clear inputs
            self.smc_part_type_var.set("")
            self.smc_scrap_reason_var.set("")
            self.smc_scrap_count_var.set("")
            
            # Refresh SMC scrap display
            self.refresh_smc_scrap_entries()
            
            # Show success message
            messagebox.showinfo("SMC Scrap Logged", 
                               f"SMC scrap logged successfully:\n"
                               f"Part: {part_type}\n"
                               f"Reason: {self.smc_scrap_reason_var.get()}\n"
                               f"Count: {smc_count} parts")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to log SMC scrap: {str(e)}")
    
    def refresh_smc_scrap_entries(self):
        """Refresh recent SMC scrap entries for current operator"""
        if not hasattr(self, 'smc_scrap_listbox') or not self.operator_number:
            return
        
        try:
            # Clear existing entries
            self.smc_scrap_listbox.delete(0, tk.END)
            
            # Get recent SMC scrap entries
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, part_type, smc_scrap_reason, smc_scrap_count
                FROM smc_scrap_entries
                WHERE operator_number = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (self.operator_number,))
            
            smc_scrap_entries = cursor.fetchall()
            conn.close()
            
            # Display entries
            if smc_scrap_entries:
                for timestamp, part_type, reason, count in smc_scrap_entries:
                    # Format timestamp 
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    time_str = dt.strftime('%m/%d %H:%M')
                    
                    display_text = f"{time_str} - {part_type}: {reason} ({count} parts)"
                    self.smc_scrap_listbox.insert(tk.END, display_text)
            else:
                self.smc_scrap_listbox.insert(tk.END, "No SMC scrap entries found")
                
        except Exception as e:
            print(f"Error refreshing SMC scrap entries: {e}")
    
    def finish_tracking(self):
        if not self.order:
            messagebox.showerror("Error", "Please create an order first")
            return
        
        if not hasattr(self, 'parts_made') or self.parts_made <= 0:
            messagebox.showerror("Error", "Invalid parts made count")
            return
        
        # Calculate totals
        total_scrap = sum(entry[1] for entry in self.scrap_entries)
        good_parts = self.parts_made - total_scrap
        remaining_parts = self.order.parts_per_order - good_parts
        
        # Validate calculations
        if total_scrap > self.parts_made:
            messagebox.showerror("Error", "Total scrap cannot exceed parts made")
            return
        
        try:
            # Save to database
            for reason, count, operator_num in self.scrap_entries:
                save_scrap_entry(operator_num, self.order.part_number, self.order.order_number, reason, count)
            
            # Calculate rate percentage
            part = Part(self.order.part_number)
            rate_percentage = part.rate_percentage(good_parts)
            
            # Display results
            results = []
            results.append("=== PRODUCTION SUMMARY ===")
            results.append(f"Order: {self.order.order_number}")
            results.append(f"Part: {self.order.part_number}")
            results.append(f"Order Quantity: {self.order.parts_per_order}")
            results.append(f"Parts Made: {self.parts_made}")
            results.append("")
            results.append("=== SCRAP BREAKDOWN ===")
            
            if self.scrap_entries:
                for reason, count, _ in self.scrap_entries:
                    results.append(f"  {reason}: {count} parts")
            else:
                results.append("  No scrap recorded")
            
            results.append(f"Total Scrap: {total_scrap}")
            results.append(f"Good Parts: {good_parts}")
            results.append(f"Remaining Parts: {remaining_parts}")
            results.append("")
            results.append("=== PERFORMANCE ===")
            results.append(f"Rate Made: {rate_percentage:.1f}% of expected {part.expected_rate}")
            results.append("")
            results.append("Data saved to database successfully!")
            
            if hasattr(self, 'results_text'):
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(1.0, "\n".join(results))
            
            # Disable scrap tracking until new order (check if method exists to avoid errors)
            if hasattr(self, 'toggle_scrap_tracking'):
                self.toggle_scrap_tracking(False)
            
            messagebox.showinfo("Success", "Production tracking completed and saved successfully!")
            
        except Exception as e:
            import traceback
            print(f"Debug - Exception in finish_tracking: {e}")
            print(f"Debug - Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to save tracking data: {str(e)}")


def main():
    try:
        print("Starting Parts Tracker application...")
        
        # Initialize tkinter root window first
        root = tk.Tk()
        
        # Check if GUI is actually available by testing basic operations
        try:
            # Test basic tkinter operations
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            print(f"Screen resolution: {screen_width}x{screen_height}")
            
            print("GUI environment available, initializing application...")
            
            # Create GUI app (it will handle showing/hiding the window)
            app = PartsTrackerGUI(root)
            
            # Ensure root window gets focus and starts mainloop
            root.focus_force()
            print("Starting main event loop...")
            root.mainloop()
            print("Main event loop ended")
            
        except tk.TclError as gui_error:
            print(f"GUI display error: {gui_error}")
            messagebox.showerror("Error", f"GUI display error: {gui_error}")
            input("Press Enter to continue...")  # Keep window open to see error
            root.destroy()
            raise Exception("GUI cannot be displayed")
        except Exception as app_error:
            print(f"Application error: {app_error}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Application Error", f"Application error: {app_error}")
            input("Press Enter to continue...")  # Keep window open to see error
            raise
            
    except Exception as e:
        print(f"Starting command-line mode. (Reason: {e})")
        try:
            messagebox.showerror("Error", f"Application failed to start: {e}\n\nFalling back to command-line mode.")
        except:
            pass  # messagebox might not work if GUI failed
        input("Press Enter to continue with command-line mode...")
        run_command_line_mode()


def run_command_line_mode():
    """Fallback command-line interface when GUI is not available"""
    print("\n=== PARTS TRACKER - COMMAND LINE MODE ===")
    print("Available admin credentials (stored securely in database):")
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
            admin_command_line_interface()
        else:
            print("Invalid credentials!")
            return
    else:
        try:
            operator_input = input("Enter operator number (0-9999): ").strip()
            operator_num = int(operator_input)
            if 0 <= operator_num <= 9999:
                print(f"Welcome, Operator {operator_num}!")
                operator_command_line_interface(operator_num)
            else:
                print("Invalid operator number!")
                return
        except ValueError:
            print("Invalid operator number!")
            return


def admin_command_line_interface():
    """Command-line interface for administrators"""
    while True:
        print("\nAdmin Menu:")
        print("1. Create new order")
        print("2. View orders")
        print("3. Exit")
        
        choice = input("Select option (1-3): ")
        
        if choice == "1":
            create_order_cli()
        elif choice == "2":
            print("Order viewing functionality would be implemented here.")
        elif choice == "3":
            break
        else:
            print("Invalid choice!")


def operator_command_line_interface(operator_num):
    """Command-line interface for operators"""
    while True:
        print("\nOperator Menu:")
        print("1. Track scrap for existing order")
        print("2. Exit")
        
        choice = input("Select option (1-2): ")
        
        if choice == "1":
            track_scrap_cli(operator_num)
        elif choice == "2":
            break
        else:
            print("Invalid choice!")


def create_order_cli():
    """Command-line order creation"""
    print("\nCreate New Order:")
    
    print("Available part numbers:", ", ".join(part_numbers))
    part_number = input("Enter part number: ")
    
    if part_number not in part_numbers:
        print("Invalid part number!")
        return
    
    mix_number = input("Enter mix number: ")
    part_number_full = part_number + mix_number
    
    order_quantity = random.randint(110, 5000)
    order = Order(part_number_full, order_quantity)
    
    print(f"Order created successfully!")
    print(f"Order Number: {order.order_number}")
    print(f"Part: {part_number_full}")
    print(f"Quantity: {order_quantity}")


def track_scrap_cli(operator_num):
    """Command-line scrap tracking"""
    print("\nTrack Scrap:")
    
    try:
        order_number = int(input("Enter order number: "))
        parts_made = int(input("Enter parts made: "))
        
        if parts_made < 0:
            print("Invalid parts made!")
            return
            
    except ValueError:
        print("Invalid input!")
        return
    
    print("Available scrap reasons:", ", ".join(scrap_reasons))
    
    total_scrap = 0
    while True:
        reason = input("Enter scrap reason (or 'done' to finish): ")
        
        if reason.lower() == 'done':
            break
            
        if reason not in scrap_reasons:
            print("Invalid scrap reason!")
            continue
        
        try:
            count = int(input(f"Enter scrap count for '{reason}': "))
            if count < 0:
                print("Invalid count!")
                continue
                
            if total_scrap + count > parts_made:
                print(f"Total scrap would exceed parts made!")
                continue
                
            total_scrap += count
            
            # Save to database
            save_scrap_entry(operator_num, f"Order{order_number}", order_number, reason, count)
            print(f"Added {count} parts for '{reason}'. Total scrap: {total_scrap}")
            
        except ValueError:
            print("Invalid count!")
    
    good_parts = parts_made - total_scrap
    print(f"\nSummary:")
    print(f"Parts made: {parts_made}")
    print(f"Total scrap: {total_scrap}")
    print(f"Good parts: {good_parts}")
    print("Data saved to database.")


if __name__ == "__main__":
    main()
