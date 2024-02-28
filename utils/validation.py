import re

def is_valid_email(email):
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email) is not None

def is_valid_password(password):
    return len(password) >= 8

def is_valid_phone_number(phone_number):
    return len(phone_number) == 10 and phone_number.isdigit()

def is_valid_username(username):
    return len(username) >= 3