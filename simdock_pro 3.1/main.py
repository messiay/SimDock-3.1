#!/usr/bin/env python3
import sys
import os

# Add both the root directory and the simdock package to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'simdock'))

try:
    from simdock.gui.main_window import MainWindow
except ImportError:
    # Fallback: try direct import
    from gui.main_window import MainWindow

from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SimDock")
    app.setApplicationVersion("3.1")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
