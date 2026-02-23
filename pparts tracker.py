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

# Security configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
MIN_LOGIN_DELAY_SECONDS = 1

# Input validation limits
MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_LENGTH = 128
MAX_OPERATOR_NAME_LENGTH = 100
MAX_MIX_LENGTH = 10


def sanitize_input(input_string, max_length=None):
    """Sanitize user input to prevent injection attacks"""
    if input_string is None:
        return ""
    
    # Convert to string and strip whitespace
    sanitized = str(input_string).strip()
    
    # Apply length limit if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove or escape potentially dangerous characters
    # Allow only alphanumeric, spaces, and safe special characters
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


def add_operator(operator_number, operator_name):
    """Add operator with hashed name for privacy protection"""
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    # Validate inputs
    if not validate_operator_number(operator_number):
        conn.close()
        return False
    
    # Sanitize operator name
    operator_name = sanitize_input(operator_name, MAX_OPERATOR_NAME_LENGTH)
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
            self.login_window.geometry("400x350")
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
            y = (screen_height // 2) - (350 // 2)
            
            # Ensure window is not off-screen
            x = max(0, min(x, screen_width - 400))
            y = max(0, min(y, screen_height - 350))
            
            self.login_window.geometry(f"400x350+{x}+{y}")
            
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
        
        # Login button
        login_btn = ttk.Button(main_frame, text="Login", command=self.login)
        login_btn.pack(pady=(10, 0))
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="red")
        self.status_label.pack(pady=(10, 0))
    
    def toggle_admin_fields(self):
        if self.login_type.get() == "admin":
            self.username_frame.pack(fill=tk.X, pady=(0, 10))
            self.password_frame.pack(fill=tk.X, pady=(0, 10))
            self.operator_frame.pack_forget()
        else:
            self.username_frame.pack_forget()
            self.password_frame.pack_forget()
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
            operator_input = sanitize_input(self.operator_var.get(), 10)
            
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
    
    def on_login_close(self):
        """Handle login window close event"""
        print("Login cancelled by user")
        try:
            messagebox.showinfo("Application Closing", "Login was cancelled. The application will now close.")
        except:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            import sys
            sys.exit(1)


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
            
            logout_btn = ttk.Button(user_frame, text="Logout", command=self.logout)
            logout_btn.pack(side=tk.RIGHT)
            
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
        
        ttk.Label(order_frame, text="Order Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.order_number_var = tk.StringVar()
        self.order_number_entry = ttk.Entry(order_frame, textvariable=self.order_number_var, width=10)
        self.order_number_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(order_frame, text="Parts Made:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.parts_made_var = tk.StringVar()
        self.parts_made_entry = ttk.Entry(order_frame, textvariable=self.parts_made_var, width=10)
        self.parts_made_entry.grid(row=0, column=3, padx=(0, 20))
        
        self.select_order_btn = ttk.Button(order_frame, text="Select Order", command=self.select_order_for_scrap)
        self.select_order_btn.grid(row=0, column=4)
        
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
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Initially disable scrap tracking
        self.toggle_scrap_tracking(False)
    
    def toggle_scrap_tracking(self, enabled):
        state = "normal" if enabled else "disabled"
        self.operator_entry.config(state=state)
        self.scrap_reason_combo.config(state=state)
        self.scrap_count_entry.config(state=state)
        self.add_scrap_btn.config(state=state)
        self.remove_scrap_btn.config(state=state)
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
    
    def refresh_orders(self):
        if not hasattr(self, 'orders_text'):
            return
        
        # Get orders from database
        conn = sqlite3.connect('parts_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT order_number, part_number, parts_per_order, created_date, status FROM orders ORDER BY order_number DESC')
        orders = cursor.fetchall()
        conn.close()
        
        # Display orders
        orders_info = "=== ALL ORDERS ===\n\n"
        
        if orders:
            for order_num, part_num, parts_per_order, created_date, status in orders:
                orders_info += f"Order #{order_num}: Part {part_num}, Quantity: {parts_per_order}, Status: {status}\n"
                orders_info += f"  Created: {created_date}\n\n"
        else:
            orders_info += "No orders found in database.\n"
        
        self.orders_text.delete(1.0, tk.END)
        self.orders_text.insert(1.0, orders_info)
    
    def add_operator(self):
        # Validate inputs with enhanced security
        op_number_input = sanitize_input(self.new_op_number_var.get(), 10)
        op_name_input = sanitize_input(self.new_op_name_var.get(), MAX_OPERATOR_NAME_LENGTH)
        
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
    
    def select_order_for_scrap(self):
        try:
            order_number = int(self.order_number_var.get())
            parts_made = int(self.parts_made_var.get())
            
            if parts_made < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter valid order number and parts made")
            return
        
        # Create a mock order for scrap tracking
        # In production, this would fetch the actual order from database
        self.order = type('Order', (), {
            'order_number': order_number,
            'part_number': f"Part{order_number}",  # Would be fetched from DB
            'parts_per_order': random.randint(110, 5000)  # Would be from DB
        })()
        
        self.parts_made = parts_made
        
        # Update display
        self.order_info_var.set(f"Order {order_number}: {self.order.part_number}, "
                               f"Parts Made: {parts_made}")
        
        # Enable scrap tracking
        self.toggle_scrap_tracking(True)
        
        # Clear previous results
        if hasattr(self, 'results_text'):
            self.results_text.delete(1.0, tk.END)
        self.scrap_entries.clear()
        if hasattr(self, 'scrap_listbox'):
            self.scrap_listbox.delete(0, tk.END)
    
    def create_order(self):
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can create orders")
            return
            
        # Validate and sanitize inputs
        part_number = self.part_var.get()
        mix_number = sanitize_input(self.mix_var.get(), MAX_MIX_LENGTH)
        parts_input = sanitize_input(self.parts_per_order_var.get(), 10)
        
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
            
            # Disable scrap tracking until new order
            self.toggle_scrap_tracking(False)
            
            messagebox.showinfo("Success", "Production tracking completed and saved successfully!")
            
        except Exception as e:
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
