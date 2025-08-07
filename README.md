# Provider_lookup

Provider Lookup API
A Django-based healthcare provider search system using official NPPES data from CMS. Find healthcare providers by name, location, specialty, and more.

🎯 Features
Provider Search: Search by name, location, specialty
Advanced Filtering: Multi-criteria search with specialty grouping
RESTful API: JSON responses with pagination
Official Data: Built on CMS NPPES provider registry

🚀 Quick Start
Prerequisites:
Python 3.8+, PostgreSQL 12+, Django 5.2+

Setup
bash# Clone and setup
git clone https://github.com/yourusername/provider_lookup.git
cd provider_lookup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment file (.env)
SECRET_KEY=your_django_secret_key_here
DB_PASSWORD=your_postgresql_password

# Database
createdb "Provider LookUp"
python manage.py migrate

# Run server
python manage.py runserver
Visit the Application

API Info: http://localhost:8000/
Search Providers: http://localhost:8000/api/search/
Quick Search: http://localhost:8000/api/quick-search/?q=smith
Health Check: http://localhost:8000/api/health/

📊 Database Schema
Providers Table - Core provider data (NPI, names, addresses, taxonomy)
NUCC Taxonomy Table - Healthcare specialty classifications


Mermaid Webflow: https://www.mermaidchart.com/app/projects/73ed8f3f-f909-4cf7-abb1-0e572c6260ae/diagrams/951d91b4-f45b-44c5-8049-7ca352f08435/version/v0.1/edit

📄 Data Sources
Uses official data from:

NPPES: National provider registry
NUCC: Healthcare taxonomy codes
CMS: Centers for Medicare and Medicaid Services

