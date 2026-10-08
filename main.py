import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from app.db import Database

class Window(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Engineering Course File Manager")
        s=db.stats()
        self.setCentralWidget(QLabel(f"Courses: {s['courses']} | Faculty: {s['faculty']} | Assignments: {s['assignments']}"))

if __name__ == "__main__":
    app=QApplication(sys.argv)
    win=Window(Database())
    win.resize(900,300)
    win.show()
    sys.exit(app.exec())
