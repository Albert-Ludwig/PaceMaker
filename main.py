import tkinter as tk
from tkinter import messagebox
from modules.auth import register_user, login_user
from modules.dashboard import DashboardWindow

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
            DashboardWindow(root, name)
            root.mainloop()
        else:
            messagebox.showerror("Login", msg)

def main():
    root = tk.Tk()
    app = WelcomeWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
