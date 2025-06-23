# Templates for this app should be placed in a 'templates' directory at the project root.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from .forms import RegistrationForm, LoginForm, PatientProfileForm, MedicalRecordForm, LabResultForm, PrescriptionForm, ChangePasswordForm
from .models import SessionLocal, User, Base, PatientProfile, LabResult, Prescription, MedicalRecord, Appointment, DoctorProfile
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from django.http import HttpResponse
from django import forms
from sqlalchemy.orm import joinedload
import time
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

# Always deploy with HTTPS in production!
# Never log sensitive data (passwords, tokens, medical info, etc.)

# Ensure tables exist
Base.metadata.create_all(bind=SessionLocal.kw["bind"])

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Content-Security-Policy'] = "default-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com;"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            db = SessionLocal()
            try:
                user = User(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password_hash=generate_password_hash(form.cleaned_data['password']),
                    role=form.cleaned_data['role'],
                )
                db.add(user)
                db.commit()
                # Create profile for user
                if user.role == 'doctor':
                    doctor_profile = DoctorProfile(user_id=user.id, full_name=user.username)
                    db.add(doctor_profile)
                elif user.role == 'patient':
                    patient_profile = PatientProfile(user_id=user.id, full_name=user.username)
                    db.add(patient_profile)
                db.commit()
                messages.success(request, 'Registration successful. Please log in.')
                return redirect('login')
            except IntegrityError:
                db.rollback()
                messages.error(request, 'Username or email already exists.')
            finally:
                db.close()
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        ip = request.META.get('REMOTE_ADDR')
        fail_key = f'login_fail_{ip}'
        block_key = f'login_block_{ip}'
        if cache.get(block_key):
            messages.error(request, 'Too many failed login attempts. Please try again later.')
            return render(request, 'login.html', {'form': form})
        if form.is_valid():
            db = SessionLocal()
            user = db.query(User).filter_by(username=form.cleaned_data['username'], role=form.cleaned_data['role']).first()
            if user and check_password_hash(user.password_hash, form.cleaned_data['password']):
                cache.delete(fail_key)
                cache.delete(block_key)
                request.session.cycle_key()  # Prevent session fixation
                request.session['user_id'] = user.id
                request.session['role'] = user.role
                messages.success(request, f'Welcome, {user.username}!')
                return redirect('dashboard')
            else:
                fails = cache.get(fail_key, 0) + 1
                cache.set(fail_key, fails, 600)
                if fails >= 5:
                    cache.set(block_key, True, 600)
                    messages.error(request, 'Too many failed login attempts. Please try again in 10 minutes.')
                else:
                    messages.error(request, 'Invalid username, password, or role.')
            db.close()
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def dashboard(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id:
        return redirect('login')
    return render(request, 'dashboard.html', {'role': role})

def patient_profile(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    if not profile or profile.user_id != user_id:
        db.close()
        return HttpResponse('Unauthorized', status=403)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            if not profile:
                profile = PatientProfile(user_id=user_id)
                db.add(profile)
            profile.full_name = form.cleaned_data['full_name']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.address = form.cleaned_data['address']
            profile.phone = form.cleaned_data['phone']
            db.commit()
            messages.success(request, 'Profile updated successfully.')
            db.close()
            return redirect('patient_profile')
    else:
        initial = {}
        if profile:
            initial = {
                'full_name': profile.full_name,
                'date_of_birth': profile.date_of_birth,
                'address': profile.address,
                'phone': profile.phone,
            }
        form = PatientProfileForm(initial=initial)
    db.close()
    return render(request, 'patient_profile.html', {'form': form})

def patient_profile_view(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(id=patient_id).first()
    db.close()
    if not profile:
        return HttpResponse('Patient profile not found.', status=404)
    return render(request, 'patient_profile_view.html', {'profile': profile})

def patient_lab_results(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    results = (
        db.query(LabResult)
        .options(joinedload(LabResult.doctor))
        .filter_by(patient_id=profile.id)
        .all()
    ) if profile else []
    db.close()
    return render(request, 'patient_lab_results.html', {'results': results})

def patient_prescriptions(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    prescriptions = (
        db.query(Prescription)
        .options(joinedload(Prescription.doctor))
        .filter_by(patient_id=profile.id)
        .all()
    ) if profile else []
    db.close()
    return render(request, 'patient_prescriptions.html', {'prescriptions': prescriptions})

def patient_medical_history(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    records = (
        db.query(MedicalRecord)
        .options(joinedload(MedicalRecord.doctor))
        .filter_by(patient_id=profile.id)
        .all()
    ) if profile else []
    db.close()
    return render(request, 'patient_medical_history.html', {'records': records})

def patient_appointments(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    appointments = (
        db.query(Appointment)
        .options(joinedload(Appointment.doctor))
        .filter_by(patient_id=profile.id)
        .all()
    ) if profile else []
    db.close()
    return render(request, 'patient_appointments.html', {'appointments': appointments})

class AppointmentForm(forms.Form):
    doctor_id = forms.ChoiceField(label='Doctor', choices=[], required=True)
    appointment_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=True)
    reason = forms.CharField(widget=forms.Textarea, required=True)

def book_appointment(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'patient':
        return redirect('login')
    db = SessionLocal()
    profile = db.query(PatientProfile).filter_by(user_id=user_id).first()
    doctors = db.query(DoctorProfile).all()
    doctor_choices = [(str(d.id), d.full_name or f"Doctor {d.id}") for d in doctors]
    debug_message = None
    if not doctor_choices:
        debug_message = "No doctors are available. Please ask an admin to register a doctor."
    if request.method == 'POST':
        # Set choices before instantiating with POST data
        form = AppointmentForm()
        form.fields['doctor_id'].choices = doctor_choices
        form = AppointmentForm(request.POST)
        form.fields['doctor_id'].choices = doctor_choices
        if form.is_valid():
            appointment = Appointment(
                patient_id=profile.id,
                doctor_id=int(form.cleaned_data['doctor_id']),
                appointment_time=form.cleaned_data['appointment_time'],
                reason=form.cleaned_data['reason'],
                status='pending',
            )
            db.add(appointment)
            db.commit()
            messages.success(request, 'Appointment booked successfully.')
            db.close()
            return redirect('dashboard')
    else:
        form = AppointmentForm()
        form.fields['doctor_id'].choices = doctor_choices
    db.close()
    return render(request, 'book_appointment.html', {'form': form, 'debug_message': debug_message})

def create_missing_doctor_profiles():
    db = SessionLocal()
    doctor_users = db.query(User).filter_by(role='doctor').all()
    for user in doctor_users:
        if not db.query(DoctorProfile).filter_by(user_id=user.id).first():
            doctor_profile = DoctorProfile(user_id=user.id, full_name=user.username)
            db.add(doctor_profile)
    db.commit()
    db.close()

def doctor_appointments(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    doctor_profile = db.query(DoctorProfile).filter_by(user_id=user_id).first()
    appointments = (
        db.query(Appointment)
        .options(joinedload(Appointment.patient))
        .filter_by(doctor_id=doctor_profile.id)
        .all()
    ) if doctor_profile else []
    # Handle status update actions
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        appointment = db.query(Appointment).filter_by(id=appointment_id, doctor_id=doctor_profile.id).first()
        if appointment and action in ['confirmed', 'completed', 'cancelled']:
            appointment.status = action
            db.commit()
            messages.success(request, f'Appointment marked as {action}.')
        return redirect('doctor_appointments')
    db.close()
    return render(request, 'doctor_appointments.html', {'appointments': appointments})

def doctor_patients(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    query = request.GET.get('q', '').strip()
    patients_query = db.query(PatientProfile)
    if query:
        patients_query = patients_query.filter(PatientProfile.full_name.ilike(f'%{query}%'))
    patients = patients_query.all()
    db.close()
    return render(request, 'doctor_patients.html', {'patients': patients, 'query': query})

def add_medical_record(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    doctor = db.query(DoctorProfile).filter_by(user_id=user_id).first()
    if not patient or not doctor:
        db.close()
        return HttpResponse('Patient or doctor not found.', status=404)
    patient_name = patient.full_name
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                diagnosis=form.cleaned_data['diagnosis'],
                treatment=form.cleaned_data['treatment'],
                date=form.cleaned_data['date'],
            )
            db.add(record)
            db.commit()
            patient_id_val = patient.id
            db.close()
            messages.success(request, 'Medical record added.')
            return redirect('patient_profile_view', patient_id=patient_id_val)
    else:
        form = MedicalRecordForm()
    db.close()
    return render(request, 'add_medical_record.html', {'form': form, 'patient': {'id': patient_id, 'full_name': patient_name}})

def add_lab_result(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    doctor = db.query(DoctorProfile).filter_by(user_id=user_id).first()
    if not patient or not doctor:
        db.close()
        return HttpResponse('Patient or doctor not found.', status=404)
    patient_name = patient.full_name
    if request.method == 'POST':
        form = LabResultForm(request.POST)
        if form.is_valid():
            result = LabResult(
                patient_id=patient.id,
                doctor_id=doctor.id,
                test_name=form.cleaned_data['test_name'],
                result=form.cleaned_data['result'],
                date=form.cleaned_data['date'],
            )
            db.add(result)
            db.commit()
            patient_id_val = patient.id
            db.close()
            messages.success(request, 'Lab result added.')
            return redirect('patient_profile_view', patient_id=patient_id_val)
    else:
        form = LabResultForm()
    db.close()
    return render(request, 'add_lab_result.html', {'form': form, 'patient': {'id': patient_id, 'full_name': patient_name}})

def add_prescription(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    doctor = db.query(DoctorProfile).filter_by(user_id=user_id).first()
    if not patient or not doctor:
        db.close()
        return HttpResponse('Patient or doctor not found.', status=404)
    patient_name = patient.full_name
    doctor_name = doctor.full_name
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=doctor.id,
                medical_record_id=None,  # Could be linked to a record if needed
                medication=form.cleaned_data['medication'],
                dosage=form.cleaned_data['dosage'],
                instructions=form.cleaned_data['instructions'],
                date=form.cleaned_data['date'],
            )
            db.add(prescription)
            db.commit()
            patient_id_val = patient.id
            db.close()
            messages.success(request, 'Prescription added.')
            return redirect('patient_profile_view', patient_id=patient_id_val)
    else:
        form = PrescriptionForm()
    db.close()
    return render(request, 'add_prescription.html', {'form': form, 'patient': {'id': patient_id, 'full_name': patient_name}, 'doctor_name': doctor_name})

def doctor_patient_medical_history(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    records = (
        db.query(MedicalRecord)
        .options(joinedload(MedicalRecord.doctor))
        .filter_by(patient_id=patient_id)
        .all()
    ) if patient else []
    db.close()
    return render(request, 'doctor_patient_medical_history.html', {'patient': patient, 'records': records})

def doctor_patient_lab_results(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    results = (
        db.query(LabResult)
        .options(joinedload(LabResult.doctor))
        .filter_by(patient_id=patient_id)
        .all()
    ) if patient else []
    db.close()
    return render(request, 'doctor_patient_lab_results.html', {'patient': patient, 'results': results})

def doctor_patient_prescriptions(request, patient_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    patient = db.query(PatientProfile).filter_by(id=patient_id).first()
    prescriptions = (
        db.query(Prescription)
        .options(joinedload(Prescription.doctor))
        .filter_by(patient_id=patient_id)
        .all()
    ) if patient else []
    db.close()
    return render(request, 'doctor_patient_prescriptions.html', {'patient': patient, 'prescriptions': prescriptions})

def home(request):
    return render(request, 'home.html')

def edit_medical_record(request, record_id):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id or role != 'doctor':
        return redirect('login')
    db = SessionLocal()
    record = db.query(MedicalRecord).filter_by(id=record_id).first()
    if not record:
        db.close()
        return HttpResponse('Medical record not found.', status=404)
    patient_id_val = record.patient_id
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record.diagnosis = form.cleaned_data['diagnosis']
            record.treatment = form.cleaned_data['treatment']
            record.date = form.cleaned_data['date']
            db.commit()
            db.close()
            messages.success(request, 'Medical record updated.')
            return redirect('doctor_patient_medical_history', patient_id=patient_id_val)
    else:
        form = MedicalRecordForm(initial={
            'diagnosis': record.diagnosis,
            'treatment': record.treatment,
            'date': record.date,
        })
    db.close()
    return render(request, 'edit_medical_record.html', {'form': form, 'record': record, 'patient_id': patient_id_val})

def change_password(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if not user_id:
        return redirect('login')
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        db.close()
        messages.error(request, 'User not found.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, username=user.username, email=user.email)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            if not check_password_hash(user.password_hash, old_password):
                form.add_error('old_password', 'Old password is incorrect.')
            else:
                user.password_hash = generate_password_hash(form.cleaned_data['new_password'])
                db.commit()
                db.close()
                messages.success(request, 'Password changed successfully.')
                return redirect('dashboard')
    else:
        form = ChangePasswordForm(username=user.username, email=user.email)
    db.close()
    return render(request, 'change_password.html', {'form': form, 'role': role})

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)
