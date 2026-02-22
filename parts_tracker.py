import random
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import sys
import os

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

# Admin credentials (in production, store securely with hashing)
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
    print(f"Scrap entry saved: {scrap_count} parts for reason '{scrap_reason}'")


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
            username = self.username_var.get()
            password = self.password_var.get()
            
            if not username or not password:
                self.status_var.set("Please enter username and password")
                return
            
            if authenticate_admin(username, password):
                print(f"Admin login successful: {username}")
                self.is_admin = True
                self.username = username
                self.login_window.destroy()
                self.callback(self.is_admin, self.username)
            else:
                self.status_var.set("Invalid credentials")
                print("Admin login failed: Invalid credentials")
        else:
            # Operator login
            try:
                operator_num = int(self.operator_var.get())
                if operator_num < 0 or operator_num > 9999:
                    raise ValueError
                print(f"Operator login successful: {operator_num}")
                self.is_admin = False
                self.username = f"Operator {operator_num}"
                self.login_window.destroy()
                self.callback(self.is_admin, self.username, operator_num)
            except ValueError:
                self.status_var.set("Please enter a valid 4-digit operator number (0-9999)")
                print("Operator login failed: Invalid operator number")
    
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
            
            # Hide main window until login completes
            self.root.withdraw()
            
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
        
        # Part Selection Section (Admin Only)
        part_frame = ttk.LabelFrame(main_frame, text="Order Creation (Admin Only)", padding="10")
        part_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(part_frame, text="Part Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.part_var = tk.StringVar()
        self.part_combo = ttk.Combobox(part_frame, textvariable=self.part_var, values=part_numbers, state="readonly")
        self.part_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(part_frame, text="Mix Number:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.mix_var = tk.StringVar()
        self.mix_entry = ttk.Entry(part_frame, textvariable=self.mix_var, width=10)
        self.mix_entry.grid(row=0, column=3, padx=(0, 20))
        
        self.create_order_btn = ttk.Button(part_frame, text="Create New Order", command=self.create_order)
        self.create_order_btn.grid(row=0, column=4)
        
        # Current Orders Section
        orders_frame = ttk.LabelFrame(main_frame, text="Current Orders", padding="10")
        orders_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.orders_text = scrolledtext.ScrolledText(orders_frame, height=15, width=80)
        self.orders_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        refresh_btn = ttk.Button(orders_frame, text="Refresh Orders", command=self.refresh_orders)
        refresh_btn.grid(row=1, column=0, pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        orders_frame.columnconfigure(0, weight=1)
        orders_frame.rowconfigure(0, weight=1)
        
        self.refresh_orders()
    
    def create_operator_widgets(self, main_frame):
        # Operator-specific widgets (scrap tracking only)
        
        # Scrap Entry Section
        scrap_frame = ttk.LabelFrame(main_frame, text="Scrap Entry", padding="10")
        scrap_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Current order selection
        ttk.Label(scrap_frame, text="Order Number:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.order_var = tk.StringVar()
        self.order_combo = ttk.Combobox(scrap_frame, textvariable=self.order_var, state="readonly")
        self.order_combo.grid(row=0, column=1, padx=(0, 20))
        
        # Parts made
        ttk.Label(scrap_frame, text="Parts Made:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.parts_made_var = tk.StringVar()
        self.parts_made_entry = ttk.Entry(scrap_frame, textvariable=self.parts_made_var, width=10)
        self.parts_made_entry.grid(row=0, column=3, padx=(0, 20))
        
        # Scrap reason
        ttk.Label(scrap_frame, text="Scrap Reason:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.scrap_reason_var = tk.StringVar()
        self.scrap_reason_combo = ttk.Combobox(scrap_frame, textvariable=self.scrap_reason_var, values=scrap_reasons, state="readonly")
        self.scrap_reason_combo.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))
        
        # Scrap count
        ttk.Label(scrap_frame, text="Scrap Count:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.scrap_count_var = tk.StringVar()
        self.scrap_count_entry = ttk.Entry(scrap_frame, textvariable=self.scrap_count_var, width=10)
        self.scrap_count_entry.grid(row=1, column=3, padx=(0, 20), pady=(10, 0))
        
        # Submit button
        submit_btn = ttk.Button(scrap_frame, text="Submit Scrap Entry", command=self.submit_scrap_entry)
        submit_btn.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        # Scrap History
        history_frame = ttk.LabelFrame(main_frame, text="Today's Scrap Entries", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.scrap_history_text = scrolledtext.ScrolledText(history_frame, height=10, width=80)
        self.scrap_history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        refresh_history_btn = ttk.Button(history_frame, text="Refresh History", command=self.refresh_scrap_history)
        refresh_history_btn.grid(row=1, column=0, pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Load available orders
        self.refresh_operator_orders()
        self.refresh_scrap_history()
    
    def refresh_orders(self):
        """Refresh the orders display"""
        # This is a simplified version - in the full app this would load from database
        self.orders_text.delete(1.0, tk.END)
        self.orders_text.insert(tk.END, "Current Orders:\n")
        self.orders_text.insert(tk.END, "-" * 50 + "\n")
        self.orders_text.insert(tk.END, "Order 1: Part 780208A, 2500 parts\n")
        self.orders_text.insert(tk.END, "Order 2: Part 780508B, 1800 parts\n")
        self.orders_text.insert(tk.END, "Order 3: Part 780108C, 3200 parts\n")
    
    def refresh_operator_orders(self):
        """Load available orders for operator"""
        # This would typically load from database
        available_orders = ["Order 1", "Order 2", "Order 3"]
        self.order_combo['values'] = available_orders
    
    def refresh_scrap_history(self):
        """Refresh scrap history display"""
        self.scrap_history_text.delete(1.0, tk.END)
        
        # Load from database
        try:
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            
            # Get today's entries for this operator
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT timestamp, part_number, order_number, scrap_reason, scrap_count
                FROM scrap_entries 
                WHERE operator_number = ? AND DATE(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (self.operator_number, today))
            
            entries = cursor.fetchall()
            
            if entries:
                self.scrap_history_text.insert(tk.END, f"Today's scrap entries for Operator {self.operator_number}:\n")
                self.scrap_history_text.insert(tk.END, "-" * 70 + "\n")
                
                for timestamp, part_number, order_number, scrap_reason, scrap_count in entries:
                    entry_line = f"{timestamp} | Order {order_number} | Part {part_number} | {scrap_reason}: {scrap_count}\n"
                    self.scrap_history_text.insert(tk.END, entry_line)
            else:
                self.scrap_history_text.insert(tk.END, "No scrap entries for today.")
            
            conn.close()
            
        except Exception as e:
            print(f"Error loading scrap history: {e}")
            self.scrap_history_text.insert(tk.END, "Error loading scrap history.")
    
    def create_order(self):
        """Create a new order (admin only)"""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can create orders.")
            return
        
        part_number = self.part_var.get()
        mix_number = self.mix_var.get()
        
        if not part_number or not mix_number:
            messagebox.showerror("Input Error", "Please select a part number and enter a mix number.")
            return
        
        full_part_number = part_number + mix_number
        order_quantity = random.randint(110, 5000)  # Random quantity for demo
        
        # Create order (in full app, this would save to database)
        messagebox.showinfo("Order Created", 
                          f"Order created successfully:\n\n"
                          f"Part: {full_part_number}\n"
                          f"Quantity: {order_quantity}")
        
        # Clear the form
        self.part_var.set("")
        self.mix_var.set("")
        
        # Refresh orders display
        self.refresh_orders()
    
    def submit_scrap_entry(self):
        """Submit a scrap entry (operator)"""
        try:
            order_number = self.order_var.get()
            parts_made = int(self.parts_made_var.get() or "0")
            scrap_reason = self.scrap_reason_var.get()
            scrap_count = int(self.scrap_count_var.get() or "0")
            
            if not all([order_number, parts_made, scrap_reason, scrap_count]):
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return
            
            if scrap_count > parts_made:
                messagebox.showerror("Input Error", "Scrap count cannot exceed parts made.")
                return
            
            # Save to database
            part_number = "DemoPartXXX"  # In full app, this would be looked up from order
            order_num = int(order_number.split()[-1])  # Extract number from "Order X"
            
            save_scrap_entry(self.operator_number, part_number, order_num, scrap_reason, scrap_count)
            
            messagebox.showinfo("Success", f"Scrap entry recorded:\n{scrap_count} parts for '{scrap_reason}'")
            
            # Clear the form
            self.parts_made_var.set("")
            self.scrap_reason_var.set("")
            self.scrap_count_var.set("")
            
            # Refresh history
            self.refresh_scrap_history()
            
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for parts made and scrap count.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scrap entry: {e}")
    
    def logout(self):
        """Logout and return to login screen"""
        self.root.withdraw()
        self.show_login()


def run_command_line_mode():
    """Fallback command-line interface when GUI is not available"""
    print("\n=== PARTS TRACKER - COMMAND LINE MODE ===")
    print("Available admin credentials:")
    print("Username: admin, Password: admin123")
    print("Username: supervisor, Password: super456")
    print("=" * 45)
    
    init_database()
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Part Selection and Tracking")
        print("2. View Scrap Data")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            try:
                part_number, order_quantity, parts_made = part_selection()
                order = Order(part_number, order_quantity)
                
                print(f"\n{order.summary()}")
                
                part = Part(part_number)
                rate_percentage = part.rate_percentage(parts_made)
                print(f"Rate percentage: {rate_percentage:.2f}%")
                
                good_parts_made, total_scrap = scrap_tracking(parts_made, part_number, order.order_number)
                
                print(f"\nFinal Summary:")
                print(f"Good parts made: {good_parts_made}")
                print(f"Total scrap: {total_scrap}")
                print(f"Rate percentage: {rate_percentage:.2f}%")
                
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == "2":
            view_scrap_data()
        
        elif choice == "3":
            print("Exiting Parts Tracker. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def view_scrap_data():
    """View scrap data from database"""
    try:
        conn = sqlite3.connect('parts_tracker.db')
        cursor = conn.cursor()
        
        print("\n--- SCRAP DATA VIEWER ---")
        print("1. View all entries")
        print("2. View by operator")
        print("3. View by date")
        print("4. View by part number")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            cursor.execute('SELECT * FROM scrap_entries ORDER BY timestamp DESC LIMIT 50')
            entries = cursor.fetchall()
            
        elif choice == "2":
            operator = input("Enter operator number: ")
            cursor.execute('SELECT * FROM scrap_entries WHERE operator_number = ? ORDER BY timestamp DESC', (operator,))
            entries = cursor.fetchall()
            
        elif choice == "3":
            date = input("Enter date (YYYY-MM-DD): ")
            cursor.execute('SELECT * FROM scrap_entries WHERE DATE(timestamp) = ? ORDER BY timestamp DESC', (date,))
            entries = cursor.fetchall()
            
        elif choice == "4":
            part_num = input("Enter part number: ")
            cursor.execute('SELECT * FROM scrap_entries WHERE part_number LIKE ? ORDER BY timestamp DESC', (f"%{part_num}%",))
            entries = cursor.fetchall()
            
        else:
            print("Invalid choice.")
            return
        
        if entries:
            print(f"\n{'ID':<5} {'Operator':<10} {'Part':<15} {'Order':<8} {'Reason':<15} {'Count':<8} {'Timestamp':<20}")
            print("-" * 85)
            
            for entry in entries:
                id, operator, part, order, reason, count, timestamp = entry
                print(f"{id:<5} {operator:<10} {part:<15} {order:<8} {reason:<15} {count:<8} {timestamp:<20}")
        else:
            print("No entries found.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")
    
    print("Data saved to database.")


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


if __name__ == "__main__":
    main()