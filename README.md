# IT Company Task Manager

Django portfolio project for managing development workflow in an IT company.  
The app supports workers, positions, teams, projects, tasks, assignees, priorities, and tags.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [Setup and Run](#setup-and-run)
- [Load Fixture Data](#load-fixture-data)
- [Admin Access](#admin-access)
- [Author](#author)


---

## About

This project is a task manager for IT teams.  
It allows teams to organize work by projects, assign tasks to workers, track deadlines and completion status, and classify tasks with tags and task types.

---

## Features

- Custom user model: `Worker` (based on `AbstractUser`)
- Worker positions (`Position`)
- Teams with members (`Team`)
- Projects linked to teams (`Project`)
- Tasks with:
  - name and description
  - deadline (`DateTime`)
  - completion status
  - priority (`Urgent`, `High`, `Medium`, `Low`)
  - task type (`TaskType`)
  - assignees (Many-to-Many with workers)
  - tags (Many-to-Many with `Tag`)
- Django Admin support for managing all entities

---

## Tech Stack

- Python
- Django
- SQLite (default database)
- Django Admin

---

## Database Schema

> ER diagram

### Current model relationships (short)

- `Position` **1 : N** `Worker`
- `TaskType` **1 : N** `Task`
- `Team` **1 : N** `Project`
- `Project` **1 : N** `Task`
- `Worker` **M : N** `Task` (assignees)
- `Worker` **M : N** `Team` (members)
- `Task` **M : N** `Tag`

---

## Setup and Run

### 1) Clone repository

```bash
git clone https://github.com/idubina/it-company-task-manager.git
cd it_company_task_manager
```

### 2) Create virtual environment

```bash
python -m venv venv
```

### 3) Activate virtual environment

**macOS / Linux**

```bash
source venv/bin/activate
```
**Windows (PowerShell)**

```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD)**

```bat
venv\Scripts\activate.bat
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

### 5) Apply migrations

```bash
python manage.py migrate
```

### 6) Run development server

```bash
python manage.py runserver
```

By default, Django runs at:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

---

## Load Fixture Data

To load prepared test data:

```bash
python manage.py loaddata it_company_task_manager_db_data.json
```

---

## Admin Access

After loading data from fixture you can use following superuser:
  - Login: `admin.user`
  - Password: `1qazcde3`

or create another one by yourself:

```bash
python manage.py createsuperuser
```
Feel free to add more data using admin panel, if needed.

---

## Author

**Illia Dubina**

GitHub: https://github.com/idubina