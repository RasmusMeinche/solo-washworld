from flask import Flask, render_template, request
import uuid
import time

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
        user_email = x.validate_email( request.form.get("user_email", "" ))
        user_password = x.validate_user_password()
        user_hashed_password = generate_password_hash(user_password)
        verification_key = uuid.uuid4().hex




        db, cursor = x.db()

        return "We have sent a confirmation email to your account"
    except Exception as ex:

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()
