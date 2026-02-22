#!/usr/bin/env python3

print("Starting application test...")

try:
    print("Importing tkinter...")
    import tkinter as tk
    from tkinter import ttk, messagebox
    print("Tkinter imported successfully")
    
    print("Creating root window...")
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("300x200")
    print("Root window created")
    
    print("Adding test label...")
    label = ttk.Label(root, text="Test Application - GUI Working!")
    label.pack(pady=50)
    
    print("Starting mainloop...")
    # Auto-close after 3 seconds for testing
    root.after(3000, lambda: root.quit())
    root.mainloop()
    print("Application finished successfully")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test complete")