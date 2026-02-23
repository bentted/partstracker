"""
Simplified Parts Tracker Test - for debugging window closing issue
"""

import tkinter as tk
from tkinter import messagebox
import sys
import traceback

class TestWindow:
    def __init__(self):
        try:
            print("Creating test window...")
            
            # Create root window
            self.root = tk.Tk()
            self.root.title("Parts Tracker - Test Window")
            self.root.geometry("400x300")
            
            # Center the window
            self.center_window()
            
            # Add some basic widgets
            frame = tk.Frame(self.root, padx=20, pady=20)
            frame.pack(fill="both", expand=True)
            
            tk.Label(frame, text="Parts Tracker Test", font=("Arial", 16, "bold")).pack(pady=10)
            tk.Label(frame, text="If you can see this window, the basic GUI is working.").pack(pady=5)
            
            # Test button
            tk.Button(frame, text="Test Button", command=self.test_click).pack(pady=10)
            
            # Close button
            tk.Button(frame, text="Close", command=self.close_app).pack(pady=5)
            
            # Status area
            self.status_var = tk.StringVar()
            self.status_var.set("Window created successfully")
            tk.Label(frame, textvariable=self.status_var, fg="green").pack(pady=10)
            
            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.close_app)
            
            print("Test window created successfully")
            
        except Exception as e:
            print(f"Error creating test window: {e}")
            traceback.print_exc()
            try:
                messagebox.showerror("Error", f"Failed to create test window: {e}")
            except:
                pass
            raise
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = 400
        height = 300
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def test_click(self):
        """Test button click handler"""
        self.status_var.set("Button clicked successfully!")
        messagebox.showinfo("Test", "Button click works correctly!")
    
    def close_app(self):
        """Close the application"""
        print("Closing test window...")
        self.root.destroy()
    
    def run(self):
        """Start the main event loop"""
        try:
            print("Starting main event loop...")
            self.root.mainloop()
            print("Main event loop ended normally")
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()
            raise

def main():
    """Main function"""
    try:
        print("=" * 50)
        print("Parts Tracker - Simple Test")
        print("=" * 50)
        print("Starting application...")
        
        # Create and run test window
        app = TestWindow()
        app.run()
        
        print("Application completed normally")
        
    except Exception as e:
        print(f"Application error: {e}")
        traceback.print_exc()
        
        try:
            # Try to show error dialog
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", 
                               f"The application failed to start:\n\n{str(e)}\n\nCheck the console for more details.")
            root.destroy()
        except:
            pass
        
        print("Press Enter to exit...")
        try:
            input()
        except:
            pass
    
    finally:
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()