#!/usr/bin/env python3
"""
Parts Tracker - Admin Application
Comprehensive administrative interface for management and analytics.

This application provides:
- Operator analytics and performance tracking
- Downtime analytics and reporting  
- SMC (Sheet Moulding Compound) scrap analytics
- Operator management (add/remove)
- Order management
- System administration features
- Secure authentication

Author: matthew A Ruess
Date: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
import sys
import os
from datetime import datetime

# Import shared database functions
from shared_db import (
    init_database, authenticate_admin, add_operator, remove_operator,
    get_all_operators, get_operator_analytics, get_detailed_operator_analytics,
    save_order, get_recent_orders, part_numbers,
    get_all_time_entries, get_employee_time_summary, update_time_entry
)


class AdminInterface:
    """Comprehensive admin interface for management and analytics"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Parts Tracker - Admin Interface")
        self.root.state('zoomed')  # Start maximized
        
        # Authentication state
        self.authenticated = False
        self.current_admin = None
        
        # Set up improved styling
        self.setup_styling()
        
        # Initialize database
        init_database()
        
        # Show login screen first
        self.show_login_screen()
    
    
    def setup_styling(self):
        """Set up improved styling for admin interface"""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure fonts
        self.header_font = font.Font(family="Arial", size=16, weight="bold")
        self.label_font = font.Font(family="Arial", size=12, weight="bold")
        self.button_font = font.Font(family="Arial", size=11, weight="bold")
        self.entry_font = font.Font(family="Arial", size=11)
        self.small_font = font.Font(family="Arial", size=9)
        
        # Configure ttk styles
        style.configure('Header.TLabel', font=self.header_font, foreground='darkblue')
        style.configure('Bold.TLabel', font=self.label_font)
        style.configure('Large.TButton', font=self.button_font, padding=(10, 5))
        style.configure('Entry.TEntry', font=self.entry_font, fieldbackground='white')
        style.configure('Small.TLabel', font=self.small_font)
        
        # Configure colors
        self.root.configure(bg='#f5f5f5')
    
    
    def show_login_screen(self):
        """Show secure admin login screen"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ttk.Frame(self.root, padding="50")
        login_frame.pack(expand=True)
        
        # Title
        title_label = ttk.Label(login_frame, text="Parts Tracker - Admin Login", style='Header.TLabel')
        title_label.pack(pady=(0, 30))
        
        # Security warning
        security_label = ttk.Label(login_frame, 
                                  text="⚠️ Authorized Administrative Personnel Only ⚠️",
                                  style='Bold.TLabel', foreground='red')
        security_label.pack(pady=(0, 20))
        
        # Login form frame
        form_frame = ttk.LabelFrame(login_frame, text="Administrative Access", padding="30")
        form_frame.pack(pady=20)
        
        # Username
        ttk.Label(form_frame, text="Username:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 10))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form_frame, textvariable=self.username_var, style='Entry.TEntry', width=25)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        username_entry.focus()
        
        # Password
        ttk.Label(form_frame, text="Password:", style='Bold.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 10))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", style='Entry.TEntry', width=25)
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Login button
        login_btn = ttk.Button(form_frame, text="Login", style='Large.TButton',
                              command=self.attempt_login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=(20, 10))
        
        # Bind Enter key to login
        password_entry.bind('<Return>', lambda e: self.attempt_login())
        username_entry.bind('<Return>', lambda e: password_entry.focus())
        
        # Help text
        help_label = ttk.Label(form_frame, 
                              text="Default credentials: FeuerWasser/Jennifer124! or supervisor/super456",
                              style='Small.TLabel', foreground='gray')
        help_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))
    
    
    def attempt_login(self):
        """Attempt admin login with validation"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("Invalid Input", "Please enter both username and password")
            return
        
        # Show loading message
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            # Attempt authentication
            if authenticate_admin(username, password):
                self.authenticated = True
                self.current_admin = username
                messagebox.showinfo("Login Successful", f"Welcome, {username}!")
                self.show_admin_interface()
            else:
                messagebox.showerror("Login Failed", 
                                   "Invalid credentials or account locked.\n"
                                   "Please check your username and password.")
                # Clear password field
                self.password_var.set("")
        except Exception as e:
            messagebox.showerror("Login Error", f"Authentication error: {str(e)}")
        finally:
            self.root.config(cursor="")
    
    
    def show_admin_interface(self):
        """Show the main admin interface after successful login"""
        # Clear login screen
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main admin interface
        self.create_main_admin_interface()
    
    
    def create_main_admin_interface(self):
        """Create the main admin interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with logout
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        header_label = ttk.Label(header_frame, text="Parts Tracker - Admin Interface", style='Header.TLabel')
        header_label.pack(side=tk.LEFT)
        
        admin_info_label = ttk.Label(header_frame, text=f"Logged in as: {self.current_admin}", style='Bold.TLabel')
        admin_info_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        logout_btn = ttk.Button(header_frame, text="Logout", style='Large.TButton',
                               command=self.logout)
        logout_btn.pack(side=tk.RIGHT)
        
        # Create notebook for different admin functions
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create tabs
        self.create_analytics_tab()
        self.create_time_tracking_tab()
        self.create_operator_management_tab()
        self.create_order_management_tab()
        self.create_system_info_tab()
        
        # Footer with timestamp
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        timestamp_label = ttk.Label(footer_frame, 
                                   text=f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                   style='Small.TLabel')
        timestamp_label.pack()
    
    
    def create_analytics_tab(self):
        """Create comprehensive analytics tab"""
        analytics_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(analytics_frame, text="Analytics Dashboard")
        
        # Title
        title_label = ttk.Label(analytics_frame, text="Operator Analytics Dashboard", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Refresh button
        refresh_btn = ttk.Button(analytics_frame, text="Refresh Analytics", style='Large.TButton',
                                command=self.refresh_analytics)
        refresh_btn.pack(pady=(0, 10))
        
        # Create analytics treeview
        analytics_tree_frame = ttk.Frame(analytics_frame)
        analytics_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Analytics treeview with comprehensive columns
        self.analytics_tree = ttk.Treeview(analytics_tree_frame, 
                                         columns=('op_num', 'name', 'entries', 'scrap', 'orders', 'efficiency',
                                                'downtime_entries', 'total_downtime', 'avg_downtime',
                                                'smc_entries', 'smc_scrap', 'avg_smc_scrap'), 
                                         show='headings', height=15)
        
        # Configure columns
        self.analytics_tree.heading('op_num', text='Op #')
        self.analytics_tree.heading('name', text='Operator')
        self.analytics_tree.heading('entries', text='Total Entries')
        self.analytics_tree.heading('scrap', text='Total Scrap')
        self.analytics_tree.heading('orders', text='Orders Worked')
        self.analytics_tree.heading('efficiency', text='Efficiency %')
        self.analytics_tree.heading('downtime_entries', text='Downtime Events')
        self.analytics_tree.heading('total_downtime', text='Total Downtime (hrs)')
        self.analytics_tree.heading('avg_downtime', text='Avg Downtime/Day (min)')
        self.analytics_tree.heading('smc_entries', text='SMC Scrap Events')
        self.analytics_tree.heading('smc_scrap', text='Total SMC Scrap')
        self.analytics_tree.heading('avg_smc_scrap', text='Avg SMC Scrap/Day')
        
        # Configure column widths
        self.analytics_tree.column('op_num', width=50, anchor='center')
        self.analytics_tree.column('name', width=120, anchor='w')
        self.analytics_tree.column('entries', width=80, anchor='center')
        self.analytics_tree.column('scrap', width=80, anchor='center')
        self.analytics_tree.column('orders', width=80, anchor='center')
        self.analytics_tree.column('efficiency', width=80, anchor='center')
        self.analytics_tree.column('downtime_entries', width=100, anchor='center')
        self.analytics_tree.column('total_downtime', width=120, anchor='center')
        self.analytics_tree.column('avg_downtime', width=130, anchor='center')
        self.analytics_tree.column('smc_entries', width=110, anchor='center')
        self.analytics_tree.column('smc_scrap', width=100, anchor='center')
        self.analytics_tree.column('avg_smc_scrap', width=120, anchor='center')
        
        # Add scrollbars
        analytics_v_scrollbar = ttk.Scrollbar(analytics_tree_frame, orient=tk.VERTICAL, command=self.analytics_tree.yview)
        analytics_h_scrollbar = ttk.Scrollbar(analytics_tree_frame, orient=tk.HORIZONTAL, command=self.analytics_tree.xview)
        self.analytics_tree.configure(yscrollcommand=analytics_v_scrollbar.set, xscrollcommand=analytics_h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.analytics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        analytics_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        analytics_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Detailed view section
        detailed_frame = ttk.LabelFrame(analytics_frame, text="Detailed Operator View", padding="10")
        detailed_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(detailed_frame, text="Operator Number:", style='Bold.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.detail_op_var = tk.StringVar()
        ttk.Entry(detailed_frame, textvariable=self.detail_op_var, style='Entry.TEntry', width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        detail_btn = ttk.Button(detailed_frame, text="View Detailed Analytics", style='Large.TButton',
                               command=self.show_detailed_analytics)
        detail_btn.pack(side=tk.LEFT)
        
        # Load analytics on startup
        self.refresh_analytics()
    
    
    def create_operator_management_tab(self):
        """Create operator management tab"""
        operator_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(operator_frame, text="Operator Management")
        
        # Title
        title_label = ttk.Label(operator_frame, text="Operator Management", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Add operator section
        add_frame = ttk.LabelFrame(operator_frame, text="Add New Operator", padding="15")
        add_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Add operator form
        add_form_frame = ttk.Frame(add_frame)
        add_form_frame.pack()
        
        ttk.Label(add_form_frame, text="Operator Number:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.add_op_number_var = tk.StringVar()
        ttk.Entry(add_form_frame, textvariable=self.add_op_number_var, style='Entry.TEntry', width=15).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(add_form_frame, text="Operator Name:", style='Bold.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.add_op_name_var = tk.StringVar()
        ttk.Entry(add_form_frame, textvariable=self.add_op_name_var, style='Entry.TEntry', width=25).grid(row=0, column=3, padx=(0, 20))
        
        add_btn = ttk.Button(add_form_frame, text="Add Operator", style='Large.TButton',
                            command=self.add_new_operator)
        add_btn.grid(row=0, column=4)
        
        # Current operators section
        operators_frame = ttk.LabelFrame(operator_frame, text="Current Operators", padding="15")
        operators_frame.pack(fill=tk.BOTH, expand=True)
        
        # Operators treeview
        operators_tree_frame = ttk.Frame(operators_frame)
        operators_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.operators_tree = ttk.Treeview(operators_tree_frame, 
                                         columns=('op_num', 'name', 'created'), 
                                         show='headings', height=12)
        
        # Configure columns
        self.operators_tree.heading('op_num', text='Operator Number')
        self.operators_tree.heading('name', text='Anonymized Name')
        self.operators_tree.heading('created', text='Created Date')
        
        self.operators_tree.column('op_num', width=150, anchor='center')
        self.operators_tree.column('name', width=200, anchor='w')
        self.operators_tree.column('created', width=150, anchor='center')
        
        # Add scrollbar
        operators_scrollbar = ttk.Scrollbar(operators_tree_frame, orient=tk.VERTICAL, command=self.operators_tree.yview)
        self.operators_tree.configure(yscrollcommand=operators_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.operators_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        operators_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Remove operator section
        remove_frame = ttk.Frame(operators_frame)
        remove_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(remove_frame, text="Remove Operator Number:", style='Bold.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.remove_op_var = tk.StringVar()
        ttk.Entry(remove_frame, textvariable=self.remove_op_var, style='Entry.TEntry', width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        remove_btn = ttk.Button(remove_frame, text="Remove Operator", style='Large.TButton',
                               command=self.remove_selected_operator)
        remove_btn.pack(side=tk.LEFT)
        
        refresh_operators_btn = ttk.Button(remove_frame, text="Refresh List", style='Large.TButton',
                                          command=self.refresh_operators_list)
        refresh_operators_btn.pack(side=tk.RIGHT)
        
        # Load operators on startup
        self.refresh_operators_list()
    
    
    def create_order_management_tab(self):
        """Create order management tab"""
        order_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(order_frame, text="Order Management")
        
        # Title
        title_label = ttk.Label(order_frame, text="Order Management", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Add order section
        add_order_frame = ttk.LabelFrame(order_frame, text="Create New Order", padding="15")
        add_order_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Add order form
        order_form_frame = ttk.Frame(add_order_frame)
        order_form_frame.pack()
        
        ttk.Label(order_form_frame, text="Part Number:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.order_part_var = tk.StringVar()
        part_combo = ttk.Combobox(order_form_frame, textvariable=self.order_part_var, values=part_numbers,
                                 font=self.entry_font, width=20, state="readonly")
        part_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(order_form_frame, text="Parts per Order:", style='Bold.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.order_count_var = tk.StringVar()
        ttk.Entry(order_form_frame, textvariable=self.order_count_var, style='Entry.TEntry', width=15).grid(row=0, column=3, padx=(0, 20))
        
        create_order_btn = ttk.Button(order_form_frame, text="Create Order", style='Large.TButton',
                                     command=self.create_new_order)
        create_order_btn.grid(row=0, column=4)
        
        # Recent orders section
        recent_orders_frame = ttk.LabelFrame(order_frame, text="Recent Orders", padding="15")
        recent_orders_frame.pack(fill=tk.BOTH, expand=True)
        
        # Orders treeview
        orders_tree_frame = ttk.Frame(recent_orders_frame)
        orders_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.admin_orders_tree = ttk.Treeview(orders_tree_frame, 
                                            columns=('order', 'part', 'count', 'created', 'status'), 
                                            show='headings', height=15)
        
        # Configure columns
        self.admin_orders_tree.heading('order', text='Order Number')
        self.admin_orders_tree.heading('part', text='Part Number')
        self.admin_orders_tree.heading('count', text='Parts Count')
        self.admin_orders_tree.heading('created', text='Created Date')
        self.admin_orders_tree.heading('status', text='Status')
        
        self.admin_orders_tree.column('order', width=120, anchor='center')
        self.admin_orders_tree.column('part', width=120, anchor='center')
        self.admin_orders_tree.column('count', width=120, anchor='center')
        self.admin_orders_tree.column('created', width=150, anchor='center')
        self.admin_orders_tree.column('status', width=100, anchor='center')
        
        # Add scrollbar
        orders_admin_scrollbar = ttk.Scrollbar(orders_tree_frame, orient=tk.VERTICAL, command=self.admin_orders_tree.yview)
        self.admin_orders_tree.configure(yscrollcommand=orders_admin_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.admin_orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        orders_admin_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_orders_btn = ttk.Button(recent_orders_frame, text="Refresh Orders", style='Large.TButton',
                                       command=self.refresh_admin_orders)
        refresh_orders_btn.pack(pady=(10, 0))
        
        # Load orders on startup
        self.refresh_admin_orders()
    
    
    def create_system_info_tab(self):
        """Create system information and settings tab"""
        system_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(system_frame, text="System Information")
        
        # Title
        title_label = ttk.Label(system_frame, text="System Information & Settings", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # System info sections
        info_notebook = ttk.Notebook(system_frame)
        info_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Application info
        app_info_frame = ttk.Frame(info_notebook, padding="15")
        info_notebook.add(app_info_frame, text="Application Info")
        
        app_info_text = """
