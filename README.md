# Roby Data Services Portal

A Django-based web portal that serves as a gateway to various data service applications.

## Features

- Modern, responsive design
- User authentication system
- Dashboard for accessing different data applications
- PostgreSQL database integration
- Clean, colorful UI based on the Roby Data Services branding

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/roby-data-portal.git
cd roby-data-portal
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
   - Create a PostgreSQL database named `roby_db`
   - Create a user `roby_user` with password `roby_password`
   - Grant all privileges on the database to the user

```sql
CREATE DATABASE roby_db;
CREATE USER roby_user WITH PASSWORD 'roby_password';
ALTER ROLE roby_user SET client_encoding TO 'utf8';
ALTER ROLE roby_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE roby_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE roby_db TO roby_user;
```

5. Apply migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Collect static files:
```bash
python manage.py collectstatic
```

8. Start the development server:
```bash
python manage.py runserver
```

9. Navigate to http://127.0.0.1:8000/ in your web browser to see the portal.

## Project Structure

```
roby_data_portal/
├── manage.py
├── roby_data_portal/       # Project settings
├── portal/                # Main app
│   ├── templates/        # HTML templates
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # URL routing
│   └── forms.py          # Form definitions
└── static/                # Static files (CSS, JS, images)
    ├── css/
    ├── js/
    └── images/
```

## Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Update the `ALLOWED_HOSTS` setting
3. Use a production-ready web server like Nginx or Apache
4. Use Gunicorn or uWSGI as the WSGI server

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com).