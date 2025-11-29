from PySide6.QtWidgets import QApplication
from window import MainWindow
import sys

# Create application
app = QApplication(sys.argv)

# Create and show window
window = MainWindow()
window.show()

# Run application
sys.exit(app.exec())
