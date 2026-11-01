
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOM_FILE = BASE_DIR / "room.txt"
BOOKING_FILE = BASE_DIR / "booking.txt"
IMAGE_DIR = BASE_DIR / "room_images"

# Colour palette
BG = "#DFE2E5"
NAVY = "#486B92"
LAVENDER = "#9497B6"
SLATE_BLUE = "#7E93A9"
PALE_BLUE = "#C5D6E2"
BLUE_GREY = "#ACB7C6"
WHITE = "#FFFFFF"
TEXT = "#34465A"
MUTED = "#647588"
BORDER = "#D0D9E0"
PALE_CARD = "#F7F9FA"

ROOM_FIELDS = (
    "room_type", "room_number", "price_per_night", "features", "status", "image_filename",
)

BOOKING_FIELDS = (
    "name", "email", "hp", "ic", "room_type", "room_number", "check_in", "check_out", "amount_of_room", "adults",
    "children", "special_requests", "promo_code", "total_price", "payment_method", "status"
)
PAYMENT_METHODS = ("Credit/Debit Card", "E-wallet")
EWALLET_PROVIDERS = ("Touch 'n Go eWallet", "GrabPay", "Boosts", "ShopeePay")

class AccommodationPage(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._ensure_booking_file()
        self.rooms = self._read_rooms()
        self.bookings = self._read_bookings()
        self.selected_room = None # Start with no room selected
        self.photo_refs = [] # Keep references to room images so Tkinter does not discard them
        self.detail_photo = None # Store the image shown in the selected room detail panel
        self.form_vars = {} # hold variables for the booking form
        self.payment_detail_vars = {}
        self.payment_var = None # hold the selected payment method
        self.wallet_provider_var = None
        self.total_var = None # hold the total price for the booking
        self.availability_var = None
        self.quantity_var = None
        self.quantity_spinbox = None
        self.payment_detail_frame = None
        self.payment_form_inner = None
        self.booking_form_canvas = None
        self.current_canvas = None # Keeps track of the current canvas widget, likely for scrolling or updating the page

        self._setup_styles() # Sets up the styles for the widgets
        self._build_shell() # Creates the main layout of the page
        self.show_gallery() # Displays the gallery of available rooms
        if not self.rooms:
            self.after(200, self._show_missing_rooms_message)

    # Data files        
    def _read_rooms(self):
        rooms = []
        if not ROOM_FILE.exists():
            return rooms
        try:
            with ROOM_FILE.open("r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("//"):
                        continue
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) != len(ROOM_FIELDS):
                        continue
                    room = dict(zip(ROOM_FIELDS, parts))
                    if room.get("room_type", "").strip().lower() == "room_type":
                        continue
                    try:
                        room["price_per_night"] = float(room["price_per_night"])
                    except (ValueError, TypeError):
                        continue
                    room["room_type"] = str(room.get("room_type", "")).strip()
                    room["room_number"] = str(room.get("room_number", "")).strip()
                    room["status"] = str(room.get("status", "")).strip().title()
                    if room["room_type"] and room["room_number"]:
                        rooms.append(room)
        except OSError:
            return []
        return rooms

    def _ensure_booking_file(self):
        if not BOOKING_FILE.exists():
            self._write_booking_file([])

    def _write_booking_file(self, bookings):
        lines = ["# Caramel Hotel booking records (stored locally)", "|".join(BOOKING_FIELDS)]
        for booking in bookings:
            lines.append("|".join(self._safe_field(booking.get(field, "")) for field in BOOKING_FIELDS))
        try:
            BOOKING_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as error:
            messagebox.showerror("File error", f"Could not write booking.txt:\n{error}", parent=self)  

    def _read_bookings(self):
        bookings = []
        if not BOOKING_FILE.exists():
            return bookings
        try:
            with BOOKING_FILE.open("r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [part.strip() for part in line.split("|")]
                    if [part.lower() for part in parts] == list(BOOKING_FIELDS):
                        continue
                    # Ignore rows that do not match the current file format.
                    if len(parts) != len(BOOKING_FIELDS):
                        continue
                    bookings.append(dict(zip(BOOKING_FIELDS, parts)))
        except OSError:
            return []
        return bookings

    @staticmethod # Safely format a field value for writing to the booking file
    def _safe_field(value):
        return str(value).replace("|", "/").replace("\r", " ").replace("\n", " ").strip()

    def _append_booking(self, booking):
        row = "|".join(self._safe_field(booking.get(field, "")) for field in BOOKING_FIELDS)
        try:
            with BOOKING_FILE.open("a", encoding="utf-8") as file:
                file.write(row + "\n")
            return True
        except OSError as error:
            messagebox.showerror("File error", f"Could not save booking.txt:\n{error}", parent=self)
            return False

    # Room Image support
    def _room_image_path(self, room):
        filename = str(room.get("image_filename", "")).strip()
        if not filename:
            return None
        
        folders = (IMAGE_DIR, BASE_DIR)
        target = filename.casefold()
        for folder in folders:
            candidate = folder / filename
            if candidate.is_file():
                return candidate
            if folder.is_dir():
                try:
                    for path in folder.iterdir():
                        if path.is_file() and path.name.casefold() == target:
                            return path
                except OSError:
                    pass
        return None

    def _load_photo(self, room, size):
        # Get the image path for the room and load it as a PhotoImage, resizing it to the specified size.
        path = self._room_image_path(room)
        if path is None:
            return None
        try:
            from PIL import Image, ImageOps, ImageTk
            image = Image.open(path).convert("RGB")
            resampling = getattr(Image, "Resampling", Image)
            resample_filter = getattr(resampling, "LANCZOS", getattr(Image, "LANCZOS", 3))
            image = ImageOps.fit(image, size, method=resample_filter)
            return ImageTk.PhotoImage(image)
        except ImportError:
            # Tkinter's PhotoImage can display PNG/GIF but not usually JPEG.
            try:
                return tk.PhotoImage(file=str(path))
            except tk.TclError:
                return None
        except (OSError, ValueError, tk.TclError):
            return None

    # Page layout and widgets
    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Hotel.Treeview", background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT, rowheight=34, font=("Arial", 10), borderwidth=0)
        style.configure("Hotel.Treeview.Heading", background=NAVY, foreground=WHITE,
                        font=("Arial", 9, "bold"), padding=(8, 10))
        style.map("Hotel.Treeview", background=[("selected", LAVENDER)],
                  foreground=[("selected", WHITE)])
        style.configure("Hotel.TCombobox", padding=(7, 7), fieldbackground=WHITE,
                        background=PALE_BLUE, foreground=TEXT, arrowcolor=NAVY,
                        font=("Arial", 11))
        style.map("Hotel.TCombobox", fieldbackground=[("readonly", WHITE)],
                  selectbackground=[("readonly", PALE_BLUE)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("Hotel.TEntry", padding=(7, 7), font=("Arial", 11))
        style.configure("Hotel.TSpinbox", padding=(7, 7), font=("Arial", 11))
        
    def _build_shell(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=22, pady=(16, 8))
        title_area = tk.Frame(header, bg=BG)
        title_area.pack(side="left", fill="x", expand=True)
        tk.Label(title_area, text="ACCOMMODATION", bg=BG, fg=NAVY,
                 font=("Arial", 19, "bold")).pack(anchor="w")
        tk.Label(title_area, text="Find a room that feels like your own space.", bg=BG,
                 fg=MUTED, font=("Arial", 10)).pack(anchor="w", pady=(3, 0))

        navigation = tk.Frame(header, bg=BG)
        navigation.pack(side="right", anchor="e", pady=(4, 0))
        self.gallery_button = self._make_button(navigation, "Browse Rooms", self.show_gallery,
                                                primary=True, padx=14, pady=9)
        self.gallery_button.pack(side="left", padx=(0, 7))
        self.history_button = self._make_button(navigation, "Booking History", self.show_history,
                                                primary=False, padx=14, pady=9)
        self.history_button.pack(side="left")

        self.content_area = tk.Frame(self, bg=BG)
        self.content_area.pack(fill="both", expand=True, padx=18, pady=(4, 16))

    def _make_button(self, parent, text, command, primary=True, **kwargs):
        bg = NAVY if primary else PALE_BLUE
        fg = WHITE if primary else NAVY
        active_bg = LAVENDER if primary else BLUE_GREY
        return tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=active_bg, activeforeground=WHITE if primary else TEXT,
            relief="flat", borderwidth=0, cursor="hand2", font=("Arial", 9, "bold"),
            highlightthickness=0, padx=kwargs.get("padx", 12), pady=kwargs.get("pady", 7)
        )

    def _clear_content(self):
        for child in self.content_area.winfo_children():
            child.destroy()
        self.photo_refs = []
        self.detail_photo = None
        self._current_canvas = None
        self.payment_detail_vars = {}
        self.payment_detail_frame = None
        self.booking_form_canvas = None
        self.payment_var = None
        self.quantity_spinbox = None

    def _set_navigation_state(self, selected):
        if selected == "gallery":
            self.gallery_button.config(bg=NAVY, fg=WHITE)
            self.history_button.config(bg=NAVY, fg=WHITE)
        else:
            self.gallery_button.config(bg=PALE_BLUE, fg=NAVY)
            self.history_button.config(bg=PALE_BLUE, fg=NAVY)

    def _show_missing_rooms_message(self):
        if self.winfo_exists():
            messagebox.showwarning(
                "Room data not found",
                "No room records were found. Put a valid room.txt in the same folder as accommodation.py.",
                parent=self,
            )

    # Room gallery - photo are clickable
    def show_gallery(self):
        self._clear_content()
        self._set_navigation_state("gallery")

        intro = tk.Frame(self.content_area, bg=BG)
        intro.pack(fill="x", padx=4, pady=(0, 10))
        tk.Label(intro, text="Choose your room", bg=BG, fg=TEXT,
                 font=("Arial", 15, "bold")).pack(side="left")
        tk.Label(intro, text=f"{len(self.rooms)} rooms listed · Click a photo to view details",
                 bg=BG, fg=MUTED, font=("Arial", 9)).pack(side="right", pady=(4, 0))

        outer = tk.Frame(self.content_area, bg=BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        card_grid = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window((0, 0), window=card_grid, anchor="nw")
        card_grid.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.bind("<MouseWheel>", self._on_mousewheel)
        canvas.bind("<Button-4>", lambda event: self._on_linux_mousewheel(event, -1))
        canvas.bind("<Button-5>", lambda event: self._on_linux_mousewheel(event, 1))
        self._current_canvas = canvas

        # Three columns at the normal window width; cards expand with the window
        for column in range(3):
            card_grid.grid_columnconfigure(column, weight=1, uniform="room_cards")
        for index, room in enumerate(self.rooms):
            row, column = divmod(index, 3)
            self._build_room_card(card_grid, room, row, column)

    def _on_mousewheel(self, event):
        if self._current_canvas is None:
            return
        try:
            if self._current_canvas.winfo_exists():
                delta = int(-1 * (event.delta / 120))
                if delta == 0 and event.delta:
                    delta = -1 if event.delta > 0 else 1
                self._current_canvas.yview_scroll(delta, "units")
        except tk.TclError:
            pass

    def _on_linux_mousewheel(self, _event, direction):
        if self._current_canvas is not None:
            try:
                if self._current_canvas.winfo_exists():
                    self._current_canvas.yview_scroll(direction, "units")
            except tk.TclError:
                pass

    def _build_room_card(self, parent, room, row, column):
        shell = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        shell.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card = tk.Frame(shell, bg=WHITE)
        card.pack(fill="both", expand=True)

        image_holder = tk.Frame(card, bg=PALE_BLUE, height=155, cursor="hand2")
        image_holder.pack(fill="x")
        image_holder.pack_propagate(False)
        photo = self._load_photo(room, (330, 155))
        if photo is not None:
            self.photo_refs.append(photo)
            image_widget = tk.Label(image_holder, image=photo, bg=PALE_BLUE, cursor="hand2", bd=0)
            image_widget.pack(fill="both", expand=True)
        else:
            image_widget = tk.Frame(image_holder, bg=PALE_BLUE, cursor="hand2")
            image_widget.pack(fill="both", expand=True)
            tk.Label(image_widget, text="✦", bg=PALE_BLUE, fg=SLATE_BLUE,
                     font=("Arial", 28, "bold")).pack(pady=(22, 2))
            tk.Label(image_widget, text="ROOM PHOTO", bg=PALE_BLUE, fg=NAVY,
                     font=("Arial", 9, "bold")).pack()
            tk.Label(image_widget, text="Add image to room_images", bg=PALE_BLUE,
                     fg=MUTED, font=("Arial", 8)).pack(pady=(2, 0))

        body = tk.Frame(card, bg=WHITE, padx=13, pady=11)
        body.pack(fill="both", expand=True)
        top_line = tk.Frame(body, bg=WHITE)
        top_line.pack(fill="x")
        tk.Label(top_line, text=room["room_type"], bg=WHITE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        status = room["status"].upper()
        tk.Label(top_line, text=status,
                 bg="#E7EEF4" if status == "AVAILABLE" else "#F0E7E7",
                 fg=NAVY if status == "AVAILABLE" else "#8B5C64",
                 font=("Arial", 7, "bold"), padx=6, pady=4).pack(side="right", padx=(5, 0))
        features = self._feature_list(room)
        short_features = "  ·  ".join(features[:3]) if features else "Room features on details page"
        tk.Label(body, text=short_features, bg=WHITE, fg=MUTED, font=("Arial", 8),
                 wraplength=310, justify="left", anchor="w", height=2).pack(anchor="w", fill="x")

        bottom = tk.Frame(body, bg=WHITE)
        bottom.pack(fill="x", pady=(9, 0))
        tk.Label(bottom, text=f"RM{room['price_per_night']:.2f}", bg=WHITE, fg=NAVY,
                 font=("Arial", 15, "bold")).pack(side="left")
        tk.Label(bottom, text="/ night", bg=WHITE, fg=MUTED,
                 font=("Arial", 8)).pack(side="left", padx=(3, 0), pady=(5, 0))
        details_link = tk.Label(bottom, text="View details  ›", bg=WHITE, fg=NAVY,
                                font=("Arial", 9, "bold"), cursor="hand2")
        details_link.pack(side="right", pady=(3, 0))
        for widget in (shell, card, image_holder, image_widget, body, top_line):
            widget.bind("<Button-1>", lambda _event, selected=room: self.show_details(selected))
        for child in image_widget.winfo_children():
            child.bind("<Button-1>", lambda _event, selected=room: self.show_details(selected))
        details_link.bind("<Button-1>", lambda _event, selected=room: self.show_details(selected))
        for child in body.winfo_children():
            if child is not bottom:
                child.bind("<Button-1>", lambda _event, selected=room: self.show_details(selected))

    @staticmethod
    def _feature_list(room):
        return [item.strip() for item in str(room.get("features", "")).split(",") if item.strip()]

    @staticmethod
    def _room_numbers_in_booking(booking):
        """Return the physical room numbers stored in a booking record.

        Multiple rooms are stored comma-separated in the existing room_number
        field, for example "101, 150". Room numbers are used internally only;
        they are not shown on the guest-facing pages.
        """
        value = str(booking.get("room_number", "")).strip()
        return {number.strip() for number in value.split(",") if number.strip()}

    def _is_reserved_for_dates(self, room_number, check_in, check_out, bookings=None):
        if bookings is None:
            bookings = self._read_bookings()
        for booking in bookings:
            status = str(booking.get("status", "")).strip().lower()
            if status in ("cancelled", "canceled", "rejected"):
                continue
            if room_number not in self._room_numbers_in_booking(booking):
                continue
            try:
                booked_in = datetime.strptime(booking["check_in"], "%Y-%m-%d").date()
                booked_out = datetime.strptime(booking["check_out"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            # A booking conflicts only when the date ranges overlap.
            if check_in < booked_out and check_out > booked_in:
                return True
        return False

    def _available_rooms_for_dates(self, selected_room, check_in, check_out):
        bookings = self._read_bookings()
        selected_type = str(selected_room.get("room_type", "")).strip().casefold()
        available = []
        for room in self.rooms:
            if str(room.get("room_type", "")).strip().casefold() != selected_type:
                continue
            if str(room.get("status", "")).strip().lower() != "available":
                continue
            if not self._is_reserved_for_dates(room["room_number"], check_in, check_out, bookings):
                available.append(room)
        # Prefer the room the guest clicked, followed by the other matching rooms.
        chosen_number = str(selected_room.get("room_number", ""))
        available.sort(key=lambda item: (str(item.get("room_number", "")) != chosen_number,
                                         str(item.get("room_number", ""))))
        return available

    # Separate room details page
    def show_details(self, room):
        self.selected_room = room
        self._clear_content()
        self._set_navigation_state("gallery")

        top = tk.Frame(self.content_area, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        self._make_button(top, "‹  Back to rooms", self.show_gallery, primary=False).pack(side="left")
        tk.Label(top, text="ROOM DETAILS", bg=BG, fg=NAVY,
                 font=("Arial", 10, "bold")).pack(side="right", pady=7)

        card_shell = tk.Frame(self.content_area, bg=BORDER, padx=1, pady=1)
        card_shell.pack(fill="both", expand=True)
        card = tk.Frame(card_shell, bg=WHITE, padx=18, pady=17)
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(0, weight=5, uniform="detail")
        card.grid_columnconfigure(1, weight=6, uniform="detail")
        card.grid_rowconfigure(0, weight=1)

        left = tk.Frame(card, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        image_panel = tk.Frame(left, bg=PALE_BLUE, height=290)
        image_panel.pack(fill="x")
        image_panel.pack_propagate(False)
        self.detail_photo = self._load_photo(room, (460, 290))
        if self.detail_photo:
            tk.Label(image_panel, image=self.detail_photo, bg=PALE_BLUE, bd=0).pack(fill="both", expand=True)
        else:
            tk.Label(image_panel, text="✦", bg=PALE_BLUE, fg=SLATE_BLUE,
                     font=("Arial", 42, "bold")).pack(pady=(75, 6))
            tk.Label(image_panel, text="ROOM PHOTO", bg=PALE_BLUE, fg=NAVY,
                     font=("Arial", 11, "bold")).pack()
            tk.Label(image_panel, text="Put the photo in room_images", bg=PALE_BLUE,
                     fg=MUTED, font=("Arial", 8), wraplength=380).pack(pady=5)
        tk.Label(left, text=f"Status: {room['status']}",
                 bg=WHITE, fg=MUTED, font=("Arial", 10)).pack(anchor="w", pady=(10, 0))
        description = str(room.get("description", "")).strip()
        if description:
            tk.Label(left, text=description, bg=WHITE, fg=MUTED, font=("Arial", 9),
                     wraplength=420, justify="left").pack(anchor="w", pady=(5, 0))
            
        right = tk.Frame(card, bg=WHITE)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text=room["room_type"], bg=WHITE, fg=TEXT,
                 font=("Arial", 20, "bold"), wraplength=450, justify="left").pack(anchor="w")
        price_row = tk.Frame(right, bg=WHITE)
        price_row.pack(fill="x", pady=(7, 4))
        tk.Label(price_row, text=f"RM{room['price_per_night']:.2f}", bg=WHITE, fg=NAVY,
                 font=("Arial", 19, "bold")).pack(side="left")
        tk.Label(price_row, text="per room, per night", bg=WHITE, fg=MUTED,
                 font=("Arial", 9)).pack(side="left", padx=(6, 0), pady=(7, 0))
        tk.Label(right, text="Your room number will be provided when you check in.",
                 bg="#EAF0F4", fg=NAVY, font=("Arial", 9, "bold"), padx=9, pady=8,
                 anchor="w").pack(fill="x", pady=(2, 12))
        tk.Label(right, text="ROOM FEATURES", bg=WHITE, fg=NAVY,
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 6))
        features_outer = tk.Frame(right, bg=WHITE)
        features_outer.pack(fill="both", expand=True)
        features_canvas = tk.Canvas(features_outer, bg=WHITE, highlightthickness=0, height=210)
        features_scroll = ttk.Scrollbar(features_outer, orient="vertical", command=features_canvas.yview)
        features_canvas.configure(yscrollcommand=features_scroll.set)
        features_scroll.pack(side="right", fill="y")
        features_canvas.pack(side="left", fill="both", expand=True)
        features_inner = tk.Frame(features_canvas, bg=WHITE)
        features_window = features_canvas.create_window((0, 0), window=features_inner, anchor="nw")
        features_inner.bind("<Configure>", lambda _event: features_canvas.configure(scrollregion=features_canvas.bbox("all")))
        features_canvas.bind("<Configure>", lambda event: features_canvas.itemconfigure(features_window, width=event.width))
        for feature in self._feature_list(room):
            line = tk.Frame(features_inner, bg=WHITE)
            line.pack(fill="x", anchor="w", pady=2)
            tk.Label(line, text="✓", bg=WHITE, fg=SLATE_BLUE,
                     font=("Arial", 9, "bold")).pack(side="left", padx=(1, 8))
            tk.Label(line, text=feature, bg=WHITE, fg=TEXT, font=("Arial", 9),
                     wraplength=390, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        action = tk.Frame(card, bg=WHITE)
        action.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        tk.Label(action, text="Select your dates and room quantity on the next page.",
                 bg=WHITE, fg=MUTED, font=("Arial", 9)).pack(side="left")
        self._make_button(action, "Book this room  →", lambda selected=room: self.show_booking_form(selected),
                          primary=True, padx=18, pady=10).pack(side="right")
        self._make_button(action, "Back to rooms", self.show_gallery,
                          primary=False, padx=15, pady=10).pack(side="right", padx=(0, 8))

    # Booking form
    def show_booking_form(self, room):
        self.selected_room = room
        self._clear_content()
        self._set_navigation_state("gallery")

        top = tk.Frame(self.content_area, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        self._make_button(top, "‹  Back to room details",
                          lambda selected=room: self.show_details(selected), primary=False).pack(side="left")
        tk.Label(top, text="COMPLETE YOUR BOOKING", bg=BG, fg=NAVY,
                 font=("Arial", 10, "bold")).pack(side="right", pady=7)

        body_shell = tk.Frame(self.content_area, bg=BORDER, padx=1, pady=1)
        body_shell.pack(fill="both", expand=True)
        body = tk.Frame(body_shell, bg=WHITE, padx=18, pady=14)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=5, uniform="booking_columns")
        body.grid_columnconfigure(1, weight=6, uniform="booking_columns")
        body.grid_rowconfigure(0, weight=1)

        # Left side: selected room summary
        left = tk.Frame(body, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        tk.Label(left, text="YOUR SELECTED ROOM", bg=WHITE, fg=NAVY,
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 10))
        img = tk.Frame(left, bg=PALE_BLUE, height=175)
        img.pack(fill="x")
        img.pack_propagate(False)
        photo = self._load_photo(room, (390, 175))
        if photo:
            self.photo_refs.append(photo)
            tk.Label(img, image=photo, bg=PALE_BLUE, bd=0).pack(fill="both", expand=True)
        else:
            tk.Label(img, text="✦", bg=PALE_BLUE, fg=SLATE_BLUE,
                     font=("Arial", 30, "bold")).pack(pady=(34, 3))
            tk.Label(img, text="ROOM PHOTO", bg=PALE_BLUE, fg=NAVY,
                     font=("Arial", 9, "bold")).pack()
        tk.Label(left, text=room["room_type"], bg=WHITE, fg=TEXT,
                 font=("Arial", 15, "bold"), wraplength=400).pack(anchor="w", pady=(10, 2))
        tk.Label(left, text=f"Status: {room['status']}",
                 bg=WHITE, fg=MUTED, font=("Arial", 9)).pack(anchor="w")
        tk.Label(left, text=f"RM{room['price_per_night']:.2f} / room / night", bg=WHITE, fg=NAVY,
                 font=("Arial", 15, "bold")).pack(anchor="w", pady=(10, 3))
        tk.Label(left, text="Choose how many rooms you need. Your room number will be provided when you check in.",
                 bg=WHITE, fg=MUTED, font=("Arial", 9), wraplength=400, justify="left").pack(anchor="w", pady=(4, 8))
        self.availability_var = tk.StringVar(value="Availability is checked for your selected dates.")
        tk.Label(left, textvariable=self.availability_var, bg=PALE_CARD, fg=TEXT,
                 font=("Arial", 9), wraplength=400, justify="left", padx=10, pady=9).pack(fill="x", pady=(4, 0))
        tk.Label(left, text="Demo only: do not enter real card details. Payment details are not saved.",
                 bg=WHITE, fg="#8B5C64", font=("Arial", 8), wraplength=400,
                 justify="left").pack(anchor="w", pady=(9, 0))

        # Right side: scrollable form
        right = tk.Frame(body, bg=WHITE)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        tk.Label(right, text="Guest information", bg=WHITE, fg=NAVY,
                 font=("Arial", 13, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 7))

        form_outer = tk.Frame(right, bg=WHITE)
        form_outer.grid(row=1, column=0, sticky="nsew")
        form_outer.grid_rowconfigure(0, weight=1)
        form_outer.grid_columnconfigure(0, weight=1)
        self.booking_form_canvas = tk.Canvas(form_outer, bg=WHITE, highlightthickness=0, bd=0)
        form_scroll = ttk.Scrollbar(form_outer, orient="vertical", command=self.booking_form_canvas.yview)
        self.booking_form_canvas.configure(yscrollcommand=form_scroll.set)
        self.booking_form_canvas.grid(row=0, column=0, sticky="nsew")
        form_scroll.grid(row=0, column=1, sticky="ns")
        form = tk.Frame(self.booking_form_canvas, bg=WHITE)
        self.payment_form_inner = form
        form_window = self.booking_form_canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _event: self.booking_form_canvas.configure(
            scrollregion=self.booking_form_canvas.bbox("all")))
        self.booking_form_canvas.bind("<Configure>", lambda event: self.booking_form_canvas.itemconfigure(
            form_window, width=event.width))
        self.booking_form_canvas.bind("<MouseWheel>", self._on_booking_form_mousewheel)

        form.grid_columnconfigure(1, weight=1)
        self.form_vars = {}
        fields = [
            ("name", "Full name", ""),
            ("email", "Email address", ""),
            ("hp", "Phone number", ""),
            ("ic", "IC / Passport", ""),
            ("check_in", "Check-in (YYYY-MM-DD)", date.today().isoformat()),
            ("check_out", "Check-out (YYYY-MM-DD)", (date.today() + timedelta(days=1)).isoformat()),
            ("adults", "Adults", "1"),
            ("children", "Children", "0"),
            ("amount_of_room", "Amount of rooms", "1"),
            ("special_requests", "Special requests (optional)", ""),
            ("promo_code", "Promo code (optional)", ""),
        ]
        row = 0
        for key, label_text, default in fields:
            tk.Label(form, text=label_text, bg=WHITE, fg=TEXT,
                     font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            variable = tk.StringVar(value=default)
            self.form_vars[key] = variable
            if key == "amount_of_room":
                self.quantity_var = variable
                self.quantity_spinbox = ttk.Spinbox(
                    form, from_=1, to=99, textvariable=variable, width=8,
                    style="Hotel.TSpinbox", font=("Arial", 11), command=self._refresh_booking_total
                )
                self.quantity_spinbox.grid(row=row, column=1, sticky="ew", pady=5)
                self.quantity_spinbox.bind("<KeyRelease>", lambda _event: self._refresh_booking_total())
            else:
                entry = ttk.Entry(form, textvariable=variable, style="Hotel.TEntry", font=("Arial", 11))
                entry.grid(row=row, column=1, sticky="ew", pady=5, ipady=2)
            row += 1

        tk.Label(form, text="Payment method", bg=WHITE, fg=TEXT,
                 font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        self.payment_var = tk.StringVar(value="")
        self.payment_combo = ttk.Combobox(form, textvariable=self.payment_var,
                                          values=PAYMENT_METHODS, state="readonly",
                                          style="Hotel.TCombobox")
        self.payment_combo.grid(row=row, column=1, sticky="ew", pady=5)
        self.payment_combo.bind("<<ComboboxSelected>>", self._on_payment_method_change)
        row += 1
        self.payment_detail_frame = tk.Frame(form, bg=PALE_CARD, padx=10, pady=8)
        self.payment_detail_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        tk.Label(self.payment_detail_frame, text="Choose a payment method to enter its demo details.",
                 bg=PALE_CARD, fg=MUTED, font=("Arial", 9), wraplength=430,
                 justify="left").pack(anchor="w")

        # Persistent total and action buttons remain visible below the scrolling form.
        self.total_var = tk.StringVar(value="Estimated total: RM0.00")
        tk.Label(right, textvariable=self.total_var, bg=LAVENDER, fg=WHITE,
                 font=("Arial", 11, "bold"), padx=12, pady=10, anchor="w").grid(
                     row=2, column=0, sticky="ew", pady=(9, 9))
        buttons = tk.Frame(right, bg=WHITE)
        buttons.grid(row=3, column=0, sticky="ew")
        self._make_button(buttons, "Confirm booking", self._handle_confirm_booking,
                          primary=True, padx=14, pady=9).pack(side="right")
        self._make_button(buttons, "Cancel", lambda selected=room: self.show_details(selected),
                          primary=False, padx=14, pady=9).pack(side="right", padx=(0, 8))

        for key in ("check_in", "check_out", "amount_of_room"):
            self.form_vars[key].trace_add("write", lambda *_args: self._refresh_booking_total())
        self._refresh_booking_total()

    def _on_booking_form_mousewheel(self, event):
        if self.booking_form_canvas is not None:
            try:
                self.booking_form_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, ZeroDivisionError):
                pass

    def _on_payment_method_change(self, _event=None):
        if self.payment_detail_frame is None:
            return
        for child in self.payment_detail_frame.winfo_children():
            child.destroy()
        self.payment_detail_vars = {}
        method = self.payment_var.get().strip() if self.payment_var else ""
        if method == "Credit/Debit Card":
            tk.Label(self.payment_detail_frame, text="Card payment details (demo only)",
                     bg=PALE_CARD, fg=NAVY, font=("Arial", 9, "bold")).grid(
                         row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
            payment_fields = [
                ("cardholder", "Cardholder name", ""),
                ("card_number", "Card number (test only)", ""),
                ("expiry", "Expiry (MM/YY)", ""),
                ("cvv", "Security code (test only)", ""),
            ]
            self.payment_detail_frame.grid_columnconfigure(1, weight=1)
            for row, (key, label_text, default) in enumerate(payment_fields, start=1):
                tk.Label(self.payment_detail_frame, text=label_text, bg=PALE_CARD, fg=TEXT,
                         font=("Arial", 9)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
                variable = tk.StringVar(value=default)
                self.payment_detail_vars[key] = variable
                ttk.Entry(self.payment_detail_frame, textvariable=variable,
                          style="Hotel.TEntry", font=("Arial", 11), show="*" if key == "cvv" else "").grid(
                              row=row, column=1, sticky="ew", pady=4)
        elif method == "E-wallet":
            tk.Label(self.payment_detail_frame, text="E-wallet details (demo only)",
                     bg=PALE_CARD, fg=NAVY, font=("Arial", 9, "bold")).grid(
                         row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
            tk.Label(self.payment_detail_frame, text="E-wallet provider", bg=PALE_CARD, fg=TEXT,
                     font=("Arial", 9)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
            self.wallet_provider_var = tk.StringVar(value=EWALLET_PROVIDERS[0])
            ttk.Combobox(self.payment_detail_frame, textvariable=self.wallet_provider_var,
                         values=EWALLET_PROVIDERS, state="readonly", style="Hotel.TCombobox").grid(
                             row=1, column=1, sticky="ew", pady=4)
            self.payment_detail_vars["wallet_account"] = tk.StringVar(value="")
            tk.Label(self.payment_detail_frame, text="Wallet phone/account", bg=PALE_CARD, fg=TEXT,
                     font=("Arial", 9)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)
            ttk.Entry(self.payment_detail_frame, textvariable=self.payment_detail_vars["wallet_account"],
                      style="Hotel.TEntry", font=("Arial", 11)).grid(row=2, column=1, sticky="ew", pady=4)
            self.payment_detail_frame.grid_columnconfigure(1, weight=1)
        else:
            tk.Label(self.payment_detail_frame, text="Select Credit/Debit Card or E-wallet. Cash and online banking are not available.",
                     bg=PALE_CARD, fg=MUTED, font=("Arial", 9), wraplength=430,
                     justify="left").grid(row=0, column=0, sticky="w")
        if self.payment_form_inner is not None and self.booking_form_canvas is not None:
            self.payment_form_inner.update_idletasks()
            self.booking_form_canvas.configure(scrollregion=self.booking_form_canvas.bbox("all"))
    def _validate_payment_details(self):
        method = self.payment_var.get().strip() if self.payment_var else ""
        if method not in PAYMENT_METHODS:
            messagebox.showerror("Payment method required", "Choose Credit/Debit Card or E-wallet.", parent=self)
            return False
        if method == "Credit/Debit Card":
            cardholder = self.payment_detail_vars.get("cardholder", tk.StringVar(value="")).get().strip()
            card_number = self.payment_detail_vars.get("card_number", tk.StringVar(value="")).get().replace(" ", "").replace("-", "")
            expiry = self.payment_detail_vars.get("expiry", tk.StringVar(value="")).get().strip()
            cvv = self.payment_detail_vars.get("cvv", tk.StringVar(value="")).get().strip()
            if not cardholder or not card_number.isdigit() or not (13 <= len(card_number) <= 19):
                messagebox.showerror("Check card details", "For this demo, enter a cardholder name and a test card number containing 13–19 digits.", parent=self)
                return False
            if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", expiry):
                messagebox.showerror("Check expiry date", "Enter expiry in MM/YY format, for example 08/28.", parent=self)
                return False
            if not re.fullmatch(r"\d{3,4}", cvv):
                messagebox.showerror("Check security code", "For this demo, enter a 3- or 4-digit test security code.", parent=self)
                return False
        elif method == "E-wallet":
            account = self.payment_detail_vars.get("wallet_account", tk.StringVar(value="")).get().strip()
            if not account:
                messagebox.showerror("E-wallet details required", "Enter a demo wallet phone/account value.", parent=self)
                return False
        return True

    # Dates, quantity and estimates
    def _parse_dates(self, show_errors=True):
        try:
            check_in = datetime.strptime(self.form_vars["check_in"].get().strip(), "%Y-%m-%d").date()
            check_out = datetime.strptime(self.form_vars["check_out"].get().strip(), "%Y-%m-%d").date()
        except (ValueError, KeyError):
            if show_errors:
                messagebox.showerror("Invalid dates", "Enter dates as YYYY-MM-DD, for example 2026-10-26.", parent=self)
            return None
        if check_in < date.today():
            if show_errors:
                messagebox.showerror("Invalid check-in", "Check-in cannot be earlier than today.", parent=self)
            return None
        if check_out <= check_in:
            if show_errors:
                messagebox.showerror("Invalid check-out", "Check-out must be later than check-in.", parent=self)
            return None
        return check_in, check_out

    def _refresh_booking_total(self):
        if self.total_var is None or self.selected_room is None:
            return
        dates = self._parse_dates(show_errors=False)
        if dates is None:
            self.total_var.set("Estimated total: check dates")
            if self.availability_var is not None:
                self.availability_var.set("Enter valid check-in/check-out dates to check room availability.")
            return
        check_in, check_out = dates
        nights = (check_out - check_in).days
        try:
            quantity = int(self.quantity_var.get().strip())
            if quantity < 1:
                raise ValueError
        except (ValueError, AttributeError):
            self.total_var.set("Estimated total: enter room quantity")
            return
        available_rooms = self._available_rooms_for_dates(self.selected_room, check_in, check_out)
        available_count = len(available_rooms)
        if self.availability_var is not None:
            self.availability_var.set(
                f"{available_count} room(s) of this type are available for your selected dates."
            )
        total = self.selected_room["price_per_night"] * nights * quantity
        self.total_var.set(f"Estimated total: RM{total:.2f}  ·  {nights} night(s)  ·  {quantity} room(s)")

    def _handle_confirm_booking(self):
        """Run booking confirmation and show unexpected errors to the user."""
        try:
            self._confirm_booking()
        except Exception as error:
            # Keep the GUI responsive and make unexpected issues visible rather
            # than leaving the user unsure why the button did nothing.
            messagebox.showerror(
                "Booking could not be completed",
                "Something unexpected stopped the booking from being saved.\n\n"
                f"Details: {error}\n\n"
                "Please check your room.txt and booking.txt files, then try again.",
                parent=self.winfo_toplevel(),
            )

    # Confirm booking: reserve physical room inventory internally, do not show numbers of guests
    def _confirm_booking(self):
        room = self.selected_room
        if room is None:
            messagebox.showwarning("Choose a room", "Please select a room first.", parent=self)
            return
        dates = self._parse_dates(show_errors=True)
        if dates is None:
            return
        check_in, check_out = dates
        try:
            quantity = int(self.form_vars["amount_of_room"].get().strip())
            if quantity < 1:
                raise ValueError
        except (ValueError, KeyError):
            messagebox.showerror("Invalid room quantity", "Enter a whole number of rooms (at least 1).", parent=self)
            return
        available_rooms = self._available_rooms_for_dates(room, check_in, check_out)
        if len(available_rooms) < quantity:
            messagebox.showerror(
                "Not enough rooms available",
                f"You requested {quantity} room(s), but only {len(available_rooms)} room(s) of this type "
                "are available for these dates. Please reduce the quantity or choose different dates.",
                parent=self,
            )
            return

        name = self.form_vars["name"].get().strip()
        email = self.form_vars["email"].get().strip()
        phone = self.form_vars["hp"].get().strip()
        ic = self.form_vars["ic"].get().strip()
        if not all((name, email, phone, ic)):
            messagebox.showerror("Missing information", "Complete the name, email, phone and IC/passport fields.", parent=self)
            return
        if "@" not in email or "." not in email.split("@")[-1]:
            messagebox.showerror("Invalid email", "Please enter a valid email address.", parent=self)
            return
        try:
            adults = int(self.form_vars["adults"].get().strip())
            children = int(self.form_vars["children"].get().strip())
            if adults < 1 or children < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid guest numbers", "Adults must be at least 1 and children cannot be negative.", parent=self)
            return
        if not self._validate_payment_details():
            return

        nights = (check_out - check_in).days
        # Assign distinct physical room numbers; store several numbers comma-separated
        # in the existing room_number field, and the count in amount_of_room.
        assigned_rooms = available_rooms[:quantity]
        room_numbers = [str(item["room_number"]).strip() for item in assigned_rooms]
        total = nights * room["price_per_night"] * quantity
        booking = {
            "name": name,
            "email": email,
            "hp": phone,
            "ic": ic,
            "room_type": room["room_type"],
            "room_number": ", ".join(room_numbers),
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "amount_of_room": str(quantity),
            "adults": str(adults),
            "children": str(children),
            "special_requests": self.form_vars["special_requests"].get().strip(),
            "promo_code": self.form_vars["promo_code"].get().strip(),
            "total_price": f"{total:.2f}",
            "payment_method": self.payment_var.get().strip(),
            "status": "Confirmed",
        }
        if not self._append_booking(booking):
            return
        self.bookings = self._read_bookings()
        # Do not display the assigned room number until check-in.
        # Payment details are never saved in booking.txt.
        messagebox.showinfo(
            "Booking confirmed",
            f"Your booking has been saved on this device.\n\n"
            f"Room type: {room['room_type']}\n"
            "Your room number will be provided when you check in.\n"
            f"Dates: {check_in.isoformat()} to {check_out.isoformat()}\n"
            f"Rooms: {quantity}\nNights: {nights}\nTotal: RM{total:.2f}\n\n"
            "Payment detail fields are not stored in booking.txt.",
            parent=self,
        )
        self.show_history()

        # Booking history
    def show_history(self):
        self._clear_content()
        self._set_navigation_state("history")
        self.bookings = self._read_bookings()

        top = tk.Frame(self.content_area, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Booking history", bg=BG, fg=TEXT,
                 font=("Arial", 15, "bold")).pack(side="left")
        tk.Label(top, text=f"{len(self.bookings)} saved booking(s) on this device", bg=BG,
                 fg=MUTED, font=("Arial", 9)).pack(side="left", padx=(12, 0), pady=(4, 0))
        self._make_button(top, "Refresh", self.show_history, primary=False).pack(side="right")

        table_shell = tk.Frame(self.content_area, bg=BORDER, padx=1, pady=1)
        table_shell.pack(fill="both", expand=True)
        table_frame = tk.Frame(table_shell, bg=WHITE)
        table_frame.pack(fill="both", expand=True)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "room_type", "check_in", "check_out", "rooms",
                   "adults", "children", "total", "payment", "status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Hotel.Treeview")
        self.booking_tree = tree
        headers = {
            "name": "Guest name", "room_type": "Room type",
            "check_in": "Check-in", "check_out": "Check-out", "rooms": "Rooms",
            "adults": "Adults", "children": "Children", "total": "Total price",
            "payment": "Payment method", "status": "Status",
        }
        widths = {"name": 145, "room_type": 170, "check_in": 110,
                  "check_out": 110, "rooms": 70, "adults": 70, "children": 75,
                  "total": 110, "payment": 135, "status": 100}
        for col in columns:
            tree.heading(col, text=headers[col])
            tree.column(col, width=widths[col], minwidth=65,
                        anchor="w" if col in ("name", "room_type") else "center",
                        stretch=True)
        ybar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        tree.tag_configure("even", background=PALE_CARD)
        tree.tag_configure("odd", background=WHITE)

        for index, booking in enumerate(self.bookings):
            try:
                total = f"RM{float(booking.get('total_price', '0') or 0):.2f}"
            except (ValueError, TypeError):
                total = booking.get("total_price", "")
            tree.insert("", "end", values=(
                booking.get("name", ""),
                booking.get("room_type", ""),
                booking.get("check_in", ""),
                booking.get("check_out", ""),
                booking.get("amount_of_room", "1"),
                booking.get("adults", ""),
                booking.get("children", ""),
                total,
                booking.get("payment_method", ""),
                booking.get("status", ""),
            ), tags=("even" if index % 2 == 0 else "odd",))

        if not self.bookings:
            empty_state = tk.Frame(table_frame, bg=WHITE, padx=20, pady=20)
            empty_state.place(relx=0.5, rely=0.48, anchor="center")
            tk.Label(empty_state, text="No bookings yet", bg=WHITE, fg=NAVY,
                     font=("Arial", 14, "bold")).pack(pady=(0, 5))
            tk.Label(empty_state, text="Your confirmed bookings will be saved to booking.txt and appear here.",
                     bg=WHITE, fg=MUTED, font=("Arial", 10)).pack()


# Run this file directly to test the accommodation page by itself.
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Caramel Hotel - Accommodation")
    root.geometry("1180x780")
    root.minsize(980, 640)
    page = AccommodationPage(root)
    page.pack(fill="both", expand=True)
    root.mainloop()