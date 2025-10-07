import os
import sys
import tkinter as tk


# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Main entry point for SimDock 3.1"""
    try:
        print("Starting SimDock 3.1...")
        print("Available docking engines will be detected automatically.")
        
        # Import and create the application
        from gui.main_window import MainWindow
        app = MainWindow()
        app.run()
        
    except Exception as e:
        print(f"Failed to start SimDock: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")

if __name__ == "__main__":
    main()