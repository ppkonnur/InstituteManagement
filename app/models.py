from decimal import Decimal
from datetime import date

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Trainer(db.Model):
    __tablename__ = "trainers"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    courses = db.relationship("Course", back_populates="trainer", passive_deletes=True)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainers.id", ondelete="SET NULL"), nullable=True)

    trainer = db.relationship("Trainer", back_populates="courses")
    enquiries = db.relationship("Enquiry", back_populates="course", passive_deletes=True)


class Enquiry(db.Model):
    __tablename__ = "enquiries"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    enquiry_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    followup_calls = db.Column(db.Boolean, nullable=False, default=False)
    enrolled = db.Column(db.Boolean, nullable=False, default=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)

    course = db.relationship("Course", back_populates="enquiries")
