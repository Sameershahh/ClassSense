# backend/routers/hod.py
# REST API endpoints for HOD management.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.database import get_db
from backend.auth import require_hod
from backend.models.user import User as DbUser, Department, Course, CourseSlot, InstructorCourseMapping

router = APIRouter(dependencies=[Depends(require_hod)])


# ── Pydantic Request Validation Schemas ───────────────────────

class InstructorOnboard(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    department_code: str  # "CS" or "BBA"
    course_slot_ids: List[int]  # List of CourseSlot IDs to map


# ── HOD Endpoints ─────────────────────────────────────────────

@router.get("/departments", summary="List all Departments")
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.get("/courses", summary="List courses by Department")
def list_courses(dept_code: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Course)
    if dept_code:
        query = query.join(Department).filter(Department.code == dept_code)
    courses = query.all()
    
    result = []
    for c in courses:
        slots = []
        for s in c.slots:
            slots.append({
                "id": s.id,
                "time_slot": s.time_slot,
                "room_name": s.classroom.name if s.classroom else "Unassigned"
            })
        result.append({
            "id": c.id,
            "course_name": c.course_name,
            "course_code": c.course_code,
            "slots": slots
        })
    return result


@router.post("/instructors", status_code=201, summary="Onboard new Instructor and assign courses")
def onboard_instructor(payload: InstructorOnboard, db: Session = Depends(get_db)):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Check unique email
    existing = db.query(DbUser).filter(DbUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Instructor email address already registered.")

    # Get default Iqra University
    from backend.models.user import University
    uni = db.query(University).filter(University.name == "Iqra University").first()
    uni_id = uni.id if uni else 1

    instructor = DbUser(
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password),
        role="instructor",
        full_name=payload.name,
        university_id=uni_id
    )
    db.add(instructor)
    db.commit()
    db.refresh(instructor)

    # Link to selected course slots
    mappings = []
    for slot_id in payload.course_slot_ids:
        slot = db.query(CourseSlot).filter(CourseSlot.id == slot_id).first()
        if slot:
            mapping = InstructorCourseMapping(instructor_id=instructor.id, course_slot_id=slot_id)
            db.add(mapping)
            mappings.append(slot_id)
    db.commit()

    return {
        "instructor_id": instructor.id,
        "email": instructor.email,
        "name": instructor.full_name,
        "assigned_slots": mappings
    }


@router.get("/instructors", summary="List all Instructors and their mapped courses")
def list_instructors(db: Session = Depends(get_db)):
    instructors = db.query(DbUser).filter(DbUser.role == "instructor").all()
    result = []
    for inst in instructors:
        mappings = db.query(InstructorCourseMapping).filter(InstructorCourseMapping.instructor_id == inst.id).all()
        assigned_courses = []
        for m in mappings:
            slot = m.course_slot
            if slot:
                assigned_courses.append({
                    "slot_id": slot.id,
                    "course_code": slot.course.course_code,
                    "course_name": slot.course.course_name,
                    "time_slot": slot.time_slot,
                    "room_name": slot.classroom.name if slot.classroom else "Unassigned"
                })
        result.append({
            "id": inst.id,
            "name": inst.name if hasattr(inst, "name") else inst.full_name,
            "email": inst.email,
            "assigned_courses": assigned_courses
        })
    return result
