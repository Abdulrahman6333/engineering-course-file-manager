import sys
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from app.db import Database, REQUIREMENTS

STYLE = """
QWidget{font-family:Segoe UI;font-size:13px;background:#F6F8FB;color:#15395F}
QPushButton{background:#1769C2;color:white;border:0;border-radius:8px;padding:9px 12px}
QTableWidget{background:white;border:1px solid #D9E4EF;gridline-color:#E9F0F6}
QHeaderView::section{background:#EAF2FB;color:#15395F;padding:8px;border:0;font-weight:700}
"""

def fill(table, rows):
    table.setRowCount(len(rows))
    for i,row in enumerate(rows):
        for j,value in enumerate(row):
            table.setItem(i,j,QTableWidgetItem(str(value)))

class CoursesPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        l=QVBoxLayout(self);l.addWidget(QLabel("Academic Management"))
        self.t=QTableWidget(0,5)
        self.t.setHorizontalHeaderLabels(["Code","Course","Department","Level","Regulation"])
        self.t.horizontalHeader().setStretchLastSection(True);l.addWidget(self.t);self.refresh()
    def refresh(self):
        fill(self.t,[[r["code"],r["title"],r["department"],r["level"],r["regulation"]] for r in self.db.courses()])

class FacultyPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        l=QVBoxLayout(self);l.addWidget(QLabel("Faculty and Assignments"))
        self.t=QTableWidget(0,3)
        self.t.setHorizontalHeaderLabels(["Display Name","Academic Rank","Department"])
        self.t.horizontalHeader().setStretchLastSection(True);l.addWidget(self.t);self.refresh()
    def refresh(self):
        fill(self.t,[[r["name"],r["rank"],r["department"]] for r in self.db.faculty()])

class ReportsPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        l=QVBoxLayout(self);l.addWidget(QLabel("Course File Reports"))
        self.t=QTableWidget(0,6)
        self.t.setHorizontalHeaderLabels(["Faculty","Code","Course","Department","Progress","Status"])
        self.t.horizontalHeader().setStretchLastSection(True);l.addWidget(self.t);self.refresh()
    def refresh(self):
        rows=[]
        for r in self.db.offerings():
            done,total=self.db.progress(r["id"])
            status="Complete" if done==total else "In Progress" if done else "Missing"
            rows.append([r["faculty_name"] or "Unassigned",r["code"],r["title"],r["department"],f"{done}/{total}",status])
        fill(self.t,rows)

class CourseFilesPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        l=QVBoxLayout(self);l.addWidget(QLabel("Course File Requirements"))
        self.t=QTableWidget(0,4)
        self.t.setHorizontalHeaderLabels(["Course","Faculty","Requirement","Status"])
        self.t.horizontalHeader().setStretchLastSection(True);l.addWidget(self.t);self.refresh()
    def refresh(self):
        rows=[]
        for off in self.db.offerings():
            complete={x["requirement_no"] for x in self.db.conn.execute(
                "SELECT requirement_no FROM requirement_state WHERE offering_id=? AND status='Complete'",(off["id"],))}
            for i,req in enumerate(REQUIREMENTS,1):
                rows.append([off["code"],off["faculty_name"] or "Unassigned",req,"Complete" if i in complete else "Missing"])
        fill(self.t,rows)

class Dashboard(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        l=QVBoxLayout(self)
        self.title=QLabel();self.title.setStyleSheet("font-size:24px;font-weight:800")
        l.addWidget(QLabel("Dashboard"));l.addWidget(self.title);l.addStretch();self.refresh()
    def refresh(self):
        s=self.db.stats()
        self.title.setText(f"Courses: {s['courses']}   |   Faculty: {s['faculty']}   |   Assignments: {s['assignments']}")

class Window(QMainWindow):
    def __init__(self,db):
        super().__init__();self.db=db
        self.setWindowTitle("Engineering Course File Manager")
        self.setStyleSheet(STYLE);self.resize(1280,760)
        root=QWidget();self.setCentralWidget(root);outer=QHBoxLayout(root)
        side=QVBoxLayout();brand=QLabel("Engineering Course File Manager\nPublic Portfolio Edition")
        brand.setStyleSheet("font-size:18px;font-weight:800;color:#1769C2");side.addWidget(brand)
        self.stack=QStackedWidget()
        pages=[
            ("Dashboard",Dashboard(db)),
            ("Academic Management",CoursesPage(db)),
            ("Faculty and Assignments",FacultyPage(db)),
            ("Course Files",CourseFilesPage(db)),
            ("Reports",ReportsPage(db)),
        ]
        for name,page in pages:
            self.stack.addWidget(page)
            b=QPushButton(name);b.clicked.connect(lambda _,p=page:self.open_page(p));side.addWidget(b)
        side.addStretch();outer.addLayout(side);outer.addWidget(self.stack,1)
    def open_page(self,page):
        if hasattr(page,"refresh"):page.refresh()
        self.stack.setCurrentWidget(page)

if __name__=="__main__":
    app=QApplication(sys.argv)
    win=Window(Database())
    win.show()
    sys.exit(app.exec())
