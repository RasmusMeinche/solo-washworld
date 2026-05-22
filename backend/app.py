from flask import Flask, render_template, request
import uuid
import time

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import x

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from icecream import ic
ic.configureOutput(prefix=f"_____ | ", includeContext=True)

app = Flask(__name__)

##############################
@app.get("/")
def show_sign_up():
    return render_template("/sign_up.html")

##############################
@app.post("/sign-up")
def sign_up():
    try:
        user_pk = uuid.uuid4().hex
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email( request.form.get("user_email", "" ))
        user_password = x.validate_user_password()
        user_password_hashed = generate_password_hash(user_password)
        user_created_at = time.time()
        ic(user_created_at)
        user_verification_key = uuid.uuid4().hex
        user_verified_at = 0
        user_reset_password_key = uuid.uuid4().hex + uuid.uuid4().hex

        db, cursor = x.db()
        q = "INSERT INTO users (user_pk, user_first_name, user_last_name, user_email, user_password_hashed, user_created_at, user_verification_key, user_verified_at, user_reset_password_key) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(q, (user_pk, user_first_name, user_last_name, user_email, user_password_hashed, user_created_at, user_verification_key, user_verified_at, user_reset_password_key))
        db.commit()

        activation_email = render_template("email_welcome.html", user_verification_key=user_verification_key)

        x.send_email("Activate your account", activation_email)

        return "We have sent a confirmation email to your account", 201
    except Exception as ex:
        ic(ex)
        if "company_exception user_first_name" in str(ex):
            return f"First name must be between {x.USER_FIRST_NAME_MIN} and {x.USER_FIRST_NAME_MAX} characters", 400
            
        if "company_exception user_last_name" in str(ex):
            return f"Last name must be between {x.USER_LAST_NAME_MIN} and {x.USER_LAST_NAME_MAX} characters", 400

        if "company_exception user_email" in str(ex):
            return "Invalid Email", 400

        if "company_exception user_password" in str(ex):
            return f"At least {x.USER_PASSWORD_MIN} characters", 400

        return str(ex), 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
@app.get("/verify/<key>")
def verify_account(key):
    try:
        key = x.validate_uuid4(key)
        db, cursor = x.db()
        user_verified_at = int(time.time())
        q = """
            UPDATE users
            SET user_verified_at = %s
            WHERE user_verification_key = %s AND user_verified_at = 0
        """
        cursor.execute(q, (user_verified_at, key))
        db.commit()
        if cursor.rowcount == 0:
            return "user already verified"

        return f"Welcome to the system, you are verified"
    except Exception as ex: 
        ic(ex)
        if "company_exception uuid4 invalid" in str(ex):
            return "Invalid key", 400

        return str(ex), 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.get("/forgot_password")
def show_forgot_password():
    return render_template("/forgot_password.html")

##############################
@app.post("/forgot-password")
def forgot_password():
    try:
        user_email = x.validate_user_email(request.form.get("user_email", ""))
        db, cursor = x.db()
        q = "SELECT user_reset_password_key AS 'reset_key' FROM users WHERE user_email = %s"
        cursor.execute(q, (user_email,))
        row = cursor.fetchone()

        if not row:
            return "Email not found", 400

        forgot_password_html = render_template("/forgot_password_email.html", user_reset_password_key=row["reset_key"])

        x.send_email("Reset your password", forgot_password_html)

        return "Check your email"

    except Exception as ex:
        ic(ex)

        if "company_exception email" in str(ex):
            return "invalid email", 400
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
@app.get("/reset-password/<reset_key>")
def show_reset_password(reset_key):
    try:
        reset_key = x.validate_uuid4_paranoia(reset_key)
        db, cursor = x.db()

        q = """SELECT user_reset_password_key FROM users WHERE user_reset_password_key = %s"""
        cursor.execute(q, (reset_key,))
        row = cursor.fetchone()

        if not row:
            return "ups...", 400

        return render_template("/page_reset_password.html")

    except Exception as ex: 
        ic(ex)
        if "company_exception uuid4 invalid" in str(ex):
            return "Invalid key", 400

        return str(ex), 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
@app.post("/reset-password")
def reset_password():
    try:
        user_password = x.validate_user_password()
        confirm_user_password = x.validate_user_password()

        if user_password != confirm_user_password:
            return "Tjek om adgangskoderne er ens", 400

        reset_key = x.validate_user_password( request.form.get("reset_key", ""))

        return "Agangskode ændret, vær venlig at logge ind"
    except Exception as ex:

        if "company_exception user_password" in str(ex):
            return f"Password {x.USER_PASSWORD_MIN} to {x.USER_PASSWORD_MAX} characters", 400

        if "company_exception paranoia" in str(ex):
            return "Invalid key", 400

        return str(ex), 500
    finally: 
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()