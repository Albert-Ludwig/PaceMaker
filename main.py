import tkinter as tk
from tkinter import messagebox
from modules.auth import register_user, login_user

class WelcomeWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("DCM Login")
        self.root.geometry("400x300")

        tk.Label(root, text="Name").pack()
        self.name_entry = tk.Entry(root)
        self.name_entry.pack()

        tk.Label(root, text="Password").pack()
        self.pass_entry = tk.Entry(root, show="*")
        self.pass_entry.pack()

        tk.Button(root, text="Register", command=self.register).pack(pady=5)
        tk.Button(root, text="Login", command=self.login).pack(pady=5)

    def register(self):
        name = self.name_entry.get()
        password = self.pass_entry.get()
        msg = register_user(name, password)
        messagebox.showinfo("Register", msg)

    def login(self):
        name = self.name_entry.get()
        password = self.pass_entry.get()
        msg = login_user(name, password)
        if msg == "Login successful":
            self.root.destroy()
            root = tk.Tk()
            ApplicationWindow(root, name)
            root.mainloop()
        else:
            messagebox.showerror("Login", msg)

class ApplicationWindow:
    def __init__(self, root, username):
        self.root = root
        self.root.title("Pacing Mode Selection")
        self.root.geometry("1920x1080")
        self.username = username

        tk.Label(root, text=f"Welcome, {self.username}!", font=("Arial", 24)).pack(pady=20)
        # Add pacing mode UI here

if __name__ == "__main__":
    root = tk.Tk()
    WelcomeWindow(root)
    root.mainloop()
