# IT Company Task Manager

Django portfolio project for managing workers, teams, projects, and tasks inside an IT company workflow.

## Live Demo

- App: `https://it-company-task-manager-se9a.onrender.com/`

Production uses PostgreSQL and is deployed on Render.

## Overview

The project simulates an internal task management system where users can manage:

- workers and positions
- teams and team members
- projects linked to teams
- tasks with priorities, deadlines, assignees, task types, and tags

## Features

- Custom user model: `Worker`
- Team, project, and task management
- Task assignment limited to team members
- Search and pagination across list views
- User-specific pages such as **My Teams** and **My Projects**
- Multi-step creation flow for projects and tasks
- Custom 403 and 404 pages
- Query optimization with `select_related`, `prefetch_related`, and `annotate`

## Tech Stack

- Python
- Django
- SQLite for local development
- PostgreSQL for production
- Bootstrap 4
- Django Crispy Forms
- Gunicorn
- WhiteNoise
- Render
- Neon PostgreSQL

## Database Schema

![Database schema](docs/db-schema.png)

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
![Task List](docs/screenshots/task-list.png)
![Task Detail](docs/screenshots/task-detail.png)

## Local Setup

```bash
git clone https://github.com/idubina/it-company-task-manager.git
cd it-company-task-manager
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
python manage.py migrate
python manage.py loaddata it_company_task_manager_db_data.json  # optional
python manage.py runserver
```

## Local Demo Access

Available after loading fixture data:

- Login: `admin.user`
- Password: `1qazcde3`

For local development and review only.

## Production Demo Access

Use a separate regular demo user for the deployed version:

- Login: `user`
- Password: `user12345`


## Environment Variables

### Local

Create `.env` from `.env.sample`:

```bash
cp .env.sample .env
```

Example:

```env
DJANGO_SECRET_KEY=replace-with-your-secret-key
DJANGO_SETTINGS_MODULE=it_company_task_manager.settings.dev
```

### Production

Set these variables in your hosting platform environment settings:

- `DJANGO_SECRET_KEY`
- `DJANGO_SETTINGS_MODULE=it_company_task_manager.settings.prod`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_DB_PORT`
- `RENDER_EXTERNAL_HOSTNAME`

## Deployment

### Build Script

`build.sh`:

- installs dependencies
- collects static files
- applies migrations

### Start Command

```bash
gunicorn it_company_task_manager.wsgi:application --workers 1 --threads 10
```

## Tests

```bash
python manage.py test
```

## Author

Illia Dubina  
GitHub: [idubina](https://github.com/idubina)