from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan_number: Optional[str] = None
    base_salary: float = 0.0
    status: str = "active"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    user_id: Optional[int] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan_number: Optional[str] = None
    base_salary: Optional[float] = None
    status: Optional[str] = None
    photo_url: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: int
    employee_id: str
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    status: str = "present"
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None


class AttendanceUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[str] = None
    work_hours: Optional[float] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: int
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_hours: float
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveBase(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: float
    reason: Optional[str] = None


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None


class LeaveResponse(LeaveBase):
    id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SalaryRecordBase(BaseModel):
    employee_id: int
    month: int
    year: int
    basic_salary: float = 0.0
    hra: float = 0.0
    allowances: float = 0.0
    deductions: float = 0.0
    tax: float = 0.0
    notes: Optional[str] = None


class SalaryRecordCreate(SalaryRecordBase):
    payment_date: Optional[date] = None
    payment_status: str = "pending"


class SalaryRecordUpdate(BaseModel):
    basic_salary: Optional[float] = None
    hra: Optional[float] = None
    allowances: Optional[float] = None
    deductions: Optional[float] = None
    tax: Optional[float] = None
    payment_date: Optional[date] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class SalaryRecordResponse(SalaryRecordBase):
    id: int
    net_salary: float
    payment_date: Optional[date] = None
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True
