"""Staff login and management pages for Caramel Hotel.

The Staff module is displayed inside the main Caramel Hotel window.
It shares booking.txt with Accommodation and order.txt with Restaurant.
"""

import ast
import json
import math
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
from pathlib import Path
from booking_manager import LEGACY_ROOM_NUMBER_MAP


# Staff login details used by the demonstration system.
USERS = {
    "ADMIN": "admin123",
    "CHIN YANG LIANG": "105820999",
    "NG ZHI YING": "105817373",
    "TAN YUAN": "105821552",
    "PUI YI XUAN": "105819201",
}

# Colours used by the Staff pages.
COLORS = {
    "bg": "#DFE2E5",
    "nav": "#486B92",
    "nav_text": "#FFFFFF",
    "card": "#FFFFFF",
    "text": "#34465A",
    "muted": "#647588",
    "accent": "#486B92",
    "accent_hover": "#7E93A9",
    "line": "#D0D9E0",
    "banner": "#C5D6E2",
    "red": "#A85248",
    "green": "#477B68",
    "pale": "#F7F9FA",
}

BOOKING_FIELDS = (
    "name", "email", "hp", "ic", "room_type", "room_number",
    "check_in", "check_out", "amount_of_room", "adults", "children",
    "special_requests", "promo_code", "total_price", "payment_method", "status",
)
MENU_CATEGORIES = (
    "Appetizers", "Chinese", "Western", "Thai", "Japanese",
    "Desserts", "Beverages", "Wines",
)


def menu_item_sort_key(item):
    # Sort menu IDs by their letter prefix, then by the numeric suffix.
    item_id = str(item.get("id", "")).strip().upper()
    match = re.fullmatch(r"([A-Z]+)(\d+)", item_id)
    if match:
        return (match.group(1), 0, int(match.group(2)), item_id)

    # Keep unusual IDs visible after normal letter-and-number IDs.
    return (item_id, 1, 0, item_id)


