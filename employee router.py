from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
import random
import string

from app.database import get_db
from app.models.employee import Employee, Attendance, Leave, SalaryRecord
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    LeaveCreate, LeaveUpdate, LeaveResponse,
    SalaryRecordCreate, SalaryRecordUpdate, SalaryRecordResponse,
)
from app.core.security import get_current_active_user, require_manager_or_admin, require_any_role

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def generate_employee_id():
    return "EMP" + "".join(random.choices(string.digits, k=5))


# Employees
@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    query = db.query(Employee)
    if search:
        query = query.filter(
            (Employee.first_name.ilike(f"%{search}%")) |
            (Employee.last_name.ilike(f"%{search}%")) |
            (Employee.email.ilike(f"%{search}%")) |
            (Employee.employee_id.ilike(f"%{search}%"))
        )
    if department:
        query = query.filter(Employee.department == department)
    if status:
        query = query.filter(Employee.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    existing = db.query(Employee).filter(Employee.email == employee_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")

    emp_id = generate_employee_id()
    while db.query(Employee).filter(Employee.employee_id == emp_id).first():
        emp_id = generate_employee_id()

    employee = Employee(**employee_in.model_dump(), employee_id=emp_id)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    for field, value in employee_update.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted"}


# Attendance
@router.get("/{employee_id}/attendance", response_model=List[AttendanceResponse])
async def get_employee_attendance(
    employee_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    if month and year:
        query = query.filter(
            func.extract("month", Attendance.date) == month,
            func.extract("year", Attendance.date) == year,
        )
    return query.order_by(Attendance.date.desc()).all()


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_in: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    existing = db.query(Attendance).filter(
        Attendance.employee_id == attendance_in.employee_id,
        Attendance.date == attendance_in.date,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already recorded for this date")

    work_hours = 0.0
    if attendance_in.check_in and attendance_in.check_out:
        delta = attendance_in.check_out - attendance_in.check_in
        work_hours = round(delta.total_seconds() / 3600, 2)

    attendance = Attendance(**attendance_in.model_dump(), work_hours=work_hours)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    attendance_update: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    for field, value in attendance_update.model_dump(exclude_unset=True).items():
        setattr(attendance, field, value)
    if attendance.check_in and attendance.check_out:
        delta = attendance.check_out - attendance.check_in
        attendance.work_hours = round(delta.total_seconds() / 3600, 2)
    db.commit()
    db.refresh(attendance)
    return attendance


# Leaves
@router.get("/leaves/all", response_model=List[LeaveResponse])
async def list_all_leaves(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    query = db.query(Leave)
    if status:
        query = query.filter(Leave.status == status)
    return query.order_by(Leave.created_at.desc()).all()


@router.get("/{employee_id}/leaves", response_model=List[LeaveResponse])
async def get_employee_leaves(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    return db.query(Leave).filter(Leave.employee_id == employee_id).order_by(Leave.created_at.desc()).all()


@router.post("/leaves", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_leave(
    leave_in: LeaveCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    leave = Leave(**leave_in.model_dump())
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.put("/leaves/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: int,
    leave_update: LeaveUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    from datetime import datetime
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    for field, value in leave_update.model_dump(exclude_unset=True).items():
        setattr(leave, field, value)
    if leave_update.status in ("approved", "rejected"):
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(leave)
    return leave


# Salary Records
@router.get("/{employee_id}/salary", response_model=List[SalaryRecordResponse])
async def get_employee_salary(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    return db.query(SalaryRecord).filter(SalaryRecord.employee_id == employee_id).order_by(
        SalaryRecord.year.desc(), SalaryRecord.month.desc()
    ).all()


@router.post("/salary", response_model=SalaryRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_record(
    salary_in: SalaryRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    existing = db.query(SalaryRecord).filter(
        SalaryRecord.employee_id == salary_in.employee_id,
        SalaryRecord.month == salary_in.month,
        SalaryRecord.year == salary_in.year,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Salary record already exists for this month/year")

    net_salary = (
        salary_in.basic_salary + salary_in.hra + salary_in.allowances
        - salary_in.deductions - salary_in.tax
    )
    salary = SalaryRecord(**salary_in.model_dump(), net_salary=net_salary)
    db.add(salary)
    db.commit()
    db.refresh(salary)
    return salary


@router.put("/salary/{salary_id}", response_model=SalaryRecordResponse)
async def update_salary_record(
    salary_id: int,
    salary_update: SalaryRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    salary = db.query(SalaryRecord).filter(SalaryRecord.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary record not found")
    for field, value in salary_update.model_dump(exclude_unset=True).items():
        setattr(salary, field, value)
    salary.net_salary = salary.basic_salary + salary.hra + salary.allowances - salary.deductions - salary.tax
    db.commit()
    db.refresh(salary)
    return salary


@router.get("/departments/list")
async def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role),
):
    departments = db.query(Employee.department).filter(
        Employee.department.isnot(None)
    ).distinct().all()
    return [d[0] for d in departments if d[0]]
