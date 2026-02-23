#!/usr/bin/env python3
"""
Debug runner for Parts Tracker application.
This script captures all output and errors to help diagnose issues.
"""

import sys
import traceback
from datetime import datetime

def run_with_error_capture():
    """Run the parts tracker with comprehensive error capture"""
    
    log_file = "debug_log.txt"
    
    try:
        # Redirect output to capture everything
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        output_capture = io.StringIO()
        error_capture = io.StringIO()
        
        print(f"Starting Parts Tracker debug run at {datetime.now()}")
        print(f"Capturing output to {log_file}")
        
        with open(log_file, 'w') as log:
            log.write(f"Parts Tracker Debug Log - {datetime.now()}\n")
            log.write("=" * 50 + "\n")
            log.flush()
            
            try:
                # Import and run the main application
                print("Importing parts tracker...")
                log.write("Importing parts tracker module...\n")
                log.flush()
                
                # Import the main module
                import importlib.util
                spec = importlib.util.spec_from_file_location("parts_tracker", "pparts tracker.py")
                parts_tracker = importlib.util.module_from_spec(spec)
                
                log.write("Module imported successfully, executing...\n")
                log.flush()
                
                # Execute the module (this will call main())
                spec.loader.exec_module(parts_tracker)
                
                log.write("Application completed normally\n")
                
            except Exception as e:
                error_msg = f"Application error: {str(e)}\n"
                error_traceback = traceback.format_exc()
                
                print(f"ERROR: {error_msg}")
                print("Full traceback:")
                print(error_traceback)
                
                log.write(f"ERROR: {error_msg}\n")
                log.write("Full traceback:\n")
                log.write(error_traceback)
                log.write("\n")
                
                # Try to show error in GUI if possible
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()  # Hide the root window
                    messagebox.showerror("Parts Tracker Error", 
                                       f"Application failed with error:\n\n{error_msg}\n\nSee {log_file} for details.")
                    root.destroy()
                except:
                    pass  # GUI might not be available
            
            finally:
                log.write(f"\nDebug run completed at {datetime.now()}\n")
    
    except Exception as setup_error:
        print(f"Failed to set up error capture: {setup_error}")
        traceback.print_exc()
    
    finally:
        print(f"\nCheck {log_file} for detailed output")
        input("Press Enter to exit...")

if __name__ == "__main__":
    run_with_error_capture()