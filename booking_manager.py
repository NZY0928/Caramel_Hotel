"""Booking and accommodation support functions for Caramel Hotel.

This module handles room/booking text files, date-based room availability,
room-photo loading and the mouse-wheel helpers used by AccommodationPage.
The visible room pages and booking form remain in accommodation.py.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path


class BookingManager:
    """Manage accommodation data and shared helpers for the accommodation screen."""

    def __init__(self, page):
        # Keep a reference to the AccommodationPage so errors and scrolling can
        # be connected to the correct window and widgets.
        self.page = page
        self.base_dir = Path(__file__).resolve().parent
        self.room_file = self.base_dir / "room.txt"
        self.booking_file = self.base_dir / "booking.txt"

        # The project stores general hotel pictures in images/ and room photos
        # in images/room_images/.
        self.image_dir = self.base_dir / "images"
        self.room_image_dir = self.image_dir / "room_images"

        # These field names must match the headings and order in the text files.
        self.room_fields = (
            "room_type", "room_number", "price_per_night",
            "features", "status", "image_filename"
        )
        self.booking_fields = (
            "name", "email", "hp", "ic", "room_type", "room_number",
            "check_in", "check_out", "amount_of_room", "adults", "children",
            "special_requests", "promo_code", "total_price", "payment_method", "status"
        )

    def read_bookings(self):
        """Read saved booking records from booking.txt without changing the file."""
        bookings = []
        if not self.booking_file.exists():
            return bookings
        try:
            with self.booking_file.open("r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()
                    # Ignore blank lines and comment/header notes.
                    if not line or line.startswith("#"):
                        continue
                    parts = [part.strip() for part in line.split("|")]
                    # Ignore the column-heading line if it is present.
                    if [part.lower() for part in parts] == list(self.booking_fields):
                        continue
                    # Only accept rows that have all 16 fields in the correct format.
                    if len(parts) != len(self.booking_fields):
                        continue
                    bookings.append(dict(zip(self.booking_fields, parts)))
        except OSError:
            return []
        return bookings

    def read_rooms(self):
        """Read room details and prices from the six-column room.txt file."""
        rooms = []
        if not self.room_file.exists():
            return rooms
        try:
            with self.room_file.open("r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("//"):
                        continue
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) != len(self.room_fields):
                        continue
                    room = dict(zip(self.room_fields, parts))
                    # Skip a heading row if the room file includes one.
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

    def ensure_booking_file(self):
        """Create booking.txt with the current headings only if it does not exist."""
        if not self.booking_file.exists():
            self.write_booking_file([])

    def write_booking_file(self, bookings):
        """Write the supplied booking records using the current 16-column format."""
        lines = ["# Caramel Hotel booking records (stored locally)", "|".join(self.booking_fields)]
        for booking in bookings:
            lines.append("|".join(self.safe_field(booking.get(field, "")) for field in self.booking_fields))
        try:
            self.booking_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as error:
            messagebox.showerror("File error", f"Could not write booking.txt:\n{error}", parent=self.page)

    @staticmethod
    def safe_field(value):
        """Prevent a value from breaking the pipe-separated text-file format."""
        return str(value).replace("|", "/").replace("\r", " ").replace("\n", " ").strip()

    def append_booking(self, booking):
        """Append one confirmed booking to booking.txt and report whether it succeeded."""
        row = "|".join(self.safe_field(booking.get(field, "")) for field in self.booking_fields)
        try:
            with self.booking_file.open("a", encoding="utf-8") as file:
                file.write(row + "\n")
            return True
        except OSError as error:
            messagebox.showerror("File error", f"Could not save booking.txt:\n{error}", parent=self.page)
            return False

    def room_image_path(self, room):
        """Find the room image in images/room_images or the images folder."""
        filename = str(room.get("image_filename", "")).strip()
        if not filename:
            return None

        folders = (self.room_image_dir, self.image_dir, self.base_dir)
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

    def load_photo(self, room, size):
        """Open a room photo and resize/crop it to fit the requested frame."""
        path = self.room_image_path(room)
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
            # Tkinter can load PNG files directly if Pillow is not installed.
            try:
                return tk.PhotoImage(file=str(path))
            except tk.TclError:
                return None
        except (OSError, ValueError, tk.TclError):
            return None

    def register_scroll_target(self, target, *related_widgets):
        """Register a scrollable canvas/table and the scrollbar attached to it."""
        if target not in self.page._scroll_targets:
            self.page._scroll_targets.append(target)
        for widget in related_widgets:
            # This lets the mouse wheel work while the pointer is over the scrollbar too.
            widget._wheel_scroll_target = target

    def scroll_target_under_pointer(self, event):
        """Find the scrollable widget underneath the current mouse pointer."""
        try:
            widget = self.page.winfo_containing(event.x_root, event.y_root)
        except tk.TclError:
            return None

        while widget is not None:
            target = getattr(widget, "_wheel_scroll_target", None)
            if target is not None:
                try:
                    if target.winfo_exists():
                        return target
                except tk.TclError:
                    pass

            if widget in self.page._scroll_targets:
                try:
                    if widget.winfo_exists():
                        return widget
                except tk.TclError:
                    pass

            widget = getattr(widget, "master", None)
        return None

    def on_mousewheel(self, event):
        """Handle mouse-wheel scrolling on Windows/macOS for the area under the pointer."""
        target = self.scroll_target_under_pointer(event)
        if target is None:
            return None
        delta = int(-1 * (event.delta / 120))
        if delta == 0 and event.delta:
            delta = -1 if event.delta > 0 else 1
        try:
            target.yview_scroll(delta, "units")
        except (tk.TclError, AttributeError):
            return None
        return "break"

    def on_linux_mousewheel(self, event, direction):
        """Handle Linux wheel-up and wheel-down events for the area under the pointer."""
        target = self.scroll_target_under_pointer(event)
        if target is None:
            return None
        try:
            target.yview_scroll(direction, "units")
        except (tk.TclError, AttributeError):
            return None
        return "break"

    @staticmethod
    def feature_list(room):
        """Split the comma-separated room feature text into individual features."""
        return [item.strip() for item in str(room.get("features", "")).split(",") if item.strip()]

    @staticmethod
    def room_numbers_in_booking(booking):
        """Return the physical room numbers stored inside a booking record."""
        value = str(booking.get("room_number", "")).strip()
        return {number.strip() for number in value.split(",") if number.strip()}

    def is_reserved_for_dates(self, room_number, check_in, check_out, bookings=None):
        """Return True when this physical room is already booked for an overlapping date range."""
        if bookings is None:
            bookings = self.read_bookings()
        for booking in bookings:
            status = str(booking.get("status", "")).strip().lower()
            if status in ("cancelled", "canceled", "rejected"):
                continue
            if room_number not in self.room_numbers_in_booking(booking):
                continue
            try:
                booked_in = datetime.strptime(booking["check_in"], "%Y-%m-%d").date()
                booked_out = datetime.strptime(booking["check_out"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            # Check-out is the end boundary: another guest may check in that day.
            if check_in < booked_out and check_out > booked_in:
                return True
        return False

    def available_rooms_for_dates(self, selected_room, check_in, check_out):
        """List unreserved rooms of the same room type for the requested dates."""
        bookings = self.read_bookings()
        selected_type = str(selected_room.get("room_type", "")).strip().casefold()
        available = []
        for room in self.page.rooms:
            if str(room.get("room_type", "")).strip().casefold() != selected_type:
                continue
            if str(room.get("status", "")).strip().lower() != "available":
                continue
            if not self.is_reserved_for_dates(room["room_number"], check_in, check_out, bookings):
                available.append(room)
        chosen_number = str(selected_room.get("room_number", ""))
        available.sort(key=lambda item: (
            str(item.get("room_number", "")) != chosen_number,
            str(item.get("room_number", "")),
        ))
        return available

    def schedule_gallery_photo_resize(self, room, image_widget, image_holder, height):
        """Schedule a resize after Tkinter has calculated the room-card width."""
        try:
            pending = getattr(image_holder, "_photo_resize_after_id", None)
            if pending is not None:
                self.page.after_cancel(pending)
            image_holder._photo_resize_after_id = self.page.after_idle(
                lambda selected=room, target=image_widget, holder=image_holder, h=height:
                    self.resize_gallery_photo(selected, target, holder.winfo_width(), h)
            )
        except tk.TclError:
            pass

    def resize_gallery_photo(self, room, image_widget, width, height):
        """Resize a gallery photo to the real card width without side bars."""
        if width <= 1:
            return
        try:
            if not image_widget.winfo_exists():
                return
        except tk.TclError:
            return
        target_size = (int(width), int(height))
        if getattr(image_widget, "_photo_size", None) == target_size:
            return
        photo = self.load_photo(room, target_size)
        if photo is None:
            return
        image_widget.configure(image=photo)
        image_widget.image = photo
        image_widget._photo_size = target_size
        self.page.photo_refs.append(photo)

    def resize_detail_photo(self, room, image_panel, image_label, width):
        """Resize the detail photo to the left panel width while keeping a 2:1 ratio."""
        width = int(width)
        if width < 2 or not image_panel.winfo_exists() or image_label is None:
            return
        height = max(1, width // 2)
        target_size = (width, height)
        if image_panel.winfo_height() != height:
            image_panel.configure(height=height)
        if getattr(image_label, "_photo_size", None) == target_size:
            return
        photo = self.load_photo(room, target_size)
        if photo is None:
            return
        image_label.configure(image=photo)
        image_label.image = photo
        image_label._photo_size = target_size
        self.page.detail_photo = photo
        self.page.photo_refs.append(photo)
