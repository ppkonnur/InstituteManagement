import os

from dotenv import load_dotenv
from flask import Flask
from flask.cli import with_appcontext
import click
from sqlalchemy import inspect, text

from app.extensions import db
from app.models import AdminUser
from app.routes import main_bp


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    default_db_url = "sqlite:///institute.db"
    database_url = os.getenv("DATABASE_URL", default_db_url)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    engine_options = {"pool_pre_ping": True}
    if database_url.startswith("postgresql"):
        # Keep login and other queries responsive when DB is unreachable.
        engine_options["connect_args"] = {"connect_timeout": 3}
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    db.init_app(app)

    app.register_blueprint(main_bp)
    app.cli.add_command(init_db_command)

    return app


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    db.create_all()

    inspector = inspect(db.engine)
    enquiry_columns = {column["name"] for column in inspector.get_columns("enquiries")}
    alter_statements = []

    if "enquiry_date" not in enquiry_columns:
        alter_statements.append("ALTER TABLE enquiries ADD COLUMN enquiry_date DATE")
    if "gender" not in enquiry_columns:
        alter_statements.append("ALTER TABLE enquiries ADD COLUMN gender VARCHAR(10)")
    if "followup_calls" not in enquiry_columns:
        alter_statements.append("ALTER TABLE enquiries ADD COLUMN followup_calls BOOLEAN DEFAULT 0")

    for stmt in alter_statements:
        db.session.execute(text(stmt))

    if alter_statements:
        db.session.commit()

    default_username = os.getenv("ADMIN_USERNAME", "admin")
    default_password = os.getenv("ADMIN_PASSWORD", "admin123")

    existing_admin = AdminUser.query.filter_by(username=default_username).first()
    if not existing_admin:
        admin = AdminUser(username=default_username)
        admin.set_password(default_password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Initialized DB and created default admin: {default_username}")
    else:
        click.echo("Initialized DB. Default admin already exists.")
