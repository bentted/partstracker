#!/usr/bin/env python3
"""
Shared database and utility functions for Parts Tracker applications.
Used by both operator and admin applications to maintain consistency.
"""

import sqlite3
from datetime import datetime, timedelta
import hashlib
import re
import time

# Data lists
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


def validate_employee_number(employee_number):
    """Validate 5-digit employee number input"""
    try:
        # Convert to string first to handle both string and int inputs
        emp_str = str(employee_number).strip()
        # Check if it's exactly 5 digits
        if len(emp_str) == 5 and emp_str.isdigit():
            num = int(emp_str)
            return 10000 <= num <= 99999
        return False
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
    """Initialize database with all required tables"""
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_number INTEGER NOT NULL,
            clock_in_time TEXT,
            clock_out_time TEXT,
            shift_date TEXT NOT NULL,
            total_hours REAL,
            status TEXT DEFAULT 'clocked_in',
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Create index for performance on login attempts
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_login_attempts_username_time 
        ON login_attempts(username, attempt_time)
    ''')
    
    # Create index for time entries performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_time_entries_employee_date 
        ON time_entries(employee_number, shift_date)
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


def get_all_operators():
    """Get all operators with anonymized names for display"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT operator_number, operator_name_hash, created_date FROM operators ORDER BY operator_number')
    operators = cursor.fetchall()
    
    conn.close()
    
    # Return with anonymized display names
    result = []
    for op_number, name_hash, created_date in operators:
        anonymized_name = f"User_{name_hash[:8]}..."
        result.append((op_number, anonymized_name, created_date))
    
    return result


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
        
        # Calculate efficiency metrics
        efficiency_percentage = 0
        if total_entries > 0:
            efficiency_percentage = max(0, 100 - (total_scrap / max(total_entries, 1)) * 100)
        
        # Anonymize name for display
        anonymized_name = f"User_{name_hash[:8]}..."
        
        analytics_data.append({
            'operator_number': op_number,
            'anonymized_name': anonymized_name,
            'total_entries': total_entries,
            'total_scrap': total_scrap,
            'orders_worked': orders_worked,
            'efficiency': round(efficiency_percentage, 2),
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
        LIMIT 50
    ''', (operator_number,))
    
    detailed_entries = cursor.fetchall()
    
    # Get detailed downtime entries
    cursor.execute('''
        SELECT timestamp, downtime_reason, downtime_duration_minutes, shift_date
        FROM downtime_entries 
        WHERE operator_number = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (operator_number,))
    
    downtime_entries = cursor.fetchall()
    
    # Get detailed SMC scrap entries
    cursor.execute('''
        SELECT timestamp, part_type, smc_scrap_reason, smc_scrap_count, shift_date
        FROM smc_scrap_entries
        WHERE operator_number = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (operator_number,))
    
    smc_scrap_entries = cursor.fetchall()
    
    conn.close()
    
    return {
        'operator_number': operator_number,
        'anonymized_name': f"User_{name_hash[:8]}...",
        'created_date': created_date,
        'scrap_entries': detailed_entries,
        'downtime_entries': downtime_entries,
        'smc_scrap_entries': smc_scrap_entries
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


def get_recent_orders(limit=10):
    """Get recent orders"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT order_number, part_number, parts_per_order, created_date, status
        FROM orders 
        ORDER BY created_date DESC
        LIMIT ?
    ''', (limit,))
    
    orders = cursor.fetchall()
    conn.close()
    
    return orders


def get_order_by_number(order_number):
    """Get specific order by order number"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT order_number, part_number, parts_per_order, created_date, status
        FROM orders 
        WHERE order_number = ?
    ''', (order_number,))
    
    order = cursor.fetchone()
    conn.close()
    
    return order


def clock_in(employee_number):
    """Clock in an employee"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate employee number
    if not validate_employee_number(employee_number):
        conn.close()
        raise ValueError("Invalid 5-digit employee number")
    
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    # Check if employee is already clocked in today
    cursor.execute('''
        SELECT id, clock_in_time, status FROM time_entries 
        WHERE employee_number = ? AND shift_date = ? AND status = 'clocked_in'
    ''', (employee_number, current_date))
    
    existing_entry = cursor.fetchone()
    
    if existing_entry:
        conn.close()
        return False, f"Employee {employee_number} is already clocked in since {existing_entry[1]}"
    
    # Create new clock-in entry
    cursor.execute('''
        INSERT INTO time_entries (employee_number, clock_in_time, shift_date, status, timestamp)
        VALUES (?, ?, ?, 'clocked_in', ?)
    ''', (employee_number, current_time, current_date, current_time))
    
    conn.commit()
    conn.close()
    return True, f"Employee {employee_number} clocked in at {current_datetime.strftime('%H:%M:%S')}"


def clock_out(employee_number):
    """Clock out an employee"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate employee number
    if not validate_employee_number(employee_number):
        conn.close()
        raise ValueError("Invalid 5-digit employee number")
    
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    # Find active clock-in entry for today
    cursor.execute('''
        SELECT id, clock_in_time FROM time_entries 
        WHERE employee_number = ? AND shift_date = ? AND status = 'clocked_in'
    ''', (employee_number, current_date))
    
    entry = cursor.fetchone()
    
    if not entry:
        conn.close()
        return False, f"Employee {employee_number} is not clocked in today"
    
    entry_id, clock_in_time = entry
    
    # Calculate total hours
    try:
        clock_in_dt = datetime.strptime(clock_in_time, '%Y-%m-%d %H:%M:%S')
        time_diff = current_datetime - clock_in_dt
        total_hours = time_diff.total_seconds() / 3600
    except:
        total_hours = 0
    
    # Update entry with clock-out time
    cursor.execute('''
        UPDATE time_entries 
        SET clock_out_time = ?, total_hours = ?, status = 'clocked_out'
        WHERE id = ?
    ''', (current_time, round(total_hours, 2), entry_id))
    
    conn.commit()
    conn.close()
    return True, f"Employee {employee_number} clocked out at {current_datetime.strftime('%H:%M:%S')}. Total hours: {round(total_hours, 2)}"


def get_employee_status(employee_number):
    """Get current clock status for an employee"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    if not validate_employee_number(employee_number):
        conn.close()
        return None, "Invalid employee number"
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT clock_in_time, clock_out_time, status, total_hours FROM time_entries 
        WHERE employee_number = ? AND shift_date = ?
        ORDER BY timestamp DESC LIMIT 1
    ''', (employee_number, current_date))
    
    entry = cursor.fetchone()
    conn.close()
    
    if not entry:
        return "not_clocked_in", "Not clocked in today"
    
    clock_in_time, clock_out_time, status, total_hours = entry
    
    if status == 'clocked_in':
        clock_in_dt = datetime.strptime(clock_in_time, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        elapsed = current_time - clock_in_dt
        hours_worked = elapsed.total_seconds() / 3600
        return "clocked_in", f"Clocked in at {clock_in_dt.strftime('%H:%M:%S')} - Current hours: {round(hours_worked, 2)}"
    else:
        return "clocked_out", f"Clocked out - Total hours today: {total_hours or 0}"


def get_all_time_entries(limit=100):
    """Get all time entries for admin view"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, employee_number, shift_date, clock_in_time, clock_out_time, 
               total_hours, status, timestamp
        FROM time_entries 
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    entries = cursor.fetchall()
    conn.close()
    return entries


def get_employee_time_summary():
    """Get time summary for all employees"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT employee_number,
               COUNT(*) as total_days,
               SUM(total_hours) as total_hours,
               AVG(total_hours) as avg_hours_per_day,
               MAX(shift_date) as last_worked
        FROM time_entries 
        WHERE status = 'clocked_out'
        GROUP BY employee_number
        ORDER BY employee_number
    ''')
    
    summary = cursor.fetchall()
    conn.close()
    return summary


def update_time_entry(entry_id, clock_in_time, clock_out_time):
    """Update a time entry (admin function)"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Calculate total hours
    try:
        if clock_in_time and clock_out_time:
            clock_in_dt = datetime.strptime(clock_in_time, '%Y-%m-%d %H:%M:%S')
            clock_out_dt = datetime.strptime(clock_out_time, '%Y-%m-%d %H:%M:%S')
            time_diff = clock_out_dt - clock_in_dt
            total_hours = time_diff.total_seconds() / 3600
            status = 'clocked_out'
        else:
            total_hours = None
            status = 'clocked_in' if clock_in_time and not clock_out_time else 'clocked_out'
    except:
        total_hours = None
        status = 'clocked_out'
    
    cursor.execute('''
        UPDATE time_entries 
        SET clock_in_time = ?, clock_out_time = ?, total_hours = ?, status = ?
        WHERE id = ?
    ''', (clock_in_time, clock_out_time, round(total_hours, 2) if total_hours else None, status, entry_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0