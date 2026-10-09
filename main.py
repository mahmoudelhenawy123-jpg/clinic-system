from datetime import datetime
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# 1. إعدادات قاعدة البيانات
SQLALCHEMY_DATABASE_URL = "sqlite:///./clinic.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 2. النماذج (Database Models)
class PatientModel(Base):
  __tablename__ = "patients"
  id = Column(Integer, primary_key=True, index=True)
  full_name = Column(String(100), nullable=False)
  phone = Column(String(20), unique=True, index=True, nullable=False)
  age = Column(Integer, nullable=False)
  gender = Column(String(10), nullable=False)
  medical_history = Column(Text, nullable=True)
  created_at = Column(DateTime, default=datetime.utcnow)

  appointments = relationship(
      "AppointmentModel", back_populates="patient", cascade="all, delete"
  )


class AppointmentModel(Base):
  __tablename__ = "appointments"
  id = Column(Integer, primary_key=True, index=True)
  patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
  appointment_date = Column(DateTime, nullable=False)
  reason = Column(String(255), nullable=True)
  status = Column(String(50), default="Pending")  # Pending, Confirmed, Cancelled

  patient = relationship("PatientModel", back_populates="appointments")


Base.metadata.create_all(bind=engine)


# 3. نماذج التحقق (Pydantic Schemas)
class PatientCreate(BaseModel):
  full_name: str
  phone: str
  age: int
  gender: str
  medical_history: Optional[str] = None


class PatientResponse(PatientCreate):
  id: int
  created_at: datetime

  class Config:
    from_attributes = True


class AppointmentCreate(BaseModel):
  patient_id: int
  appointment_date: datetime
  reason: Optional[str] = None


class AppointmentResponse(AppointmentCreate):
  id: int
  status: str

  class Config:
    from_attributes = True


# دالة الاتصال
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


# 4. التطبيق والمسارات
app = FastAPI(title="Clinic Management System API")


@app.get("/")
def read_root():
  return {"message": "نظام إدارة العيادة جاهز ومتكامل 🚀"}


# إضافة مريض
@app.post("/patients/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
  existing = (
      db.query(PatientModel)
      .filter(PatientModel.phone == patient.phone)
      .first()
  )
  if existing:
    raise HTTPException(
        status_code=400, detail="رقم الهاتف مسجل مسبقاً لمريض آخر."
    )
  db_patient = PatientModel(**patient.dict())
  db.add(db_patient)
  db.commit()
  db.refresh(db_patient)
  return db_patient


# عرض المرضى
@app.get("/patients/", response_model=List[PatientResponse])
def get_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
  return db.query(PatientModel).offset(skip).limit(limit).all()


# حجز موعد لمريض
@app.post("/appointments/", response_model=AppointmentResponse)
def create_appointment(
    appointment: AppointmentCreate, db: Session = Depends(get_db)
):
  patient = (
      db.query(PatientModel)
      .filter(PatientModel.id == appointment.patient_id)
      .first()
  )
  if not patient:
    raise HTTPException(status_code=404, detail="المريض غير موجود.")

  db_app = AppointmentModel(**appointment.dict())
  db.add(db_app)
  db.commit()
  db.refresh(db_app)
  return db_app


# عرض المواعيد
@app.get("/appointments/", response_model=List[AppointmentResponse])
def get_appointments(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
  return db.query(AppointmentModel).offset(skip).limit(limit).all()
