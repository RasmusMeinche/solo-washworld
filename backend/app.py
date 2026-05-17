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
            return "First name must be between {x.USER_FIRST_NAME_MIN} and {x.USER_FIRST_NAME_MAX} characters", 400
            
        if "company_exception last_name" in str(ex):
            return "Last name must be between {x.USER_LAST_NAME_MIN} and {x.USER_LAST_NAME_MAX} characters", 400

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