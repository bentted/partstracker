#!/usr/bin/env python3
"""
Parts Tracker - Operator Application
Streamlined interface for production floor operators.

This application provides:
- Scrap entry recording
- Downtime recording  
- SMC (Sheet Moulding Compound) scrap recording
- Simple order lookup
- Clean, production-floor friendly interface

Author: Matthew A Ruess
Date: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import sys
import os

# Import shared database functions
from shared_db import (
    init_database, save_scrap_entry, save_downtime_entry, save_smc_scrap_entry,
    get_recent_orders, get_order_by_number, scrap_reasons, part_numbers,
    downtime_reasons, smc_scrap_reasons, validate_operator_number,
    validate_parts_count, validate_downtime_duration, validate_smc_scrap_count,
    clock_in, clock_out, get_employee_status, validate_employee_number
)


class OperatorInterface:
    """Streamlined operator interface for production floor use"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Parts Tracker - Operator Interface")
        self.root.state('zoomed')  # Start maximized for production floor visibility
        
        # Set up improved styling for production floor visibility
        self.setup_styling()
        
        # Initialize database
        init_database()
        
        # Create the main interface
        self.create_main_interface()
        
        # Update orders on startup
        self.update_available_orders()
    
    
    def setup_styling(self):
        """Set up improved styling for production floor visibility"""
        # Configure styles for better visibility
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure larger fonts for production floor visibility
        self.header_font = font.Font(family="Arial", size=16, weight="bold")
        self.label_font = font.Font(family="Arial", size=12, weight="bold")
        self.button_font = font.Font(family="Arial", size=11, weight="bold")
        self.entry_font = font.Font(family="Arial", size=11)
        
        # Configure ttk styles
        style.configure('Header.TLabel', font=self.header_font, foreground='navy')
        style.configure('Bold.TLabel', font=self.label_font)
        style.configure('Large.TButton', font=self.button_font, padding=(10, 5))
        style.configure('Entry.TEntry', font=self.entry_font, fieldbackground='white')
        
        # Configure colors for better visibility
        self.root.configure(bg='#f0f0f0')
    
    
    def create_main_interface(self):
        """Create the main operator interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(main_frame, text="Parts Tracker - Operator Interface", style='Header.TLabel')
        header_label.pack(pady=(0, 20))
        
        # Create notebook for different functions
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create tabs
        self.create_time_tracking_tab()
        self.create_scrap_tab()
        self.create_downtime_tab()
        self.create_smc_scrap_tab()
        self.create_orders_tab()
        
        # Footer with instructions
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        instructions_label = ttk.Label(footer_frame, 
                                     text="Use the tabs above to clock in/out, record scrap, downtime, SMC scrap, or view orders.",
                                     style='Bold.TLabel')
        instructions_label.pack()
    
    
    def create_time_tracking_tab(self):
        """Create time tracking (clock in/out) tab"""
        time_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(time_frame, text="Time Tracking")
        
        # Title
        title_label = ttk.Label(time_frame, text="Employee Time Tracking", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # Current status display
        self.status_frame = ttk.LabelFrame(time_frame, text="Current Status", padding="15")
        self.status_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 20))
        
        self.status_label = ttk.Label(self.status_frame, text="Enter employee number to check status", 
                                     style='Bold.TLabel', foreground='blue')
        self.status_label.pack()
        
        # Employee number entry
        ttk.Label(time_frame, text="5-Digit Employee Number:", style='Bold.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.employee_number_var = tk.StringVar()
        employee_entry = ttk.Entry(time_frame, textvariable=self.employee_number_var, style='Entry.TEntry', width=15)
        employee_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 20))
        
        # Bind change event to update status
        employee_entry.bind('<KeyRelease>', self.update_employee_status)
        
        # Clock in/out buttons
        buttons_frame = ttk.Frame(time_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(20, 0))
        
        clock_in_btn = ttk.Button(buttons_frame, text="Clock In", style='Large.TButton',
                                 command=self.clock_in_employee)
        clock_in_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        clock_out_btn = ttk.Button(buttons_frame, text="Clock Out", style='Large.TButton',
                                  command=self.clock_out_employee)
        clock_out_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        check_status_btn = ttk.Button(buttons_frame, text="Check Status", style='Large.TButton',
                                     command=self.check_employee_status)
        check_status_btn.pack(side=tk.LEFT)
        
        # Instructions
        instructions_text = """Instructions:
