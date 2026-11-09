import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from booking_manager import BookingManager

# Colours used by the accommodation pages.
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

PAYMENT_METHODS = ("Credit/Debit Card", "E-wallet")
EWALLET_PROVIDERS = ("Touch 'n Go eWallet", "GrabPay", "Boosts", "ShopeePay")

class AccommodationPage(tk.Frame):

    # Set up the Accommodation page and display the room gallery.
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.services = BookingManager(self)
        self.services.ensure_booking_file()
        self.rooms = self.services.read_rooms()
        self.bookings = self.services.read_bookings()
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
        self._scroll_targets = [] # Canvases and tables that support mouse-wheel scrolling
        self._mousewheel_binding_ids = []

        # Listen for the mouse wheel anywhere inside this page, including over
        # labels, entry fields, room cards, feature text and scrollbars.
        wheel_bindings = (
            ("<MouseWheel>", self.services.on_mousewheel),
            ("<Button-4>", lambda event: self.services.on_linux_mousewheel(event, -1)),
            ("<Button-5>", lambda event: self.services.on_linux_mousewheel(event, 1)),
        )
        for sequence, callback in wheel_bindings:
            binding_id = self.bind_all(sequence, callback, add="+")
            self._mousewheel_binding_ids.append((sequence, binding_id))

        self._setup_styles() # Sets up the styles for the widgets
        self._build_shell() # Creates the main layout of the page
        self.show_gallery() # Displays the gallery of available rooms
        if not self.rooms:
            self.after(200, self._show_missing_rooms_message)

    # Remove the mouse-wheel events when the Accommodation page is closed.
    def destroy(self):
        # Remove this page's global mouse-wheel bindings when the page closes.
        for sequence, binding_id in getattr(self, "_mousewheel_binding_ids", []):
            if binding_id:
                try:
                    self._root()._unbind(("bind", "all", sequence), binding_id)
                except (tk.TclError, AttributeError):
                    pass
        self._mousewheel_binding_ids = []
        super().destroy()

    # Set the appearance of the tables, entry boxes and dropdown lists.
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

    # Create the Accommodation heading, page buttons and content area.
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

    # Create a button using the Caramel Hotel colour palette.
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

    # Clear the current Accommodation screen before showing another one.
    def _clear_content(self):
        for child in self.content_area.winfo_children():
            child.destroy()
        self.photo_refs = []
        self.detail_photo = None
        self._scroll_targets = []
        self.payment_detail_vars = {}
        self.payment_detail_frame = None
        self.booking_form_canvas = None
        self.payment_var = None
        self.quantity_spinbox = None

    # Highlight the selected Accommodation page button.
    def _set_navigation_state(self, selected):
        if selected == "gallery":
            self.gallery_button.config(bg=NAVY, fg=WHITE)
            self.history_button.config(bg=NAVY, fg=WHITE)
        else:
            self.gallery_button.config(bg=PALE_BLUE, fg=NAVY)
            self.history_button.config(bg=PALE_BLUE, fg=NAVY)

    # Show a warning when room.txt does not contain room records.
    def _show_missing_rooms_message(self):
        if self.winfo_exists():
            messagebox.showwarning(
                "Room data not found",
                "No room records were found. Put a valid room.txt in the same folder as accommodation.py.",
                parent=self,
            )

    # Display the available rooms as a gallery of room cards.
    def show_gallery(self):
        self._clear_content()
        self._set_navigation_state("gallery")

        intro = tk.Frame(self.content_area, bg=BG)
        intro.pack(fill="x", padx=4, pady=(0, 10))
        tk.Label(intro, text="Choose your room", bg=BG, fg=TEXT,
                 font=("Arial", 15, "bold")).pack(side="left")
        room_types = {}
        for room in self.rooms:
            room_types.setdefault(room["room_type"].casefold(), room)
        tk.Label(intro, text=f"{len(room_types)} room types · {len(self.rooms)} rooms in total · Click a photo to view details",
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
        self.services.register_scroll_target(canvas, scrollbar)

        # Three columns at the normal window width; cards expand with the window
        for column in range(3):
            card_grid.grid_columnconfigure(column, weight=1, uniform="room_cards")
        # Show one room card per room type, while keeping all 50 physical
        # room records available to the booking and availability checks.
        for index, room in enumerate(room_types.values()):
            row, column = divmod(index, 3)
            self._build_room_card(card_grid, room, row, column)

    # Create one room card with its photo, room type and price.
    def _build_room_card(self, parent, room, row, column):
        shell = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        shell.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card = tk.Frame(shell, bg=WHITE)
        card.pack(fill="both", expand=True)

        # Room photo area. Resize after Tkinter has calculated the card's real width.
        image_height = 180
        image_holder = tk.Frame(card, bg=PALE_BLUE, height=image_height, cursor="hand2")
        image_holder.pack(fill="x")
        image_holder.pack_propagate(False)

        photo = self.services.load_photo(room, (330, image_height))
        if photo is not None:
            self.photo_refs.append(photo)
            image_widget = tk.Label(
                image_holder, image=photo, bg=PALE_BLUE, cursor="hand2", bd=0
            )
            image_widget.image = photo
            image_widget._photo_size = (330, image_height)
            image_widget.pack(fill="both", expand=True)

            # Recalculate when Tkinter gives this card its final width.
            image_holder.bind(
                "<Configure>",
                lambda event, selected=room, target=image_widget,
                       holder=image_holder, h=image_height:
                    self.services.schedule_gallery_photo_resize(selected, target, holder, h)
            )
            # Also resize once after the initial layout. Binding alone can miss
            # the first size calculation on some Tkinter/Windows setups.
            self.after_idle(
                lambda selected=room, target=image_widget,
                       holder=image_holder, h=image_height:
                    self.services.resize_gallery_photo(
                        selected, target, holder.winfo_width(), h
                    )
            )
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
        room_type_rooms = [item for item in self.rooms
                           if item["room_type"].casefold() == room["room_type"].casefold()]
        available_tonight = self.services.available_rooms_for_dates(
            room, date.today(), date.today() + timedelta(days=1)
        )
        status = "AVAILABLE" if available_tonight else "UNAVAILABLE"
        tk.Label(top_line, text=status,
                 bg="#E7EEF4" if status == "AVAILABLE" else "#F0E7E7",
                 fg=NAVY if status == "AVAILABLE" else "#8B5C64",
                 font=("Arial", 7, "bold"), padx=6, pady=4).pack(side="right", padx=(5, 0))
        features = self.services.feature_list(room)
        short_features = "  ·  ".join(features[:3]) if features else "Room features on details page"
        tk.Label(body, text=short_features, bg=WHITE, fg=MUTED, font=("Arial", 8),
                 wraplength=310, justify="left", anchor="w", height=2).pack(anchor="w", fill="x")
        tk.Label(body, text=f"{len(room_type_rooms)} rooms in this room type",
                 bg=WHITE, fg=NAVY, font=("Arial", 8, "bold"), anchor="w").pack(anchor="w", pady=(4, 0))

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

    # Display the details and features of the selected room.
    def show_details(self, room):
        self.selected_room = room
        self._clear_content()
        self._set_navigation_state("gallery")

        # Keep the page heading and back button at the top.
        top = tk.Frame(self.content_area, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        self._make_button(top, "‹  Back to rooms", self.show_gallery,
                          primary=False).pack(side="left")
        tk.Label(top, text="ROOM DETAILS", bg=BG, fg=NAVY,
                 font=("Arial", 10, "bold")).pack(side="right", pady=7)

        # The detail card fills the available area. Its two columns are
        # allowed to resize with the window instead of using fixed widths.
        card_shell = tk.Frame(self.content_area, bg=BORDER, padx=1, pady=1)
        card_shell.pack(fill="both", expand=True)
        card = tk.Frame(card_shell, bg=WHITE, padx=16, pady=14)
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(0, weight=5, uniform="detail", minsize=0)
        card.grid_columnconfigure(1, weight=6, uniform="detail", minsize=0)
        card.grid_rowconfigure(0, weight=1)

        # Left column: responsive photo and status. Do not disable geometry
        # propagation or set a fixed width; those were causing the overflow.
        left = tk.Frame(card, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        initial_photo_width = 420
        initial_photo_height = initial_photo_width // 2
        image_panel = tk.Frame(left, bg=PALE_BLUE, height=initial_photo_height)
        image_panel.pack(fill="x")
        image_panel.pack_propagate(False)

        self.detail_photo = self.services.load_photo(room, (initial_photo_width, initial_photo_height))
        image_label = None
        if self.detail_photo is not None:
            image_label = tk.Label(image_panel, image=self.detail_photo, bg=PALE_BLUE, bd=0)
            image_label.image = self.detail_photo
            image_label._photo_size = (initial_photo_width, initial_photo_height)
            image_label.pack(fill="both", expand=True)
        else:
            tk.Label(image_panel, text="✦", bg=PALE_BLUE, fg=SLATE_BLUE,
                     font=("Arial", 42, "bold")).pack(pady=(35, 6))
            tk.Label(image_panel, text="ROOM PHOTO", bg=PALE_BLUE, fg=NAVY,
                     font=("Arial", 11, "bold")).pack()
            tk.Label(image_panel, text="Put the photo in room_images", bg=PALE_BLUE,
                     fg=MUTED, font=("Arial", 8), wraplength=300).pack(pady=5)

        # Show live room-type availability for tonight; the booking form checks
        # the exact dates selected by the customer.
        available_tonight = self.services.available_rooms_for_dates(
            room, date.today(), date.today() + timedelta(days=1)
        )
        status_text = "Available" if available_tonight else "Unavailable"
        tk.Label(left, text=f"Status for tonight: {status_text} ({len(available_tonight)} rooms available)",
                 bg=WHITE, fg=MUTED, font=("Arial", 10)).pack(anchor="w", pady=(10, 0))
        description = str(room.get("description", "")).strip()
        if description:
            description_label = tk.Label(
                left, text=description, bg=WHITE, fg=MUTED, font=("Arial", 9),
                wraplength=400, justify="left", anchor="w"
            )
            description_label.pack(anchor="w", fill="x", pady=(5, 0))
        else:
            description_label = None

        # Right column: content flows inside the width available in the card.
        right = tk.Frame(card, bg=WHITE)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        room_type_label = tk.Label(
            right, text=room["room_type"], bg=WHITE, fg=TEXT,
            font=("Arial", 20, "bold"), wraplength=420, justify="left", anchor="w"
        )
        room_type_label.grid(row=0, column=0, sticky="ew")

        price_row = tk.Frame(right, bg=WHITE)
        price_row.grid(row=1, column=0, sticky="ew", pady=(7, 8))
        tk.Label(price_row, text=f"RM{room['price_per_night']:.2f}", bg=WHITE, fg=NAVY,
                 font=("Arial", 19, "bold")).pack(side="left")
        tk.Label(price_row, text="per room, per night", bg=WHITE, fg=MUTED,
                 font=("Arial", 9)).pack(side="left", padx=(8, 0), pady=(7, 0))

        room_number_notice = tk.Label(
            right, text="Your room number will be provided when you check in.",
            bg="#EAF0F4", fg=NAVY, font=("Arial", 9, "bold"), padx=9, pady=8,
            anchor="w", justify="left", wraplength=420
        )
        room_number_notice.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        tk.Label(right, text="ROOM FEATURES", bg=WHITE, fg=NAVY,
                 font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="nw", pady=(0, 6))

        # Features use a separate expanding area, with a scrollbar if needed.
        features_outer = tk.Frame(right, bg=WHITE)
        features_outer.grid(row=4, column=0, sticky="nsew")
        right.grid_rowconfigure(4, weight=1)
        features_outer.grid_rowconfigure(0, weight=1)
        features_outer.grid_columnconfigure(0, weight=1)
        features_canvas = tk.Canvas(features_outer, bg=WHITE, highlightthickness=0, bd=0)
        features_scroll = ttk.Scrollbar(features_outer, orient="vertical", command=features_canvas.yview)
        features_canvas.configure(yscrollcommand=features_scroll.set)
        features_canvas.grid(row=0, column=0, sticky="nsew")
        features_scroll.grid(row=0, column=1, sticky="ns")
        self.services.register_scroll_target(features_canvas, features_scroll)
        features_inner = tk.Frame(features_canvas, bg=WHITE)
        features_window = features_canvas.create_window((0, 0), window=features_inner, anchor="nw")
        features_inner.bind(
            "<Configure>",
            lambda _event: features_canvas.configure(scrollregion=features_canvas.bbox("all"))
        )
        features_canvas.bind(
            "<Configure>",
            lambda event: features_canvas.itemconfigure(features_window, width=event.width)
        )
        feature_labels = []
        for feature in self.services.feature_list(room):
            line = tk.Frame(features_inner, bg=WHITE)
            line.pack(fill="x", anchor="w", pady=3)
            tk.Label(line, text="✓", bg=WHITE, fg=SLATE_BLUE,
                     font=("Arial", 9, "bold")).pack(side="left", padx=(1, 8))
            feature_label = tk.Label(
                line, text=feature, bg=WHITE, fg=TEXT, font=("Arial", 9),
                wraplength=420, justify="left", anchor="w"
            )
            feature_label.pack(side="left", fill="x", expand=True)
            feature_labels.append(feature_label)

        # Resize wrapped text and the photo to the real column widths.
        # Adjust the room description text to fit its panel.
        def resize_detail_text(event=None):
            right_width = max(200, right.winfo_width() - 18)
            room_type_label.configure(wraplength=right_width)
            room_number_notice.configure(wraplength=right_width)
            for label in feature_labels:
                label.configure(wraplength=max(160, right_width - 24))
            if description_label is not None:
                description_label.configure(wraplength=max(180, left.winfo_width() - 8))

        right.bind("<Configure>", resize_detail_text)
        left.bind(
            "<Configure>",
            lambda event, selected=room, panel=image_panel, label=image_label:
                self.services.resize_detail_photo(selected, panel, label, event.width)
                if label is not None else None
        )
        if image_label is not None:
            left.after_idle(
                lambda selected=room, panel=image_panel, label=image_label, holder=left:
                    self.services.resize_detail_photo(selected, panel, label, holder.winfo_width())
            )

        # Keep the action buttons at the bottom of the card.
        action = tk.Frame(card, bg=WHITE)
        action.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        tk.Label(action, text="Select your dates and room quantity on the next page.",
                 bg=WHITE, fg=MUTED, font=("Arial", 9)).pack(side="left")
        self._make_button(action, "Book this room  →", lambda selected=room: self.show_booking_form(selected),
                          primary=True, padx=18, pady=10).pack(side="right")
        self._make_button(action, "Back to rooms", self.show_gallery,
                          primary=False, padx=15, pady=10).pack(side="right", padx=(0, 8))

    # Display the form for entering a guest reservation.
    def show_booking_form(self, room):
        self.selected_room = room
        self._clear_content()
        self._set_navigation_state("gallery")

        top = tk.Frame(self.content_area, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        self._make_button(top, "<  Back to room details",
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
        # Make the room photo use the full width of the selected-room panel.
        # The previous fixed 390-pixel image left blue gaps on both sides when
        # the left panel became wider than the original image.
        image_height = 175
        img = tk.Frame(left, bg=PALE_BLUE, height=image_height)
        img.pack(fill="x")
        img.pack_propagate(False)

        # Keep one Label across the full photo area. The BookingManager resizes
        # the image to this Label's actual width after Tkinter lays out the page.
        image_widget = tk.Label(img, bg=PALE_BLUE, bd=0)
        image_widget.pack(fill="both", expand=True)
        photo = self.services.load_photo(room, (390, image_height))
        if photo:
            self.photo_refs.append(photo)
            image_widget.configure(image=photo)
            image_widget.image = photo
            image_widget._photo_size = (390, image_height)
        else:
            image_widget.configure(
                text="✦\nROOM PHOTO",
                fg=NAVY,
                font=("Arial", 12, "bold"),
                justify="center",
            )

        # Resize and crop the photo to fill the complete panel when its real
        # width is known, and repeat if the application window is resized.
        img.bind(
            "<Configure>",
            lambda _event, selected=room, target=image_widget, holder=img, height=image_height:
                self.services.schedule_gallery_photo_resize(selected, target, holder, height)
        )
        self.after_idle(
            lambda selected=room, target=image_widget, holder=img, height=image_height:
                self.services.resize_gallery_photo(selected, target, holder.winfo_width(), height)
        )
        tk.Label(left, text=room["room_type"], bg=WHITE, fg=TEXT,
                 font=("Arial", 15, "bold"), wraplength=400).pack(anchor="w", pady=(10, 2))
        tk.Label(left, text=f"Status: {room['status']}",
                 bg=WHITE, fg=MUTED, font=("Arial", 9)).pack(anchor="w")
        tk.Label(left, text=f"RM{room['price_per_night']:.2f} / night", bg=WHITE, fg=NAVY,
                 font=("Arial", 15, "bold")).pack(anchor="w", pady=(10, 3))
        tk.Label(left, text="Choose how many rooms you need. Your room number will be provided when you check in.",
                 bg=WHITE, fg=MUTED, font=("Arial", 9), wraplength=400, justify="left").pack(anchor="w", pady=(4, 8))
        self.availability_var = tk.StringVar(value="Availability is checked for your selected dates.")
        tk.Label(left, textvariable=self.availability_var, bg=PALE_CARD, fg=TEXT,
                 font=("Arial", 9), wraplength=400, justify="left", padx=10, pady=9).pack(fill="x", pady=(4, 0))

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
        self.services.register_scroll_target(self.booking_form_canvas, form_scroll)
        form = tk.Frame(self.booking_form_canvas, bg=WHITE)
        self.payment_form_inner = form
        form_window = self.booking_form_canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _event: self.booking_form_canvas.configure(
            scrollregion=self.booking_form_canvas.bbox("all")))
        self.booking_form_canvas.bind("<Configure>", lambda event: self.booking_form_canvas.itemconfigure(
            form_window, width=event.width))

        form.grid_columnconfigure(1, weight=1)
        self.form_vars = {}
        self.special_request_vars = {}
        # If guests started with the homepage search bar, prefill the same
        # dates and guest/room counts after they select a room.
        home_search = getattr(self, "home_booking_search", {}) or {}
        fields = [
            ("name", "Full name", ""),
            ("email", "Email address", ""),
            ("hp", "Phone number", ""),
            ("ic", "IC / Passport", ""),
            ("check_in", "Check-in (YYYY-MM-DD)", home_search.get("check_in", date.today().isoformat())),
            ("check_out", "Check-out (YYYY-MM-DD)", home_search.get("check_out", (date.today() + timedelta(days=1)).isoformat())),
            ("adults", "Adults", home_search.get("adults", "1")),
            ("children", "Children", home_search.get("children", "0")),
            ("amount_of_room", "Amount of rooms", home_search.get("amount_of_room", "1")),
            ("special_requests", "Special requests (optional)", ""),
            ("promo_code", "Promo code (optional)", ""),
        ]
        row = 0
        for key, label_text, default in fields:
            tk.Label(form, text=label_text, bg=WHITE, fg=TEXT,
                     font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            variable = tk.StringVar(value=default)
            self.form_vars[key] = variable
            if key == "special_requests":
                # Let guests select the specific room preferences from Stage 1.
                request_frame = tk.Frame(form, bg=WHITE)
                request_frame.grid(row=row, column=1, sticky="ew", pady=5)
                request_choices = ("Smoke-free", "Smoking", "Kids room", "No corner room", "Quiet room")
                for choice_index, choice in enumerate(request_choices):
                    choice_var = tk.BooleanVar(value=False)
                    self.special_request_vars[choice] = choice_var
                    tk.Checkbutton(
                        request_frame, text=choice, variable=choice_var,
                        bg=WHITE, fg=TEXT, activebackground=WHITE,
                        selectcolor=PALE_BLUE, font=("Arial", 9),
                    ).grid(row=choice_index // 2, column=choice_index % 2, sticky="w", padx=(0, 12), pady=2)
                row += 1
                continue
            elif key == "amount_of_room":
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
        tk.Label(self.payment_detail_frame, text="Choose a payment method to enter.",
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

        for key in ("check_in", "check_out", "amount_of_room", "promo_code"):
            self.form_vars[key].trace_add("write", lambda *_args: self._refresh_booking_total())
        self._refresh_booking_total()

    # Show the payment fields that match the selected payment method.
    def _on_payment_method_change(self, _event=None):
        if self.payment_detail_frame is None:
            return
        for child in self.payment_detail_frame.winfo_children():
            child.destroy()
        self.payment_detail_vars = {}
        method = self.payment_var.get().strip() if self.payment_var else ""
        if method == "Credit/Debit Card":
            tk.Label(self.payment_detail_frame, text="Card payment details",
                     bg=PALE_CARD, fg=NAVY, font=("Arial", 9, "bold")).grid(
                         row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
            payment_fields = [
                ("cardholder", "Cardholder name", ""),
                ("card_number", "Card number", ""),
                ("expiry", "Expiry (MM/YY)", ""),
                ("cvv", "Security code", ""),
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

    # Check that the payment details entered by the guest are valid.
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
                messagebox.showerror("Check card details", "Enter a cardholder name and a card number containing 13–19 digits.", parent=self)
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
                messagebox.showerror("E-wallet details required", "Enter a phone/account value.", parent=self)
                return False
        return True


    # Read the check-in and check-out dates and check that they are valid.
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



    # Recalculate the booking price when the room quantity or dates change.
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
        available_rooms = self.services.available_rooms_for_dates(self.selected_room, check_in, check_out)
        available_count = len(available_rooms)
        if self.availability_var is not None:
            total_type_rooms = sum(
                1 for item in self.rooms
                if item["room_type"].casefold() == self.selected_room["room_type"].casefold()
            )
            if available_count == 0:
                self.availability_var.set(
                    f"UNAVAILABLE: all {total_type_rooms} rooms of this type are booked or checked in for your selected dates."
                )
            else:
                self.availability_var.set(
                    f"{available_count} of {total_type_rooms} rooms are available for your selected dates."
                )
        total_before_discount = self.selected_room["price_per_night"] * nights * quantity
        promo_code = self.form_vars.get("promo_code", tk.StringVar()).get().strip().upper()
        discount = 0.0
        promo_note = ""
        if promo_code == "LONGSTAY15":
            if nights >= 5:
                discount = total_before_discount * 0.15
            else:
                promo_note = " · LONGSTAY15 requires at least 5 nights"
        elif promo_code == "WEEKEND20":
            if nights >= 2 and check_in.weekday() in (4, 5):
                discount = self.selected_room["price_per_night"] * quantity * 0.20
            else:
                promo_note = " · WEEKEND20 requires 2 nights starting Friday/Saturday"
        elif promo_code:
            promo_note = " · Promo code not recognised"
        final_total = total_before_discount - discount
        self.total_var.set(
            f"Estimated total: RM{final_total:.2f}  ·  {nights} night(s)  ·  {quantity} room(s)"
            + (f"  ·  Discount RM{discount:.2f}" if discount else "") + promo_note
        )


    # Check the booking form before passing it to the confirmation step.
    def _handle_confirm_booking(self):
        # Run booking confirmation and show unexpected errors to the user.
        try:
            self._confirm_booking()
        except Exception as error:
            # Keep the GUI responsive and make unexpected issues visible rather
            # than leaving the user unsure why the button did nothing.
            messagebox.showerror(
                "Booking could not be completed",
                "Something unexpected stopped the booking from being saved.\n\n"
                f"Details: {error}",
                parent=self.winfo_toplevel(),
            )

    # Check room availability and save the confirmed booking.
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
        available_rooms = self.services.available_rooms_for_dates(room, check_in, check_out)
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
        total_before_discount = nights * room["price_per_night"] * quantity
        promo_code = self.form_vars["promo_code"].get().strip().upper()
        discount = 0.0
        if promo_code == "LONGSTAY15":
            if nights < 5:
                messagebox.showwarning("Promo Conditions", "LONGSTAY15 is valid for stays of at least 5 nights.", parent=self)
                return
            discount = total_before_discount * 0.15
        elif promo_code == "WEEKEND20":
            if nights < 2 or check_in.weekday() not in (4, 5):
                messagebox.showwarning(
                    "Promo Conditions",
                    "WEEKEND20 is valid for stays of at least 2 nights starting on Friday or Saturday.",
                    parent=self,
                )
                return
            discount = room["price_per_night"] * quantity * 0.20
        elif promo_code:
            messagebox.showwarning("Invalid Promo Code", "Please check the promo code and try again.", parent=self)
            return
        total = total_before_discount - discount
        selected_requests = [name for name, variable in self.special_request_vars.items() if variable.get()]
        if "Smoke-free" in selected_requests and "Smoking" in selected_requests:
            messagebox.showwarning("Conflicting Room Requests", "Please choose Smoke-free or Smoking, not both.", parent=self)
            return
        special_requests = ", ".join(selected_requests)
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
            "special_requests": special_requests,
            "promo_code": promo_code,
            "total_price": f"{total:.2f}",
            "payment_method": self.payment_var.get().strip(),
            "status": "Confirmed",
        }
        if not self.services.append_booking(booking):
            return
        self.bookings = self.services.read_bookings()
        # Do not display the assigned room number until check-in.
        # Payment details are never saved in booking.txt.
        messagebox.showinfo(
            "Booking confirmed",
            f"Your booking has been saved on this device.\n\n"
            f"Room type: {room['room_type']}\n"
            "Your room number will be provided when you check in.\n"
            f"Dates: {check_in.isoformat()} to {check_out.isoformat()}\n"
            f"Rooms: {quantity}\nNights: {nights}\nSubtotal: RM{total_before_discount:.2f}\n"
            f"Discount: RM{discount:.2f}\nTotal: RM{total:.2f}\n\n"
            "Payment detail fields are not stored in our data system.",
            parent=self.winfo_toplevel(),
        )
        # Return to the Home page after the guest closes the confirmation message.
        main_window = self.winfo_toplevel()
        if hasattr(main_window, "show_page"):
            main_window.show_page("Home")


    # Display the bookings saved in booking.txt.
    def show_history(self):
        self._clear_content()
        self._set_navigation_state("history")
        self.bookings = self.services.read_bookings()

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
        self.services.register_scroll_target(tree, ybar)
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
            tk.Label(empty_state, text="Your confirmed bookings will be saved and appear here.",
                     bg=WHITE, fg=MUTED, font=("Arial", 10)).pack()