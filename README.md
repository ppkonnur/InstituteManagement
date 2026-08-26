# Institute Management Web App (Flask + PostgreSQL)

This project provides an admin web application for:

- Course list with fees and assigned trainer
- Trainer list with first name, last name, mobile, email
- Student enquiry list with first name, last name, mobile, email, selected course
- Enrolled status toggle icon for each enquiry
- Admin login and full Add/Edit/Delete management

## Tech Stack

- Python + Flask
- PostgreSQL
- SQLAlchemy ORM
- Bootstrap for UI

## Setup

Note:
- If `DATABASE_URL` is not set, the app uses a local SQLite DB (`institute.db`) so you can run immediately.
- To use PostgreSQL, set `DATABASE_URL` in `.env`.

1. Create a virtual environment:

```bat
py -m venv .venv
```

2. Activate the virtual environment:

For Command Prompt (CMD):

```bat
.venv\Scripts\activate
```

For PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment file:

```bash
copy .env.example .env
```

5. Update `DATABASE_URL` in `.env` with your PostgreSQL credentials.
	Use format: `postgresql+psycopg://username:password@127.0.0.1:5432/database_name?connect_timeout=3`
6. Initialize database tables and default admin user:

```bash
flask --app run.py init-db
```

7. Run the app:

```bash
python run.py
```

Open `http://127.0.0.1:5000` in your browser.

## Default Admin Login

Use the values from `.env`:

- Username: `ADMIN_USERNAME`
- Password: `ADMIN_PASSWORD`

Default sample values are `admin` and `admin123`.