1. Enter your 5-digit employee number (e.g., 12345)
2. Click 'Clock In' at the start of your shift
3. Click 'Clock Out' at the end of your shift
4. Use 'Check Status' to verify your current time status"""
        
        instructions_label = ttk.Label(time_frame, text=instructions_text, 
                                      justify=tk.LEFT, style='Small.TLabel', foreground='gray')
        instructions_label.grid(row=4, column=0, columnspan=3, pady=(20, 0), sticky=tk.W)
        
        # Configure grid weights
        time_frame.columnconfigure(1, weight=1)
        """Create scrap entry tab"""
        scrap_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(scrap_frame, text="Scrap Entry")
        
        # Title
        title_label = ttk.Label(scrap_frame, text="Record Production Scrap", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # Operator number
        ttk.Label(scrap_frame, text="Operator Number:", style='Bold.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.scrap_op_var = tk.StringVar()
        ttk.Entry(scrap_frame, textvariable=self.scrap_op_var, style='Entry.TEntry', width=15).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        # Part number
        ttk.Label(scrap_frame, text="Part Number:", style='Bold.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.scrap_part_var = tk.StringVar()
        part_combo = ttk.Combobox(scrap_frame, textvariable=self.scrap_part_var, values=part_numbers, 
                                 font=self.entry_font, width=20, state="readonly")
        part_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Order number
        ttk.Label(scrap_frame, text="Order Number:", style='Bold.TLabel').grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.scrap_order_var = tk.StringVar()
        ttk.Entry(scrap_frame, textvariable=self.scrap_order_var, style='Entry.TEntry', width=15).grid(row=3, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Scrap reason
        ttk.Label(scrap_frame, text="Scrap Reason:", style='Bold.TLabel').grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.scrap_reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(scrap_frame, textvariable=self.scrap_reason_var, values=scrap_reasons,
                                   font=self.entry_font, width=25, state="readonly")
        reason_combo.grid(row=4, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Scrap count
        ttk.Label(scrap_frame, text="Scrap Count:", style='Bold.TLabel').grid(row=5, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.scrap_count_var = tk.StringVar()
        ttk.Entry(scrap_frame, textvariable=self.scrap_count_var, style='Entry.TEntry', width=15).grid(row=5, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Submit button
        submit_btn = ttk.Button(scrap_frame, text="Record Scrap Entry", style='Large.TButton',
                               command=self.submit_scrap_entry)
        submit_btn.grid(row=6, column=0, columnspan=2, pady=(20, 0), sticky=tk.W)
        
        # Clear button
        clear_btn = ttk.Button(scrap_frame, text="Clear Form", style='Large.TButton',
                              command=self.clear_scrap_form)
        clear_btn.grid(row=6, column=1, pady=(20, 0), sticky=tk.E, padx=(20, 0))
        
        # Configure grid weights
        scrap_frame.columnconfigure(1, weight=1)
    
    
    def create_downtime_tab(self):
        """Create downtime entry tab"""
        downtime_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(downtime_frame, text="Downtime Entry")
        
        # Title
        title_label = ttk.Label(downtime_frame, text="Record Downtime", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # Operator number
        ttk.Label(downtime_frame, text="Operator Number:", style='Bold.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.downtime_op_var = tk.StringVar()
        ttk.Entry(downtime_frame, textvariable=self.downtime_op_var, style='Entry.TEntry', width=15).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        # Downtime reason
        ttk.Label(downtime_frame, text="Downtime Reason:", style='Bold.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.downtime_reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(downtime_frame, textvariable=self.downtime_reason_var, values=downtime_reasons,
                                   font=self.entry_font, width=25, state="readonly")
        reason_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Duration
        ttk.Label(downtime_frame, text="Duration (minutes):", style='Bold.TLabel').grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.downtime_duration_var = tk.StringVar()
        ttk.Entry(downtime_frame, textvariable=self.downtime_duration_var, style='Entry.TEntry', width=15).grid(row=3, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Help text
        help_label = ttk.Label(downtime_frame, text="(Enter duration between 1-480 minutes)", 
                              font=('Arial', 9), foreground='gray')
        help_label.grid(row=4, column=1, sticky=tk.W, padx=(0, 20), pady=(5, 0))
        
        # Submit button
        submit_btn = ttk.Button(downtime_frame, text="Record Downtime Entry", style='Large.TButton',
                               command=self.submit_downtime_entry)
        submit_btn.grid(row=5, column=0, columnspan=2, pady=(20, 0), sticky=tk.W)
        
        # Clear button
        clear_btn = ttk.Button(downtime_frame, text="Clear Form", style='Large.TButton',
                              command=self.clear_downtime_form)
        clear_btn.grid(row=5, column=1, pady=(20, 0), sticky=tk.E, padx=(20, 0))
        
        # Configure grid weights
        downtime_frame.columnconfigure(1, weight=1)
    
    
    def create_smc_scrap_tab(self):
        """Create SMC (Sheet Moulding Compound) scrap tab"""
        smc_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(smc_frame, text="SMC Scrap Entry")
        
        # Title
        title_label = ttk.Label(smc_frame, text="Record SMC (Sheet Moulding Compound) Scrap", style='Header.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # Operator number
        ttk.Label(smc_frame, text="Operator Number:", style='Bold.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.smc_op_var = tk.StringVar()
        ttk.Entry(smc_frame, textvariable=self.smc_op_var, style='Entry.TEntry', width=15).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        # Part type
        ttk.Label(smc_frame, text="Part Type:", style='Bold.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.smc_part_type_var = tk.StringVar()
        ttk.Entry(smc_frame, textvariable=self.smc_part_type_var, style='Entry.TEntry', width=25).grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # SMC scrap reason
        ttk.Label(smc_frame, text="SMC Scrap Reason:", style='Bold.TLabel').grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.smc_scrap_reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(smc_frame, textvariable=self.smc_scrap_reason_var, values=smc_scrap_reasons,
                                   font=self.entry_font, width=25, state="readonly")
        reason_combo.grid(row=3, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # SMC scrap count
        ttk.Label(smc_frame, text="SMC Scrap Count:", style='Bold.TLabel').grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.smc_scrap_count_var = tk.StringVar()
        ttk.Entry(smc_frame, textvariable=self.smc_scrap_count_var, style='Entry.TEntry', width=15).grid(row=4, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Submit button
        submit_btn = ttk.Button(smc_frame, text="Record SMC Scrap Entry", style='Large.TButton',
                               command=self.submit_smc_scrap_entry)
        submit_btn.grid(row=5, column=0, columnspan=2, pady=(20, 0), sticky=tk.W)
        
        # Clear button
        clear_btn = ttk.Button(smc_frame, text="Clear Form", style='Large.TButton',
                              command=self.clear_smc_scrap_form)
        clear_btn.grid(row=5, column=1, pady=(20, 0), sticky=tk.E, padx=(20, 0))
        
        # Configure grid weights
        smc_frame.columnconfigure(1, weight=1)
    
    
    def create_orders_tab(self):
        """Create orders viewing tab"""
        orders_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(orders_frame, text="View Orders")
        
        # Title
        title_label = ttk.Label(orders_frame, text="Available Orders", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Refresh button
        refresh_btn = ttk.Button(orders_frame, text="Refresh Orders", style='Large.TButton',
                                command=self.update_available_orders)
        refresh_btn.pack(pady=(0, 10))
        
        # Orders listbox with scrollbar
        orders_list_frame = ttk.Frame(orders_frame)
        orders_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for better display
        self.orders_tree = ttk.Treeview(orders_list_frame, columns=('order', 'part', 'count', 'status'), 
                                       show='headings', height=15)
        
        # Configure columns
        self.orders_tree.heading('order', text='Order Number')
        self.orders_tree.heading('part', text='Part Number')
        self.orders_tree.heading('count', text='Parts Count')
        self.orders_tree.heading('status', text='Status')
        
        self.orders_tree.column('order', width=120, anchor='center')
        self.orders_tree.column('part', width=120, anchor='center')
        self.orders_tree.column('count', width=120, anchor='center')
        self.orders_tree.column('status', width=100, anchor='center')
        
        # Add scrollbar
        orders_scrollbar = ttk.Scrollbar(orders_list_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=orders_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Order lookup section
        lookup_frame = ttk.LabelFrame(orders_frame, text="Order Lookup", padding="10")
        lookup_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(lookup_frame, text="Order Number:", style='Bold.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.lookup_order_var = tk.StringVar()
        ttk.Entry(lookup_frame, textvariable=self.lookup_order_var, style='Entry.TEntry', width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        lookup_btn = ttk.Button(lookup_frame, text="Lookup Order", style='Large.TButton',
                               command=self.lookup_specific_order)
        lookup_btn.pack(side=tk.LEFT)
    
    
    def submit_scrap_entry(self):
        """Submit scrap entry with validation"""
        try:
            # Get values
            operator_number = self.scrap_op_var.get().strip()
            part_number = self.scrap_part_var.get().strip()
            order_number = self.scrap_order_var.get().strip()
            scrap_reason = self.scrap_reason_var.get().strip()
            scrap_count = self.scrap_count_var.get().strip()
            
            # Validate required fields
            if not operator_number:
                messagebox.showerror("Error", "Please enter operator number")
                return
            
            if not part_number:
                messagebox.showerror("Error", "Please select part number")
                return
            
            if not order_number:
                messagebox.showerror("Error", "Please enter order number")
                return
            
            if not scrap_reason:
                messagebox.showerror("Error", "Please select scrap reason")
                return
            
            if not scrap_count:
                messagebox.showerror("Error", "Please enter scrap count")
                return
            
            # Validate data types and ranges
            if not validate_operator_number(operator_number):
                messagebox.showerror("Error", "Invalid operator number (0-9999)")
                return
                
            if not validate_parts_count(scrap_count):
                messagebox.showerror("Error", "Invalid scrap count")
                return
            
            # Validate order number
            try:
                order_num = int(order_number)
                if order_num <= 0:
                    messagebox.showerror("Error", "Order number must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid order number")
                return
            
            # Save the entry
            save_scrap_entry(int(operator_number), part_number, int(order_number), 
                           scrap_reason, int(scrap_count))
            
            messagebox.showinfo("Success", f"Scrap entry recorded successfully!\n"
                                         f"Operator: {operator_number}\n"
                                         f"Part: {part_number}\n"
                                         f"Order: {order_number}\n"
                                         f"Reason: {scrap_reason}\n"
                                         f"Count: {scrap_count}")
            
            # Clear form
            self.clear_scrap_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scrap entry: {str(e)}")
    
    
    def submit_downtime_entry(self):
        """Submit downtime entry with validation"""
        try:
            # Get values
            operator_number = self.downtime_op_var.get().strip()
            downtime_reason = self.downtime_reason_var.get().strip()
            duration = self.downtime_duration_var.get().strip()
            
            # Validate required fields
            if not operator_number:
                messagebox.showerror("Error", "Please enter operator number")
                return
            
            if not downtime_reason:
                messagebox.showerror("Error", "Please select downtime reason")
                return
            
            if not duration:
                messagebox.showerror("Error", "Please enter downtime duration")
                return
            
            # Validate data types and ranges
            if not validate_operator_number(operator_number):
                messagebox.showerror("Error", "Invalid operator number (0-9999)")
                return
                
            if not validate_downtime_duration(duration):
                messagebox.showerror("Error", "Invalid duration (1-480 minutes)")
                return
            
            # Save the entry
            save_downtime_entry(int(operator_number), downtime_reason, int(duration))
            
            messagebox.showinfo("Success", f"Downtime entry recorded successfully!\n"
                                         f"Operator: {operator_number}\n"
                                         f"Reason: {downtime_reason}\n"
                                         f"Duration: {duration} minutes")
            
            # Clear form
            self.clear_downtime_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save downtime entry: {str(e)}")
    
    
    def submit_smc_scrap_entry(self):
        """Submit SMC scrap entry with validation"""
        try:
            # Get values
            operator_number = self.smc_op_var.get().strip()
            part_type = self.smc_part_type_var.get().strip()
            smc_scrap_reason = self.smc_scrap_reason_var.get().strip()
            smc_scrap_count = self.smc_scrap_count_var.get().strip()
            
            # Validate required fields
            if not operator_number:
                messagebox.showerror("Error", "Please enter operator number")
                return
            
            if not part_type:
                messagebox.showerror("Error", "Please enter part type")
                return
            
            if not smc_scrap_reason:
                messagebox.showerror("Error", "Please select SMC scrap reason")
                return
            
            if not smc_scrap_count:
                messagebox.showerror("Error", "Please enter SMC scrap count")
                return
            
            # Validate data types and ranges
            if not validate_operator_number(operator_number):
                messagebox.showerror("Error", "Invalid operator number (0-9999)")
                return
                
            if not validate_smc_scrap_count(smc_scrap_count):
                messagebox.showerror("Error", "Invalid SMC scrap count")
                return
            
            # Save the entry
            save_smc_scrap_entry(int(operator_number), part_type, smc_scrap_reason, int(smc_scrap_count))
            
            messagebox.showinfo("Success", f"SMC scrap entry recorded successfully!\n"
                                         f"Operator: {operator_number}\n"
                                         f"Part Type: {part_type}\n"
                                         f"Reason: {smc_scrap_reason}\n"
                                         f"Count: {smc_scrap_count}")
            
            # Clear form
            self.clear_smc_scrap_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save SMC scrap entry: {str(e)}")
    
    
    def clear_scrap_form(self):
        """Clear scrap entry form"""
        self.scrap_op_var.set("")
        self.scrap_part_var.set("")
        self.scrap_order_var.set("")
        self.scrap_reason_var.set("")
        self.scrap_count_var.set("")
    
    
    def clear_downtime_form(self):
        """Clear downtime entry form"""
        self.downtime_op_var.set("")
        self.downtime_reason_var.set("")
        self.downtime_duration_var.set("")
    
    
    def clear_smc_scrap_form(self):
        """Clear SMC scrap entry form"""
        self.smc_op_var.set("")
        self.smc_part_type_var.set("")
        self.smc_scrap_reason_var.set("")
        self.smc_scrap_count_var.set("")
    
    
    def update_available_orders(self):
        """Update the available orders display"""
        try:
            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            
            # Get recent orders
            orders = get_recent_orders(50)  # Get more orders for production floor
            
            if orders:
                for order in orders:
                    order_number, part_number, parts_per_order, created_date, status = order
                    self.orders_tree.insert('', 'end', values=(order_number, part_number, parts_per_order, status))
            else:
                # Insert a message if no orders
                self.orders_tree.insert('', 'end', values=("No orders", "available", "", ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update orders: {str(e)}")
    
    
    def lookup_specific_order(self):
        """Lookup a specific order by number"""
        try:
            order_number = self.lookup_order_var.get().strip()
            
            if not order_number:
                messagebox.showwarning("Warning", "Please enter an order number")
                return
            
            try:
                order_num = int(order_number)
            except ValueError:
                messagebox.showerror("Error", "Invalid order number")
                return
            
            # Get order details
            order = get_order_by_number(order_num)
            
            if order:
                order_number, part_number, parts_per_order, created_date, status = order
                messagebox.showinfo("Order Found", 
                                   f"Order Number: {order_number}\n"
                                   f"Part Number: {part_number}\n"
                                   f"Parts per Order: {parts_per_order}\n"
                                   f"Created: {created_date}\n"
                                   f"Status: {status}")
            else:
                messagebox.showinfo("Order Not Found", f"No order found with number {order_num}")
            
            # Clear the lookup field
            self.lookup_order_var.set("")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to lookup order: {str(e)}")
    
    
    def update_employee_status(self, event=None):
        """Update employee status display as user types"""
        employee_number = self.employee_number_var.get().strip()
        
        if len(employee_number) == 5 and employee_number.isdigit():
            try:
                status, message = get_employee_status(employee_number)
                if status == "clocked_in":
                    self.status_label.config(text=message, foreground='green')
                elif status == "clocked_out":
                    self.status_label.config(text=message, foreground='orange')
                else:
                    self.status_label.config(text=message, foreground='blue')
            except Exception:
                self.status_label.config(text="Enter valid 5-digit employee number", foreground='blue')
        else:
            self.status_label.config(text="Enter 5-digit employee number (e.g., 12345)", foreground='blue')
    
    
    def check_employee_status(self):
        """Check and display employee status"""
        try:
            employee_number = self.employee_number_var.get().strip()
            
            if not employee_number:
                messagebox.showwarning("Warning", "Please enter your 5-digit employee number")
                return
            
            if not validate_employee_number(employee_number):
                messagebox.showerror("Error", "Please enter a valid 5-digit employee number")
                return
            
            status, message = get_employee_status(int(employee_number))
            
            if status == "clocked_in":
                messagebox.showinfo("Status - Clocked In", message)
            elif status == "clocked_out":
                messagebox.showinfo("Status - Clocked Out", message)
            else:
                messagebox.showinfo("Status", message)
            
            self.update_employee_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check status: {str(e)}")
    
    
    def clock_in_employee(self):
        """Clock in an employee"""
        try:
            employee_number = self.employee_number_var.get().strip()
            
            if not employee_number:
                messagebox.showwarning("Warning", "Please enter your 5-digit employee number")
                return
            
            if not validate_employee_number(employee_number):
                messagebox.showerror("Error", "Please enter a valid 5-digit employee number")
                return
            
            success, message = clock_in(int(employee_number))
            
            if success:
                messagebox.showinfo("Clock In Successful", message)
            else:
                messagebox.showwarning("Clock In Failed", message)
            
            self.update_employee_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clock in: {str(e)}")
    
    
    def clock_out_employee(self):
        """Clock out an employee"""
        try:
            employee_number = self.employee_number_var.get().strip()
            
            if not employee_number:
                messagebox.showwarning("Warning", "Please enter your 5-digit employee number")
                return
            
            if not validate_employee_number(employee_number):
                messagebox.showerror("Error", "Please enter a valid 5-digit employee number")
                return
            
            success, message = clock_out(int(employee_number))
            
            if success:
                messagebox.showinfo("Clock Out Successful", message)
            else:
                messagebox.showwarning("Clock Out Failed", message)
            
            self.update_employee_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clock out: {str(e)}")


def main():
    """Main function to run the operator interface"""
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
        app = OperatorInterface(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()