class StaffPage(tk.Frame):
    # Staff login and management screens shown inside main.py.

    # Set up the Staff page and load the shared hotel records.
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.base_dir = Path(__file__).resolve().parent
        self.booking_file = self.base_dir / "booking.txt"
        self.room_file = self.base_dir / "room.txt"
        self.menu_file = self.base_dir / "menu.txt"
        self.order_file = self.base_dir / "order.txt"
        self.images_folder = self.base_dir / "images"
        self.current_user = ""
        self.bookings = []
        self.rooms = []
        self.arrivals = []
        self.departures = []
        self.orders = []
        self.table_groups = []
        self.content_area = None
        self._load_data()
        self._build_login()


    # ------------------------------------------------------------
    # STAFF LOGIN
    # Display the Staff login page in the same visual style as the Staff portal.
    # Checks staff credentials before opening the admin portal.
    # ------------------------------------------------------------
    def _build_login(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=COLORS["bg"])

        # Keep the login screen simple because the shared Caramel Hotel navigation
        # already displays the hotel's name and logo.
        center = tk.Frame(self, bg=COLORS["bg"])
        center.pack(fill="both", expand=True)
        card = tk.Frame(center, bg=COLORS["card"], highlightbackground=COLORS["line"],
                        highlightthickness=1, padx=42, pady=30)
        card.place(relx=0.5, rely=0.48, anchor="center", width=440)

        # Show the hotel logo without repeating a large Caramel Hotel heading.
        self.login_logo_image = None
        logo_path = self.images_folder / "caramel_hotel_logo.png"
        if logo_path.is_file():
            try:
                self.login_logo_image = tk.PhotoImage(file=str(logo_path))
                logo_size = 64
                scale = max(1, math.ceil(self.login_logo_image.width() / logo_size),
                            math.ceil(self.login_logo_image.height() / logo_size))
                if scale > 1:
                    self.login_logo_image = self.login_logo_image.subsample(scale, scale)
                tk.Label(card, image=self.login_logo_image, bg=COLORS["card"]).pack(pady=(0, 8))
            except (tk.TclError, OSError):
                self.login_logo_image = None

        tk.Label(card, text="STAFF SIGN IN", bg=COLORS["card"], fg=COLORS["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="center", pady=(0, 7))
        tk.Label(card, text="Welcome back", bg=COLORS["card"], fg=COLORS["text"],
                 font=("Georgia", 20, "bold")).pack(anchor="center")
        tk.Label(card, text="Sign in to access hotel operations and guest services.",
                 bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 9),
                 wraplength=340, justify="center").pack(anchor="center", pady=(5, 22))

        tk.Label(card, text="STAFF ID / USERNAME", bg=COLORS["card"], fg=COLORS["text"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.username_entry = tk.Entry(card, font=("Segoe UI", 11), relief="solid", bd=1)
        self.username_entry.pack(fill="x", ipady=8, pady=(6, 15))
        tk.Label(card, text="PASSWORD", bg=COLORS["card"], fg=COLORS["text"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.password_entry = tk.Entry(card, font=("Segoe UI", 11), show="*", relief="solid", bd=1)
        self.password_entry.pack(fill="x", ipady=8, pady=(6, 20))
        self.password_entry.bind("<Return>", lambda _event: self._login())

        tk.Button(card, text="SIGN IN  →", command=self._login, bg=COLORS["nav"], fg="white",
                  activebackground=COLORS["accent_hover"], relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"), pady=11).pack(fill="x")
        tk.Button(card, text="Return to Home", command=lambda: self.winfo_toplevel().show_page("Home"),
                  bg=COLORS["card"], fg=COLORS["accent"], activebackground=COLORS["pale"],
                  relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"), pady=9).pack(fill="x", pady=(8, 0))
        tk.Label(center, text="Authorised hotel staff only", bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(side="bottom", pady=13)

    # Check the entered Staff ID and password before opening the admin dashboard.
    def _login(self):
        username = self.username_entry.get().strip().upper()
        password = self.password_entry.get().strip()
        if username in USERS and USERS[username] == password:
            self.current_user = username
            self._load_data()
            self._build_portal()
        else:
            messagebox.showerror("Login Failed", "The Staff ID or password is incorrect.", parent=self)

    # Clean a value before saving it in a pipe-separated text file.
    @staticmethod
    def _safe_field(value):
        return str(value).replace("|", "/").replace("\r", " ").replace("\n", " ").strip()

    # Read the shared booking, room and restaurant order records.
    def _load_data(self):
        self.bookings = []
        if self.booking_file.is_file():
            try:
                with self.booking_file.open("r", encoding="utf-8-sig") as file:
                    for line in file:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = [part.strip() for part in line.split("|")]
                        if tuple(part.lower() for part in parts) == BOOKING_FIELDS or len(parts) != len(BOOKING_FIELDS):
                            continue
                        booking = dict(zip(BOOKING_FIELDS, parts))
                        # Convert older assigned room numbers to the corrected room.txt numbering.
                        number_map = LEGACY_ROOM_NUMBER_MAP.get(booking.get("room_type", "").casefold(), {})
                        saved_numbers = [number.strip() for number in booking.get("room_number", "").split(",")]
                        booking["room_number"] = ", ".join(
                            number_map.get(number, number) for number in saved_numbers if number
                        )
                        try:
                            booking["total_price"] = float(booking["total_price"] or 0)
                        except (TypeError, ValueError):
                            booking["total_price"] = 0.0
                        self.bookings.append(booking)
            except OSError as error:
                messagebox.showerror("Booking File Error", f"Could not read booking.txt:\n{error}", parent=self)

        self.rooms = self._read_rooms()
        self.arrivals = [b for b in self.bookings if b.get("status", "").casefold() == "checked in"]
        self.departures = [b for b in self.bookings if b.get("status", "").casefold() == "checked out"]
        self.orders = []
        old_order_file = self.base_dir / "rorders.txt"
        order_source = self.order_file if self.order_file.is_file() else old_order_file
        if order_source.is_file():
            try:
                saved = json.loads(order_source.read_text(encoding="utf-8"))
                if isinstance(saved, list):
                    self.orders = [order for order in saved if isinstance(order, dict)]
            except (OSError, json.JSONDecodeError):
                self.orders = []

        # Give older restaurant records an Order ID once, then save it in order.txt.
        highest_order_number = 0
        for saved_order in self.orders:
            saved_id = str(saved_order.get("order_id", "")).strip()
            if saved_id:
                try:
                    highest_order_number = max(highest_order_number, int(saved_id.rsplit("-", 1)[-1]))
                except ValueError:
                    pass
        order_ids_changed = False
        for saved_order in self.orders:
            if not str(saved_order.get("order_id", "")).strip():
                highest_order_number += 1
                saved_order["order_id"] = f"ORD-{highest_order_number:05d}"
                order_ids_changed = True
        if order_ids_changed:
            try:
                self.order_file.write_text(json.dumps(self.orders, ensure_ascii=False, indent=4) + "\n",
                                           encoding="utf-8")
            except OSError:
                # The existing order records remain available in memory if the file is read-only.
                pass

    # Save the current booking records while keeping the same 16-field format.
    def _save_data(self):
        lines = ["# Caramel Hotel booking records (stored locally)", "|".join(BOOKING_FIELDS)]
        for booking in self.bookings:
            values = []
            for field in BOOKING_FIELDS:
                value = booking.get(field, "")
                if field == "total_price":
                    try:
                        value = f"{float(value):.2f}"
                    except (TypeError, ValueError):
                        value = "0.00"
                values.append(self._safe_field(value))
            lines.append("|".join(values))
        try:
            self.booking_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
        except OSError as error:
            messagebox.showerror("Booking File Error", f"Could not save booking.txt:\n{error}", parent=self)
            return False

    # Read compact room-type records and create the individual physical rooms.
    def _read_rooms(self):
        room_records = []
        if not self.room_file.is_file():
            return []
        try:
            with self.room_file.open("r", encoding="utf-8-sig") as file:
                for line in file:
                    if not line.strip() or line.lstrip().startswith(("#", "//")):
                        continue
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) != 6 or parts[0].casefold() == "room_type":
                        continue
                    try:
                        price = float(parts[2])
                        first_number = int(parts[1])
                        if not math.isfinite(price) or price < 0 or first_number < 1:
                            continue
                    except ValueError:
                        continue
                    if parts[0]:
                        room_records.append({
                            "room_type": parts[0], "room_number": str(first_number),
                            "price_per_night": price, "features": parts[3],
                            "status": parts[4].title(), "image_filename": parts[5],
                        })
        except OSError:
            return []

        # One record per type is the compact format. Repeated types are treated
        # as an older file that already contains one row per physical room.
        type_counts = {}
        for room in room_records:
            key = room["room_type"].casefold()
            type_counts[key] = type_counts.get(key, 0) + 1

        rooms = []
        for room in room_records:
            if type_counts[room["room_type"].casefold()] == 1:
                # Generate 50 consecutive room numbers from the starting number.
                first_number = int(room["room_number"])
                for offset in range(50):
                    physical_room = room.copy()
                    physical_room["room_number"] = str(first_number + offset)
                    rooms.append(physical_room)
            else:
                rooms.append(room)
        return rooms

    # ------------------------------------------------------------
    # ADMIN PORTAL AND NAVIGATION
    # Build the Staff sidebar and the main admin content area.
    # ------------------------------------------------------------      
    def _build_portal(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=COLORS["bg"])
        sidebar = tk.Frame(self, bg=COLORS["nav"], width=218)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        # Build a clearer Admin brand area at the top of the navigation panel.
        brand = tk.Frame(sidebar, bg="#3D5F82", padx=15, pady=20)
        brand.pack(fill="x", padx=10, pady=(12, 18))
        self.sidebar_logo_image = None
        logo_path = self.images_folder / "caramel_hotel_logo.png"
        if logo_path.is_file():
            try:
                self.sidebar_logo_image = tk.PhotoImage(file=str(logo_path))
                logo_size = 46
                scale = max(1, math.ceil(self.sidebar_logo_image.width() / logo_size),
                            math.ceil(self.sidebar_logo_image.height() / logo_size))
                if scale > 1:
                    self.sidebar_logo_image = self.sidebar_logo_image.subsample(scale, scale)
                tk.Label(brand, image=self.sidebar_logo_image, bg="#3D5F82").pack(anchor="w", pady=(0, 10))
            except (tk.TclError, OSError):
                self.sidebar_logo_image = None
        tk.Label(brand, text="CARAMEL HOTEL", bg="#3D5F82", fg="white",
                 font=("Georgia", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(brand, text="ADMINISTRATION", bg="#3D5F82", fg="#DCE7F0",
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(4, 0))
        tk.Frame(sidebar, bg="#7892AA", height=1).pack(fill="x", padx=16, pady=(0, 18))
        tk.Label(sidebar, text="WORKSPACE", bg=COLORS["nav"], fg="#DCE7F0",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(0, 8))

        # Remember the current Admin page so only its navigation label is bold.
        self.active_admin_page = tk.StringVar(value="")
        self.admin_nav_buttons = {}
        for label, command in (
            ("Overview", self._show_dashboard),
            ("Reservations", self._show_reservations),
            ("Check-in", self._show_checkin),
            ("Check-out", self._show_checkout),
            ("Menu Management", self._show_menu_management),
            ("Table Overview", self._show_table_overview),
        ):
            button = tk.Button(
                sidebar, text=label,
                command=lambda selected=label, action=command: (self.active_admin_page.set(selected), action()),
                bg=COLORS["nav"], fg="white",
                activebackground=COLORS["accent_hover"], activeforeground="white",
                relief="flat", anchor="w", padx=22, pady=12,
                font=("Segoe UI", 10, "normal"), cursor="hand2"
            )
            button.pack(fill="x", padx=9, pady=2)
            self.admin_nav_buttons[label] = button

        # Update the active navigation style whenever a page is selected.
        self.active_admin_page.trace_add("write", lambda *_args: [
            button.configure(
                bg=COLORS["banner"] if page_name == self.active_admin_page.get() else COLORS["nav"],
                fg=COLORS["nav"] if page_name == self.active_admin_page.get() else "white",
                activebackground=COLORS["banner"] if page_name == self.active_admin_page.get() else COLORS["accent_hover"],
                activeforeground=COLORS["nav"] if page_name == self.active_admin_page.get() else "white",
                font=("Segoe UI", 10, "bold" if page_name == self.active_admin_page.get() else "normal")
            ) for page_name, button in self.admin_nav_buttons.items()
        ])
        self.active_admin_page.set("Overview")
        tk.Button(sidebar, text="Sign Out", command=self._sign_out, bg=COLORS["nav"], fg="#FFD0D0",
                  activebackground=COLORS["red"], activeforeground="white", relief="flat",
                  anchor="w", padx=22, pady=13, font=("Segoe UI", 10, "bold"),
                  cursor="hand2").pack(side="bottom", fill="x", pady=15)
        self.content_area = tk.Frame(self, bg=COLORS["bg"])
        self.content_area.pack(side="left", fill="both", expand=True, padx=25, pady=23)
        self._show_dashboard()

    # Clear the previous Staff screen before displaying another one.
    def _clear_content(self):
        # Remove the temporary page-wide scrolling bindings before changing pages.
        for sequence, binding_id in getattr(self, "_checkin_scroll_bindings", []):
            if binding_id:
                try:
                    self._root()._unbind(("bind", "all", sequence), binding_id)
                except (tk.TclError, AttributeError):
                    pass
        self._checkin_scroll_bindings = []
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # Create a consistent Treeview with a scrollbar for Staff records.
    def _create_table(self, parent, columns, widths):
        # The clam theme applies the same readable header and row colours on
        # Windows, so the first data row does not blend into the table heading.
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Staff.Treeview", background=COLORS["card"], fieldbackground=COLORS["card"],
                        foreground=COLORS["text"], rowheight=38, font=("Segoe UI", 9),
                        borderwidth=1, relief="solid")
        style.configure("Staff.Treeview.Heading", background=COLORS["nav"], foreground="#FFFFFF",
                        font=("Segoe UI", 9, "bold"), padding=(10, 12), relief="raised", borderwidth=1)
        style.map("Staff.Treeview",
                  background=[("selected", "#C5D6E2")],
                  foreground=[("selected", COLORS["text"])])
        style.map("Staff.Treeview.Heading",
                  background=[("active", COLORS["accent_hover"])],
                  foreground=[("active", "#FFFFFF")])

        wrapper = tk.Frame(parent, bg=COLORS["card"])
        wrapper.pack(fill="both", expand=True, pady=8)
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)
        # A smaller visible row count leaves room for the scrollbar on screens
        # where the check-in form and table are displayed together.
        tree = ttk.Treeview(wrapper, columns=columns, show="headings",
                            style="Staff.Treeview", height=7, selectmode="browse")
        for index, column in enumerate(columns):
            tree.heading(column, text=column, anchor="w" if index == 0 else "center")
            tree.column(column, width=widths[index], minwidth=75, stretch=True,
                        anchor="w" if index == 0 else "center")
        ybar = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")

        # Set both background AND foreground for every row style. This keeps
        # the first row's text visible instead of relying on theme defaults.
        tree.tag_configure("even", background=COLORS["pale"], foreground=COLORS["text"])
        tree.tag_configure("odd", background=COLORS["card"], foreground=COLORS["text"])

        # Allow mouse-wheel scrolling while the pointer is over the table.
        tree.bind("<MouseWheel>", lambda event, target=tree: (
            target.yview_scroll(-(int(event.delta / 120) or (1 if event.delta > 0 else -1)), "units"),
            "break"
        )[1])
        tree.bind("<Button-4>", lambda _event, target=tree: (target.yview_scroll(-1, "units"), "break")[1])
        tree.bind("<Button-5>", lambda _event, target=tree: (target.yview_scroll(1, "units"), "break")[1])
        # Let the vertical scrollbar respond to the mouse wheel as well.
        for target_widget in (ybar,):
            target_widget.bind("<MouseWheel>", lambda event, target=tree: (
                target.yview_scroll(-(int(event.delta / 120) or (1 if event.delta > 0 else -1)), "units"),
                "break"
            )[1])
            target_widget.bind("<Button-4>", lambda _event, target=tree: (target.yview_scroll(-1, "units"), "break")[1])
            target_widget.bind("<Button-5>", lambda _event, target=tree: (target.yview_scroll(1, "units"), "break")[1])
        return tree


    # ------------------------------------------------------------
    # ADMIN DASHBOARD
    # Show the admin homepage with operating information and quick actions only.
    # ------------------------------------------------------------
    def _show_dashboard(self):
        self.active_admin_page.set("Overview")
        self._load_data()
        self._clear_content()
        top = tk.Frame(self.content_area, bg=COLORS["banner"], padx=22, pady=20)
        top.pack(fill="x", pady=(0, 18))
        tk.Label(top, text="Good day, " + self.current_user.title(), bg=COLORS["banner"],
                 fg=COLORS["text"], font=("Georgia", 21, "bold")).pack(anchor="w")
        tk.Label(top, text="Here is your hotel operations overview.", bg=COLORS["banner"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        confirmed = sum(1 for booking in self.bookings if booking.get("status", "").casefold() == "confirmed")
        checked_in = sum(1 for booking in self.bookings if booking.get("status", "").casefold() == "checked in")
        current_orders = [order for order in self.orders if order.get("dining") == "Restaurant dining"
                          and order.get("status", "Received").casefold() not in ("left", "completed", "cancelled")]
        pending_cash = sum(1 for order in current_orders
                           if order.get("payment", "").casefold() == "cash"
                           and order.get("payment_status", "Pending").casefold() != "paid")
        cards = (
            ("Reservations", confirmed, "Awaiting guest check-in"),
            ("Guests in-house", checked_in, "Currently checked in"),
            ("Restaurant customers", len({(o.get("location"), o.get("customer")) for o in current_orders}), "Currently dining"),
            ("Cash payments", pending_cash, "Awaiting counter payment"),
        )
        stats = tk.Frame(self.content_area, bg=COLORS["bg"])
        stats.pack(fill="x", pady=(0, 18))
        for title, value, subtitle in cards:
            card = tk.Frame(stats, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(card, text=title.upper(), bg=COLORS["card"], fg=COLORS["muted"],
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15, pady=(14, 2))
            tk.Label(card, text=str(value), bg=COLORS["card"], fg=COLORS["accent"],
                     font=("Georgia", 25, "bold")).pack(anchor="w", padx=15)
            tk.Label(card, text=subtitle, bg=COLORS["card"], fg=COLORS["muted"],
                     font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(1, 14))

        tk.Label(self.content_area, text="Quick actions", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Georgia", 16, "bold")).pack(anchor="w", pady=(0, 9))
        quick = tk.Frame(self.content_area, bg=COLORS["bg"])
        quick.pack(fill="x")
        actions = (
            ("Reservations", "Search customer bookings", self._show_reservations),
            ("Check-in", "Register a reservation or walk-in", self._show_checkin),
            ("Menu Management", "Browse categories and add food", self._show_menu_management),
            ("Table Overview", "View customers currently dining", self._show_table_overview),
        )
        for index, (title, subtitle, command) in enumerate(actions):
            row, column = divmod(index, 2)
            card = tk.Frame(quick, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 10), pady=6)
            quick.grid_columnconfigure(column, weight=1)
            tk.Button(card, text=title + "  →", command=command, anchor="w", bg=COLORS["card"],
                      fg=COLORS["accent"], activebackground=COLORS["pale"], relief="flat",
                      font=("Segoe UI", 11, "bold"), padx=16, pady=12).pack(fill="x")
            tk.Label(card, text=subtitle, bg=COLORS["card"], fg=COLORS["muted"],
                     font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=17, pady=(0, 13))

    # ------------------------------------------------------------
    # RESERVATION MANAGEMENT
    # Display only customer reservations and filter them with the search bar.
    # ------------------------------------------------------------
    def _show_reservations(self, search_text=None):
        self.active_admin_page.set("Reservations")
        if search_text is not None and getattr(self, "reservation_tree", None) is not None:
            tree = self.reservation_tree
            if not tree.winfo_exists():
                return
            tree.delete(*tree.get_children())
            count = 0
            for index, booking in enumerate(self.bookings):
                if booking.get("status", "").casefold() != "confirmed":
                    continue
                name = str(booking.get("name", ""))
                phone = str(booking.get("hp", ""))
                email = str(booking.get("email", ""))
                query = search_text.strip().casefold()
                if query and query not in name.casefold() and query not in phone.casefold() and query not in email.casefold():
                    continue
                total = float(booking.get("total_price", 0) or 0)
                tree.insert("", "end", iid=str(index), values=(
                            name, phone, booking.get("room_type", ""),
                            booking.get("amount_of_room", "1"),
                            booking.get("check_in", ""), booking.get("check_out", ""),
                            f"RM {total:.2f}", booking.get("payment_method", "")),
                            tags=("even" if count % 2 == 0 else "odd",))
                count += 1
            self.reservation_count_label.config(text=f"{count} customer reservation(s)")
            return

        self._load_data()
        self._clear_content()
        self.reservation_tree = None
        tk.Label(self.content_area, text="Reservations", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Georgia", 23, "bold")).pack(anchor="w")
        tk.Label(self.content_area, text="Search customer bookings. Select a reservation to open its check-in form.",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 12))
        search_row = tk.Frame(self.content_area, bg=COLORS["bg"])
        search_row.pack(fill="x", pady=(0, 8))
        search_entry = tk.Entry(search_row, font=("Segoe UI", 10), relief="solid", bd=1)
        search_entry.pack(side="left", fill="x", expand=True, ipady=7)
        search_entry.insert(0, "Search customer name, phone or email...")
        search_entry.bind("<FocusIn>", lambda _event: search_entry.delete(0, tk.END)
                          if search_entry.get() == "Search customer name, phone or email..." else None)
        self.reservation_count_label = tk.Label(search_row, text="", bg=COLORS["bg"],
                                                fg=COLORS["muted"], font=("Segoe UI", 9))
        self.reservation_count_label.pack(side="right", padx=(12, 0))
        panel = tk.Frame(self.content_area, bg=COLORS["card"], padx=12, pady=10)
        panel.pack(fill="both", expand=True)
        self.reservation_tree = self._create_table(
            panel, ("Customer", "Phone", "Room Type", "Rooms", "Check-in", "Check-out", "Total Price", "Payment Method"),
            (155, 100, 140, 65, 105, 105, 100, 130),
        )
        self.reservation_tree.bind("<<TreeviewSelect>>", lambda _event: (
            self._show_checkin(self.bookings[int(self.reservation_tree.selection()[0])])
            if self.reservation_tree.selection() else None
        ))
        search_entry.bind("<KeyRelease>", lambda _event: self._show_reservations(search_entry.get()))
        self._show_reservations("")

    # ------------------------------------------------------------
    # CHECK-IN MANAGEMENT
    # Handles reservation check-in and walk-in room assignments.
    # ------------------------------------------------------------

    # Display the check-in form or save a reservation/walk-in check-in.
    def _show_checkin(self, selected_booking=None, action="show", fields=None):
        self.active_admin_page.set("Check-in")
        if action == "save":
            values = {key: widget.get().strip() for key, widget in fields["entries"].items()}
            walk_in = fields["walk_in"]
            if not all(values.get(key) for key in ("name", "ic", "room_type", "check_in", "check_out")):
                messagebox.showwarning("Missing Information", "Complete the guest, room and date information.", parent=self)
                return
            try:
                check_in = datetime.strptime(values["check_in"], "%Y-%m-%d").date()
                check_out = datetime.strptime(values["check_out"], "%Y-%m-%d").date()
                adults = int(values["adults"] or "1")
                children = int(values["children"] or "0")
                quantity = int(values["amount_of_room"] or "1")
                if check_out <= check_in or adults < 1 or children < 0 or quantity < 1:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Check Details", "Use YYYY-MM-DD dates, check-out after check-in, at least one adult and at least one room.", parent=self)
                return
            if selected_booking is not None and not walk_in:
                if check_in > date.today() or check_out <= date.today():
                    messagebox.showwarning("Check-in Date", "This reservation is not scheduled for check-in today.", parent=self)
                    return
            payment_method = fields["payment"].get().strip() if walk_in else selected_booking.get("payment_method", "")
            if walk_in and payment_method not in ("Cash", "Credit/Debit Card", "E-wallet"):
                messagebox.showwarning("Payment Method", "Choose a payment method for the walk-in customer.", parent=self)
                return

            self._load_data()
            # Reloading the file creates new dictionary objects, so find the selected
            # reservation again before excluding it from the room availability check.
            booking_to_update = None
            if selected_booking is not None and not walk_in:
                booking_to_update = next((saved for saved in self.bookings
                    if saved.get("name", "").casefold() == selected_booking.get("name", "").casefold()
                    and saved.get("ic", "").casefold() == selected_booking.get("ic", "").casefold()
                    and saved.get("check_in", "") == selected_booking.get("check_in", "")
                    and saved.get("check_out", "") == selected_booking.get("check_out", "")
                    and saved.get("room_type", "").casefold() == selected_booking.get("room_type", "").casefold()
                    and saved.get("room_number", "") == selected_booking.get("room_number", "")
                    and saved.get("amount_of_room", "1") == selected_booking.get("amount_of_room", "1")
                    and saved.get("status", "").casefold() == "confirmed"), None)
                if booking_to_update is None:
                    messagebox.showwarning("Reservation Not Found", "This reservation may already have been checked in.", parent=self)
                    self._show_reservations()
                    return
            # Check all rooms of this type so an existing reservation can keep
            # the room numbers that were already assigned when it was booked.
            available_numbers = self._available_room_numbers(
                values["room_type"], check_in, check_out, None,
                exclude_booking=booking_to_update,
            )
            if len(available_numbers) < quantity:
                messagebox.showwarning(
                    "No Rooms Available",
                    f"Only {len(available_numbers)} room(s) are available for this room type and date range.",
                    parent=self,
                )
                return

            if booking_to_update is not None:
                # Reuse the customer's reserved rooms whenever they remain free.
                reserved_numbers = [
                    number.strip()
                    for number in str(booking_to_update.get("room_number", "")).split(",")
                    if number.strip()
                ]
            else:
                reserved_numbers = []

            if len(reserved_numbers) == quantity and all(
                number in available_numbers for number in reserved_numbers
            ):
                assigned_numbers = reserved_numbers
            else:
                # Old records without a complete room assignment receive the
                # first available rooms of the selected room type.
                assigned_numbers = available_numbers[:quantity]

            if walk_in:
                price = next((r["price_per_night"] for r in self.rooms
                              if r["room_type"].casefold() == values["room_type"].casefold()), 0)
                nights = (check_out - check_in).days
                total = price * nights * quantity
                promo = values.get("promo_code", "").upper()
                if promo == "LONGSTAY15" and nights >= 5:
                    total *= 0.85
                elif promo == "WEEKEND20" and nights >= 2 and check_in.weekday() in (4, 5):
                    total -= price * quantity * 0.20
                elif promo:
                    messagebox.showwarning("Promo Code", "The promo code is invalid or its conditions are not met.", parent=self)
                    return
                booking = {
                    "name": values["name"], "email": values.get("email", "") or "-",
                    "hp": values.get("hp", "") or "-", "ic": values["ic"],
                    "room_type": values["room_type"], "room_number": ", ".join(assigned_numbers),
                    "check_in": check_in.isoformat(), "check_out": check_out.isoformat(),
                    "amount_of_room": str(quantity), "adults": str(adults), "children": str(children),
                    "special_requests": values.get("special_requests", ""), "promo_code": promo,
                    "total_price": f"{total:.2f}", "payment_method": payment_method,
                    "status": "Checked In",
                }
                self.bookings.append(booking)
            else:
                booking = booking_to_update
                booking["room_number"] = ", ".join(assigned_numbers)
                booking["status"] = "Checked In"
                booking["payment_method"] = payment_method
            if not self._save_data():
                if walk_in:
                    self.bookings.pop()
                else:
                    booking["status"] = "Confirmed"
                return
            self._load_data()
            messagebox.showinfo("Check-in Complete", f"{booking['name']} has been checked in.\n\nRoom number: {', '.join(assigned_numbers)}\nPayment method: {payment_method}\nTotal paid: RM{float(booking.get('total_price', 0) or 0):.2f}\n\nThe room assignment has been saved.", parent=self)
            self._show_checkin()
            return

        self._load_data()
        self._clear_content()
        is_walk_in = selected_booking is None

        # Put the form and the checked-in guest table inside one scrollable page.
        page_outer = tk.Frame(self.content_area, bg=COLORS["bg"])
        page_outer.pack(fill="both", expand=True)
        page_canvas = tk.Canvas(page_outer, bg=COLORS["bg"], highlightthickness=0, bd=0)
        page_scrollbar = ttk.Scrollbar(page_outer, orient="vertical", command=page_canvas.yview)
        page_canvas.configure(yscrollcommand=page_scrollbar.set)
        page_scrollbar.pack(side="right", fill="y")
        page_canvas.pack(side="left", fill="both", expand=True)
        page_body = tk.Frame(page_canvas, bg=COLORS["bg"])
        page_window = page_canvas.create_window((0, 0), window=page_body, anchor="nw")
        page_body.bind("<Configure>", lambda _event: page_canvas.configure(scrollregion=page_canvas.bbox("all")))
        page_canvas.bind("<Configure>", lambda event: page_canvas.itemconfigure(page_window, width=event.width))

        # The table's own mouse-wheel binding takes priority when the pointer is over it.
        # Elsewhere, the whole Check-in page scrolls to the guest table below the form.
        self._checkin_scroll_bindings = [
            ("<MouseWheel>", self.bind_all(
                "<MouseWheel>",
                lambda event, target=page_canvas: (target.yview_scroll(
                    -int(event.delta / 120) if event.delta else -1, "units"), "break")[1], add="+")),
            ("<Button-4>", self.bind_all(
                "<Button-4>", lambda _event, target=page_canvas: (target.yview_scroll(-1, "units"), "break")[1], add="+")),
            ("<Button-5>", self.bind_all(
                "<Button-5>", lambda _event, target=page_canvas: (target.yview_scroll(1, "units"), "break")[1], add="+")),
        ]

        # Keep one consistent heading for both reservation and walk-in guests.
        tk.Label(page_body, text="Check-in", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Georgia", 23, "bold")).pack(anchor="w")
        subtitle = ("Review the selected reservation and assign an available room."
                    if selected_booking is not None else
                    "Enter walk-in guest information and assign an available room.")
        tk.Label(page_body, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 10))
        card = tk.Frame(page_body, bg=COLORS["card"], padx=16, pady=14,
                        highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="x", pady=(0, 12))
        form = tk.Frame(card, bg=COLORS["card"])
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)
        today = date.today()
        defaults = {
            "name": selected_booking.get("name", "") if selected_booking else "",
            "email": selected_booking.get("email", "") if selected_booking else "",
            "hp": selected_booking.get("hp", "") if selected_booking else "",
            "ic": selected_booking.get("ic", "") if selected_booking else "",
            "check_in": selected_booking.get("check_in", today.isoformat()) if selected_booking else today.isoformat(),
            "check_out": selected_booking.get("check_out", (today + timedelta(days=1)).isoformat()) if selected_booking else (today + timedelta(days=1)).isoformat(),
            "adults": selected_booking.get("adults", "1") if selected_booking else "1",
            "children": selected_booking.get("children", "0") if selected_booking else "0",
            "amount_of_room": selected_booking.get("amount_of_room", "1") if selected_booking else "1",
            "special_requests": selected_booking.get("special_requests", "") if selected_booking else "",
            "promo_code": selected_booking.get("promo_code", "") if selected_booking else "",
        }
        room_values = list(dict.fromkeys(room["room_type"] for room in self.rooms if room["status"].casefold() == "available"))
        if not room_values:
            room_values = list(dict.fromkeys(room["room_type"] for room in self.rooms))
        defaults["room_type"] = selected_booking.get("room_type", room_values[0] if room_values else "") if selected_booking else (room_values[0] if room_values else "")
        entries = {}
        labels = (("name", "Guest name *"), ("email", "Email"), ("hp", "Phone number"),
                  ("ic", "IC / Passport *"), ("room_type", "Room type *"),
                  ("check_in", "Check-in * (YYYY-MM-DD)"), ("check_out", "Check-out * (YYYY-MM-DD)"),
                  ("amount_of_room", "Number of rooms"), ("adults", "Adults"),
                  ("children", "Children"), ("special_requests", "Special requests"),
                  ("promo_code", "Promo code"))
        for index, (key, label) in enumerate(labels):
            row, col = divmod(index, 2)
            cell = tk.Frame(form, bg=COLORS["card"])
            cell.grid(row=row * 2, column=col * 2, sticky="ew", padx=(0, 12), pady=4)
            tk.Label(cell, text=label, bg=COLORS["card"], fg=COLORS["text"],
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            if key == "room_type":
                widget = ttk.Combobox(cell, values=room_values, state="readonly")
                widget.set(defaults[key])
            else:
                widget = tk.Entry(cell, font=("Segoe UI", 9), relief="solid", bd=1)
                widget.insert(0, str(defaults[key]))
            widget.pack(fill="x", ipady=4, pady=(3, 0))
            if selected_booking is not None:
                widget.configure(state="disabled")
            entries[key] = widget
            form.grid_columnconfigure(col * 2, weight=1)

        tk.Label(form, text="Payment method" if is_walk_in else "Reservation payment",
                 bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 8, "bold")).grid(
                     row=12, column=0, sticky="w", pady=(8, 3))
        payment_var = tk.StringVar(value="Cash" if is_walk_in else selected_booking.get("payment_method", ""))
        if is_walk_in:
            payment_box = ttk.Combobox(form, textvariable=payment_var,
                                       values=("Cash", "Credit/Debit Card", "E-wallet"), state="readonly")
            payment_box.grid(row=13, column=0, sticky="ew", pady=(0, 8))
        else:
            tk.Label(form, text=f"{payment_var.get()} (selected during reservation)",
                     bg=COLORS["pale"], fg=COLORS["text"], padx=9, pady=7).grid(row=13, column=0, sticky="ew", pady=(0, 8))
        if is_walk_in:
            tk.Label(form, text="Walk-in payment is recorded as completed when Check In is confirmed.",
                     bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(
                         row=13, column=1, columnspan=3, sticky="w", padx=8)

        actions = tk.Frame(card, bg=COLORS["card"])
        actions.pack(fill="x", pady=(8, 0))
        tk.Button(actions, text="Confirm Check-in  →",
                  command=lambda: self._show_checkin(selected_booking, "save", {"entries": entries, "payment": payment_var, "walk_in": is_walk_in}),
                  bg=COLORS["accent"], fg="white", relief="flat", padx=16, pady=9,
                  font=("Segoe UI", 9, "bold")).pack(side="right")
        if selected_booking is not None:
            tk.Button(actions, text="Back to Reservations", command=self._show_reservations,
                      bg=COLORS["pale"], fg=COLORS["accent"], relief="flat", padx=14, pady=9).pack(side="right", padx=8)

        panel = tk.Frame(page_body, bg=COLORS["card"], padx=12, pady=10)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, text=f"Currently Checked-in Guests ({len(self.arrivals)})", bg=COLORS["card"],
                 fg=COLORS["accent"], font=("Georgia", 14, "bold")).pack(anchor="w")
        tree = self._create_table(panel, ("Customer", "Room Type", "Room Number", "Check-in", "Check-out", "Payment Method"),
                                  (150, 140, 105, 105, 105, 140))
        for index, booking in enumerate(self.bookings):
            if booking.get("status", "").casefold() != "checked in":
                continue
            tree.insert("", "end", iid=str(index), values=(booking.get("name", ""), booking.get("room_type", ""),
                        booking.get("room_number", ""), booking.get("check_in", ""), booking.get("check_out", ""),
                        booking.get("payment_method", "")), tags=("even" if index % 2 == 0 else "odd",))
        tree.bind("<<TreeviewSelect>>", lambda _event: (
            self._show_checkout(self.bookings[int(tree.selection()[0])]) if tree.selection() else None
        ))

    # ------------------------------------------------------------
    # CHECK-OUT MANAGEMENT
    # Displays checked-in guests and records their check-out.
    # ------------------------------------------------------------
    def _show_checkout(self, selected_booking=None, finish=False):
        self.active_admin_page.set("Check-out")
        self._load_data()
        self._clear_content()
        tk.Label(self.content_area, text="Check-out", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Georgia", 23, "bold")).pack(anchor="w")
        tk.Label(self.content_area,
                 text="Records of guests who have completed their check-out.",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 12))

        if selected_booking is not None:
            selected = next((booking for booking in self.bookings
                             if booking.get("name", "").casefold() == selected_booking.get("name", "").casefold()
                             and booking.get("ic", "").casefold() == selected_booking.get("ic", "").casefold()
                             and booking.get("check_in", "") == selected_booking.get("check_in", "")
                             and booking.get("room_number", "") == selected_booking.get("room_number", "")
                             and booking.get("status", "").casefold() in ("checked in", "checked out")), None)
            if selected is None:
                messagebox.showwarning("Guest Not Found", "This guest record could not be found.", parent=self)
                self._show_checkout()
                return

            if finish:
                if selected.get("status", "").casefold() != "checked in":
                    messagebox.showinfo("Already Checked Out", "This guest has already checked out.", parent=self)
                    self._show_checkout(selected)
                    return
                selected["status"] = "Checked Out"
                if not self._save_data():
                    selected["status"] = "Checked In"
                    return
                self._load_data()
                messagebox.showinfo(
                    "Check-out Complete",
                    f"{selected_booking.get('name', '')} has checked out successfully.\n"
                    f"Room number: {selected_booking.get('room_number', '')}", parent=self
                )
                self._show_checkout()
                return

            card = tk.Frame(self.content_area, bg=COLORS["card"], padx=22, pady=18,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(fill="x")
            tk.Label(card, text=selected.get("name", ""), bg=COLORS["card"], fg=COLORS["text"],
                     font=("Georgia", 18, "bold")).pack(anchor="w", pady=(0, 10))
            details = (
                "IC / Passport: " + selected.get("ic", ""),
                "Room type: " + selected.get("room_type", ""),
                "Room number: " + selected.get("room_number", ""),
                "Check-in: " + selected.get("check_in", ""),
                "Scheduled check-out: " + selected.get("check_out", ""),
                "Payment method: " + selected.get("payment_method", ""),
                f"Total price: RM {float(selected.get('total_price', 0) or 0):.2f}",
                "Stay status: " + selected.get("status", ""),
            )
            for value in details:
                tk.Label(card, text=value, bg=COLORS["card"], fg=COLORS["text"],
                         font=("Segoe UI", 9)).pack(anchor="w", pady=2)
            if selected.get("status", "").casefold() == "checked in":
                tk.Button(card, text="Confirm Check-out",
                          command=lambda saved=selected: self._show_checkout(saved, True),
                          bg=COLORS["red"], fg="white", relief="flat", padx=16, pady=9,
                          font=("Segoe UI", 9, "bold")).pack(anchor="e", pady=(15, 0))
            else:
                tk.Label(card, text="This stay has already been checked out.",
                         bg=COLORS["pale"], fg=COLORS["green"], padx=10, pady=8,
                         font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(14, 0))
            tk.Button(card, text="Back to Check-out Records", command=self._show_checkout,
                      bg=COLORS["pale"], fg=COLORS["accent"], relief="flat", padx=14, pady=8).pack(anchor="e", pady=(8, 0))
            return

        panel = tk.Frame(self.content_area, bg=COLORS["card"], padx=12, pady=10)
        panel.pack(fill="both", expand=True)
        all_stays = [(index, booking) for index, booking in enumerate(self.bookings)
                     if booking.get("status", "").casefold() == "checked out"]
        tk.Label(panel, text=f"Completed Check-outs ({len(all_stays)})",
                 bg=COLORS["card"], fg=COLORS["accent"], font=("Georgia", 14, "bold")).pack(anchor="w")
        tree = self._create_table(
            panel,
            ("Customer", "Room Type", "Room Number", "Check-in", "Scheduled Check-out", "Payment Method", "Status"),
            (155, 145, 110, 110, 135, 135, 105),
        )
        for row_index, (booking_index, booking) in enumerate(all_stays):
            tree.insert(
                "", "end", iid=str(booking_index),
                values=(booking.get("name", ""), booking.get("room_type", ""),
                        booking.get("room_number", ""), booking.get("check_in", ""),
                        booking.get("check_out", ""), booking.get("payment_method", ""),
                        booking.get("status", "")),
                tags=("even" if row_index % 2 == 0 else "odd",),
            )
        tree.bind("<<TreeviewSelect>>", lambda _event: (
            self._show_checkout(self.bookings[int(tree.selection()[0])]) if tree.selection() else None
        ))
        if not all_stays:
            tk.Label(panel, text="No completed check-out records yet.",
                     bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(pady=15)

    # Find room numbers that have no overlapping reservation for the requested dates.
    def _available_room_numbers(self, room_type, check_in, check_out, quantity=None, exclude_booking=None):
        self.rooms = self._read_rooms()
        available = []
        for room in self.rooms:
            if room["room_type"].casefold() != room_type.casefold() or room["status"].casefold() != "available":
                continue
            reserved = False
            for saved in self.bookings:
                if exclude_booking is not None and saved is exclude_booking:
                    continue
                if saved.get("status", "").casefold() in ("cancelled", "canceled", "rejected", "checked out"):
                    continue
                room_numbers = {
                    part.strip() for part in str(saved.get("room_number", "")).split(",")
                    if part.strip()
                }
                if room["room_number"] not in room_numbers:
                    continue
                try:
                    saved_in = datetime.strptime(saved["check_in"], "%Y-%m-%d").date()
                    saved_out = datetime.strptime(saved["check_out"], "%Y-%m-%d").date()
                except (KeyError, ValueError):
                    continue
                if check_in < saved_out and check_out > saved_in:
                    reserved = True
                    break
            if not reserved:
                available.append(room["room_number"])
        return available if quantity is None else available[:quantity]

    # ------------------------------------------------------------
    # MENU MANAGEMENT
    # Handles menu display, editing, adding and removing items.
    # ------------------------------------------------------------

    # Manage the food and drink menu, including adding, editing and removing items.
    def _show_menu_management(self, category="All", action=None, data=None):
        self.active_admin_page.set("Menu Management")

        # Let the admin choose a picture from the computer.
        if action == "browse":
            selected_file = filedialog.askopenfilename(
                parent=self,
                title="Choose food picture",
                filetypes=(("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")),
            )
            if selected_file and data is not None:
                data.delete(0, tk.END)
                data.insert(0, selected_file)
            return

        # Save a new menu item or update an existing item.
        if action == "save":
            form_data = data
            entries = form_data["entries"]
            mode = form_data["mode"]
            original_id = form_data.get("original_id", "")
            item = {
                key: widget.get().strip()
                for key, widget in entries.items()
                if key != "description"
            }
            item["description"] = entries["description"].get("1.0", "end").strip()

            if not all(item.get(key) for key in ("id", "name", "category", "price", "image")):
                messagebox.showwarning(
                    "Missing Information",
                    "Complete the item ID, name, category, price and picture.",
                    parent=self,
                )
                return

            try:
                price = float(item["price"])
                if not math.isfinite(price) or price < 0:
                    raise ValueError
            except (TypeError, ValueError):
                messagebox.showwarning("Invalid Price", "Enter a valid price of zero or more.", parent=self)
                return

            menu_items = self._read_menu_items()
            existing_index = next(
                (index for index, saved in enumerate(menu_items)
                 if saved["id"].casefold() == str(original_id).casefold()),
                None,
            ) if mode == "edit" else None

            if mode == "edit" and existing_index is None:
                messagebox.showwarning(
                    "Menu Item Not Found",
                    "This item is no longer in the menu. Refresh the menu and try again.",
                    parent=self,
                )
                self._show_menu_management(category)
                return

            if mode == "add" and any(
                saved["id"].casefold() == item["id"].casefold() for saved in menu_items
            ):
                messagebox.showwarning(
                    "Duplicate Item ID",
                    "This item ID already exists. Enter a different ID.",
                    parent=self,
                )
                return

            try:
                self.images_folder.mkdir(exist_ok=True)
                original_item = menu_items[existing_index] if existing_index is not None else None
                image_text = item["image"].strip()

                # When editing, keep the current image if the admin did not choose
                # a replacement. This also avoids requiring the same image again.
                if original_item is not None and image_text == str(original_item.get("image", "")).strip():
                    item["image"] = original_item.get("image", "")
                else:
                    source_image = Path(image_text)
                    if not source_image.is_file():
                        image_in_assets = self.images_folder / source_image.name
                        if image_in_assets.is_file():
                            source_image = image_in_assets
                    if not source_image.is_file():
                        messagebox.showwarning(
                            "Picture Not Found",
                            "Choose an existing image file.",
                            parent=self,
                        )
                        return

                    destination = self.images_folder / source_image.name
                    if source_image.resolve() != destination.resolve():
                        # Avoid overwriting another menu picture when filenames match.
                        if destination.exists():
                            stem = source_image.stem
                            suffix = source_image.suffix
                            counter = 2
                            while destination.exists():
                                destination = self.images_folder / f"{stem}_{counter}{suffix}"
                                counter += 1
                        shutil.copy2(source_image, destination)
                    item["image"] = destination.name

                item["price"] = f"{price:.2f}"
                if mode == "edit":
                    menu_items[existing_index] = item
                else:
                    menu_items.append(item)

                self._write_menu_items(menu_items)
            except (OSError, ImportError, ValueError, SyntaxError) as error:
                messagebox.showerror("Could Not Save Menu Item", str(error), parent=self)
                return

            if mode == "edit":
                messagebox.showinfo("Menu Updated", f"{item['name']} has been updated.", parent=self)
            else:
                messagebox.showinfo("Menu Updated", f"{item['name']} has been added to the hotel menu.", parent=self)
            self._show_menu_management(item["category"])
            return

        # Remove the selected item only after the admin confirms the action.
        if action == "remove":
            item_id = str(data or "").strip()
            menu_items = self._read_menu_items()
            selected_item = next(
                (saved for saved in menu_items if saved["id"].casefold() == item_id.casefold()),
                None,
            )
            if selected_item is None:
                messagebox.showwarning("Menu Item Not Found", "This item is no longer in the menu.", parent=self)
                self._show_menu_management(category)
                return
            confirmed = messagebox.askyesno(
                "Remove Menu Item",
                f"Remove {selected_item['name']} from the menu?\n\n"
                "Existing orders will keep their saved item details.",
                parent=self,
            )
            if not confirmed:
                return
            menu_items = [saved for saved in menu_items if saved["id"].casefold() != item_id.casefold()]
            try:
                self._write_menu_items(menu_items)
            except (OSError, ImportError, ValueError, SyntaxError) as error:
                messagebox.showerror("Could Not Remove Menu Item", str(error), parent=self)
                return
            messagebox.showinfo("Menu Updated", f"{selected_item['name']} has been removed from the menu.", parent=self)
            self._show_menu_management(category)
            return

        # Load current menu records and available category filters.
        menu_items = self._read_menu_items()
        categories = ["All"] + sorted(set(item["category"] for item in menu_items if item.get("category")))

        # Show the same form for creating a new item and editing an existing one.
        if action in ("add", "edit"):
            mode = action
            original_item = None
            if mode == "edit":
                item_id = str(data or "").strip()
                original_item = next(
                    (saved for saved in menu_items if saved["id"].casefold() == item_id.casefold()),
                    None,
                )
                if original_item is None:
                    messagebox.showwarning("Menu Item Not Found", "Select a valid menu item to edit.", parent=self)
                    self._show_menu_management(category)
                    return

            self._clear_content()
            heading = "Edit Food / Drink" if mode == "edit" else "Add Food / Drink"
            instruction = (
                "Update the selected food or drink details. The item ID stays the same so existing orders remain linked."
                if mode == "edit" else
                "Enter the item details and choose a picture from your computer."
            )
            tk.Label(self.content_area, text=heading, bg=COLORS["bg"], fg=COLORS["accent"],
                     font=("Georgia", 23, "bold")).pack(anchor="w")
            tk.Label(self.content_area, text=instruction, bg=COLORS["bg"], fg=COLORS["muted"],
                     font=("Segoe UI", 9), wraplength=850, justify="left").pack(anchor="w", pady=(3, 12))
            card = tk.Frame(self.content_area, bg=COLORS["card"], padx=20, pady=18,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(fill="both", expand=True)
            entries = {}
            field_labels = (
                ("id", "Item ID *"),
                ("name", "Food / drink name *"),
                ("category", "Category *"),
                ("price", "Price (RM) *"),
                ("image", "Food picture *"),
            )
            for index, (key, label) in enumerate(field_labels):
                row, column = divmod(index, 2)
                tk.Label(card, text=label, bg=COLORS["card"], fg=COLORS["text"],
                         font=("Segoe UI", 8, "bold")).grid(
                             row=row * 2, column=column, sticky="w", padx=8, pady=(5, 2)
                         )
                if key == "category":
                    widget = ttk.Combobox(
                        card,
                        values=sorted(set(MENU_CATEGORIES + tuple(
                            saved["category"] for saved in menu_items if saved.get("category")
                        ))),
                        state="readonly",
                    )
                else:
                    widget = tk.Entry(card, font=("Segoe UI", 10), relief="solid", bd=1)
                widget.grid(row=row * 2 + 1, column=column, sticky="ew", padx=8, pady=(2, 10), ipady=5)
                if original_item is not None:
                    field_value = original_item.get(key, "")
                    if key == "price":
                        field_value = f"{float(field_value):.2f}"
                    if key == "category":
                        widget.set(str(field_value))
                    else:
                        widget.insert(0, str(field_value))
                entries[key] = widget
                card.grid_columnconfigure(column, weight=1)

                # Keep item IDs stable because the order history refers to them.
                if key == "id" and mode == "edit":
                    widget.configure(state="disabled")

            tk.Button(
                card,
                text="Browse Picture…",
                command=lambda: self._show_menu_management(category, "browse", entries["image"]),
                bg=COLORS["pale"], fg=COLORS["accent"], relief="flat", padx=12, pady=8,
            ).grid(row=5, column=0, sticky="w", padx=8, pady=(0, 12))
            tk.Label(card, text="Description", bg=COLORS["card"], fg=COLORS["text"],
                     font=("Segoe UI", 8, "bold")).grid(row=6, column=0, sticky="w", padx=8)
            description = tk.Text(card, height=4, font=("Segoe UI", 9), relief="solid", bd=1, wrap="word")
            description.grid(row=7, column=0, columnspan=2, sticky="ew", padx=8, pady=(3, 12))
            if original_item is not None:
                description.insert("1.0", str(original_item.get("description", "")))
            entries["description"] = description

            buttons = tk.Frame(card, bg=COLORS["card"])
            buttons.grid(row=8, column=0, columnspan=2, sticky="e", padx=8)
            tk.Button(
                buttons, text="Cancel", command=lambda: self._show_menu_management(category),
                bg=COLORS["pale"], fg=COLORS["accent"], relief="flat", padx=14, pady=8,
            ).pack(side="right", padx=(8, 0))
            save_label = "Save Changes" if mode == "edit" else "Save Food / Drink"
            tk.Button(
                buttons,
                text=save_label,
                command=lambda: self._show_menu_management(
                    category, "save",
                    {"entries": entries, "mode": mode,
                     "original_id": original_item.get("id", "") if original_item else ""},
                ),
                bg=COLORS["accent"], fg="white", relief="flat", padx=15, pady=8,
            ).pack(side="right")
            return

        # Display the menu items in a table with edit and remove actions.
        self._clear_content()
        tk.Label(self.content_area, text="Menu Management", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Georgia", 23, "bold")).pack(anchor="w")
        top = tk.Frame(self.content_area, bg=COLORS["bg"])
        top.pack(fill="x", pady=(5, 12))
        tk.Label(top, text="Filter by category", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        category_var = tk.StringVar(value=category if category in categories else "All")
        category_box = ttk.Combobox(top, textvariable=category_var, values=categories, state="readonly", width=20)
        category_box.pack(side="left", padx=9)
        category_box.bind("<<ComboboxSelected>>", lambda _event: self._show_menu_management(category_var.get()))
        tk.Button(
            top,
            text="+ Add Food / Drink",
            command=lambda: self._show_menu_management(category_var.get(), "add"),
            bg=COLORS["accent"], fg="white", relief="flat", padx=14, pady=8,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right")

        panel = tk.Frame(self.content_area, bg=COLORS["card"], padx=12, pady=10)
        panel.pack(fill="both", expand=True)
        # Apply the selected category filter, then sort by ID letters and numeric part.
        # For example: A01, A02, A10 (not A01, A10, A02).
        visible = sorted(
            (
                item for item in menu_items
                if category_var.get() == "All" or item["category"] == category_var.get()
            ),
            key=menu_item_sort_key,
        )
        tk.Label(panel, text=f"{category_var.get()} · {len(visible)} item(s)", bg=COLORS["card"],
                 fg=COLORS["accent"], font=("Georgia", 14, "bold")).pack(anchor="w")
        tree = self._create_table(
            panel,
            ("Item ID", "Name", "Category", "Price", "Description", "Image"),
            (85, 165, 120, 90, 280, 130),
        )
        for item in visible:
            tree.insert(
                "", "end", iid=item["id"],
                values=(item["id"], item["name"], item["category"],
                        f"RM {float(item['price']):.2f}", item.get("description", ""), item["image"]),
            )

        tk.Label(
            panel,
            text="Select a food or drink above to edit its details or remove it from the menu.",
            bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(10, 4))
        action_row = tk.Frame(panel, bg=COLORS["card"])
        action_row.pack(fill="x")

        def selected_item_id():
            selection = tree.selection()
            return str(tree.item(selection[0], "values")[0]) if selection else ""

        def edit_selected_item():
            selected_id = selected_item_id()
            if selected_id:
                self._show_menu_management(category_var.get(), "edit", selected_id)

        def remove_selected_item():
            selected_id = selected_item_id()
            if selected_id:
                self._show_menu_management(category_var.get(), "remove", selected_id)

        edit_button = tk.Button(
            action_row, text="Edit Details", command=edit_selected_item,
            bg=COLORS["accent"], fg="white", relief="flat", padx=16, pady=8,
            font=("Segoe UI", 9, "bold"), state="disabled",
        )
        edit_button.pack(side="left", padx=(0, 8))
        remove_button = tk.Button(
            action_row, text="Remove from Menu", command=remove_selected_item,
            bg=COLORS["red"], fg="white", relief="flat", padx=16, pady=8,
            font=("Segoe UI", 9, "bold"), state="disabled",
        )
        remove_button.pack(side="left")

        def update_menu_actions(_event=None):
            state = "normal" if tree.selection() else "disabled"
            edit_button.configure(state=state)
            remove_button.configure(state=state)

        tree.bind("<<TreeviewSelect>>", update_menu_actions)
        tree.bind("<Double-1>", lambda _event: edit_selected_item())

    # Read menu_dict or the six-column text format into one consistent list.
    def _read_menu_items(self):
        if not self.menu_file.is_file():
            return []
        menu_text = self.menu_file.read_text(encoding="utf-8-sig")
        items = []

        # Support the original Python dictionary format used by menu.txt.
        if "menu_dict" in menu_text:
            tree = ast.parse(menu_text, filename=str(self.menu_file))
            assignment = next(
                node for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "menu_dict" for target in node.targets)
            )
            menu_data = ast.literal_eval(assignment.value)
            if isinstance(menu_data, dict):
                for item_id, details in menu_data.items():
                    if isinstance(details, dict):
                        items.append({
                            "id": str(item_id),
                            "name": str(details.get("Name", "")).strip(),
                            "category": str(details.get("Category", "")).strip(),
                            "price": float(details.get("Price", 0)),
                            "image": str(details.get("Image", "")).strip(),
                            "description": str(details.get("Description", "")).strip(),
                        })
            return items

        # Also accept the five-column and six-column text formats.
        for line in menu_text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = [value.strip() for value in line.split("|")]
            if parts and parts[0].casefold() in ("id", "item_id", "food_id"):
                continue
            if len(parts) == 5:
                parts.append("")
            if len(parts) != 6:
                continue
            try:
                price = float(parts[3])
            except ValueError:
                continue
            items.append({
                "id": parts[0], "name": parts[1], "category": parts[2],
                "price": price, "image": parts[4], "description": parts[5],
            })
        return items

    # Save menu records in the text format supported by both Staff and Restaurant.
    def _write_menu_items(self, menu_items):
        # Always save in natural Item ID order so a deleted item added again
        # returns to its correct position instead of being appended at the bottom.
        menu_items = sorted(menu_items, key=menu_item_sort_key)
        lines = ["# ID|Name|Category|Price|Image|Description"]
        for item in menu_items:
            lines.append("|".join(
                self._safe_field(item.get(key, ""))
                for key in ("id", "name", "category", "price", "image", "description")
            ))
        self.menu_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Refresh the customer-facing menu after the file has been updated.
        try:
            import restaurant
            try:
                restaurant.products = restaurant.read_menu()
            except ValueError:
                restaurant.products = []
            if hasattr(restaurant, "IMAGE_CACHE"):
                restaurant.IMAGE_CACHE.clear()
        except ImportError:
            # The file is still saved; the menu module will read it next time it opens.
            pass

    # Save the current order records in the shared order.txt JSON file.
    def _save_orders(self):
        try:
            self.order_file.write_text(json.dumps(self.orders, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
            return True
        except OSError as error:
            messagebox.showerror("Order File Error", f"Could not save order.txt:\n{error}", parent=self)
            return False

    # ------------------------------------------------------------
    # RESTAURANT ORDER MANAGEMENT
    # Displays active restaurant customers and order history.
    # ------------------------------------------------------------
    def _show_table_overview(self, view="current", selected_group=None, action=None):
        self.active_admin_page.set("Table Overview")
        self._load_data()
        for saved_order in self.orders:
            saved_payment = str(saved_order.get("payment", "")).casefold()
            saved_status = str(saved_order.get("payment_status", "")).casefold()
            if saved_payment != "cash" and saved_status in ("", "recorded (demonstration only)"):
                saved_order["payment_status"] = "Paid"
            elif saved_payment == "cash" and not saved_status:
                saved_order["payment_status"] = "Pending"
        if action in ("paid", "leave") and selected_group is not None:
            active_groups = {}
            for order in self.orders:
                if order.get("dining") != "Restaurant dining" or order.get("status", "Received").casefold() in ("left", "completed", "cancelled"):
                    continue
                key = (str(order.get("location", "")).strip(), str(order.get("customer", "")).strip())
                active_groups.setdefault(key, []).append(order)
            keys = list(active_groups)
            if selected_group >= len(keys):
                messagebox.showwarning("Order Not Found", "This restaurant customer is no longer active.", parent=self)
                self._show_table_overview()
                return
            group_orders = active_groups[keys[selected_group]]
            if action == "paid":
                for order in group_orders:
                    order["payment_status"] = "Paid"
                    order["paid_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                unpaid = [order for order in group_orders if order.get("payment_status", "Pending").casefold() != "paid"]
                if unpaid:
                    messagebox.showwarning("Payment Pending", "Record the customer's payment before they leave.", parent=self)
                    self._show_table_overview("details", selected_group)
                    return
                for order in group_orders:
                    order["status"] = "Left"
                    order["left_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self._save_orders():
                self._show_table_overview("current" if action == "paid" else "history")
            return

        active_groups = {}
        for order in self.orders:
            if order.get("dining") != "Restaurant dining":
                continue
            if order.get("status", "Received").casefold() in ("left", "completed", "cancelled"):
                continue
            key = (str(order.get("location", "")).strip(), str(order.get("customer", "")).strip())
            if not key[0] or not key[1]:
                continue
            active_groups.setdefault(key, []).append(order)
        self.table_groups = list(active_groups.values())

        self._clear_content()
        tk.Label(self.content_area, text="Table Overview", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Georgia", 23, "bold")).pack(anchor="w")
        nav = tk.Frame(self.content_area, bg=COLORS["bg"])
        nav.pack(fill="x", pady=(5, 10))
        tk.Button(nav, text="Current Customers", command=lambda: self._show_table_overview("current"),
                  bg=COLORS["accent"] if view == "current" else COLORS["pale"],
                  fg="white" if view == "current" else COLORS["accent"], relief="flat", padx=14, pady=8).pack(side="left", padx=(0, 7))
        tk.Button(nav, text="Order History", command=lambda: self._show_table_overview("history"),
                  bg=COLORS["accent"] if view == "history" else COLORS["pale"],
                  fg="white" if view == "history" else COLORS["accent"], relief="flat", padx=14, pady=8).pack(side="left")

        panel = tk.Frame(self.content_area, bg=COLORS["card"], padx=12, pady=10)
        panel.pack(fill="both", expand=True)
        if view == "current":
            tk.Label(panel, text=f"Customers currently dining ({len(active_groups)})", bg=COLORS["card"],
                     fg=COLORS["accent"], font=("Georgia", 14, "bold")).pack(anchor="w")
            tree = self._create_table(panel, ("Order ID(s)", "Customer", "Table Number", "Orders", "Ordered Items", "Total", "Payment Method", "Payment Status"),
                                      (120, 145, 95, 65, 210, 95, 125, 110))
            self.table_groups = list(active_groups.items())
            for index, (key, group_orders) in enumerate(self.table_groups):
                amount = sum(float(order.get("total", 0) or 0) for order in group_orders)
                items = []
                payment_methods = list(dict.fromkeys(order.get("payment", "") for order in group_orders))
                payment_statuses = [order.get("payment_status", "Pending") for order in group_orders]
                for order in group_orders:
                    for item in order.get("items", []):
                        items.append(f"{item.get('name', 'Item')} x {item.get('quantity', 1)}")
                status_text = "Paid" if all(str(value).casefold() == "paid" for value in payment_statuses) else "Payment pending"
                order_ids = ", ".join(str(order.get("order_id", "")) for order in group_orders)
                tree.insert("", "end", iid=str(index), values=(order_ids, key[1], key[0], len(group_orders),
                            ", ".join(items), f"RM {amount:.2f}", ", ".join(payment_methods), status_text),
                            tags=("even" if index % 2 == 0 else "odd",))
            tree.bind("<<TreeviewSelect>>", lambda _event: (
                self._show_table_overview("details", int(tree.selection()[0])) if tree.selection() else None
            ))
            if not active_groups:
                tk.Label(panel, text="There are no customers currently dining.", bg=COLORS["card"],
                         fg=COLORS["muted"], font=("Segoe UI", 10)).pack(pady=15)
        elif view == "details" and selected_group is not None:
            groups = list(active_groups.items())
            if selected_group >= len(groups):
                self._show_table_overview("current")
                return
            key, group_orders = groups[selected_group]
            tk.Label(panel, text=key[1], bg=COLORS["card"], fg=COLORS["text"],
                     font=("Georgia", 18, "bold")).pack(anchor="w")
            tk.Label(panel, text=f"Table {key[0]}  ·  {len(group_orders)} order(s)", bg=COLORS["card"],
                     fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 8))
            detail_tree = self._create_table(panel, ("Order ID", "Item", "Quantity", "Unit Price", "Item Total"),
                                             (100, 210, 80, 100, 100))
            total_amount = 0.0
            for order in group_orders:
                for item in order.get("items", []):
                    try:
                        quantity = int(item.get("quantity", 1))
                        price = float(item.get("price", 0))
                    except (TypeError, ValueError):
                        quantity, price = 1, 0.0
                    item_total = float(item.get("item_total", price * quantity) or 0)
                    total_amount += item_total
                    detail_tree.insert("", "end", values=(order.get("order_id", ""), item.get("name", ""),
                                      quantity, f"RM {price:.2f}", f"RM {item_total:.2f}"))
            order_total = sum(float(order.get("total", 0) or 0) for order in group_orders)
            methods = ", ".join(dict.fromkeys(order.get("payment", "") for order in group_orders))
            paid_status = "Paid" if all(order.get("payment_status", "Pending").casefold() == "paid" for order in group_orders) else "Payment pending"
            summary = tk.Frame(panel, bg=COLORS["pale"], padx=12, pady=10)
            summary.pack(fill="x", pady=(8, 8))
            tk.Label(summary, text=f"Payment method: {methods}", bg=COLORS["pale"], fg=COLORS["text"],
                     font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(summary, text=f"Payment status: {paid_status}", bg=COLORS["pale"], fg=COLORS["text"],
                     font=("Segoe UI", 9)).pack(anchor="w", pady=2)
            tk.Label(summary, text=f"Total including charges: RM {order_total:.2f}", bg=COLORS["pale"],
                     fg=COLORS["accent"], font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(3, 0))
            buttons = tk.Frame(panel, bg=COLORS["card"])
            buttons.pack(fill="x", pady=(8, 0))
            if paid_status != "Paid":
                tk.Button(buttons, text="Done Payment", command=lambda: self._show_table_overview("current", selected_group, "paid"),
                          bg=COLORS["green"], fg="white", relief="flat", padx=15, pady=9,
                          font=("Segoe UI", 9, "bold")).pack(side="right", padx=(8, 0))
            tk.Button(buttons, text="Leave", command=lambda: self._show_table_overview("current", selected_group, "leave"),
                      bg=COLORS["red"], fg="white", relief="flat", padx=18, pady=9,
                      font=("Segoe UI", 9, "bold")).pack(side="right")
            tk.Button(buttons, text="Back", command=lambda: self._show_table_overview("current"),
                      bg=COLORS["pale"], fg=COLORS["accent"], relief="flat", padx=15, pady=9).pack(side="left")
        else:
            tk.Label(panel, text="Restaurant Order History", bg=COLORS["card"], fg=COLORS["accent"],
                     font=("Georgia", 14, "bold")).pack(anchor="w")
            tree = self._create_table(panel, ("Order ID", "Date", "Customer", "Dining", "Table / Room", "Items", "Total", "Payment Method", "Payment Status", "Status"),
                                      (95, 145, 130, 110, 95, 210, 95, 125, 115, 90))
            history_orders = [order for order in self.orders
                              if (order.get("dining") == "Restaurant dining"
                                  and order.get("status", "").casefold() in ("left", "completed"))
                              or order.get("dining") == "Room delivery"]
            for index, order in enumerate(reversed(history_orders)):
                item_names = ", ".join(f"{item.get('name', 'Item')} x {item.get('quantity', 1)}" for item in order.get("items", []))
                tree.insert("", "end", values=(order.get("order_id", ""), order.get("date", ""),
                            order.get("customer", ""), order.get("dining", ""), order.get("location", ""), item_names,
                            f"RM {float(order.get('total', 0) or 0):.2f}", order.get("payment", ""),
                            order.get("payment_status", "Pending"), order.get("status", "")),
                            tags=("even" if index % 2 == 0 else "odd",))
            if not history_orders:
                tk.Label(panel, text="No restaurant orders have been marked as left yet.", bg=COLORS["card"],
                         fg=COLORS["muted"], font=("Segoe UI", 10)).pack(pady=15)

    # Return to the Staff login page after confirmation.
    def _sign_out(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?", parent=self):
            self.current_user = ""
            self._build_login()
