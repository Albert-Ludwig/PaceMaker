import tkinter as tk
from tkinter import ttk, messagebox
import os
class ApplicationWindow:
    def __init__(self,root, username):
        self.root=root
        self.root.title("Pacing Mode Selection")
        self.root.geometry("1920x1080")

        self.username=username
        