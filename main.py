"""Main Tkinter window, shared navigation and Caramel Hotel pages.

The Accommodation page is loaded from accommodation.py.
pack(), grid(), and place() arrange widgets on the screen."""
# The main module is exempt from the assignment function-count limit.
# parent = the main content area from main.py.

import ast
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from pathlib import Path
from datetime import date, datetime, timedelta
import math

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
ROOM_IMAGE_DIR = IMAGE_DIR / "room_images"
LOGO_FILE = IMAGE_DIR / "caramel_hotel_logo.png"
CONTACT_MESSAGES_FILE = BASE_DIR / "contact_messages.txt"  # Stores messages submitted through Contact Us


# ------------------------------------------------------------
# SHARED APPLICATION WINDOW AND NAVIGATION
#------------------------------------------------------------
class HotelApp(tk.Tk):
    # This runs when HotelApp() is created. It sets up the window, colour
    # navigation, scrolling support and Home page
    def __init__(self):
        # Initialise the parent Tk window first because HotelApp inherits from tk.Tk
        super().__init__()

        # Set the text displayed in the operating system title bar.
        self.title("Caramel Hotel")
        # Choose the starting window size: 1180 pixels wide and 780 pixels tall.
        self.geometry("1180x780")
        # Prevent the window from being resized smaller than 980 × 640 pixels.
        self.minsize(980, 640)

        # These colour variables keep the theme consistent and make recolouring easier.
        # Caramel Hotel colour palette
        self.BG_COLOUR = "#DFE2E5"
        self.NAV_COLOUR = "#486B92"
        self.SELECTED_COLOUR = "#9497B6"
        self.ACTIVE_COLOUR = "#7E93A9"
        self.SECONDARY_COLOUR = "#C5D6E2"
        self.TEXT_COLOUR = "#34465A"
        self.WHITE_COLOUR = "#FFFFFF"
        self.MUTED_COLOUR = "#647588"
        self.BORDER_COLOUR = "#C9D2DC"

        self.configure(bg=self.BG_COLOUR)
        self.page_canvas = None
        self.gallery_photo_refs = []
        self.home_booking_search = {}  # Preferences collected from the homepage booking bar
        self.home_hero_photo = None
        self._home_hero_resize_after_id = None

        # Create the navigation before the page content, so it remains at the top.
        self._build_navigation()

        # All page content changes inside this frame. The top navigation is
        # outside it, so it remains visible when users switch pages.
        # This frame is the area where the active page is shown. It is separaye from the navigation bar.
        self.content_frame = tk.Frame(self, bg=self.BG_COLOUR)
        # pack() arranges a widget. fill="both" lets the Frame expand horizontally/vertically;
        # expand=True lets it use any remaining space in the main window.
        self.content_frame.pack(side="top", fill="both", expand=True)

        # One global wheel binding is used only for pages with a scrollable body.
        # bind_all connects a wheel event across the application to the scrolling function.
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", lambda event: self._on_linux_mousewheel(-1))
        self.bind_all("<Button-5>", lambda event: self._on_linux_mousewheel(1))

        # Open the Home page automatically when the program starts.
        self.show_page("Home")
    
    # Shared navigation 
    # Build the shared top navigation. It is created once and stays visible when the
    # content area switches between Home, Accommodation, Facility, and so on.
    def _build_navigation(self):
        # One shared navigation bar remains visible while the page below changes.
        # A Frame is a container. The logo, hotel name and navigation buttons are placed inside this one.
        self.nav_frame = tk.Frame(self, bg=self.NAV_COLOUR, height=56)
        # pack(side="top") places the bar at the top; fill="x" stretches it across the window.
        self.nav_frame.pack(side="top", fill="x")
        # Normally a Frame may change size to fit its children. False keeps the navigation height fixed.
        self.nav_frame.pack_propagate(False)

        self.brand_frame = tk.Frame(self.nav_frame, bg=self.NAV_COLOUR)
        self.brand_frame.pack(side="left", padx=(34, 8), pady=8)

        # Keep the image reference on self so Tkinter does not discard it.
        self.logo_image = None
        try:
            if LOGO_FILE.is_file():
                # PhotoImage loads the PNG logo. str() converts the Path object to a normal filename string.
                self.logo_image = tk.PhotoImage(file=str(LOGO_FILE))
                target_logo_size = 40
                # Tkinter PhotoImage shrinks images using a whole-number factor. This chooses a factor that
                # makes the logo close to 40 pixels wide/high without stretching it.
                scale = max(
                    1,
                    math.ceil(self.logo_image.width() / target_logo_size),
                    math.ceil(self.logo_image.height() / target_logo_size),
                )
                if scale > 1:
                    self.logo_image = self.logo_image.subsample(scale, scale)

                tk.Label(
                    self.brand_frame,
                    image=self.logo_image,
                    bg=self.NAV_COLOUR,
                    bd=0,
                    highlightthickness=0,
                ).pack(side="left", padx=(0, 10))
        except (tk.TclError, OSError):
            # Keep the application running if the logo file is missing or unreadable.
            self.logo_image = None

        tk.Label(
            self.brand_frame, text="CARAMEL HOTEL", bg=self.NAV_COLOUR,
            fg=self.WHITE_COLOUR, font=("Georgia", 14),
        ).pack(side="left", pady=3)

        self.button_frame = tk.Frame(self.nav_frame, bg=self.NAV_COLOUR)
        self.button_frame.pack(side="right", padx=(8, 34), pady=8)
        # These are the main pages available from the shared navigation bar.
        self.pages = [
            "Home", "Accommodation", "Menu", "Facility",
            "Promotions", "Gallery", "Contact Us", "Login"
        ]
        self.nav_buttons = {}
        # The loop makes one button for each page name, avoiding repeated code.
        for page in self.pages:
            button = tk.Button(
                self.button_frame, text=page,
                # command defines the action for a click. lambda captures this page name for this specific button.
                command=lambda selected_page=page: self.show_page(selected_page),
                bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
                activebackground=self.NAV_COLOUR, activeforeground=self.WHITE_COLOUR,
                relief="flat", borderwidth=0, highlightthickness=0,
                font=("Arial", 9), padx=8, pady=7, cursor="hand2"
            )
            button.pack(side="left", padx=2)
            # Save each button in a dictionary so its font can be updated later.
            self.nav_buttons[page] = button

    # Switch to the requested page. It clears the old page content, then calls the
    # matching method to build the new page. The shared navigation is not deleted.
    def show_page(self, page):
        # Selected page is bold, without a box around the navigation text.
        for page_name, button in self.nav_buttons.items():
            button.config(
                bg=self.NAV_COLOUR,
                activebackground=self.NAV_COLOUR,
                activeforeground=self.WHITE_COLOUR,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                font=("Arial", 9, "bold") if page_name == page else ("Arial", 9),
            )

        # winfo_children() returns the widgets inside content_frame; destroy() removes old page widgets.
        saved_staff_page = getattr(self, "staff_page", None)

        for widget in self.content_frame.winfo_children():
            if widget is saved_staff_page:
                widget.pack_forget()
            else:
                widget.destroy()
        self.page_canvas = None
        self.gallery_photo_refs = []

        # Choose the correct page-building method based on the page name.
        if page == "Home":
            self._build_home_page()
        elif page == "Accommodation":
            self._build_accommodation_page()
        elif page == "Facility":
            self._build_facility_page()
        elif page == "Promotions":
            self._build_promotions_page()
        elif page == "Gallery":
            self._build_gallery_page()
        elif page == "Contact Us":
            self._build_contact_page()
        elif page == "Menu":
            self._build_menu_page()
        elif page == "Login":
            self._build_staff_page()


    # ------------------------------------------------------------
    # ACCOMMODATION PAGE CONNECTION
    # Load AccommodationPage from accommodation.py only when Accommodation is opened.
    # The try/except block shows a message if the separate module cannot be loaded.
    # ------------------------------------------------------------
    def _build_accommodation_page(self):
        try:
            # This import is inside the method, so the accommodation module is only needed when that page opens.
            from accommodation import AccommodationPage
            page = AccommodationPage(self.content_frame)
            # The homepage booking bar's dates and guest counts will prefill
            # the booking form after the guest chooses a room.
            page.home_booking_search = dict(self.home_booking_search or {})
            page.pack(fill="both", expand=True)
        except (ImportError, OSError) as error:
            self._show_message_page(
                "Accommodation",
                "The accommodation module could not be opened.\n\n"
                "Make sure accommodation.py is in the same folder as main.py.\n"
                f"Details: {error}"
            )

    # Shared page helpers: these pages live below the persistent nav bar.
    # Create a scrollable page area from a Canvas, a vertical Scrollbar, and a body Frame.
    # The page content goes inside body; the Canvas allows the body to scroll vertically.
    def _create_scrollable_body(self):
        container = tk.Frame(self.content_frame, bg=self.BG_COLOUR)
        container.pack(fill="both", expand=True)

        # Canvas supports scrolling. The Scrollbar controls its vertical view (yview).
        canvas = tk.Canvas(container, bg=self.BG_COLOUR, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=self.BG_COLOUR)
        # Place the body Frame inside the Canvas at its top-left corner; body holds the page widgets.
        body_window = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind(
            "<Configure>",
            lambda _event, target=canvas: target.configure(scrollregion=target.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda event, target=canvas, item=body_window:
                target.itemconfigure(item, width=event.width)
        )
        # Remember this Canvas so the mouse-wheel handler knows which area to scroll.
        self.page_canvas = canvas
        return body

    # Reusable helper for a page title and optional subtitle. Parameters:
    # body = the Frame that will contain the heading; title = heading text;
    # subtitle = optional smaller text shown below the title.
    def _page_heading(self, body, title, subtitle=None):
        heading = tk.Frame(body, bg=self.BG_COLOUR)
        heading.pack(fill="x", padx=24, pady=(20, 18))
        tk.Label(
            heading, text=title, font=("Arial", 21, "bold"),
            bg=self.SECONDARY_COLOUR, fg=self.TEXT_COLOUR, anchor="w", padx=12, pady=8
        ).pack(fill="x", pady=(0, 6))
        tk.Frame(heading, bg=self.SECONDARY_COLOUR, height=2).pack(fill="x", pady=(0, 12))
        if subtitle:
            tk.Label(
                heading, text=subtitle, font=("Helvetica", 12),
                fg=self.TEXT_COLOUR, bg=self.BG_COLOUR,
                wraplength=1000, justify="left", anchor="w"
            ).pack(fill="x")

    # Reusable helper that creates a bordered white Frame (a visual card).
    # parent is the container for the card; padx/pady set the inner left-right and top-bottom spacing.
    def _make_card(self, parent, padx=22, pady=16):
        return tk.Frame(
            parent, bg=self.WHITE_COLOUR, padx=padx, pady=pady,
            highlightbackground=self.BORDER_COLOUR, highlightthickness=1
        )

    # Handle a normal mouse-wheel event. event.delta tells us how the wheel moved;
    # the method converts it to scrolling steps and scrolls the current page Canvas.
    def _on_mousewheel(self, event):
        if self.page_canvas is None:
            return
        try:
            if self.page_canvas.winfo_exists():
                amount = int(-1 * (event.delta / 120))
                if amount == 0 and event.delta:
                    amount = -1 if event.delta > 0 else 1
                self.page_canvas.yview_scroll(amount, "units")
        except tk.TclError:
            pass

    # Handle Linux wheel-up/wheel-down events, which provide a direction instead of event.delta.
    def _on_linux_mousewheel(self, direction):
        if self.page_canvas is None:
            return
        try:
            if self.page_canvas.winfo_exists():
                self.page_canvas.yview_scroll(direction, "units")
        except tk.TclError:
            pass

    # Build a simple page with a title and a message, for example if another page module is missing.
    def _show_message_page(self, title, message):
        body = self._create_scrollable_body()
        self._page_heading(body, title)
        tk.Label(
            body, text=message, font=("Arial", 12), bg=self.BG_COLOUR,
            fg=self.TEXT_COLOUR, justify="center", wraplength=850
        ).pack(expand=True, pady=60, padx=30)

    # ------------------------------------------------------------
    # HOME PAGE
    # ------------------------------------------------------------
    # Load the Home page background photo and resize it to the requested size.
    # Pillow (PIL) adds high-quality resizing and a dark fade so white text is readable.
    def _load_home_hero_photo(self, filename, size):
        # Load a wide hero image with a subtle dark gradient behind white text.
        path = self._find_gallery_image(filename)
        if path is None:
            return None
        try:
            from PIL import Image, ImageDraw, ImageOps, ImageTk
            with Image.open(path) as original:
                resampling = getattr(Image, "Resampling", Image)
                lanczos = getattr(resampling, "LANCZOS", 1)
                image = ImageOps.fit(
                    original.convert("RGB"), size, method=lanczos,
                    centering=(0.5, 0.5)
                ).convert("RGBA")

            # A fade on the left helps the heading read without an opaque box.
            # Read the resized image dimensions so the dark text overlay matches the photo.
            width, height = image.size
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            fade_width = max(1, int(width * 0.62))
            # Draw a vertical dark fade on the left to help the white welcome text remain readable.
            for x in range(fade_width):
                alpha = int(112 * (1 - x / fade_width) ** 0.72)
                draw.line((x, 0, x, height), fill=(9, 22, 34, alpha))
            image = Image.alpha_composite(image, overlay).convert("RGB")
            return ImageTk.PhotoImage(image)
        except (ImportError, OSError, ValueError, tk.TclError, AttributeError):
            return self._load_gallery_photo(filename, size)

    # Schedule a background-photo resize.
    # This prevents the image from being resized too many times during a window resize.
    def _schedule_home_hero_resize(self, event=None):
        if not hasattr(self, "home_hero_frame"):
            return
        try:
            if not self.home_hero_frame.winfo_exists():
                return
            if self._home_hero_resize_after_id is not None:
                self.after_cancel(self._home_hero_resize_after_id)
            self._home_hero_resize_after_id = self.after_idle(self._resize_home_hero_photo)
        except tk.TclError:
            pass

    # Read the hero Canvas dimensions, resize the background photo, and place it behind the text.
    def _resize_home_hero_photo(self):
        # Resize the photo to the current hero canvas without a solid text panel.
        self._home_hero_resize_after_id = None
        try:
            canvas = self.home_hero_frame
            if not canvas.winfo_exists():
                return
            width = max(2, canvas.winfo_width())
            height = max(2, canvas.winfo_height())
            if width <= 2 or height <= 2:
                return
            photo = self._load_home_hero_photo("Suite_Apartment.png", (width, height))
            if photo is None:
                photo = self._load_home_hero_photo("Long_Stay_Discount.png", (width, height))
            if photo is not None:
                self.home_hero_photo = photo
                canvas.itemconfigure(self.home_hero_background_id, image=photo)
                canvas.coords(self.home_hero_background_id, 0, 0)
                canvas.tag_lower(self.home_hero_background_id)
        except (AttributeError, tk.TclError):
            pass

    # Schedule a photo resize after a section frame has its final size.
    # frame is the image container; label is the widget that displays the image.
    def _schedule_fitted_photo_resize(self, frame, label, filename, height=None):
        #Debounce resizing for a section image that should fill its frame.
        try:
            pending = getattr(frame, "_photo_resize_after_id", None)
            if pending is not None:
                self.after_cancel(pending)
            frame._photo_resize_after_id = self.after_idle(
                lambda target_frame=frame, target_label=label, file_name=filename, target_height=height:
                    self._resize_fitted_photo(target_frame, target_label, file_name, target_height)
            )
        except tk.TclError:
            pass
    
    # Fit a photo to the current frame width/height. The image reference is stored on the Label
    # because Tkinter may stop displaying an image if Python discards its last reference.
    def _resize_fitted_photo(self, frame, label, filename, height=None):
        # Keep a promotional image edge-to-edge as its column width changes.
        try:
            if not frame.winfo_exists() or not label.winfo_exists():
                return
            width = max(2, frame.winfo_width())
            target_height = int(height if height is not None else frame.winfo_height())
            target_height = max(2, target_height)
            target_size = (width, target_height)
            if getattr(label, "_photo_size", None) == target_size:
                return
            photo = self._load_gallery_photo(filename, target_size)
            if photo is None:
                return
            label.configure(image=photo)
            label.image = photo
            label._photo_size = target_size
            self.gallery_photo_refs.append(photo)
        except (AttributeError, tk.TclError):
            pass

    # Check the Home booking bar input. It validates dates and guest numbers, saves them in a
    # dictionary, then opens Accommodation so those choices can prefill the booking form.
    def _search_from_home(self):
        # .get() reads what the user typed/selected; .strip() removes extra spaces at the beginning/end.
        check_in_text = self.home_check_in_var.get().strip()
        check_out_text = self.home_check_out_var.get().strip()
        try:
            # Convert the date string (for example 2026-11-01) into a date object so Python can compare dates.
            check_in = datetime.strptime(check_in_text, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_text, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror(
                "Check your dates",
                "Please enter check-in and check-out dates in YYYY-MM-DD format, for example 2026-11-01.",
                parent=self,
            )
            return
        # Reject a check-in date that is earlier than today.
        if check_in < date.today():
            messagebox.showerror("Check-in date", "Check-in cannot be earlier than today.", parent=self)
            return
        # A stay must check out after its check-in date.
        if check_out <= check_in:
            messagebox.showerror("Check-out date", "Check-out must be later than check-in.", parent=self)
            return
        try:
            rooms = int(self.home_rooms_var.get())
            adults = int(self.home_adults_var.get())
            children = int(self.home_children_var.get())
        except (ValueError, TypeError):
            messagebox.showerror("Guest details", "Please select the number of rooms, adults and children.", parent=self)
            return
        if rooms < 1 or adults < 1 or children < 0:
            messagebox.showerror("Guest details", "Choose at least one room and one adult.", parent=self)
            return

        # Store validated booking choices in a dictionary to pass them to Accommodation.
        self.home_booking_search = {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "amount_of_room": str(rooms),
            "adults": str(adults),
            "children": str(children),
        }
        self.show_page("Accommodation")

    # Build the Home page from top to bottom: hero and booking bar, three numbered highlights,
    # Long Stay Discount promotion, dining cards with a sample review, and the closing banner.
    def _build_home_page(self):
        body = self._create_scrollable_body()

        # 1. HERO: full-width hotel photo with text directly over the image.
        # The overall block is 356 px high. The photo itself is 322 px high;
        hero_block = tk.Frame(body, bg=self.BG_COLOUR, height=356)
        hero_block.pack(fill="x")
        hero_block.pack_propagate(False)

        # Canvas is used for the hero because it can layer text on top of a background image.
        hero_canvas = tk.Canvas(
            hero_block, bg=self.NAV_COLOUR, height=322,
            highlightthickness=0, bd=0
        )
        hero_canvas.place(x=0, y=0, relwidth=1, height=322)
        self.home_hero_frame = hero_canvas
        self.home_hero_background_id = hero_canvas.create_image(0, 0, anchor="nw")

        # Canvas text has no solid background, so the room photo remains visible.
        # create_text() places text at x/y coordinates on a Canvas.
        hero_canvas.create_text(
            58, 68, text="WELCOME TO", anchor="nw", fill="#F4F5F6",
            font=("Arial", 10, "bold", "normal"), tags=("hero_copy",)
        )
        # create_text() places text at x/y coordinates on a Canvas.
        hero_canvas.create_text(
            58, 91, text="Caramel Hotel", anchor="nw", fill=self.WHITE_COLOUR,
            font=("Georgia", 42, "normal"), tags=("hero_copy",)
        )
        # create_text() places text at x/y coordinates on a Canvas.
        hero_canvas.create_text(
            60, 157,
            text="A perfect blend of comfort, elegance\nand warm hospitality.",
            anchor="nw", fill="#F4F5F6", font=("Georgia", 15),
            width=450, justify="left", tags=("hero_copy",)
        )
        for x in (63, 80, 97):
            hero_canvas.create_oval(
                x, 237, x + 6, 243, fill="#C5D6E2", outline="", tags=("hero_copy",)
            )
        hero_canvas.bind("<Configure>", self._schedule_home_hero_resize)

        # Booking card overlaps the bottom of the hero; all controls are selectable.
        booking_panel = tk.Frame(
            hero_block, bg=self.WHITE_COLOUR, padx=12, pady=10,
            highlightbackground="#D8E1E9", highlightthickness=1
        )
        # place() positions the booking panel relative to the hero: centred horizontally
        booking_panel.place(relx=0.5, y=273, anchor="n", relwidth=0.89)
        booking_panel.grid_columnconfigure(0, weight=2, uniform="home_booking")
        booking_panel.grid_columnconfigure(1, weight=2, uniform="home_booking")
        booking_panel.grid_columnconfigure(2, weight=1, uniform="home_booking")
        booking_panel.grid_columnconfigure(3, weight=1, uniform="home_booking")
        booking_panel.grid_columnconfigure(4, weight=1, uniform="home_booking")
        booking_panel.grid_columnconfigure(5, weight=2, uniform="home_booking")

        self.home_check_in_var = tk.StringVar(value=date.today().isoformat())
        self.home_check_out_var = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())
        self.home_rooms_var = tk.StringVar(value="1")
        self.home_adults_var = tk.StringVar(value="2")
        self.home_children_var = tk.StringVar(value="0")

        booking_fields = [
            ("▦  Check-in", self.home_check_in_var, "date"),
            ("▦  Check-out", self.home_check_out_var, "date"),
            ("▱  Rooms", self.home_rooms_var, "rooms"),
            ("♙  Adults", self.home_adults_var, "adults"),
            ("♧  Children", self.home_children_var, "children"),
        ]
        # enumerate() supplies both the index (column number) and the information for each booking field.
        for column, (label_text, variable, kind) in enumerate(booking_fields):
            field = tk.Frame(booking_panel, bg=self.WHITE_COLOUR)
            field.grid(row=0, column=column, sticky="nsew", padx=(4, 8))
            tk.Label(
                field, text=label_text, bg=self.WHITE_COLOUR, fg=self.NAV_COLOUR,
                font=("Arial", 8), anchor="w"
            ).pack(fill="x", pady=(0, 6))
            if kind == "date":
                widget = ttk.Entry(field, textvariable=variable, width=13, font=("Arial", 9))
                widget.pack(fill="x", ipady=4)
            else:
                choices = {
                    "rooms": [str(i) for i in range(1, 7)],
                    "adults": [str(i) for i in range(1, 11)],
                    "children": [str(i) for i in range(0, 11)],
                }[kind]
                # Combobox creates a dropdown with a fixed set of allowed choices.
                widget = ttk.Combobox(
                    field, textvariable=variable, values=choices,
                    state="readonly", width=5, font=("Arial", 9)
                )
                widget.pack(fill="x", ipady=3)

        tk.Button(
            booking_panel, text="CHECK AVAILABILITY  →", command=self._search_from_home,
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            relief="flat", borderwidth=0, cursor="hand2",
            font=("Arial", 9, "bold"), padx=12, pady=12
        ).grid(row=0, column=5, sticky="ew", padx=(2, 0), pady=(16, 0))

        self.after_idle(self._resize_home_hero_photo)

        # 2. The three numbered highlights, with round blue-grey icons and
        # fine vertical separators. Keep the wording and order from the design.
        benefits = tk.Frame(body, bg="#F7F9FA", padx=48, pady=31)
        benefits.pack(fill="x")
        for col in (0, 2, 4):
            benefits.grid_columnconfigure(col, weight=1, uniform="benefit_columns")
        benefits.grid_columnconfigure(1, weight=0, minsize=1)
        benefits.grid_columnconfigure(3, weight=0, minsize=1)
        # Each tuple defines one highlight: number, title, text, target page and icon type.
        benefit_items = [
            ("01", "ROOMS FOR STAY", "Spacious, stylish and designed\nfor your comfort.", "Accommodation", "bed"),
            ("02", "COMFORT AND CONVENIENCE", "Modern facilities, thoughtful services\nand a relaxing atmosphere.", "Facility", "plant"),
            ("03", "OFFERS AND UPDATES", "Exclusive deals and special packages\njust for you.", "Promotions", "tag"),
        ]
        # Build the three highlights from the data list rather than writing three almost-identical blocks.
        for index, (number, title, description, target_page, icon_kind) in enumerate(benefit_items):
            col = index * 2
            benefit = tk.Frame(benefits, bg="#F7F9FA", padx=15, pady=1)
            benefit.grid(row=0, column=col, sticky="nsew", padx=8)

            number_row = tk.Frame(benefit, bg="#F7F9FA")
            number_row.pack(anchor="center", pady=(0, 15))
            tk.Label(
                number_row, text=number, bg="#F7F9FA", fg=self.NAV_COLOUR,
                font=("Georgia", 17),
            ).pack(side="left", padx=(0, 22))
            # This small Canvas is used to draw icons from simple shapes such as lines, circles and arcs.
            icon = tk.Canvas(number_row, width=66, height=66, bg="#F7F9FA", highlightthickness=0, bd=0)
            icon.pack(side="left")
            icon.create_oval(2, 2, 64, 64, fill="#8FA8BC", outline="")
            white = self.WHITE_COLOUR
            if icon_kind == "bed": # the bed icon 
                icon.create_rectangle(18, 31, 48, 45, outline=white, width=2)
                icon.create_rectangle(17, 24, 24, 33, outline=white, width=2)
                icon.create_rectangle(25, 26, 34, 33, outline=white, width=2)
                icon.create_line(18, 45, 18, 49, fill=white, width=2)
                icon.create_line(48, 45, 48, 49, fill=white, width=2)
            elif icon_kind == "plant": # the plant icon
                icon.create_line(33, 48, 33, 29, fill=white, width=2)
                icon.create_arc(17, 20, 34, 39, start=35, extent=225, outline=white, width=2, style="arc")
                icon.create_arc(32, 14, 49, 34, start=280, extent=225, outline=white, width=2, style="arc")
                icon.create_arc(22, 13, 44, 37, start=25, extent=130, outline=white, width=2, style="arc")
                icon.create_line(22, 47, 44, 47, fill=white, width=2)
            else: # the tag icon
                icon.create_polygon(18, 24, 39, 24, 49, 34, 30, 50, 18, 38,
                                   outline=white, fill="", width=2)
                icon.create_oval(37, 28, 41, 32, outline=white, width=2)

            tk.Label(
                benefit, text=title, bg="#F7F9FA", fg=self.NAV_COLOUR,
                font=("Georgia", 12, "bold"), anchor="center", justify="center", wraplength=300
            ).pack(fill="x", pady=(0, 10))
            tk.Label(
                benefit, text=description, bg="#F7F9FA", fg=self.MUTED_COLOUR,
                font=("Georgia", 10), anchor="center", justify="center", wraplength=300
            ).pack(fill="x", pady=(0, 17))
            tk.Button(
                benefit,
                text={"Accommodation": "Explore Rooms  →", "Facility": "Our Facilities  →",
                      "Promotions": "View Promotions  →"}[target_page],
                command=lambda target=target_page: self.show_page(target),
                bg="#F7F9FA", fg=self.NAV_COLOUR, activebackground="#F7F9FA",
                activeforeground=self.ACTIVE_COLOUR, relief="flat", borderwidth=0,
                cursor="hand2", font=("Georgia", 9), highlightthickness=0
            ).pack(anchor="center")

        for separator_col in (1, 3):
            tk.Frame(benefits, bg=self.BORDER_COLOUR, width=1).grid(
                row=0, column=separator_col, sticky="ns", pady=14
            )

        # 3. Promotion block: large photo left, Long Stay Discount right.
        # The promotion section is split into two columns: a large image and its description.
        promo_section = tk.Frame(body, bg=self.SECONDARY_COLOUR, height=340)
        promo_section.pack(fill="x")
        promo_section.pack_propagate(False)
        promo_section.grid_columnconfigure(0, weight=6, uniform="promo_split")
        promo_section.grid_columnconfigure(1, weight=5, uniform="promo_split")
        promo_section.grid_rowconfigure(0, weight=1)

        promo_image_holder = tk.Frame(promo_section, bg=self.NAV_COLOUR)
        promo_image_holder.grid(row=0, column=0, sticky="nsew")
        promo_image_label = tk.Label(promo_image_holder, bg=self.NAV_COLOUR, bd=0)
        promo_image_label.pack(fill="both", expand=True)
        promo_image_holder.bind(
            "<Configure>",
            lambda _event, frame=promo_image_holder, label=promo_image_label:
                self._schedule_fitted_photo_resize(frame, label, "Long_Stay_Discount.png", 340)
        )
        self.after_idle(lambda: self._resize_fitted_photo(
            promo_image_holder, promo_image_label, "Long_Stay_Discount.png", 340
        ))

        promo_text = tk.Frame(promo_section, bg="#E5EBF2", padx=30, pady=26)
        promo_text.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            promo_text, text="FEATURED PROMOTION", bg="#E5EBF2", fg=self.NAV_COLOUR,
            font=("Arial", 8, "bold")
        ).pack(anchor="w", pady=(0, 10))
        tk.Label(
            promo_text, text="Long Stay Discount", bg="#E5EBF2", fg=self.NAV_COLOUR,
            font=("Georgia", 25, "bold"), anchor="w", justify="left", wraplength=410
        ).pack(anchor="w", pady=(0, 10))
        tk.Label(
            promo_text, text="Stay 5+ nights and save 15% on the total bill.",
            bg="#E5EBF2", fg=self.TEXT_COLOUR, font=("Georgia", 11),
            anchor="w", justify="left", wraplength=420
        ).pack(anchor="w", pady=(0, 14))
        for note in (
            "✓  Valid for all room types",
            "✓  Excludes public holidays",
            "✓  Book directly for the best rate",
        ):
            tk.Label(
                promo_text, text=note, bg="#E5EBF2", fg=self.TEXT_COLOUR,
                font=("Georgia", 10), anchor="w"
            ).pack(anchor="w", pady=4)
        tk.Button(
            promo_text, text="Book Now  →", command=lambda: self.show_page("Accommodation"),
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            relief="flat", borderwidth=0, cursor="hand2",
            font=("Arial", 9, "bold"), padx=18, pady=10
        ).pack(anchor="w", pady=(17, 0))

        # 4. Dining on the left and a customer comment on the right.
        # This section uses grid() to place dining cards beside the testimonial.
        experience_section = tk.Frame(body, bg=self.WHITE_COLOUR, padx=30, pady=29)
        experience_section.pack(fill="x")
        experience_section.grid_columnconfigure(0, weight=7, uniform="experience_split")
        experience_section.grid_columnconfigure(1, weight=4, uniform="experience_split")

        dining_left = tk.Frame(experience_section, bg=self.WHITE_COLOUR)
        dining_left.grid(row=0, column=0, sticky="nsew", padx=(0, 23))
        tk.Label(
            dining_left, text="DINE WITH US", bg=self.WHITE_COLOUR,
            fg=self.NAV_COLOUR, font=("Arial", 8, "bold")
        ).pack(anchor="w", pady=(0, 5))
        tk.Label(
            dining_left, text="Signature Dining Experience", bg=self.WHITE_COLOUR,
            fg=self.TEXT_COLOUR, font=("Georgia", 21, "bold"), wraplength=560, justify="left"
        ).pack(anchor="w")
        tk.Label(
            dining_left, text="Enjoy a variety of local and international dishes at our restaurant.",
            bg=self.WHITE_COLOUR, fg=self.MUTED_COLOUR, font=("Georgia", 10),
            wraplength=540, justify="left"
        ).pack(anchor="w", pady=(5, 14))

        # Read the featured dishes from menu.txt so the homepage uses the
        # actual food names, prices and image filenames from the restaurant menu.
        featured_ids = ("W01", "T01", "D01")
        featured_descriptions = {
            "W01": "A featured dish from our Western selection.",
            "T01": "A popular choice from our Thai selection.",
            "D01": "A sweet finish from our dessert selection.",
        }
        fallback_food_items = [
            ("w01.jpg", "Grilled Salmon", "RM 25.00", featured_descriptions["W01"]),
            ("T01.jpg", "Pad Thai", "RM 16.00", featured_descriptions["T01"]),
            ("D01.jpg", "Chocolate Lava Cake", "RM 7.00", featured_descriptions["D01"]),
        ]
        food_items = []
        menu_file = BASE_DIR / "menu.txt"
        try:
            menu_source = menu_file.read_text(encoding="utf-8-sig")
            menu_tree = ast.parse(menu_source, filename=str(menu_file))
            menu_assignment = next(
                node.value for node in menu_tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "menu_dict"
                    for target in node.targets
                )
            )
            menu_data = ast.literal_eval(menu_assignment)
            for item_id in featured_ids:
                item = menu_data.get(item_id)
                if not isinstance(item, dict):
                    continue
                food_items.append((
                    str(item.get("Image", "")).strip(),
                    str(item.get("Name", "")).strip(),
                    f"RM {float(item.get('Price', 0)):.2f}",
                    featured_descriptions[item_id],
                ))
            if len(food_items) != len(featured_ids):
                food_items = fallback_food_items
        except (OSError, SyntaxError, ValueError, StopIteration, TypeError):
            # Keep the homepage display available if menu.txt cannot be read.
            food_items = fallback_food_items
        food_grid = tk.Frame(dining_left, bg=self.WHITE_COLOUR)
        food_grid.pack(fill="x")
        for column in range(3):
            food_grid.grid_columnconfigure(column, weight=1, uniform="home_food_cards")
        # Create a food card from each tuple in the food list.
        for column, (filename, food_name, price, description) in enumerate(food_items):
            food_card = tk.Frame(
                food_grid, bg=self.WHITE_COLOUR, padx=7, pady=7,
                highlightbackground=self.BORDER_COLOUR, highlightthickness=1
            )
            food_card.grid(
                row=0, column=column, sticky="nsew",
                padx=(0 if column == 0 else 7, 7 if column < 2 else 0)
            )
            photo = self._load_gallery_photo(filename, (190, 105))
            if photo is not None:
                self.gallery_photo_refs.append(photo)
                photo_label = tk.Label(food_card, image=photo, bg=self.WHITE_COLOUR, bd=0)
                photo_label.image = photo
                photo_label.pack(fill="x")
            else:
                photo_box = tk.Frame(food_card, bg=self.SECONDARY_COLOUR, height=100)
                photo_box.pack(fill="x")
                photo_box.pack_propagate(False)
                tk.Label(
                    photo_box, text="FOOD PHOTO", bg=self.SECONDARY_COLOUR,
                    fg=self.NAV_COLOUR, font=("Arial", 8, "bold")
                ).pack(expand=True)
            tk.Label(
                food_card, text=food_name, bg=self.WHITE_COLOUR, fg=self.TEXT_COLOUR,
                font=("Georgia", 9, "bold"), anchor="w", wraplength=165, justify="left"
            ).pack(fill="x", pady=(7, 3))
            tk.Label(
                food_card, text=price, bg=self.WHITE_COLOUR, fg=self.NAV_COLOUR,
                font=("Arial", 9, "bold"), anchor="w"
            ).pack(fill="x", pady=(0, 4))
            tk.Label(
                food_card, text=description, bg=self.WHITE_COLOUR, fg=self.MUTED_COLOUR,
                font=("Arial", 8), anchor="w", justify="left", wraplength=165
            ).pack(fill="x")

        tk.Button(
            dining_left, text="View Full Menu  →", command=lambda: self.show_page("Menu"),
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            relief="flat", borderwidth=0, cursor="hand2",
            font=("Arial", 9, "bold"), padx=15, pady=9
        ).pack(anchor="w", pady=(14, 0))

        # Example content is explicitly identified as a sample customer comment.
        review_side = tk.Frame(
            experience_section, bg="#E8ECF6", padx=23, pady=22,
            highlightbackground="#E0E5ED", highlightthickness=1
        )
        review_side.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            review_side, text="“", bg="#E8ECF6", fg=self.NAV_COLOUR,
            font=("Georgia", 38, "bold")
        ).pack(anchor="w", pady=(0, 0))
        tk.Label(
            review_side,
            text="“The room was spacious and clean, the staff were very friendly and helpful. The food was amazing too! Will definitely come back again.”",
            bg="#E8ECF6", fg=self.TEXT_COLOUR, font=("Georgia", 11, "italic"),
            wraplength=285, justify="left", anchor="w"
        ).pack(fill="x", pady=(0, 15))
        tk.Label(
            review_side, text="Sarah Tan", bg="#E8ECF6", fg=self.NAV_COLOUR,
            font=("Georgia", 10, "bold")
        ).pack(anchor="w")
        tk.Label(
            review_side, text="Sample guest comment", bg="#E8ECF6", fg=self.MUTED_COLOUR,
            font=("Arial", 8, "italic")
        ).pack(anchor="w", pady=(2, 7))
        tk.Label(
            review_side, text="★★★★★", bg="#E8ECF6", fg="#D6A24B", font=("Arial", 13, "bold")
        ).pack(anchor="w")

        # 5. Closing call-to-action and footer.
        closing = tk.Frame(body, bg=self.NAV_COLOUR, padx=28, pady=24)
        closing.pack(fill="x")
        tk.Label(
            closing, text="YOUR PERFECT STAY AWAITS", bg=self.NAV_COLOUR,
            fg=self.SECONDARY_COLOUR, font=("Arial", 8, "bold")
        ).pack(anchor="center", pady=(0, 5))
        tk.Label(
            closing, text="Book Direct for the Best Rates", bg=self.NAV_COLOUR,
            fg=self.WHITE_COLOUR, font=("Georgia", 22)
        ).pack(anchor="center", pady=(0, 12))
        tk.Button(
            closing, text="Explore Rooms  →", command=lambda: self.show_page("Accommodation"),
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            relief="solid", borderwidth=1, highlightthickness=0,
            cursor="hand2", font=("Georgia", 10), padx=19, pady=9
        ).pack(anchor="center")


    # ------------------------------------------------------------
    # FACILITY PAGE
    # Build the Facility page with large photos alternating left/right with their descriptions.
    # A list of dictionaries stores each facility text and filename so one layout can be reused.
    # ------------------------------------------------------------
    def _build_facility_page(self):
        body = self._create_scrollable_body()
        page_white = "#FFFFFF"
        soft_panel = "#E7EDF3"
        body.configure(bg=page_white)
        if self.page_canvas is not None:
            self.page_canvas.configure(bg=page_white)

        # Introductory heading: clean, spacious and similar to a hotel facilities site.
        intro = tk.Frame(body, bg=page_white)
        intro.pack(fill="x", padx=38, pady=(28, 26))
        tk.Label(
            intro, text="CARAMEL HOTEL  /  FACILITIES", bg=page_white,
            fg=self.NAV_COLOUR, font=("Arial", 9, "bold")
        ).pack(anchor="center", pady=(0, 8))
        tk.Label(
            intro, text="Facilities", bg=page_white, fg="#303942",
            font=("Georgia", 30, "normal")
        ).pack(anchor="center")
        tk.Frame(intro, bg=self.NAV_COLOUR, height=2, width=70).pack(anchor="center", pady=(11, 13))
        tk.Label(
            intro,
            text="Thoughtful spaces to keep you active, refreshed and relaxed throughout your stay.",
            bg=page_white, fg=self.MUTED_COLOUR, font=("Arial", 11),
            justify="center", wraplength=850
        ).pack(anchor="center")

        # Each dictionary stores one facility’s number, text, image filename and image position.
        facilities = [
            {
                "number": "01",
                "eyebrow": "STAY ACTIVE",
                "title": "Fitness Centre",
                "description": (
                    "Keep up with your routine in a comfortable workout space, "
                    "with cardio equipment, strength-training machines and free weights. "
                    "There is room to stretch and cool down after your session."
                ),
                "detail": "Cardio equipment  ·  Strength training  ·  Stretching area",
                "hours": "Open 24 hours for hotel guests",
                "location": "Within Caramel Hotel — please ask the front desk for directions",
                "image": "Fitness_Centre.png",
                "image_side": "left",
            },
            {
                "number": "02",
                "eyebrow": "TAKE A REFRESHING BREAK",
                "title": "Swimming Pool",
                "description": (
                    "Slow down with a refreshing swim or spend a quiet afternoon beside the water. "
                    "Poolside seating gives you a place to relax between dips."
                ),
                "detail": "Outdoor pool  ·  Poolside seating  ·  Towels provided",
                "hours": "Open daily, 7:00 AM – 10:00 PM",
                "location": "Within Caramel Hotel — please ask the front desk for directions",
                "image": "pool.png",
                "image_side": "right",
            },
            {
                "number": "03",
                "eyebrow": "RESTORE YOUR BALANCE",
                "title": "Sauna & Steam",
                "description": (
                    "Unwind in a relaxing sauna and steam room after a busy day. "
                    "The warm atmosphere is designed to help guests slow down and refresh. "
                    "Please contact the front desk for access and availability."
                ),
                "detail": "Sauna  ·  Steam room  ·  Relaxation area",
                "hours": "Please contact the front desk for availability",
                "location": "Within Caramel Hotel — please ask the front desk for directions",
                "image": "spa.png",
                "image_side": "left",
            },
        ]

        section_width_pad = 28
        photo_height = 270
        # Repeat the same banner layout for every facility dictionary.
        for facility in facilities:
            banner = tk.Frame(body, bg=self.BORDER_COLOUR, height=photo_height)
            banner.pack(fill="x", padx=section_width_pad, pady=(0, 18))
            banner.pack_propagate(False)
            banner.grid_rowconfigure(0, weight=1)

            # The image gets slightly more room than the text, as in hotel feature pages.
            # Choose the image/text column order based on the image_side setting.
            if facility["image_side"] == "left":
                banner.grid_columnconfigure(0, weight=6, uniform="facility_banner")
                banner.grid_columnconfigure(1, weight=5, uniform="facility_banner")
                image_col, text_col = 0, 1
            else:
                banner.grid_columnconfigure(0, weight=5, uniform="facility_banner")
                banner.grid_columnconfigure(1, weight=6, uniform="facility_banner")
                text_col, image_col = 0, 1

            image_panel = tk.Frame(banner, bg=self.SECONDARY_COLOUR, height=photo_height)
            image_panel.grid(row=0, column=image_col, sticky="nsew")
            image_panel.grid_propagate(False)
            image_label = tk.Label(image_panel, bg=self.SECONDARY_COLOUR, bd=0)
            image_label.pack(fill="both", expand=True)

            # Load an initial photo, then resize it to the panel's actual width.
            photo = self._load_gallery_photo(facility["image"], (520, photo_height))
            if photo is not None:
                image_label.configure(image=photo)
                image_label.image = photo
                image_label._photo_size = (520, photo_height)
                self.gallery_photo_refs.append(photo)
                image_panel.bind(
                    "<Configure>",
                    lambda _event, frame=image_panel, label=image_label,
                           filename=facility["image"], h=photo_height:
                        self._schedule_fitted_photo_resize(frame, label, filename, h)
                )
                self.after_idle(
                    lambda frame=image_panel, label=image_label,
                           filename=facility["image"], h=photo_height:
                        self._resize_fitted_photo(frame, label, filename, h)
                )
            else:
                tk.Label(
                    image_panel, text=f"{facility['title']} photo\nAdd {facility['image']} beside main.py",
                    bg=self.SECONDARY_COLOUR, fg=self.NAV_COLOUR,
                    font=("Arial", 10, "bold"), justify="center"
                ).pack(fill="both", expand=True)

            text_panel = tk.Frame(
                banner, bg=soft_panel if facility["number"] in ("01", "03") else "#F7F9FB",
                padx=30, pady=20
            )
            text_panel.grid(row=0, column=text_col, sticky="nsew")
            tk.Label(
                text_panel, text=f"{facility['number']}  /  {facility['eyebrow']}",
                bg=text_panel["bg"], fg=self.NAV_COLOUR,
                font=("Arial", 8, "bold")
            ).pack(anchor="w", pady=(0, 8))
            tk.Label(
                text_panel, text=facility["title"], bg=text_panel["bg"],
                fg=self.TEXT_COLOUR, font=("Georgia", 22, "bold"),
                anchor="w", justify="left", wraplength=380
            ).pack(anchor="w", pady=(0, 10))
            tk.Label(
                text_panel, text=facility["description"], bg=text_panel["bg"],
                fg=self.TEXT_COLOUR, font=("Arial", 10),
                anchor="w", justify="left", wraplength=390
            ).pack(anchor="w", fill="x", pady=(0, 13))
            tk.Frame(text_panel, bg=self.BORDER_COLOUR, height=1).pack(fill="x", pady=(0, 10))
            tk.Label(
                text_panel, text=facility["detail"], bg=text_panel["bg"],
                fg=self.MUTED_COLOUR, font=("Arial", 9),
                anchor="w", justify="left", wraplength=390
            ).pack(anchor="w", fill="x", pady=(0, 7))
            tk.Label(
                text_panel, text=facility["hours"], bg=text_panel["bg"],
                fg=self.NAV_COLOUR, font=("Arial", 9, "bold"),
                anchor="w", justify="left", wraplength=390
            ).pack(anchor="w", fill="x")
            tk.Label(
                text_panel, text=f"Location: {facility['location']}", bg=text_panel["bg"],
                fg=self.MUTED_COLOUR, font=("Arial", 8),
                anchor="w", justify="left", wraplength=390
            ).pack(anchor="w", fill="x", pady=(5, 0))

        # Closing call-to-action like the direct-booking links on hotel websites.
        closing = tk.Frame(body, bg=self.NAV_COLOUR, padx=24, pady=23)
        closing.pack(fill="x", padx=section_width_pad, pady=(0, 30))
        tk.Label(
            closing, text="MAKE THE MOST OF YOUR STAY", bg=self.NAV_COLOUR,
            fg=self.SECONDARY_COLOUR, font=("Arial", 8, "bold")
        ).pack(anchor="center", pady=(0, 5))
        tk.Label(
            closing, text="A little more comfort, at every moment.", bg=self.NAV_COLOUR,
            fg=self.WHITE_COLOUR, font=("Georgia", 20)
        ).pack(anchor="center", pady=(0, 12))
        tk.Button(
            closing, text="Explore Rooms  →", command=lambda: self.show_page("Accommodation"),
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            relief="solid", borderwidth=1, highlightthickness=0,
            cursor="hand2", font=("Arial", 9, "bold"), padx=18, pady=8
        ).pack(anchor="center")


    # ------------------------------------------------------------
    # PROMOTIONS PAGE
    # Build the Promotions page with alternating image/text banners.
    # Each promotion dictionary stores its title, description, conditions, image filename and side.
    # ------------------------------------------------------------
    def _build_promotions_page(self):
        body = self._create_scrollable_body()
        self._page_heading(
            body,
            "Current Promotions",
            "Discover special offers designed to make your stay even better."
        )

        # The first promotion has its photo on the left. Each following
        # promotion swaps sides to create the alternating layout in the reference.
        # Each promotion dictionary contains the offer text, conditions, image and side.
        promos = [
            {
                "title": "Long Stay Discount",
                "eyebrow": "FEATURED PROMOTION",
                "description": "Stay 5+ nights and save 15% on the total bill.",
                "points": [
                    "Valid for all room types",
                    "Excludes public holidays",
                    "Use promo code LONGSTAY15 at booking",
                ],
                "note": "More time to unwind. More moments to enjoy.",
                "image": "Long_Stay_Discount.png",
                "image_side": "left",
            },
            {
                "title": "Weekend Getaway",
                "eyebrow": "MAKE TIME FOR YOU",
                "description": "Stay 2 nights and get 20% off the second night.",
                "points": [
                    "Valid Friday to Sunday",
                    "Subject to availability",
                    "Use promo code WEEKEND20 at booking",
                ],
                "note": "A refreshing escape without going too far.",
                "image": "pool.png",
                "image_side": "right",
            },
            {
                "title": "Early Bird Breakfast",
                "eyebrow": "PLAN AHEAD AND SAVE",
                "description": "Book 30 days in advance and enjoy complimentary breakfast.",
                "points": [
                    "Valid for Deluxe and Superior rooms",
                    "Reservation must be made 30 days ahead",
                    "Breakfast included with your stay",
                ],
                "note": "Wake up to a more delightful morning.",
                "image": "restaurant.png",
                "image_side": "left",
            },
            {
                "title": "Family Package",
                "eyebrow": "TIME TOGETHER",
                "description": "Book two adjoining rooms and enjoy complimentary kids' meals.",
                "points": [
                    "Valid all year",
                    "Subject to availability",
                    "Made for a more comfortable family stay",
                ],
                "note": "More room for the people who matter most.",
                "image": "suite_apartment.png",
                "image_side": "right",
            },
        ]
        # Build one promotion banner for every item in the list.
        for index, promo in enumerate(promos):
            # Keep alternating banners separated by white space and a fine border.
            banner = tk.Frame(
                body, bg=self.WHITE_COLOUR,
                highlightbackground=self.BORDER_COLOUR, highlightthickness=1,
                height=330
            )
            banner.pack(fill="x", padx=24, pady=(0, 18))
            banner.pack_propagate(False)

            image_frame = tk.Frame(banner, bg=self.SECONDARY_COLOUR)
            image_position = 0.0 if promo["image_side"] == "left" else 0.5
            # place() positions the image in half of the banner; relx selects the left/right half.
            image_frame.place(
                relx=image_position, rely=0, relwidth=0.5, relheight=1.0
            )
            image_label = tk.Label(image_frame, bg=self.SECONDARY_COLOUR, bd=0)
            image_label.pack(fill="both", expand=True)
            image_label._promo_filename = promo["image"]
            image_label._promo_size = None
            image_frame.bind(
                "<Configure>",
                lambda event, holder=image_frame, label=image_label, filename=promo["image"]:
                    self._resize_promotion_image(filename, holder, label, event.width, event.height)
            )
            self.after_idle(
                lambda holder=image_frame, label=image_label, filename=promo["image"]:
                    self._resize_promotion_image(
                        filename, holder, label, holder.winfo_width(), holder.winfo_height()
                    )
            )

            text_frame = tk.Frame(banner, bg="#E5ECF3", padx=32, pady=23)
            text_position = 0.5 if promo["image_side"] == "left" else 0.0
            text_frame.place(
                relx=text_position, rely=0, relwidth=0.5, relheight=1.0
            )

            tk.Label(
                text_frame, text=promo["eyebrow"], bg="#E5ECF3", fg=self.NAV_COLOUR,
                font=("Arial", 8, "bold"), anchor="w"
            ).pack(fill="x", pady=(0, 10))
            tk.Label(
                text_frame, text=promo["title"], bg="#E5ECF3", fg=self.NAV_COLOUR,
                font=("Georgia", 24, "bold"), anchor="w", justify="left",
                wraplength=440
            ).pack(fill="x", pady=(0, 8))
            tk.Label(
                text_frame, text=promo["description"], bg="#E5ECF3", fg=self.TEXT_COLOUR,
                font=("Georgia", 12), anchor="w", justify="left", wraplength=450
            ).pack(fill="x", pady=(0, 11))

            for point in promo["points"]:
                point_row = tk.Frame(text_frame, bg="#E5ECF3")
                point_row.pack(fill="x", pady=3)
                tk.Label(
                    point_row, text="✓", bg="#E5ECF3", fg=self.NAV_COLOUR,
                    font=("Arial", 10, "bold")
                ).pack(side="left", padx=(0, 9))
                tk.Label(
                    point_row, text=point, bg="#E5ECF3", fg=self.TEXT_COLOUR,
                    font=("Georgia", 10), anchor="w", justify="left", wraplength=420
                ).pack(side="left", fill="x", expand=True)

            tk.Label(
                text_frame, text=promo["note"], bg="#E5ECF3", fg=self.MUTED_COLOUR,
                font=("Arial", 9, "italic"), anchor="w", justify="left", wraplength=440
            ).pack(fill="x", pady=(9, 10))
            tk.Button(
                text_frame, text="Book Now  →", command=lambda: self.show_page("Accommodation"),
                bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR,
                activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
                relief="flat", borderwidth=0, highlightthickness=0,
                font=("Arial", 9, "bold"), padx=16, pady=8, cursor="hand2"
            ).pack(anchor="w")

        tk.Label(
            body, text="For reservations, contact us at info@caramelhotel.com",
            font=("Helvetica", 11, "bold"), fg=self.TEXT_COLOUR,
            bg=self.BG_COLOUR
        ).pack(pady=(6, 28))

    # Resize one promotion image to the current image frame dimensions.
    def _resize_promotion_image(self, filename, image_frame, image_label, width, height):
        # Fit a promotion photo to the current banner image frame.
        width, height = int(width), int(height)
        if width < 2 or height < 2:
            return
        target_size = (width, height)
        if getattr(image_label, "_promo_size", None) == target_size:
            return
        photo = self._load_gallery_photo(filename, target_size)
        if photo is None:
            image_label.configure(
                image="", text="CARAMEL HOTEL", compound="center",
                fg=self.NAV_COLOUR, font=("Georgia", 16, "bold"),
                bg=self.SECONDARY_COLOUR
            )
            image_label._promo_size = target_size
            return
        image_label.configure(image=photo, text="")
        image_label.image = photo
        image_label._promo_size = target_size
        self.gallery_photo_refs.append(photo)


    # Gallery page formating
    # Search for an image in the folder beside main.py and then in room_images.
    # The filename comparison ignores upper/lower case differences.
    def _find_gallery_image(self, filename):
        for folder in (BASE_DIR, IMAGE_DIR, ROOM_IMAGE_DIR):
            direct = folder / filename
            if direct.is_file():
                return direct
            if folder.is_dir():
                try:
                    for item in folder.iterdir():
                        if item.is_file() and item.name.casefold() == filename.casefold():
                            return item
                except OSError:
                    pass
        return None

    # Find and load a photo at the requested pixel size. Pillow can crop and resize;
    # if Pillow is not installed, Tkinter PhotoImage is used as a simpler fallback.
    def _load_gallery_photo(self, filename, size):
        path = self._find_gallery_image(filename)
        if path is None:
            return None
        try:
            from PIL import Image, ImageOps, ImageTk
            with Image.open(path) as original:
                resampling = getattr(Image, "Resampling", Image)
                lanczos = getattr(resampling, "LANCZOS", getattr(Image, "LANCZOS", 3))
                image = ImageOps.fit(original.convert("RGB"), size, method=lanczos)
                return ImageTk.PhotoImage(image)
        except ImportError:
            try:
                image = tk.PhotoImage(file=str(path))
                factor = max(1, math.ceil(image.width() / size[0]), math.ceil(image.height() / size[1]))
                return image.subsample(factor, factor)
            except tk.TclError:
                return None
        except (OSError, ValueError, tk.TclError, AttributeError):
            return None

    
    # ------------------------------------------------------------
    # GALLERY PAGE
    # Build the fixed ten-photo gallery in three uneven columns (a masonry layout).
    # The list below controls exactly which image filenames appear in each column.
    # ------------------------------------------------------------
    def _build_gallery_page(self):
        body = self._create_scrollable_body()
        gallery_white = "#FFFFFF"
        body.configure(bg=gallery_white)
        if self.page_canvas is not None:
            self.page_canvas.configure(bg=gallery_white)

        # Large, light heading centred above the collage.
        tk.Label(
            body, text="Gallery", font=("Times New Roman", 31, "normal"),
            bg=gallery_white, fg="#2E3338"
        ).pack(fill="x", pady=(29, 43))

        # Exactly these ten images appear. No room.txt scanning or other fallbacks.
        # This list determines exactly which gallery images appear and which column holds each one.
        requested_columns = [
            # Left column
            [("lobby.png", False), ("garden.png", False),
             ("reception.png", False), ("pool.png", False)],
            # Centre column: tall hotel sign and suite image
            [("hotel_sign.png", True), ("suite_apartment.png", False)],
            # Right column
            [("restaurant.png", False), ("spa.png", False),
             ("Chocolate_Lava_Cake.png", False), ("Fitness_Centre.png", False)],
        ]

        collage_outer = tk.Frame(body, bg=gallery_white)
        collage_outer.pack(fill="x", padx=70, pady=(0, 36))
        collage = tk.Frame(collage_outer, bg=gallery_white)
        collage.pack(fill="x")
        for column in range(3):
            collage.grid_columnconfigure(column, weight=1, uniform="masonry_columns")

        # This helper belongs only to the Gallery page. It resizes each tile after Tkinter
        # calculates its real width. is_tall tells the function if the photo should be taller.
        # This inner helper resizes a Gallery tile after Tkinter works out its true width.
        # is_tall is True for the tall centre image and False for normal landscape images.
        def resize_tile(filename, holder, image_label, is_tall):
            try:
                if not holder.winfo_exists() or not image_label.winfo_exists():
                    return
                width = holder.winfo_width()
                if width < 2:
                    return

                # Ordinary images are landscape; the hotel sign is the tall centre image.
                height = max(100, int(width * (1.48 if is_tall else 0.68)))
                if holder.winfo_height() != height:
                    holder.configure(height=height)
                target_size = (width, height)
                if getattr(image_label, "_gallery_size", None) == target_size:
                    return

                photo = self._load_gallery_photo(filename, target_size)
                if photo is None:
                    image_label.configure(image="", text=f"Missing: {filename}",
                                           fg="#486B92", font=("Arial", 9))
                    image_label._gallery_size = target_size
                    return
                image_label.configure(image=photo, text="")
                image_label.image = photo
                image_label._gallery_size = target_size
                self.gallery_photo_refs.append(photo)
            except tk.TclError:
                return

        for column_index, requested_items in enumerate(requested_columns):
            column_frame = tk.Frame(collage, bg=gallery_white)
            column_frame.grid(
                row=0, column=column_index, sticky="nsew",
                padx=(0 if column_index == 0 else 6, 0 if column_index == 2 else 6)
            )
            for requested_name, is_tall in requested_items:
                filename = requested_name
                holder = tk.Frame(column_frame, bg=gallery_white, bd=0)
                holder.pack(fill="x", pady=(0, 10))
                holder.pack_propagate(False)
                image_label = tk.Label(holder, bg=gallery_white, bd=0, highlightthickness=0)
                image_label.pack(fill="both", expand=True)
                holder.bind(
                    "<Configure>",
                    lambda _event, name=filename, tile=holder, label=image_label, tall=is_tall:
                        self.after_idle(lambda: resize_tile(name, tile, label, tall))
                )
                self.after_idle(
                    lambda name=filename, tile=holder, label=image_label, tall=is_tall:
                        resize_tile(name, tile, label, tall)
                )

    
    # ------------------------------------------------------------
    # CONTACT US PAGE
    # Build the Contact Us page, including contact details and a demo message form.
    # The form validates input and shows feedback
    # ------------------------------------------------------------
    def _build_contact_page(self):
        body = self._create_scrollable_body()
        self._page_heading(body, "Contact Us")

        info_card = self._make_card(body, padx=24, pady=20)
        info_card.pack(pady=10, padx=48, fill="x")
        tk.Label(info_card, text="Get in Touch", font=("Helvetica", 14, "bold"),
                 fg=self.TEXT_COLOUR, bg=self.WHITE_COLOUR, anchor="w").pack(fill="x", pady=(0, 10))

        # Store contact details as label/value pairs so the display rows can be built in a loop.
        rows = [
            ("Address", "123 Main Street, City, Country"),
            ("Phone", "+1234567890"),
            ("Email", "info@caramelhotel.com"),
            ("Front Desk Hours", "24 hours"),
        ]
        for label, value in rows:
            row = tk.Frame(info_card, bg=self.WHITE_COLOUR)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", font=("Helvetica", 11, "bold"),
                     fg=self.TEXT_COLOUR, bg=self.WHITE_COLOUR, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Helvetica", 11), fg=self.TEXT_COLOUR,
                     bg=self.WHITE_COLOUR, anchor="w").pack(side="left")

        form_card = self._make_card(body, padx=24, pady=20)
        form_card.pack(pady=14, padx=48, fill="x")
        tk.Label(form_card, text="Send Us a Message", font=("Helvetica", 14, "bold"),
                 fg=self.TEXT_COLOUR, bg=self.WHITE_COLOUR, anchor="w").pack(fill="x", pady=(0, 10))

        tk.Label(form_card, text="Name", font=("Helvetica", 11), fg=self.TEXT_COLOUR,
                 bg=self.WHITE_COLOUR, anchor="w").pack(fill="x")
        name_entry = tk.Entry(form_card, font=("Helvetica", 11), relief="solid", borderwidth=1,
                              highlightthickness=0)
        name_entry.pack(fill="x", pady=(2, 10), ipady=4)

        tk.Label(form_card, text="Email", font=("Helvetica", 11), fg=self.TEXT_COLOUR,
                 bg=self.WHITE_COLOUR, anchor="w").pack(fill="x")
        email_entry = tk.Entry(form_card, font=("Helvetica", 11), relief="solid", borderwidth=1,
                               highlightthickness=0)
        email_entry.pack(fill="x", pady=(2, 10), ipady=4)

        tk.Label(form_card, text="Mobile (include country code)", font=("Helvetica", 11),
                 fg=self.TEXT_COLOUR, bg=self.WHITE_COLOUR, anchor="w").pack(fill="x")
        mobile_entry = tk.Entry(form_card, font=("Helvetica", 11), relief="solid", borderwidth=1,
                                highlightthickness=0)
        mobile_entry.pack(fill="x", pady=(2, 10), ipady=4)

        tk.Label(form_card, text="Message", font=("Helvetica", 11), fg=self.TEXT_COLOUR,
                 bg=self.WHITE_COLOUR, anchor="w").pack(fill="x")
        message_text = tk.Text(form_card, font=("Helvetica", 11), height=5,
                               relief="solid", borderwidth=1, highlightthickness=0)
        message_text.pack(fill="x", pady=(2, 12))

        status = tk.Label(form_card, text="", font=("Helvetica", 10, "italic"),
                          fg=self.NAV_COLOUR, bg=self.WHITE_COLOUR)

        # Run when the Send Message button is clicked. It validates the fields,
        # saves the message in contact_messages.txt, and clears the form only if saving succeeds.
        def submit_message():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            mobile = mobile_entry.get().strip()
            message = message_text.get("1.0", "end").strip()

            if not name or not email or not mobile or not message:
                status.config(text="Please fill in all fields.", fg="#B23A48")
            elif "@" not in email or "." not in email.split("@")[-1]:
                status.config(text="Please enter a valid email address.", fg="#B23A48")
            elif len("".join(character for character in mobile if character.isdigit())) < 7:
                status.config(text="Please enter a valid mobile number with country code.", fg="#B23A48")
            else:
                # Add a date and time so the hotel staff can tell when the message arrived.
                submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    # Use append mode so new messages are added without deleting old messages.
                    # Each message is saved as a readable block in the project's main folder.
                    with CONTACT_MESSAGES_FILE.open("a", encoding="utf-8") as file:
                        file.write(
                            f"Date: {submitted_at}\n"
                            f"Name: {name}\n"
                            f"Email: {email}\n"
                            f"Mobile: {mobile}\n"
                            f"Message:\n{message}\n"
                            f"{'-' * 50}\n"
                        )
                except OSError:
                    # Keep the customer's message in the form if the file cannot be saved.
                    status.config(
                        text="Sorry, your message could not be saved. Please try again.",
                        fg="#B23A48"
                    )
                else:
                    status.config(
                        text="Thank you! Your message has been saved successfully.",
                        fg=self.NAV_COLOUR
                    )
                    name_entry.delete(0, "end")
                    email_entry.delete(0, "end")
                    mobile_entry.delete(0, "end")
                    message_text.delete("1.0", "end")
                    # Stage 1 specifies returning to the Home page after submitting a message.
                    self.after(1200, lambda: self.show_page("Home"))

            if not status.winfo_ismapped():
                status.pack(pady=(4, 0))

        tk.Button(
            form_card, text="Send Message", command=submit_message,
            bg=self.NAV_COLOUR, fg=self.WHITE_COLOUR, relief="flat",
            activebackground=self.ACTIVE_COLOUR, activeforeground=self.WHITE_COLOUR,
            font=("Arial", 11), padx=18, pady=6, cursor="hand2"
        ).pack(pady=(0, 6))
        tk.Button(
            form_card, text="Back to Home", command=lambda: self.show_page("Home"),
            bg=self.WHITE_COLOUR, fg=self.NAV_COLOUR, relief="solid",
            activebackground=self.SECONDARY_COLOUR, font=("Arial", 10),
            padx=16, pady=6, cursor="hand2",
        ).pack(pady=(0, 2))

    
    # ------------------------------------------------------------
    # RESTAURANT MENU PAGE
    # Load RestaurantPage from restaurant.py only when Menu is selected.
    # ------------------------------------------------------------
    def _build_menu_page(self):
        try:
            from restaurant import RestaurantPage
            page = RestaurantPage(self.content_frame)
            page.pack(fill="both", expand=True)
        except Exception as error:
            self._show_message_page(
                "Menu",
                "The restaurant page could not be opened.\n\n"
                "Check that restaurant.py, menu.txt, and the images folder are "
                "in the project folder. Pillow is also required for the food photos.\n\n"
                f"Details: {error}"
            )

    # ------------------------------------------------------------
    # STAFF LOGIN AND ADMIN PAGES
    # The staff login and portal are embedded in the same main window.
    # ------------------------------------------------------------
    def _build_staff_page(self):
        try:
            # Check whether the Staff page already exists.
            saved_page = getattr(self, "staff_page", None)

            if saved_page is not None:
                try:
                    if saved_page.winfo_exists():
                        saved_page.pack(fill="both", expand=True)
                        return
                except tk.TclError:
                    self.staff_page = None

            # Create the Staff page only when it has not been created before.
            from staff import StaffPage

            self.staff_page = StaffPage(self.content_frame)
            self.staff_page.pack(fill="both", expand=True)

        except Exception as error:
            self._show_message_page(
                "Login",
                "The staff portal could not be opened.\n\n"
                "Make sure staff.py is in the same folder as main.py.\n\n"
                f"Details: {error}"
            )

# Python runs this block only when this file is launched directly. It creates the app and starts
# mainloop(), the event loop that listens for clicks, typing, resizing and scrolling.
if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()