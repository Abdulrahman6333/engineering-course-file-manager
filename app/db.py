import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "portfolio_demo.db"

REQUIREMENTS = [
    "Staff CV", "Course Specification", "Course Materials", "Student Activities",
    "Quizzes", "Quizzes Answer", "Quizzes Student Samples", "Mid-Term Exam",
    "Mid-Term Model Answer", "Mid-Term Student Samples", "Final-Term Exam",
    "Final-Term Model Answer", "Oral Cards", "Practical Exam",
    "Student Attendance", "Student Grades", "Course Report", "Blue Print",
]

class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._schema()
        self._seed()

    def _schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS faculty(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, rank TEXT,
            department TEXT, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS courses(
            id INTEGER PRIMARY KEY, code TEXT NOT NULL, title TEXT NOT NULL,
            department TEXT NOT NULL, level INTEGER DEFAULT 0,
            regulation TEXT NOT NULL, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS offerings(
            id INTEGER PRIMARY KEY, academic_year TEXT NOT NULL,
            semester TEXT NOT NULL, course_id INTEGER NOT NULL,
            faculty_id INTEGER);
        CREATE TABLE IF NOT EXISTS requirement_state(
            offering_id INTEGER NOT NULL, requirement_no INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Missing',
            PRIMARY KEY(offering_id, requirement_no));
        """)
        self.conn.commit()

    def _seed(self):
        if self.conn.execute("SELECT COUNT(*) FROM faculty").fetchone()[0] == 0:
            self.conn.executemany(
                "INSERT INTO faculty(name,rank,department) VALUES(?,?,?)",
                [
                    ("Faculty Member 01","Lecturer","Mechatronics"),
                    ("Faculty Member 02","Assistant Lecturer","Basic Science"),
                    ("Faculty Member 03","Lecturer","Civil"),
                ])
        if self.conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
            self.conn.executemany(
                "INSERT INTO courses(code,title,department,level,regulation) VALUES(?,?,?,?,?)",
                [
                    ("MEC301","Control Systems","Mechatronics",3,"144 Credit Hours"),
                    ("MEC322","Robotics","Mechatronics",3,"144 Credit Hours"),
                    ("MEC410","Advanced Mechatronics Systems","Mechatronics",4,"144 Credit Hours"),
                    ("BAS201","Engineering Mathematics","Basic Science",2,"144 Credit Hours"),
                    ("CIV210","Fluid Mechanics","Civil",2,"144 Credit Hours"),
                ])
        if self.conn.execute("SELECT COUNT(*) FROM offerings").fetchone()[0] == 0:
            people=self.conn.execute("SELECT id FROM faculty ORDER BY id").fetchall()
            courses=self.conn.execute("SELECT id FROM courses ORDER BY id").fetchall()
            for i,course in enumerate(courses):
                self.conn.execute(
                    "INSERT INTO offerings(academic_year,semester,course_id,faculty_id) VALUES(?,?,?,?)",
                    ("2026/2027","Fall",course["id"],people[i%len(people)]["id"]))
        self.conn.commit()

    def faculty(self):
        return self.conn.execute("SELECT * FROM faculty WHERE active=1 ORDER BY name").fetchall()

    def courses(self):
        return self.conn.execute("SELECT * FROM courses WHERE active=1 ORDER BY department,code").fetchall()

    def offerings(self):
        return self.conn.execute("""
        SELECT o.id,o.academic_year,o.semester,c.code,c.title,c.department,
               c.regulation,f.name AS faculty_name
        FROM offerings o
        JOIN courses c ON c.id=o.course_id
        LEFT JOIN faculty f ON f.id=o.faculty_id
        ORDER BY c.department,c.code
        """).fetchall()

    def add_faculty(self,name,rank,department):
        self.conn.execute("INSERT INTO faculty(name,rank,department) VALUES(?,?,?)",
                          (name.strip(),rank.strip(),department.strip()))
        self.conn.commit()

    def add_course(self,code,title,department,level,regulation):
        self.conn.execute(
            "INSERT INTO courses(code,title,department,level,regulation) VALUES(?,?,?,?,?)",
            (code.strip(),title.strip(),department.strip(),int(level),regulation))
        self.conn.commit()

    def assign(self,course_id,faculty_id):
        self.conn.execute(
            "INSERT INTO offerings(academic_year,semester,course_id,faculty_id) VALUES(?,?,?,?)",
            ("2026/2027","Fall",course_id,faculty_id))
        self.conn.commit()

    def set_requirement(self,offering_id,requirement_no,complete):
        status="Complete" if complete else "Missing"
        self.conn.execute("""
        INSERT INTO requirement_state(offering_id,requirement_no,status)
        VALUES(?,?,?)
        ON CONFLICT(offering_id,requirement_no)
        DO UPDATE SET status=excluded.status
        """,(offering_id,requirement_no,status))
        self.conn.commit()

    def progress(self,offering_id):
        done=self.conn.execute(
            "SELECT COUNT(*) FROM requirement_state WHERE offering_id=? AND status='Complete'",
            (offering_id,)).fetchone()[0]
        return done,len(REQUIREMENTS)

    def stats(self):
        return {
            "faculty":self.conn.execute("SELECT COUNT(*) FROM faculty WHERE active=1").fetchone()[0],
            "courses":self.conn.execute("SELECT COUNT(*) FROM courses WHERE active=1").fetchone()[0],
            "assignments":self.conn.execute("SELECT COUNT(*) FROM offerings").fetchone()[0],
        }
