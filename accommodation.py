import tkinter as tk
from tkinter import ttk, messagebox
from accommodation import AccommodationPage

def show_page(self, page):
    for widget in self.content_frame.winfo_children():
        widget.destroy()

    if page == "Accommodation":
        accommodation_page = AccommodationPage(
            self.content_frame
        )
        accommodation_page.pack(fill="both", expand=True)

    else:
        tk.Label(
            self.content_frame,
            text=page,
            font=("Arial", 24, "bold"),
            bg="white"
        ).pack(pady=30)