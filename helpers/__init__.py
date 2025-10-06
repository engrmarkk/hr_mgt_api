import uuid
from passlib.hash import pbkdf2_sha256 as hasher
import re
import random
import secrets
import string
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


def format_datetime(date_time):
    return date_time.strftime("%d-%b-%Y")


# generate token
def generate_token():
    return str(random.randint(1000, 9999))


def generate_uuid():
    return str(uuid.uuid4().hex)


# generate 10 random digit for account numbebr
def generate_account_number():
    return random.randint(1000000000, 9999999999)


def generate_session_id():
    # Generate a random 30-digit integer
    return str(secrets.randbelow(10**30))


def generate_transaction_reference():
    # Get current date and time in YYYYMMDDHHMMSS format
    today_date = datetime.now().strftime("%Y%m%d%H%M%S")

    # Generate a random 12-character alphanumeric string (letters + digits)
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))

    # Combine the date/time and random suffix
    return today_date + random_suffix


def hash_password(password):
    return hasher.hash(password)


# validate password
def validate_password(password):
    """
    :param password:
    :return:

    TODO:
    - length must be at least 8
    - must contain at least one lowercase letter
    - must contain at least one uppercase letter
    - must contain at least one digit
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"

    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter"

    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter"

    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit"

    return None


# verify password
async def verify_password(password, hashed_password):
    return hasher.verify(password, hashed_password)


async def validate_correct_email(email):
    try:
        # Validate the email
        validated_email = validate_email(email)
        # Normalize the email (e.g., convert to lowercase)
        normalized_email = validated_email.email
        return True, normalized_email
    except EmailNotValidError as e:
        # Handle invalid email
        return False, str(e)


# validate nigeria phone number
def validate_phone_number(phone_number):
    if not phone_number.startswith("0"):
        return "Your phone number must start with 0"
    if not len(phone_number) == 11:
        return "Your phone number must be 11 digits"
    if not phone_number.isdigit():
        return "Your phone number must be a number"
    return None


def generate_salt():
    return secrets.token_hex(16)


# difference between join date and current date in years
def get_service_year(join_date):
    today = datetime.now()
    return today.year - join_date.year if join_date else 0
