from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

# SQLAlchemy engine and session
# Set DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME in your .env file and never commit it
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('patient', 'doctor', name='user_roles'), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    # Relationships
    patient_profile = relationship('PatientProfile', back_populates='user', uselist=False)
    doctor_profile = relationship('DoctorProfile', back_populates='user', uselist=False)

class PatientProfile(Base):
    __tablename__ = 'patient_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    full_name = Column(String(255))
    date_of_birth = Column(Date)
    address = Column(String(255))
    phone = Column(String(50))
    user = relationship('User', back_populates='patient_profile')
    medical_records = relationship('MedicalRecord', back_populates='patient')
    appointments = relationship('Appointment', back_populates='patient')

class DoctorProfile(Base):
    __tablename__ = 'doctor_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    full_name = Column(String(255))
    specialty = Column(String(255))
    phone = Column(String(50))
    user = relationship('User', back_populates='doctor_profile')
    appointments = relationship('Appointment', back_populates='doctor')

class MedicalRecord(Base):
    __tablename__ = 'medical_records'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient_profiles.id'))
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'))
    diagnosis = Column(Text)
    treatment = Column(Text)
    date = Column(DateTime)
    patient = relationship('PatientProfile', back_populates='medical_records')
    doctor = relationship('DoctorProfile')

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient_profiles.id'))
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'))
    appointment_time = Column(DateTime)
    reason = Column(Text)
    status = Column(Enum('pending', 'confirmed', 'completed', 'cancelled', name='appointment_status'))
    patient = relationship('PatientProfile', back_populates='appointments')
    doctor = relationship('DoctorProfile', back_populates='appointments')

class LabResult(Base):
    __tablename__ = 'lab_results'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient_profiles.id'))
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'))
    test_name = Column(String(255))
    result = Column(Text)
    date = Column(DateTime)
    patient = relationship('PatientProfile')
    doctor = relationship('DoctorProfile')

class Prescription(Base):
    __tablename__ = 'prescriptions'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient_profiles.id'))
    doctor_id = Column(Integer, ForeignKey('doctor_profiles.id'))
    medical_record_id = Column(Integer, ForeignKey('medical_records.id'))
    medication = Column(String(255))
    dosage = Column(String(255))
    instructions = Column(Text)
    date = Column(DateTime)
    patient = relationship('PatientProfile')
    doctor = relationship('DoctorProfile')
    medical_record = relationship('MedicalRecord')

# To create tables, run: Base.metadata.create_all(engine)
