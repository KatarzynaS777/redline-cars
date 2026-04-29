# RedLine Cars

RedLine Cars is a Django web application for browsing, filtering and comparing cars. The project is still in progress and was created to practice building full web applications with user accounts, dynamic views and Render deployment configuration.

## Status

In progress.

## Live Demo

https://redline-cars.onrender.com

Note: The project is hosted on Render Free, so the first load after inactivity may take around one minute.

## Main Features

- Landing page for the application
- Car catalog with filtering and model browsing
- User registration and login
- User profile page
- Favorite cars list
- Car comparison view
- Form for adding cars
- Responsive templates and custom styling
- Render deployment configuration

## Technologies

- Python
- Django
- HTML
- CSS
- SQLite for local development
- PostgreSQL-ready configuration
- WhiteNoise
- Gunicorn

## Deployment

The project includes Render deployment files:

- `render.yaml` defines the web service named `redline-cars` and a PostgreSQL database.
- `build.sh` runs migrations and collects static files during deployment.
- Environment variables are used for production settings such as `DJANGO_SECRET_KEY`, `DEBUG`, `DATABASE_URL` and email configuration.

## Project Structure

```text
car_project/   Django project settings and URL configuration
cars/          Main application with models, views, forms, templates and static files
manage.py      Django management script
render.yaml    Render deployment configuration for the redline-cars service
build.sh       Build script for deployment
```

## Local Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run database migrations:

```powershell
python manage.py migrate
```

Start the local server:

```powershell
python manage.py runserver
```

Open the application:

```text
http://127.0.0.1:8000/
```

## Notes

For local development, default settings are provided so the project can run without external services. Production configuration is handled through Render environment variables.
