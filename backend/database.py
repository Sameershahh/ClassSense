# backend/database.py
# SQLAlchemy database connection and session management.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./classsense_dev.db"
)

# SQLite needs special connect args; PostgreSQL uses NullPool (no connection leak)
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
    engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency. Yields one DB session per request,
    closes it automatically when the request finishes.
    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all tables defined via Base.metadata.
    Called once at application startup.
    """
    from backend.models.session import Session, FrameAnalytic, SessionSummary  # noqa
    from backend.models.user import User, University, Classroom, Department, Course, CourseSlot, InstructorCourseMapping  # noqa
    Base.metadata.create_all(bind=engine)
    seed_data()


def seed_data():
    """
    Seeds default admin, HOD, instructor, university, departments, courses, classrooms and course slots if not already present.
    """
    db = SessionLocal()
    try:
        from backend.models.user import User, University, Classroom, Department, Course, CourseSlot
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 1. Onboard default University
        iqra = db.query(University).filter(University.name == "Iqra University").first()
        if not iqra:
            iqra = University(name="Iqra University", address="Karachi, Pakistan")
            db.add(iqra)
            db.commit()
            db.refresh(iqra)

        # 2. Onboard default Classrooms
        cr1 = db.query(Classroom).filter(Classroom.name == "CS Lab 1").first()
        if not cr1:
            cr1 = Classroom(
                name="CS Lab 1",
                university_id=iqra.id,
                rtsp_url="rtsp://admin:admin123@192.168.1.100:554/stream1",
                camera_status="online"
            )
            db.add(cr1)

        cr2 = db.query(Classroom).filter(Classroom.name == "Seminar Hall").first()
        if not cr2:
            cr2 = Classroom(
                name="Seminar Hall",
                university_id=iqra.id,
                rtsp_url="rtsp://admin:admin123@192.168.1.101:554/stream1",
                camera_status="offline"
            )
            db.add(cr2)

        db.commit()
        db.refresh(cr1)
        db.refresh(cr2)

        # 3. Seed Super Admin
        admin = db.query(User).filter(User.email == "admin@classsense.com").first()
        if not admin:
            admin = User(
                email="admin@classsense.com",
                hashed_password=pwd_context.hash("admin123"),
                role="admin",
                full_name="ClassSense Admin",
                university_id=iqra.id
            )
            db.add(admin)

        # 4. Seed default HOD
        hod = db.query(User).filter(User.email == "hod@classsense.com").first()
        if not hod:
            hod = User(
                email="hod@classsense.com",
                hashed_password=pwd_context.hash("hod123"),
                role="hod",
                full_name="ClassSense HOD",
                university_id=iqra.id
            )
            db.add(hod)

        # 5. Seed default Instructor
        instructor = db.query(User).filter(User.email == "instructor@classsense.com").first()
        if not instructor:
            instructor = User(
                email="instructor@classsense.com",
                hashed_password=pwd_context.hash("instructor123"),
                role="instructor",
                full_name="ClassSense Instructor",
                university_id=iqra.id
            )
            db.add(instructor)

        db.commit()

        # 6. Seed Departments
        cs_dept = db.query(Department).filter(Department.code == "CS").first()
        if not cs_dept:
            cs_dept = Department(name="Computer Science", code="CS")
            db.add(cs_dept)
        bba_dept = db.query(Department).filter(Department.code == "BBA").first()
        if not bba_dept:
            bba_dept = Department(name="Business Administration", code="BBA")
            db.add(bba_dept)
        db.commit()
        db.refresh(cs_dept)
        db.refresh(bba_dept)

        # 7. Seed 10 CS Courses and 10 BBA Courses
        cs_courses = [
            ("CS101", "Introduction to Computing"),
            ("CS102", "Object Oriented Programming"),
            ("CS201", "Data Structures & Algorithms"),
            ("CS202", "Database Systems"),
            ("CS301", "Software Engineering"),
            ("CS302", "Computer Networks"),
            ("CS401", "Artificial Intelligence"),
            ("CS402", "Information Security"),
            ("CS498", "Final Year Project I"),
            ("CS499", "Final Year Project II"),
        ]
        
        bba_courses = [
            ("BBA101", "Principles of Management"),
            ("BBA102", "Financial Accounting"),
            ("BBA201", "Microeconomics"),
            ("BBA202", "Macroeconomics"),
            ("BBA301", "Marketing Management"),
            ("BBA302", "Human Resource Management"),
            ("BBA401", "Business Finance"),
            ("BBA402", "Strategic Management"),
            ("BBA403", "Consumer Behavior"),
            ("BBA404", "Organizational Behavior"),
        ]

        def seed_dept_courses(dept_id, courses_list):
            for code, name in courses_list:
                course = db.query(Course).filter(Course.course_code == code).first()
                if not course:
                    course = Course(course_name=name, course_code=code, department_id=dept_id)
                    db.add(course)
                    db.commit()
                    db.refresh(course)
                
                # Check if slots exist for this course
                existing_slots = db.query(CourseSlot).filter(CourseSlot.course_id == course.id).count()
                if existing_slots == 0:
                    # Seed 3 distinct slots
                    slots_data = [
                        ("Monday 09:00 AM - 10:30 AM", cr1.id),
                        ("Wednesday 11:00 AM - 12:30 PM", cr2.id),
                        ("Friday 02:00 PM - 03:30 PM", cr1.id),
                    ]
                    for time_slot, room_id in slots_data:
                        slot = CourseSlot(course_id=course.id, time_slot=time_slot, classroom_id=room_id)
                        db.add(slot)
            db.commit()

        seed_dept_courses(cs_dept.id, cs_courses)
        seed_dept_courses(bba_dept.id, bba_courses)

    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error seeding database: {e}", exc_info=True)
    finally:
        db.close()

