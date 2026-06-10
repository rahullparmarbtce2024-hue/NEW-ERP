from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class EmploymentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"
    on_leave = "on_leave"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class LeaveType(str, enum.Enum):
    annual = "annual"
    sick = "sick"
    maternity = "maternity"
    paternity = "paternity"
    unpaid = "unpaid"
    other = "other"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    late = "late"
    work_from_home = "work_from_home"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_id = Column(String(20), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    department = Column(String(100))
    designation = Column(String(100))
    date_of_joining = Column(Date)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pincode = Column(String(10))
    bank_account = Column(String(30))
    bank_name = Column(String(100))
    ifsc_code = Column(String(20))
    pan_number = Column(String(20))
    base_salary = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    photo_url = Column(String(500))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="employee")
    attendances = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")
    salary_records = relationship("SalaryRecord", back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    status = Column(String(20), default="present")
    work_hours = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="attendances")


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates="leaves")


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    payment_date = Column(Date)
    payment_status = Column(String(20), default="pending")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates="salary_records")
