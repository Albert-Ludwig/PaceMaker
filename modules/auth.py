# This file is used to do the user authentication, including registration and login.
import json, hashlib, os

USER_FILE = "data/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()

def register_user(name, password):
    users = load_users()
    if len(users) >= 10:
        return "Max users reached"
    if any(u["name"] == name for u in users):
        return "User already exists"
    users.append({"name": name, "password": hash_password(password)})
    save_users(users)
    return "Registration successful"

def login_user(name, password):
    users = load_users()
    hashed = hash_password(password)
    for u in users:
        if u["name"] == name and u["password"] == hashed:
            return "Login successful"
    return "Invalid credentials"
