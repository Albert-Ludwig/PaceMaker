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

def logout_and_delete(self):
    from tkinter import messagebox
    if not getattr(self, "username", None):
        messagebox.showerror("Error", "No active user.")
        return
    confirm = messagebox.askyesno("Confirm Log Out", "Are you sure you want to log out this account?")
    if not confirm:
        return
    try:
        users = load_users()
    except Exception:
        users = []
    new_users = [u for u in users if u.get("name") != self.username]
    try:
        save_users(new_users)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete account: {e}")
        return
    messagebox.showinfo("Logged Out", "Account removed and signed out.")
    self.sign_out()
