# Salon Booking System

## Overview
This is a Django-based salon booking system imported from GitHub. The application provides functionality for salon management, appointments, user accounts, and subscriptions. The system supports Portuguese localization and uses SQLite database for development.

## Recent Changes
- **2025-09-22**: Initial import and setup for Replit environment
  - Restructured Django project directory (created salon_booking/ package)
  - Installed Python 3.11, Django 5.2.6, and Pillow
  - Configured Django server to run on 0.0.0.0:5000 for Replit compatibility
  - Set up deployment configuration for autoscale deployment
  - Created requirements.txt with project dependencies
- **2025-09-22**: Modified registration system for salon owners only
  - Removed username field - users now login with email and password
  - Removed client registration option - only salon owners can register
  - Added salon name and address fields to registration form
  - Registration automatically creates salon and assigns trial subscription
  - Implemented email uniqueness validation and transactional integrity
  - Updated registration template with new merchant-focused design
- **2025-09-22**: Fresh import setup completed for Replit environment
  - Fixed Pillow compatibility issues by temporarily using URLField for profile pictures
  - Successfully ran database migrations and Django system checks
  - Configured and started Django development server on 0.0.0.0:5000
  - Set up workflow "Django Server" for continuous development
  - Verified application is running and responding correctly
  - Configured deployment for autoscale production deployment
- **2025-09-22**: Project successfully imported and running in Replit
  - Installed Python 3.11 and all required Django dependencies (Django 5.2.6, Pillow 11.3.0)
  - Resolved Pillow ImageField compatibility issues
  - Django system checks pass with no issues
  - Database migrations are up to date
  - Django server running successfully on port 5000 with webview output
  - Landing page loads correctly showing salon booking interface
  - Deployment configuration set for autoscale production deployment
  - All Replit-specific configurations verified and working (ALLOWED_HOSTS, CSRF settings)
  - Fresh GitHub import setup completed successfully

## Project Architecture

### Django Apps
- **accounts**: User authentication, profiles, and registration
- **appointments**: Appointment management and scheduling
- **core**: Core functionality including landing page
- **salons**: Salon information and management
- **subscriptions**: User subscription and plan management

### Key Configuration
- **Language**: Portuguese (pt-br)
- **Timezone**: America/Sao_Paulo
- **Database**: SQLite (development)
- **Static Files**: Configured for production deployment
- **Media Files**: Configured for file uploads with Pillow support

### Directory Structure
```
/
├── salon_booking/          # Django project package
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI config
│   └── asgi.py           # ASGI config
├── accounts/              # User management app
├── appointments/          # Appointment management
├── core/                 # Core functionality
├── salons/               # Salon management
├── subscriptions/        # Subscription management
├── templates/            # HTML templates
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

### Development Workflow
- **Name**: Django Server
- **Command**: `python manage.py runserver 0.0.0.0:5000`
- **Port**: 5000 (configured for Replit preview)

### Deployment Configuration
- **Target**: Autoscale (stateless web application)
- **Command**: `python manage.py runserver 0.0.0.0:5000`
- **Note**: Uses development server (suitable for demo/testing)

## Dependencies
- Django 5.2.6
- Pillow (for ImageField support)
- asgiref
- sqlparse

## Notes
- The application is configured with `ALLOWED_HOSTS = ['*']` for Replit compatibility
- Database migrations are up to date
- All Django system checks pass successfully
- The landing page redirects authenticated users to a dashboard