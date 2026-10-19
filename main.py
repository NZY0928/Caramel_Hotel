import tkinter as tk
from accommodation import AccommodationPage

class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Main page
        self.title("Caramel Hotel")
        self.geometry("1180x780")
        self.configure(bg="white")

        # Navigation Panel
        self.nav_frame = tk.Frame(self, bg="#3E2723")
        self.nav_frame.pack(side="top", fill="x")

        tk.Label(
            self.nav_frame,
            text="CARAMEL HOTEL",
            bg="#3E2723",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=20, pady=20)

        self.button_frame = tk.Frame(self.nav_frame, bg="#3E2723")
        self.button_frame.pack(side="right", padx=10)

        self.pages = [
            "Home", "Accommodation", "Menu", "Facility",
            "Promotions", "Gallery", "Contact Us"
        ]

        self.nav_buttons = {}

        for page in self.pages:
            button = tk.Button(
                self.button_frame,
                text=page,
                command=lambda selected_page=page: self.show_page(selected_page),
                bg="#3E2723",
                fg="white",
                activebackground="#795548",
                activeforeground="white",
                relief="flat",
                font=("Arial", 10),
                padx=8,
                pady=5
            )
            button.pack(side="left", padx=2)
            self.nav_buttons[page] = button

        # Area where each page is displayed
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(side="top", fill="both", expand=True)
        # Start at Home
        self.show_page("Home")

    def show_page(self, page):
        # Make the selected navigation button bold
        for page_name, button in self.nav_buttons.items():
            if page_name == page:
                button.config(font=("Arial", 10, "bold"))
            else:
                button.config(font=("Arial", 10))

        # Remove the page currently being displayed
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Show the selected page
        if page == "Accommodation":
            accommodation_page = AccommodationPage(self.content_frame)
            accommodation_page.pack(fill="both", expand=True)
        else:
            # Placeholder until the other modules are connected
            tk.Label(
                self.content_frame,
                text=page,
                font=("Arial", 24, "bold"),
                bg="white",
                fg="#3E2723"
            ).pack(pady=30)


if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()