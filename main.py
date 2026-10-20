import tkinter as tk
"""from accommodation import AccommodationPage"""

class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Main page
        self.title("Caramel Hotel")
        self.geometry("1180x780")
        self.configure(bg="#DFE2E5")

        # Colour pallete
        self.BG_COLOUR = "#DFE2E5" # pale grey-blue
        self.NAV_COLOUR = "#486B92" # deep muted blue
        self.SELECTED_COLOUR = "#9497B6" # muted lavender
        self.ACTIVE_COLOUR = "#7E93A9" # slate blue
        self.SECONDARY_COLOUR = "#C5D6E2" # pale blue
        self.TEXT_COLOUR = "#34465A" # dark blue-grey
        self.WHITE_COLOUR = "#FFFFFF"

        # Navigation Panel
        self.nav_frame = tk.Frame(self, bg=self.NAV_COLOUR)
        self.nav_frame.pack(side="top", fill="x")

        tk.Label(
            self.nav_frame,
            text="CARAMEL HOTEL",
            bg=self.NAV_COLOUR,
            fg=self.WHITE_COLOUR,
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=20, pady=20)

        self.button_frame = tk.Frame(self.nav_frame, bg=self.NAV_COLOUR)
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
                bg=self.NAV_COLOUR,
                fg=self.WHITE_COLOUR,
                activebackground=self.ACTIVE_COLOUR,
                activeforeground=self.WHITE_COLOUR,
                relief="flat",
                font=("Arial", 10),
                padx=8,
                pady=5,
                cursor="hand2"
            )
            button.pack(side="left", padx=2)
            self.nav_buttons[page] = button

        # Area where each page is displayed
        self.content_frame = tk.Frame(self, bg=self.BG_COLOUR)
        self.content_frame.pack(side="top", fill="both", expand=True)
        # Start at Home
        self.show_page("Home")

    def show_page(self, page):
        # Make the selected navigation button bold
        for page_name, button in self.nav_buttons.items():
            if page_name == page:
                button.config(
                    bg=self.SELECTED_COLOUR,
                    activebackground=self.ACTIVE_COLOUR,
                    font=("Arial", 10, "bold"))
            else:
                button.config(
                    bg=self.NAV_COLOUR,
                    activebackground=self.ACTIVE_COLOUR,
                    font=("Arial", 10))

        # Remove the page currently being displayed
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        """# Show the selected page
        if page == "Accommodation":
            accommodation_page = AccommodationPage(self.content_frame)
            accommodation_page.pack(fill="both", expand=True)
        else:"""
            # Placeholder until the other modules are connected
        tk.Label(
            self.content_frame,
            text=page,
            font=("Arial", 24, "bold"),
            bg=self.BG_COLOUR,
            fg=self.TEXT_COLOUR
        ).pack(pady=30)


if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()