import uuid
from passlib.hash import pbkdf2_sha256 as hasher
import re
import random
import secrets
import string
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from logger import logger
import base64
from io import BytesIO
import hmac
import hashlib
import time
import requests


def format_datetime(date_time):
    if not date_time:
        return None
    return date_time.strftime("%d-%b-%Y")


def format_time(t):
    return t.strftime("%I:%M %p") if t else None


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


def convert_binary(base64_file):
    try:
        logger.info("got here")
        binary_data = base64.b64decode(base64_file)
        # Convert binary data to a file-like object
        file_like = BytesIO(binary_data)
        logger.info(f"{file_like} file_like from convert_binary")
        return file_like
    except Exception as e:
        logger.error(f"{e}: error from convert_binary")
        return None


def generate_signature(params_to_sign, api_secret):
    try:
        params_to_sign["timestamp"] = int(time.time())
        sorted_params = "&".join(
            [f"{k}={params_to_sign[k]}" for k in sorted(params_to_sign)]
        )
        to_sign = f"{sorted_params}{api_secret}"
        signature = hmac.new(
            api_secret.encode("utf-8"), to_sign.encode("utf-8"), hashlib.sha1
        ).hexdigest()
        logger.info(f"{signature}: signature from generate_signature")
        return signature
    except Exception as e:
        logger.error(f"{e}: error from generate_signature")
        return None


def get_country_by_ip_address(ip_address):
    # https://ipapi.co/102.88.108.57/json
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        res = response.json()
        print(res)
        country = res.get("country", "Nigeria")
        city = res.get("city", "Lagos")
        return f"{city}, {country}"
    except Exception as e:
        logger.error(f"{e}: error from get_country_by_ip_address")
        return None


def get_ip_address(request):
    # request to this "https://api.ipify.org?format=json"
    try:
        # response = requests.get("https://api.ipify.org?format=json")
        # return response.json().get("ip")
        client_ip = (
            (
                request.headers.get("X-Forwarded-For")
                or request.headers.get("X-Real-IP")
                or request.client.host
            )
            .split(",")[0]
            .strip()
        )
        return client_ip
    except Exception as e:
        logger.error(f"{e}: error from get_ip_address")
        return None
