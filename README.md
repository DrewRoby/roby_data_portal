# Roby Data Services Portal

A Django-based web portal that serves as a gateway to various data service applications.

## Features

- Modern, responsive design
- User authentication system with email verification
- Dashboard for accessing different data applications
- Schema Navigator for analyzing data file structures
- PostgreSQL database integration
- Clean, colorful UI based on the Roby Data Services branding

## Integrated Applications

- **Schema Navigator**: Analyze and track schemas from CSV, Excel, and JSON files
- **Data Analytics**: (Coming soon)
- **Data Visualization**: (Coming soon)
- **ETL Manager**: (Coming soon)
- **Data Warehouse**: (Coming soon)

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

5. Create a .env file in the project root with the following:
```
SECRET_KEY=your_secret_key_here
DB_NAME=roby_db
DB_USER=roby_user
DB_PASSWORD=roby_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your_smtp_server
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
```

6. Apply migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Collect static files:
```bash
python manage.py collectstatic
```

9. Start the development server:
```bash
python manage.py runserver
```

10. Navigate to http://127.0.0.1:8000/ in your web browser to see the portal.

## Project Structure

```
roby_data_portal/
├── manage.py
├── roby_data_portal/       # Project settings
├── portal/                # Main app for user management and portal functions
├── tracker/               # Schema navigator app
├── api/                   # API endpoints
├── auth_detector/         # Authentication helpers
├── todo/                  # Task management app
├── templates/             # HTML templates
│   ├── base.html          # Main base template
│   ├── components/        # Reusable components
│   ├── portal/            # Portal app templates
│   └── tracker/           # Tracker app templates
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
└── media/                 # User uploaded files
```

## Adding New Applications

To add a new application to the portal:

1. Create a new Django app:
```bash
python manage.py startapp your_app_name
```

2. Add the app to INSTALLED_APPS in settings.py
3. Create templates in templates/your_app_name/
4. Add URL patterns in your_app_name/urls.py
5. Include your app's URLs in the main urls.py
6. Add an entry for your app in the dashboard template

## Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Update the `ALLOWED_HOSTS` setting
3. Use a production-ready web server like Nginx or Apache
4. Use Gunicorn or uWSGI as the WSGI server

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com)