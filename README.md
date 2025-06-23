# Patient Management System (PMC)

A secure web app for managing patients, medical records, and appointments. Built with Django, SQLAlchemy, and PostgreSQL.

## Features
- User roles: Patients & Doctors
- Secure authentication
- Patient profiles, medical records, appointments
- Role-based access
- Security best practices

## Requirements
- Python 3.8+
- PostgreSQL

## Setup

### 1. Clone the repository
```
git clone <repo-url>
cd CCMC PMC
```

### 2. Create and activate a virtual environment
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Set up PostgreSQL
- Create a database and user:
```
psql -U postgres
CREATE DATABASE pmcdb;
CREATE USER pmcuser WITH PASSWORD 'pmcpassword';
GRANT ALL PRIVILEGES ON DATABASE pmcdb TO pmcuser;
\q
```

### 5. Configure environment variables
Create a `.env` file in the project root:
```
DB_NAME=pmcdb
DB_USER=pmcuser
DB_PASSWORD=pmcpassword
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-django-secret-key
```

### 6. Run migrations and start the server
```
python manage.py migrate
python manage.py runserver
```

### 7. Access the app
Go to [http://localhost:8000](http://localhost:8000)

---

## Security Notes
- All sensitive data is encrypted at rest.
- Only HTTPS should be used in production.
- Input validation and output escaping are enforced.
- See the code and comments for more security details. 