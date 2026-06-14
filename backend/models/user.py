# backend/models/user.py
# SQLAlchemy ORM models for University, Classroom, and User roles.

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base


class University(Base):
    """
    Onboarded Universities in ClassSense.
    """
    __tablename__ = "universities"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name       = Column(String(150), unique=True, nullable=False, index=True)
    address    = Column(String(250), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    classrooms = relationship("Classroom", back_populates="university", cascade="all, delete-orphan")
    users      = relationship("User", back_populates="university")

    def __repr__(self):
        return f"<University id={self.id} name={self.name}>"


class Classroom(Base):
    """
    Classrooms inside a University with configured RTSP camera streams.
    """
    __tablename__ = "classrooms"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name          = Column(String(100), nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    rtsp_url      = Column(String(500), nullable=True)
    camera_status = Column(String(30), default="offline", nullable=False)  # online | offline
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    university    = relationship("University", back_populates="classrooms")

    def __repr__(self):
        return f"<Classroom id={self.id} name={self.name} university_id={self.university_id}>"


class User(Base):
    """
    User accounts (Super Admins and Instructors).
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email           = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(250), nullable=False)
    role            = Column(String(30), default="instructor", nullable=False)  # admin | instructor
    full_name       = Column(String(100), nullable=True)
    university_id   = Column(Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    university      = relationship("University", back_populates="users")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


class Department(Base):
    """
    University Departments (e.g. CS, BBA).
    """
    __tablename__ = "departments"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name       = Column(String(100), unique=True, nullable=False)
    code       = Column(String(20), unique=True, nullable=False)  # e.g. "CS", "BBA"

    # Relationships
    courses    = relationship("Course", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department id={self.id} code={self.code}>"


class Course(Base):
    """
    Academic Courses within a Department.
    """
    __tablename__ = "courses"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_name   = Column(String(150), nullable=False)
    course_code   = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    department    = relationship("Department", back_populates="courses")
    slots         = relationship("CourseSlot", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course id={self.id} code={self.course_code}>"


class CourseSlot(Base):
    """
    Specific time slot and room assignment for a Course.
    """
    __tablename__ = "course_slots"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id     = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    time_slot     = Column(String(100), nullable=False)
    classroom_id  = Column(Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    course        = relationship("Course", back_populates="slots")
    classroom     = relationship("Classroom")
    mappings      = relationship("InstructorCourseMapping", back_populates="course_slot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CourseSlot id={self.id} course_id={self.course_id} slot={self.time_slot}>"


class InstructorCourseMapping(Base):
    """
    Links instructors (User) to CourseSlots they are assigned to teach.
    """
    __tablename__ = "instructor_course_mappings"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instructor_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_slot_id = Column(Integer, ForeignKey("course_slots.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    instructor     = relationship("User")
    course_slot    = relationship("CourseSlot", back_populates="mappings")

    def __repr__(self):
        return f"<InstructorCourseMapping id={self.id} instructor_id={self.instructor_id} slot_id={self.course_slot_id}>"