Parts Tracker - Admin Interface
Version: 2.0 (Separated Architecture)

Features:
• Comprehensive operator analytics with efficiency tracking
• Downtime monitoring and reporting
• SMC (Sheet Moulding Compound) scrap tracking
• Secure admin authentication with brute force protection
• Operator management (add/remove with privacy protection)
• Order management and tracking
• Input validation and sanitization throughout
• Streamlined operator interface for production floor

Security Features:
• SHA-256 password hashing
• Account lockout protection
• Login attempt monitoring
• Input sanitization and validation
• Operator name privacy protection

Database Tables:
• scrap_entries - Production scrap tracking
• downtime_entries - Operator downtime logging
• smc_scrap_entries - SMC scrap tracking
• operators - Operator information (anonymized)
• orders - Order tracking and management
• admin_credentials - Secure admin authentication
• login_attempts - Security monitoring

SMC (Sheet Moulding Compound) Information:
Sheet Moulding Compound is a composite material used in 
manufacturing that may experience various quality issues 
requiring tracking and analysis.
        """
        
        app_info_label = ttk.Label(app_info_frame, text=app_info_text.strip(), 
                                  justify=tk.LEFT, style='Small.TLabel')
        app_info_label.pack(anchor=tk.W)
        
        # Database statistics
        db_stats_frame = ttk.Frame(info_notebook, padding="15")
        info_notebook.add(db_stats_frame, text="Database Statistics")
        
        self.stats_text = tk.Text(db_stats_frame, height=20, width=60, font=self.small_font,
                                 wrap=tk.WORD, state=tk.DISABLED)
        stats_scrollbar = ttk.Scrollbar(db_stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        refresh_stats_btn = ttk.Button(db_stats_frame, text="Refresh Statistics", style='Large.TButton',
                                      command=self.refresh_database_stats)
        refresh_stats_btn.pack(pady=(10, 0))
        
        # Load stats on startup
        self.refresh_database_stats()
    
    
    def refresh_analytics(self):
        """Refresh the analytics display"""
        try:
            # Clear existing items
            for item in self.analytics_tree.get_children():
                self.analytics_tree.delete(item)
            
            # Get analytics data
            analytics_data = get_operator_analytics()
            
            if analytics_data:
                for data in analytics_data:
                    values = (
                        data['operator_number'],
                        data['anonymized_name'],
                        data['total_entries'],
                        data['total_scrap'],
                        data['orders_worked'],
                        f"{data['efficiency']}%",
                        data['downtime_entries'],
                        data['total_downtime_hours'],
                        data['avg_downtime_per_day'],
                        data['smc_scrap_entries'],
                        data['total_smc_scrap'],
                        data['avg_smc_scrap_per_day']
                    )
                    self.analytics_tree.insert('', 'end', values=values)
            else:
                # Insert a message if no data
                self.analytics_tree.insert('', 'end', values=("No data", "available", "", "", "", "", "", "", "", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh analytics: {str(e)}")
    
    
    def show_detailed_analytics(self):
        """Show detailed analytics for a specific operator"""
        try:
            operator_number = self.detail_op_var.get().strip()
            
            if not operator_number:
                messagebox.showwarning("Warning", "Please enter an operator number")
                return
            
            try:
                op_num = int(operator_number)
            except ValueError:
                messagebox.showerror("Error", "Invalid operator number")
                return
            
            # Get detailed analytics
            detailed_data = get_detailed_operator_analytics(op_num)
            
            if not detailed_data:
                messagebox.showinfo("No Data", f"No data found for operator {op_num}")
                return
            
            # Create detailed analytics window
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"Detailed Analytics - Operator {op_num}")
            detail_window.geometry("800x600")
            
            # Create notebook for different data types
            detail_notebook = ttk.Notebook(detail_window, padding="10")
            detail_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Scrap entries tab
            if detailed_data['scrap_entries']:
                scrap_frame = ttk.Frame(detail_notebook, padding="10")
                detail_notebook.add(scrap_frame, text=f"Scrap Entries ({len(detailed_data['scrap_entries'])})")
                
                scrap_tree = ttk.Treeview(scrap_frame, 
                                        columns=('timestamp', 'part', 'order', 'reason', 'count'), 
                                        show='headings', height=15)
                
                scrap_tree.heading('timestamp', text='Timestamp')
                scrap_tree.heading('part', text='Part Number')
                scrap_tree.heading('order', text='Order')
                scrap_tree.heading('reason', text='Scrap Reason')
                scrap_tree.heading('count', text='Count')
                
                for entry in detailed_data['scrap_entries']:
                    timestamp, part_number, order_number, scrap_reason, scrap_count, parts_per_order = entry
                    scrap_tree.insert('', 'end', values=(timestamp, part_number, order_number, scrap_reason, scrap_count))
                
                scrap_tree.pack(fill=tk.BOTH, expand=True)
            
            # Downtime entries tab
            if detailed_data['downtime_entries']:
                downtime_frame = ttk.Frame(detail_notebook, padding="10")
                detail_notebook.add(downtime_frame, text=f"Downtime Entries ({len(detailed_data['downtime_entries'])})")
                
                downtime_tree = ttk.Treeview(downtime_frame, 
                                           columns=('timestamp', 'reason', 'duration', 'shift_date'), 
                                           show='headings', height=15)
                
                downtime_tree.heading('timestamp', text='Timestamp')
                downtime_tree.heading('reason', text='Downtime Reason')
                downtime_tree.heading('duration', text='Duration (min)')
                downtime_tree.heading('shift_date', text='Shift Date')
                
                for entry in detailed_data['downtime_entries']:
                    timestamp, downtime_reason, duration_minutes, shift_date = entry
                    downtime_tree.insert('', 'end', values=(timestamp, downtime_reason, duration_minutes, shift_date))
                
                downtime_tree.pack(fill=tk.BOTH, expand=True)
            
            # SMC entries tab
            if detailed_data['smc_scrap_entries']:
                smc_frame = ttk.Frame(detail_notebook, padding="10")
                detail_notebook.add(smc_frame, text=f"SMC Scrap Entries ({len(detailed_data['smc_scrap_entries'])})")
                
                smc_tree = ttk.Treeview(smc_frame, 
                                      columns=('timestamp', 'part_type', 'reason', 'count', 'shift_date'), 
                                      show='headings', height=15)
                
                smc_tree.heading('timestamp', text='Timestamp')
                smc_tree.heading('part_type', text='Part Type')
                smc_tree.heading('reason', text='SMC Scrap Reason')
                smc_tree.heading('count', text='Count')
                smc_tree.heading('shift_date', text='Shift Date')
                
                for entry in detailed_data['smc_scrap_entries']:
                    timestamp, part_type, smc_scrap_reason, smc_scrap_count, shift_date = entry
                    smc_tree.insert('', 'end', values=(timestamp, part_type, smc_scrap_reason, smc_scrap_count, shift_date))
                
                smc_tree.pack(fill=tk.BOTH, expand=True)
            
            # Clear the operator number field
            self.detail_op_var.set("")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show detailed analytics: {str(e)}")
    
    
    def create_time_tracking_tab(self):
        """Create time tracking management tab"""
        time_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(time_frame, text="Time Tracking")
        
        # Title
        title_label = ttk.Label(time_frame, text="Employee Time Tracking Management", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for time tracking sections
        time_notebook = ttk.Notebook(time_frame)
        time_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Time entries tab
        entries_frame = ttk.Frame(time_notebook, padding="10")
        time_notebook.add(entries_frame, text="Time Entries")
        
        # Refresh button
        refresh_time_btn = ttk.Button(entries_frame, text="Refresh Time Entries", style='Large.TButton',
                                     command=self.refresh_time_entries)
        refresh_time_btn.pack(pady=(0, 10))
        
        # Time entries treeview
        time_entries_tree_frame = ttk.Frame(entries_frame)
        time_entries_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.time_entries_tree = ttk.Treeview(time_entries_tree_frame, 
                                             columns=('id', 'employee', 'date', 'clock_in', 'clock_out', 'hours', 'status'), 
                                             show='headings', height=15)
        
        # Configure columns
        self.time_entries_tree.heading('id', text='Entry ID')
        self.time_entries_tree.heading('employee', text='Employee #')
        self.time_entries_tree.heading('date', text='Date')
        self.time_entries_tree.heading('clock_in', text='Clock In')
        self.time_entries_tree.heading('clock_out', text='Clock Out')
        self.time_entries_tree.heading('hours', text='Total Hours')
        self.time_entries_tree.heading('status', text='Status')
        
        self.time_entries_tree.column('id', width=80, anchor='center')
        self.time_entries_tree.column('employee', width=100, anchor='center')
        self.time_entries_tree.column('date', width=100, anchor='center')
        self.time_entries_tree.column('clock_in', width=150, anchor='center')
        self.time_entries_tree.column('clock_out', width=150, anchor='center')
        self.time_entries_tree.column('hours', width=100, anchor='center')
        self.time_entries_tree.column('status', width=100, anchor='center')
        
        # Add scrollbar
        time_entries_scrollbar = ttk.Scrollbar(time_entries_tree_frame, orient=tk.VERTICAL, command=self.time_entries_tree.yview)
        self.time_entries_tree.configure(yscrollcommand=time_entries_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.time_entries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        time_entries_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Edit time entry section
        edit_frame = ttk.LabelFrame(entries_frame, text="Edit Time Entry", padding="10")
        edit_frame.pack(fill=tk.X, pady=(10, 0))
        
        edit_form_frame = ttk.Frame(edit_frame)
        edit_form_frame.pack()
        
        ttk.Label(edit_form_frame, text="Entry ID:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.edit_entry_id_var = tk.StringVar()
        ttk.Entry(edit_form_frame, textvariable=self.edit_entry_id_var, style='Entry.TEntry', width=15).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(edit_form_frame, text="Clock In (YYYY-MM-DD HH:MM:SS):", style='Bold.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.edit_clock_in_var = tk.StringVar()
        ttk.Entry(edit_form_frame, textvariable=self.edit_clock_in_var, style='Entry.TEntry', width=20).grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(edit_form_frame, text="Clock Out (YYYY-MM-DD HH:MM:SS):", style='Bold.TLabel').grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.edit_clock_out_var = tk.StringVar()
        ttk.Entry(edit_form_frame, textvariable=self.edit_clock_out_var, style='Entry.TEntry', width=20).grid(row=1, column=3, padx=(0, 20), pady=(10, 0))
        
        update_entry_btn = ttk.Button(edit_form_frame, text="Update Entry", style='Large.TButton',
                                     command=self.update_selected_time_entry)
        update_entry_btn.grid(row=1, column=4, pady=(10, 0))
        
        # Bind double-click to populate edit form
        self.time_entries_tree.bind('<Double-1>', self.populate_edit_form)
        
        # Employee summary tab
        summary_frame = ttk.Frame(time_notebook, padding="10")
        time_notebook.add(summary_frame, text="Employee Summary")
        
        # Refresh button for summary
        refresh_summary_btn = ttk.Button(summary_frame, text="Refresh Summary", style='Large.TButton',
                                        command=self.refresh_time_summary)
        refresh_summary_btn.pack(pady=(0, 10))
        
        # Employee summary treeview
        summary_tree_frame = ttk.Frame(summary_frame)
        summary_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.time_summary_tree = ttk.Treeview(summary_tree_frame, 
                                             columns=('employee', 'total_days', 'total_hours', 'avg_hours', 'last_worked'), 
                                             show='headings', height=15)
        
        # Configure columns
        self.time_summary_tree.heading('employee', text='Employee #')
        self.time_summary_tree.heading('total_days', text='Total Days')
        self.time_summary_tree.heading('total_hours', text='Total Hours')
        self.time_summary_tree.heading('avg_hours', text='Avg Hours/Day')
        self.time_summary_tree.heading('last_worked', text='Last Worked')
        
        self.time_summary_tree.column('employee', width=120, anchor='center')
        self.time_summary_tree.column('total_days', width=120, anchor='center')
        self.time_summary_tree.column('total_hours', width=120, anchor='center')
        self.time_summary_tree.column('avg_hours', width=120, anchor='center')
        self.time_summary_tree.column('last_worked', width=120, anchor='center')
        
        # Add scrollbar for summary
        summary_scrollbar = ttk.Scrollbar(summary_tree_frame, orient=tk.VERTICAL, command=self.time_summary_tree.yview)
        self.time_summary_tree.configure(yscrollcommand=summary_scrollbar.set)
        
        # Pack summary treeview and scrollbar
        self.time_summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load time tracking data on startup
        self.refresh_time_entries()
        self.refresh_time_summary()
    
    
    def add_new_operator(self):
        """Add a new operator"""
        try:
            operator_number = self.add_op_number_var.get().strip()
            operator_name = self.add_op_name_var.get().strip()
            
            if not operator_number or not operator_name:
                messagebox.showwarning("Warning", "Please enter both operator number and name")
                return
            
            try:
                op_num = int(operator_number)
                if op_num < 0 or op_num > 9999:
                    messagebox.showerror("Error", "Operator number must be between 0-9999")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid operator number")
                return
            
            # Add operator
            if add_operator(op_num, operator_name):
                messagebox.showinfo("Success", f"Operator {op_num} added successfully!\nName will be anonymized for privacy.")
                
                # Clear form and refresh list
                self.add_op_number_var.set("")
                self.add_op_name_var.set("")
                self.refresh_operators_list()
                self.refresh_analytics()  # Refresh analytics too
            else:
                messagebox.showerror("Error", f"Failed to add operator {op_num}. Operator number may already exist.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add operator: {str(e)}")
    
    
    def remove_selected_operator(self):
        """Remove a selected operator"""
        try:
            operator_number = self.remove_op_var.get().strip()
            
            if not operator_number:
                messagebox.showwarning("Warning", "Please enter an operator number to remove")
                return
            
            try:
                op_num = int(operator_number)
            except ValueError:
                messagebox.showerror("Error", "Invalid operator number")
                return
            
            # Confirm removal
            if messagebox.askyesno("Confirm Removal", 
                                  f"Are you sure you want to remove operator {op_num}?\n"
                                  "This action cannot be undone."):
                
                if remove_operator(op_num):
                    messagebox.showinfo("Success", f"Operator {op_num} removed successfully!")
                    
                    # Clear form and refresh list
                    self.remove_op_var.set("")
                    self.refresh_operators_list()
                    self.refresh_analytics()  # Refresh analytics too
                else:
                    messagebox.showerror("Error", f"Failed to remove operator {op_num}. Operator may not exist.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove operator: {str(e)}")
    
    
    def refresh_operators_list(self):
        """Refresh the operators list"""
        try:
            # Clear existing items
            for item in self.operators_tree.get_children():
                self.operators_tree.delete(item)
            
            # Get operators
            operators = get_all_operators()
            
            if operators:
                for operator in operators:
                    op_number, anonymized_name, created_date = operator
                    self.operators_tree.insert('', 'end', values=(op_number, anonymized_name, created_date))
            else:
                # Insert a message if no operators
                self.operators_tree.insert('', 'end', values=("No operators", "found", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh operators list: {str(e)}")
    
    
    def create_new_order(self):
        """Create a new order"""
        try:
            part_number = self.order_part_var.get().strip()
            parts_count = self.order_count_var.get().strip()
            
            if not part_number or not parts_count:
                messagebox.showwarning("Warning", "Please select part number and enter parts count")
                return
            
            try:
                count = int(parts_count)
                if count <= 0:
                    messagebox.showerror("Error", "Parts count must be positive")
                    return
                if count > 999999:
                    messagebox.showerror("Error", "Parts count too large (max 999,999)")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid parts count")
                return
            
            # Create order
            order_number = save_order(part_number, count)
            
            messagebox.showinfo("Success", f"Order created successfully!\n"
                                         f"Order Number: {order_number}\n"
                                         f"Part Number: {part_number}\n"
                                         f"Parts Count: {count}")
            
            # Clear form and refresh list
            self.order_part_var.set("")
            self.order_count_var.set("")
            self.refresh_admin_orders()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")
    
    
    def refresh_admin_orders(self):
        """Refresh the admin orders list"""
        try:
            # Clear existing items
            for item in self.admin_orders_tree.get_children():
                self.admin_orders_tree.delete(item)
            
            # Get recent orders
            orders = get_recent_orders(100)  # Get more orders for admin view
            
            if orders:
                for order in orders:
                    order_number, part_number, parts_per_order, created_date, status = order
                    self.admin_orders_tree.insert('', 'end', values=(order_number, part_number, parts_per_order, created_date, status))
            else:
                # Insert a message if no orders
                self.admin_orders_tree.insert('', 'end', values=("No orders", "available", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh orders: {str(e)}")
    
    
    def refresh_database_stats(self):
        """Refresh database statistics"""
        try:
            import sqlite3
            
            conn = sqlite3.connect('parts_tracker.db')
            cursor = conn.cursor()
            
            stats_text = "DATABASE STATISTICS\n" + "="*50 + "\n\n"
            
            # Table row counts
            tables = [
                ('scrap_entries', 'Production Scrap Entries'),
                ('downtime_entries', 'Downtime Entries'),
                ('smc_scrap_entries', 'SMC Scrap Entries'),
                ('operators', 'Registered Operators'),
                ('orders', 'Total Orders'),
                ('admin_credentials', 'Admin Accounts'),
                ('login_attempts', 'Login Attempts')
            ]
            
            stats_text += "TABLE ROW COUNTS:\n" + "-"*30 + "\n"
            for table, description in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                stats_text += f"{description}: {count}\n"
            
            stats_text += "\n"
            
            # Scrap statistics
            cursor.execute('''
                SELECT 
                    SUM(scrap_count) as total_scrap,
                    COUNT(DISTINCT operator_number) as operators_with_scrap,
                    COUNT(DISTINCT order_number) as orders_with_scrap
                FROM scrap_entries
            ''')
            scrap_stats = cursor.fetchone()
            
            stats_text += "PRODUCTION SCRAP SUMMARY:\n" + "-"*30 + "\n"
            stats_text += f"Total Scrap Parts: {scrap_stats[0] if scrap_stats[0] else 0}\n"
            stats_text += f"Operators with Scrap: {scrap_stats[1] if scrap_stats[1] else 0}\n"
            stats_text += f"Orders with Scrap: {scrap_stats[2] if scrap_stats[2] else 0}\n\n"
            
            # Downtime statistics
            cursor.execute('''
                SELECT 
                    SUM(downtime_duration_minutes) as total_downtime,
                    AVG(downtime_duration_minutes) as avg_downtime,
                    COUNT(DISTINCT operator_number) as operators_with_downtime
                FROM downtime_entries
            ''')
            downtime_stats = cursor.fetchone()
            
            stats_text += "DOWNTIME SUMMARY:\n" + "-"*20 + "\n"
            total_downtime = downtime_stats[0] if downtime_stats[0] else 0
            avg_downtime = downtime_stats[1] if downtime_stats[1] else 0
            operators_with_downtime = downtime_stats[2] if downtime_stats[2] else 0
            
            stats_text += f"Total Downtime: {total_downtime} minutes ({total_downtime/60:.1f} hours)\n"
            stats_text += f"Average Downtime per Event: {avg_downtime:.1f} minutes\n"
            stats_text += f"Operators with Downtime: {operators_with_downtime}\n\n"
            
            # SMC statistics
            cursor.execute('''
                SELECT 
                    SUM(smc_scrap_count) as total_smc_scrap,
                    COUNT(DISTINCT operator_number) as operators_with_smc_scrap,
                    COUNT(DISTINCT part_type) as part_types_with_smc_scrap
                FROM smc_scrap_entries
            ''')
            smc_stats = cursor.fetchone()
            
            stats_text += "SMC SCRAP SUMMARY:\n" + "-"*20 + "\n"
            stats_text += f"Total SMC Scrap: {smc_stats[0] if smc_stats[0] else 0}\n"
            stats_text += f"Operators with SMC Scrap: {smc_stats[1] if smc_stats[1] else 0}\n"
            stats_text += f"Part Types with SMC Scrap: {smc_stats[2] if smc_stats[2] else 0}\n\n"
            
            # Security statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_logins,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_attempts
                FROM login_attempts
            ''')
            login_stats = cursor.fetchone()
            
            stats_text += "SECURITY SUMMARY:\n" + "-"*20 + "\n"
            stats_text += f"Total Login Attempts: {login_stats[0] if login_stats[0] else 0}\n"
            stats_text += f"Successful Logins: {login_stats[1] if login_stats[1] else 0}\n"
            stats_text += f"Failed Attempts: {login_stats[2] if login_stats[2] else 0}\n\n"
            
            # Last updated
            stats_text += f"Statistics last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            conn.close()
            
            # Update the text widget
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh database statistics: {str(e)}")
    
    
    def logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.authenticated = False
            self.current_admin = None
            self.show_login_screen()
    
    
    def refresh_time_entries(self):
        """Refresh the time entries display"""
        try:
            # Clear existing items
            for item in self.time_entries_tree.get_children():
                self.time_entries_tree.delete(item)
            
            # Get time entries
            entries = get_all_time_entries(200)
            
            if entries:
                for entry in entries:
                    entry_id, employee_number, shift_date, clock_in, clock_out, total_hours, status, timestamp = entry
                    clock_in_display = clock_in.split()[1] if clock_in else "--"
                    clock_out_display = clock_out.split()[1] if clock_out else "--"
                    total_hours_display = f"{total_hours:.2f}" if total_hours else "--"
                    
                    self.time_entries_tree.insert('', 'end', values=(
                        entry_id, employee_number, shift_date, 
                        clock_in_display, clock_out_display, 
                        total_hours_display, status
                    ))
            else:
                self.time_entries_tree.insert('', 'end', values=("No time entries", "", "", "", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh time entries: {str(e)}")
    
    
    def refresh_time_summary(self):
        """Refresh the time summary display"""
        try:
            # Clear existing items
            for item in self.time_summary_tree.get_children():
                self.time_summary_tree.delete(item)
            
            # Get summary data
            summary = get_employee_time_summary()
            
            if summary:
                for emp_data in summary:
                    employee_number, total_days, total_hours, avg_hours, last_worked = emp_data
                    total_hours_display = f"{total_hours:.2f}" if total_hours else "0.00"
                    avg_hours_display = f"{avg_hours:.2f}" if avg_hours else "0.00"
                    
                    self.time_summary_tree.insert('', 'end', values=(
                        employee_number, total_days, total_hours_display,
                        avg_hours_display, last_worked
                    ))
            else:
                self.time_summary_tree.insert('', 'end', values=("No time data", "", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh time summary: {str(e)}")
    
    
    def populate_edit_form(self, event):
        """Populate edit form when time entry is double-clicked"""
        try:
            selected_item = self.time_entries_tree.selection()[0]
            values = self.time_entries_tree.item(selected_item)['values']
            
            if len(values) >= 7:
                entry_id, employee_number, shift_date, clock_in_time, clock_out_time, total_hours, status = values[:7]
                
                self.edit_entry_id_var.set(str(entry_id))
                
                # Get full datetime from database for editing
                entries = get_all_time_entries(500)
                for entry in entries:
                    if entry[0] == entry_id:
                        self.edit_clock_in_var.set(entry[3] if entry[3] else "")
                        self.edit_clock_out_var.set(entry[4] if entry[4] else "")
                        break
                        
        except (IndexError, ValueError):
            pass
    
    
    def update_selected_time_entry(self):
        """Update a selected time entry"""
        try:
            entry_id = self.edit_entry_id_var.get().strip()
            clock_in_time = self.edit_clock_in_var.get().strip()
            clock_out_time = self.edit_clock_out_var.get().strip()
            
            if not entry_id:
                messagebox.showwarning("Warning", "Please enter an entry ID")
                return
            
            try:
                entry_id = int(entry_id)
            except ValueError:
                messagebox.showerror("Error", "Invalid entry ID")
                return
            
            # Validate datetime format if provided
            if clock_in_time:
                try:
                    datetime.strptime(clock_in_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    messagebox.showerror("Error", "Invalid clock in time format. Use YYYY-MM-DD HH:MM:SS")
                    return
            
            if clock_out_time:
                try:
                    datetime.strptime(clock_out_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    messagebox.showerror("Error", "Invalid clock out time format. Use YYYY-MM-DD HH:MM:SS")
                    return
            
            # Update the entry
            success = update_time_entry(entry_id, clock_in_time or None, clock_out_time or None)
            
            if success:
                messagebox.showinfo("Success", "Time entry updated successfully")
                
                # Clear form and refresh display
                self.edit_entry_id_var.set("")
                self.edit_clock_in_var.set("")
                self.edit_clock_out_var.set("")
                self.refresh_time_entries()
                self.refresh_time_summary()
            else:
                messagebox.showerror("Error", "Failed to update time entry")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update time entry: {str(e)}")


def main():
    """Main function to run the admin interface"""
    # Check if shared_db module is available
    try:
        import shared_db
    except ImportError:
        print("Error: shared_db.py module not found!")
        print("Please ensure shared_db.py is in the same directory as this file.")
        sys.exit(1)
    
    # Create and run the application
    try:
        root = tk.Tk()
        app = AdminInterface(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()