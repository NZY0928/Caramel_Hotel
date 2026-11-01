import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGO_FILE = BASE_DIR / "caramel_hotel_logo.png"

class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Main page
        self.title("Caramel Hotel")
        self.geometry("1180x780")
        self.minsize(980, 640)

        # Colour palette
        self.BG_COLOUR = "#DFE2E5"
        self.NAV_COLOUR = "#486B92"
        self.SELECTED_COLOUR = "#9497B6"
        self.ACTIVE_COLOUR = "#7E93A9"
        self.SECONDARY_COLOUR = "#C5D6E2"
        self.TEXT_COLOUR = "#34465A"
        self.WHITE_COLOUR = "#FFFFFF"

        self.configure(bg=self.BG_COLOUR)

        # Top navigation remains visible on every page
        self.nav_frame = tk.Frame(self, bg=self.NAV_COLOUR)
        self.nav_frame.pack(side="top", fill="x")

        # logo & hotel name
        self.brand_frame = tk.Label(self.nav_frame, bg=self.NAV_COLOUR)
        self.brand_frame.pack(side="left", padx=(16,8), pady=6)

        self.logo_image = None
        try:
            # Keep a reference to the image on self so Tkinter does not discard it
            self.logo_image = tk.PhotoImage(file=str(LOGO_FILE))
            tk.Label(
                self.brand_frame,
                image=self.logo_image,
                bg=self.NAV_COLOUR,
                borderwidth=0,
            ).pack(side="left", padx=(0, 10))
        except tk.TclError:
            # It can still run if the logo is missing
            pass

        tk.Label(
            self.brand_frame,
            text="CARAMEL HOTEL",
            bg=self.NAV_COLOUR,
            fg=self.WHITE_COLOUR,
            font=("Arial", 16, "bold"),
        ).pack(side="left", padx=(0, 8), pady=8)

        # Navigation buttons are plain text without visible button boxes.
        self.button_frame = tk.Frame(self.nav_frame, bg=self.NAV_COLOUR)
        self.button_frame.pack(side="right", padx=10, pady=15)

        self.pages = [
            "Home",
            "Accommodation",
            "Menu",
            "Facility",
            "Promotions",
            "Gallery",
            "Contact Us",
        ]
        self.nav_buttons = {}

        for page in self.pages:
            button = tk.Button(
                self.button_frame,
                text=page,
                command=lambda selected_page=page: self.show_page(selected_page),
                bg=self.NAV_COLOUR,
                fg=self.WHITE_COLOUR,
                activebackground=self.NAV_COLOUR,
                activeforeground=self.WHITE_COLOUR,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 10),
                padx=8,
                pady=7,
                cursor="hand2",
            )
            button.pack(side="left", padx=2)
            self.nav_buttons[page] = button

        # Pages appear below the shared navigation bar.
        self.content_frame = tk.Frame(self, bg=self.BG_COLOUR)
        self.content_frame.pack(side="top", fill="both", expand=True)

        self.show_page("Home")

    def show_page(self, page):
        # Keep navigation items looking like plain text, not boxed buttons.
        # Show the selected page using bold text only.
        for page_name, button in self.nav_buttons.items():
            button.config(
                bg=self.NAV_COLOUR,
                activebackground=self.NAV_COLOUR,
                activeforeground=self.WHITE_COLOUR,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 10, "bold") if page_name == page else ("Arial", 10),
            )

        # Remove the previously displayed page.
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        """if page == "Accommodation":
            # Import only when Accommodation is opened. This lets the main
            # window still start if accommodation.py has not been added yet.
            try:
                from accommodation import AccommodationPage

                accommodation_page = AccommodationPage(self.content_frame)
                accommodation_page.pack(fill="both", expand=True)
            except ImportError as error:
                self._show_placeholder(
                    "Accommodation module not found\n\n"
                    "Make sure accommodation.py is in the same folder as main.py.\n"
                    f"Details: {error}"
                )
        else:
            # Placeholder until the other page modules are connected.
            self._show_placeholder(page)"""

    def _show_placeholder(self, text):
        tk.Label(
            self.content_frame,
            text=text,
            font=("Arial", 21, "bold"),
            bg=self.BG_COLOUR,
            fg=self.TEXT_COLOUR,
            justify="center",
        ).pack(expand=True, pady=30)


if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()