from decimal import Decimal, InvalidOperation
from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import AdminUser, Course, Enquiry, Trainer


main_bp = Blueprint("main", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_user_id"):
            flash("Please login to continue.", "warning")
            return redirect(url_for("main.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@main_bp.route("/")
def home():
    if session.get("admin_user_id"):
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        errors = {}

        if not username:
            errors["username"] = "Username is mandatory."
        if not password:
            errors["password"] = "Password is mandatory."

        if errors:
            return render_template("auth/login.html", errors=errors, form_data={"username": username}), 400

        try:
            admin = AdminUser.query.filter_by(username=username).first()
        except SQLAlchemyError:
            flash("Database is not reachable. Please check PostgreSQL service and DATABASE_URL.", "danger")
            return render_template("auth/login.html"), 503

        if admin and admin.check_password(password):
            session["admin_user_id"] = admin.id
            flash("Welcome back!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@main_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    counts = {
        "courses": Course.query.count(),
        "trainers": Trainer.query.count(),
        "enquiries": Enquiry.query.count(),
        "enrolled": Enquiry.query.filter_by(enrolled=True).count(),
    }
    return render_template("dashboard.html", counts=counts)


@main_bp.route("/courses")
@login_required
def courses_list():
    courses = Course.query.order_by(Course.name.asc()).all()
    return render_template("courses/list.html", courses=courses)


@main_bp.route("/courses/add", methods=["GET", "POST"])
@login_required
def courses_add():
    trainers = Trainer.query.order_by(Trainer.first_name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        fee_raw = request.form.get("fee", "").strip()
        trainer_id_raw = request.form.get("trainer_id", "").strip()
        errors = {}
        form_data = {"name": name, "fee": fee_raw, "trainer_id": trainer_id_raw}

        if not name:
            errors["name"] = "Cource name is mandatory."

        fee = None
        if not fee_raw:
            errors["fee"] = "Course fee is mandatory."
        else:
            try:
                fee = Decimal(fee_raw)
            except InvalidOperation:
                errors["fee"] = "Course fee must be a valid number."

        if errors:
            return (
                render_template(
                    "courses/form.html",
                    mode="add",
                    trainers=trainers,
                    errors=errors,
                    form_data=form_data,
                ),
                400,
            )

        trainer_id = int(trainer_id_raw) if trainer_id_raw else None
        course = Course(name=name, fee=fee, trainer_id=trainer_id)
        db.session.add(course)
        db.session.commit()

        flash("Course added successfully.", "success")
        return redirect(url_for("main.courses_list"))

    return render_template("courses/form.html", mode="add", trainers=trainers)


@main_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def courses_edit(course_id: int):
    course = Course.query.get_or_404(course_id)
    trainers = Trainer.query.order_by(Trainer.first_name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        fee_raw = request.form.get("fee", "").strip()
        trainer_id_raw = request.form.get("trainer_id", "").strip()
        errors = {}
        form_data = {"name": name, "fee": fee_raw, "trainer_id": trainer_id_raw}

        if not name:
            errors["name"] = "Cource name is mandatory."

        fee = None
        if not fee_raw:
            errors["fee"] = "Course fee is mandatory."
        else:
            try:
                fee = Decimal(fee_raw)
            except InvalidOperation:
                errors["fee"] = "Course fee must be a valid number."

        if errors:
            return (
                render_template(
                    "courses/form.html",
                    mode="edit",
                    trainers=trainers,
                    course=course,
                    errors=errors,
                    form_data=form_data,
                ),
                400,
            )

        course.name = name
        course.fee = fee
        course.trainer_id = int(trainer_id_raw) if trainer_id_raw else None
        db.session.commit()

        flash("Course updated successfully.", "success")
        return redirect(url_for("main.courses_list"))

    return render_template("courses/form.html", mode="edit", trainers=trainers, course=course)


@main_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def courses_delete(course_id: int):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted successfully.", "info")
    return redirect(url_for("main.courses_list"))


@main_bp.route("/trainers")
@login_required
def trainers_list():
    trainers = Trainer.query.order_by(Trainer.first_name.asc(), Trainer.last_name.asc()).all()
    return render_template("trainers/list.html", trainers=trainers)


@main_bp.route("/trainers/add", methods=["GET", "POST"])
@login_required
def trainers_add():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        errors = {}
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
        }

        if not first_name:
            errors["first_name"] = "First name is mandatory."
        if not last_name:
            errors["last_name"] = "Last name is mandatory."
        if not mobile:
            errors["mobile"] = "Mobile number is mandatory."
        if not email:
            errors["email"] = "Email is mandatory."

        if email and Trainer.query.filter_by(email=email).first():
            errors["email"] = "A trainer with this email already exists."

        if errors:
            return render_template("trainers/form.html", mode="add", errors=errors, form_data=form_data), 400

        trainer = Trainer(first_name=first_name, last_name=last_name, mobile=mobile, email=email)
        db.session.add(trainer)
        db.session.commit()

        flash("Trainer added successfully.", "success")
        return redirect(url_for("main.trainers_list"))

    return render_template("trainers/form.html", mode="add")


@main_bp.route("/trainers/<int:trainer_id>/edit", methods=["GET", "POST"])
@login_required
def trainers_edit(trainer_id: int):
    trainer = Trainer.query.get_or_404(trainer_id)

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        errors = {}
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
        }

        if not first_name:
            errors["first_name"] = "First name is mandatory."
        if not last_name:
            errors["last_name"] = "Last name is mandatory."
        if not mobile:
            errors["mobile"] = "Mobile number is mandatory."
        if not email:
            errors["email"] = "Email is mandatory."

        existing = Trainer.query.filter(Trainer.email == email, Trainer.id != trainer.id).first() if email else None
        if existing:
            errors["email"] = "A trainer with this email already exists."

        if errors:
            return (
                render_template(
                    "trainers/form.html",
                    mode="edit",
                    trainer=trainer,
                    errors=errors,
                    form_data=form_data,
                ),
                400,
            )

        trainer.first_name = first_name
        trainer.last_name = last_name
        trainer.mobile = mobile
        trainer.email = email
        db.session.commit()

        flash("Trainer updated successfully.", "success")
        return redirect(url_for("main.trainers_list"))

    return render_template("trainers/form.html", mode="edit", trainer=trainer)


@main_bp.route("/trainers/<int:trainer_id>/delete", methods=["POST"])
@login_required
def trainers_delete(trainer_id: int):
    trainer = Trainer.query.get_or_404(trainer_id)
    db.session.delete(trainer)
    db.session.commit()
    flash("Trainer deleted successfully.", "info")
    return redirect(url_for("main.trainers_list"))


@main_bp.route("/enquiries")
@login_required
def enquiries_list():
    enquiries = Enquiry.query.order_by(Enquiry.id.desc()).all()
    return render_template("enquiries/list.html", enquiries=enquiries)


@main_bp.route("/enquiries/add", methods=["GET", "POST"])
@login_required
def enquiries_add():
    courses = Course.query.order_by(Course.name.asc()).all()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        enquiry_date_raw = request.form.get("enquiry_date", "").strip()
        gender = request.form.get("gender", "").strip().lower()
        followup_calls = request.form.get("followup_calls") == "on"
        course_id_raw = request.form.get("course_id", "").strip()
        errors = {}
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
            "enquiry_date": enquiry_date_raw,
            "gender": gender,
            "followup_calls": followup_calls,
            "course_id": course_id_raw,
        }

        if not first_name:
            errors["first_name"] = "First name is mandatory."
        if not last_name:
            errors["last_name"] = "Last name is mandatory."
        if not mobile:
            errors["mobile"] = "Mobile number is mandatory."
        if not email:
            errors["email"] = "Email is mandatory."
        if not enquiry_date_raw:
            errors["enquiry_date"] = "Enquiry date is mandatory."
        if gender not in {"male", "female"}:
            errors["gender"] = "Gender is mandatory."

        enquiry_date_value = None
        if enquiry_date_raw:
            try:
                enquiry_date_value = date.fromisoformat(enquiry_date_raw)
            except ValueError:
                errors["enquiry_date"] = "Enquiry date is invalid."

        if errors:
            return (
                render_template(
                    "enquiries/form.html",
                    mode="add",
                    courses=courses,
                    errors=errors,
                    form_data=form_data,
                ),
                400,
            )

        enquiry = Enquiry(
            first_name=first_name,
            last_name=last_name,
            mobile=mobile,
            email=email,
            enquiry_date=enquiry_date_value,
            gender=gender,
            followup_calls=followup_calls,
            course_id=int(course_id_raw) if course_id_raw else None,
        )
        db.session.add(enquiry)
        db.session.commit()

        flash("Enquiry added successfully.", "success")
        return redirect(url_for("main.enquiries_list"))

    return render_template("enquiries/form.html", mode="add", courses=courses)


@main_bp.route("/enquiries/<int:enquiry_id>/edit", methods=["GET", "POST"])
@login_required
def enquiries_edit(enquiry_id: int):
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    courses = Course.query.order_by(Course.name.asc()).all()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        enquiry_date_raw = request.form.get("enquiry_date", "").strip()
        gender = request.form.get("gender", "").strip().lower()
        followup_calls = request.form.get("followup_calls") == "on"
        course_id_raw = request.form.get("course_id", "").strip()
        errors = {}
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
            "enquiry_date": enquiry_date_raw,
            "gender": gender,
            "followup_calls": followup_calls,
            "course_id": course_id_raw,
        }

        if not first_name:
            errors["first_name"] = "First name is mandatory."
        if not last_name:
            errors["last_name"] = "Last name is mandatory."
        if not mobile:
            errors["mobile"] = "Mobile number is mandatory."
        if not email:
            errors["email"] = "Email is mandatory."
        if not enquiry_date_raw:
            errors["enquiry_date"] = "Enquiry date is mandatory."
        if gender not in {"male", "female"}:
            errors["gender"] = "Gender is mandatory."

        enquiry_date_value = None
        if enquiry_date_raw:
            try:
                enquiry_date_value = date.fromisoformat(enquiry_date_raw)
            except ValueError:
                errors["enquiry_date"] = "Enquiry date is invalid."

        if errors:
            return (
                render_template(
                    "enquiries/form.html",
                    mode="edit",
                    courses=courses,
                    enquiry=enquiry,
                    errors=errors,
                    form_data=form_data,
                ),
                400,
            )

        enquiry.first_name = first_name
        enquiry.last_name = last_name
        enquiry.mobile = mobile
        enquiry.email = email
        enquiry.enquiry_date = enquiry_date_value
        enquiry.gender = gender
        enquiry.followup_calls = followup_calls
        enquiry.course_id = int(course_id_raw) if course_id_raw else None
        db.session.commit()

        flash("Enquiry updated successfully.", "success")
        return redirect(url_for("main.enquiries_list"))

    return render_template("enquiries/form.html", mode="edit", courses=courses, enquiry=enquiry)


@main_bp.route("/enquiries/<int:enquiry_id>/toggle-enrolled", methods=["POST"])
@login_required
def enquiries_toggle_enrolled(enquiry_id: int):
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    enquiry.enrolled = not enquiry.enrolled
    db.session.commit()

    status_text = "enrolled" if enquiry.enrolled else "not enrolled"
    flash(f"Student marked as {status_text}.", "info")
    return redirect(url_for("main.enquiries_list"))


@main_bp.route("/enquiries/<int:enquiry_id>/delete", methods=["POST"])
@login_required
def enquiries_delete(enquiry_id: int):
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    db.session.delete(enquiry)
    db.session.commit()
    flash("Enquiry deleted successfully.", "info")
    return redirect(url_for("main.enquiries_list"))
