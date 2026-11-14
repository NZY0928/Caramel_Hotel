import ast
import json
import tkinter as tk
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from tkinter import messagebox, ttk
from PIL import Image, ImageOps, ImageTk


# ------------------------------------------------------------
# CUSTOMER RESTAURANT MENU AND ORDERING
# File locations, colours and charges used by the restaurant pages.
# ------------------------------------------------------------
FOLDER = Path(__file__).resolve().parent
MENU_FILE = FOLDER / "menu.txt"
IMAGE_FOLDER = FOLDER / "images"
ORDERS_FILE = FOLDER / "order.txt"
OLD_ORDERS_FILE = FOLDER / "rorders.txt"  # Keep older records available during the change.

BG_COLOUR = "#DFE2E5"
NAV_COLOUR = "#486B92"
ACTIVE_COLOUR = "#7E93A9"
SECONDARY_COLOUR = "#C5D6E2"
TEXT_COLOUR = "#34465A"
WHITE_COLOUR = "#FFFFFF"
MUTED_COLOUR = "#7E93A9"
TAX_RATE = Decimal("0.06")
SERVICE_CHARGE_RATE = Decimal("0.10")
CENT = Decimal("0.01")
MENU_PHOTO_SIZE = (220, 145)  # Every menu photo uses the same width and height.
IMAGE_CACHE = {}  # Keep resized food pictures so they do not need to be processed again.


# Find the correct image path for a menu item using its file name.
def normalize_image_path(filename):
    image_path = Path(str(filename).strip())
    if image_path.is_absolute():
        return str(image_path)

    # Check the requested name and correct a missing dot before the jpg extension.
    requested_names = [image_path.name.casefold()]
    if requested_names[0].endswith("jpg") and not requested_names[0].endswith(".jpg"):
        requested_names.append(requested_names[0][:-3] + ".jpg")

    folders = (FOLDER / image_path.parent, IMAGE_FOLDER) if len(image_path.parts) > 1 else (IMAGE_FOLDER,)
    for folder in folders:
        if folder.is_dir():
            for candidate in folder.iterdir():
                if not candidate.is_file():
                    continue
                if candidate.name.casefold() in requested_names or candidate.stem.casefold() == image_path.stem.casefold():
                    return str(candidate)
    if len(image_path.parts) == 1:
        return str(IMAGE_FOLDER / requested_names[-1] if len(requested_names) > 1 else image_path)
    return str(FOLDER / image_path)


# Read the food and drink details from menu.txt.
def read_menu():
    if not MENU_FILE.is_file():
        raise FileNotFoundError(f"Menu file not found:\n{MENU_FILE}")
    menu_text = MENU_FILE.read_text(encoding="utf-8-sig")
    products = []

    # Support the menu_dict format used by the original project.
    if "menu_dict" in menu_text:
        try:
            tree = ast.parse(menu_text, filename=str(MENU_FILE))
            assignment = next(
                node for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "menu_dict" for target in node.targets)
            )
            menu_data = ast.literal_eval(assignment.value)
        except (SyntaxError, StopIteration, ValueError) as error:
            raise ValueError(f"{MENU_FILE.name} must contain a valid menu_dict.") from error
        if not isinstance(menu_data, dict):
            raise ValueError("menu_dict must be a dictionary.")
        for item_id, details in menu_data.items():
            try:
                price = Decimal(str(details["Price"]))
                name = str(details["Name"]).strip()
                category = str(details["Category"]).strip()
                image = str(details["Image"]).strip()
            except (KeyError, InvalidOperation, TypeError) as error:
                raise ValueError(f"Menu item {item_id} is missing valid details.") from error
            if not price.is_finite() or price < 0:
                raise ValueError(f"Menu item {item_id} has an invalid price.")
            products.append({
                "id": str(item_id).strip(),
                "name": name,
                "category": category,
                "price": price,
                "image": normalize_image_path(image),
                # The uploaded menu.txt does not currently contain Description fields.
                "description": str(details.get("Description", "")).strip(),
            })
    else:
        # Accept both the old five-column file and the newer six-column file.
        for line_number, line in enumerate(menu_text.splitlines(), start=1):
            if not line.strip() or line.startswith("#"):
                continue

            columns = [part.strip() for part in line.split("|")]

            # Skip the heading row in menu.txt.
            if columns[0].casefold() in ("id", "item_id", "food_id"):
                continue
            if len(columns) == 5:
                columns.append("")
            if len(columns) != 6:
                raise ValueError(
                    f"Menu line {line_number} must use ID|Name|Category|Price|Image|Description."
                )
            item_id, name, category, price_text, image, description = columns
            try:
                price = Decimal(price_text)
            except InvalidOperation as error:
                raise ValueError(f"Menu line {line_number} has an invalid price.") from error
            if not price.is_finite() or price < 0:
                raise ValueError(f"Menu line {line_number} has an invalid price.")
            products.append({
                "id": item_id,
                "name": name,
                "category": category,
                "price": price,
                "image": normalize_image_path(image),
                "description": description,
            })
    if not products:
        raise ValueError("No menu items were found in menu.txt.")
    return products


# Open and crop a food photo to the same size as every other menu photo.
def load_image(filename, size):
    image_path = Path(filename)
    if not image_path.is_absolute():
        image_path = FOLDER / image_path
    if not image_path.is_file():
        return None

    try:
        # Use the file details and requested size as a cache key.
        # If the same image is needed again, reuse its resized PhotoImage.
        file_info = image_path.stat()
        cache_key = (str(image_path.resolve()), tuple(size), file_info.st_mtime_ns, file_info.st_size)
        if cache_key in IMAGE_CACHE:
            return IMAGE_CACHE[cache_key]

        # Close the original image file after it has been resized.
        with Image.open(image_path) as original:
            picture = ImageOps.fit(
                original.convert("RGB"),
                size,
                method=Image.Resampling.LANCZOS,
            )
        photo = ImageTk.PhotoImage(picture)
        IMAGE_CACHE[cache_key] = photo
        return photo
    except (OSError, ValueError, tk.TclError):
        return None


# Show prices in Malaysian Ringgit.
def money(amount):
    return f"RM {Decimal(str(amount)):.2f}"


# Load saved orders from order.txt. 
products = []  # The menu is loaded when the customer opens the Menu page.
orders = []
orders_source = ORDERS_FILE if ORDERS_FILE.is_file() else OLD_ORDERS_FILE
if orders_source.is_file():
    try:
        saved_orders = json.loads(orders_source.read_text(encoding="utf-8"))
        if isinstance(saved_orders, list):
            orders = [item for item in saved_orders if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError):
        orders = []
if not ORDERS_FILE.is_file():
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

# Give older orders a permanent ID if they do not already have one.
highest_order_number = 0
for saved_order in orders:
    saved_id = str(saved_order.get("order_id", "")).strip()
    if saved_id:
        try:
            highest_order_number = max(highest_order_number, int(saved_id.rsplit("-", 1)[-1]))
        except ValueError:
            pass
order_ids_changed = False
for saved_order in orders:
    if not str(saved_order.get("order_id", "")).strip():
        highest_order_number += 1
        saved_order["order_id"] = f"ORD-{highest_order_number:05d}"
        order_ids_changed = True
if order_ids_changed:
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

# Shared menu, basket, order and page information.
basket = {}
image_references = {}
product_cards = {}
category_buttons = {}
selected_category_var = None
subtotal = Decimal("0.00")
tax_amount = Decimal("0.00")
service_charge = Decimal("0.00")
total = Decimal("0.00")
detail_product = None
detail_quantity = 1
detail_image_reference = None
basket_image_references = []
active_page = "Menu"


# Calculate the subtotal, tax, service charge and final order total.
def calculate_total():
    global subtotal, tax_amount, service_charge, total
    if not basket:
        subtotal = tax_amount = service_charge = total = Decimal("0.00")
    else:
        subtotal = sum(
            (row["product"]["price"] * row["quantity"] for row in basket.values()),
            Decimal("0.00"),
        ).quantize(CENT, rounding=ROUND_HALF_UP)
        tax_amount = (subtotal * TAX_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
        service_charge = (subtotal * SERVICE_CHARGE_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
        total = subtotal + tax_amount + service_charge
    if "subtotal_label" in globals() and subtotal_label.winfo_exists():
        subtotal_label.config(text=f"Subtotal: {money(subtotal)}")
        tax_label.config(text=f"Tax ({TAX_RATE * 100}%): {money(tax_amount)}")
        service_label.config(text=f"Service charge ({SERVICE_CHARGE_RATE * 100}%): {money(service_charge)}")
        total_label.config(text=f"Total including charges: {money(total)}")
    return bool(basket)


# Refresh My Orders using the same table layout style as Booking History.
def update_history():
    if "history_tree" not in globals() or not history_tree.winfo_exists():
        return

    history_tree.delete(*history_tree.get_children())
    for index, order in enumerate(reversed(orders)):
        item_names = ", ".join(
            f'{item.get("name", "Item")} x {item.get("quantity", 1)}'
            for item in order.get("items", [])
        )
        history_tree.insert("", "end", values=(
            order.get("order_id", ""),
            order.get("date", ""),
            order.get("customer", ""),
            order.get("dining", ""),
            order.get("location", ""),
            item_names,
            money(order.get("total", "0")),
            order.get("payment", ""),
            order.get("status", "Received"),
        ), tags=("even" if index % 2 == 0 else "odd",))

    if "history_count_label" in globals() and history_count_label.winfo_exists():
        count = len(orders)
        history_count_label.config(text=f"{count} saved order(s) on this device")


# Save a completed order to order.txt and return the customer to the Menu page.
def place_order():
    if not basket:
        messagebox.showwarning("Empty basket", "Please add food or drinks before paying.", parent=window)
        return
    customer = customer_entry.get().strip()
    location = location_entry.get().strip()
    if not customer or not location:
        messagebox.showwarning(
            "Order details", "Enter the customer's name and table or room number.", parent=window
        )
        return
    calculate_total()
    # Continue from the highest saved Order ID so deleting an old order cannot reuse its number.
    highest_order_number = 0
    for saved_order in orders:
        saved_id = str(saved_order.get("order_id", "")).strip()
        if saved_id:
            try:
                highest_order_number = max(highest_order_number, int(saved_id.rsplit("-", 1)[-1]))
            except ValueError:
                pass
    next_order_id = f"ORD-{highest_order_number + 1:05d}"
    order = {
        "order_id": next_order_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": customer,
        "dining": dining_method.get(),
        "location": location,
        "payment": payment_method.get(),
        "items": [
            {
                "id": row["product"]["id"],
                "name": row["product"]["name"],
                "quantity": row["quantity"],
                "description": row["product"].get("description", ""),
                "price": str(row["product"]["price"]),
                "item_total": str(row["product"]["price"] * row["quantity"]),
            }
            for row in basket.values()
        ],
        "subtotal": str(subtotal),
        "tax_rate": str(TAX_RATE),
        "tax": str(tax_amount),
        "service_charge_rate": str(SERVICE_CHARGE_RATE),
        "service_charge": str(service_charge),
        "total": str(total),
        # Cash orders remain unpaid until Staff records the counter payment.
        # Card and e-wallet orders are marked paid in this demonstration system.
        "payment_status": "Pending" if payment_method.get().strip() == "Cash" else "Paid",
        "status": "Eating" if dining_method.get().strip() == "Restaurant dining" else "Received",
    }
    orders.append(order)
    try:
        ORDERS_FILE.write_text(
            json.dumps(orders, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        orders.pop()
        messagebox.showerror("Could not save order", str(error), parent=window)
        return

    basket.clear()
    customer_entry.delete(0, tk.END)
    location_entry.delete(0, tk.END)
    update_basket()
    update_history()
    show_page("Menu")
    payment_note = (
        "Please proceed to the counter to complete your cash payment."
        if order["payment"] == "Cash"
        else "This is a demonstration system; no actual card or e-wallet payment has been processed."
    )
    messagebox.showinfo(
        "Thank you for your order",
        f"Thank you, {customer}!\n\n"
        f"Your order {order['order_id']} has been received successfully.\n"
        f"Order total: {money(order['total'])}\n"
        f"Payment method: {order['payment']}\n\n"
        f"{payment_note}\n\n"
        "Thank you for choosing Caramel Hotel!",
        parent=window,
    )


# Add a selected dish and quantity to the customer's basket.
def add_to_basket(product, quantity=1):
    item_id = product["id"]
    quantity = max(1, min(50, int(quantity)))
    if item_id in basket:
        basket[item_id]["quantity"] = min(50, basket[item_id]["quantity"] + quantity)
    else:
        basket[item_id] = {"product": product, "quantity": quantity}
    update_basket()
    return True


# Open the selected food item on its own detail screen.
def open_food_detail(product):
    global detail_product, detail_quantity, detail_image_reference
    detail_product = product
    detail_quantity = 1
    photo = load_image(product["image"], (760, 340))
    detail_image_reference = photo
    if photo:
        detail_image.configure(image=photo, text="")
    else:
        detail_image.configure(image="", text="Picture unavailable")
    detail_name.configure(text=product["name"])
    detail_description.configure(
        text=product.get("description", "").strip() or "Description is not available yet."
    )
    detail_quantity_label.configure(text=str(detail_quantity))
    detail_add_button.configure(text="Add to Basket")
    show_page("Detail")


# Increase or decrease the quantity on the food detail screen.
def change_detail_quantity(amount):
    global detail_quantity
    detail_quantity = max(1, min(50, detail_quantity + amount))
    detail_quantity_label.configure(text=str(detail_quantity))


# Remove one selected food item from the basket.
def remove_from_basket(item_id):
    basket.pop(item_id, None)
    update_basket()


# Refresh the basket item cards, item count and amount including taxes and charges.
def update_basket():
    global basket_image_references
    basket_image_references = []
    if "basket_items_frame" not in globals() or not basket_items_frame.winfo_exists():
        return
    for child in basket_items_frame.winfo_children():
        child.destroy()

    item_count = sum(row["quantity"] for row in basket.values())
    basket_count_label.config(text=f"{item_count} item(s)")
    nav_basket_count_label.config(text=f"{item_count} item(s)")

    if not basket:
        tk.Label(
            basket_items_frame,
            text="Your basket is empty. Choose a dish from the Menu.",
            bg=WHITE_COLOUR,
            fg=MUTED_COLOUR,
            font=("Arial", 11),
            padx=16,
            pady=25,
        ).pack(fill="x")
    else:
        for product_id, row in basket.items():
            product = row["product"]
            quantity = row["quantity"]
            line_total = product["price"] * quantity
            item_card = tk.Frame(
                basket_items_frame,
                bg=WHITE_COLOUR,
                padx=10,
                pady=10,
                highlightthickness=1,
                highlightbackground=SECONDARY_COLOUR,
            )
            item_card.pack(fill="x", padx=5, pady=5)
            photo = load_image(product["image"], (135, 95))
            if photo:
                basket_image_references.append(photo)
                tk.Label(item_card, image=photo, bg=WHITE_COLOUR).pack(side="left", padx=(0, 12))
            else:
                tk.Label(
                    item_card,
                    text="Photo unavailable",
                    bg=SECONDARY_COLOUR,
                    fg=TEXT_COLOUR,
                    width=18,
                    height=5,
                ).pack(side="left", padx=(0, 12))

            details = tk.Frame(item_card, bg=WHITE_COLOUR)
            details.pack(side="left", fill="both", expand=True)
            tk.Label(
                details,
                text=product["name"],
                bg=WHITE_COLOUR,
                fg=TEXT_COLOUR,
                font=("Arial", 12, "bold"),
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                details,
                text=product.get("description", "").strip() or "No description available.",
                bg=WHITE_COLOUR,
                fg=MUTED_COLOUR,
                font=("Arial", 8),
                anchor="w",
                justify="left",
                wraplength=420,
            ).pack(fill="x", pady=(3, 6))
            tk.Label(
                details,
                text=f"Quantity: {quantity}    Unit price: {money(product['price'])}",
                bg=WHITE_COLOUR,
                fg=TEXT_COLOUR,
                font=("Arial", 9),
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                details,
                text=f"Item total: {money(line_total)}",
                bg=WHITE_COLOUR,
                fg=NAV_COLOUR,
                font=("Arial", 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(3, 0))
            tk.Button(
                item_card,
                text="Remove",
                command=lambda selected=product_id: remove_from_basket(selected),
                bg=WHITE_COLOUR,
                fg=NAV_COLOUR,
                relief="solid",
                bd=1,
                padx=10,
            ).pack(side="right", padx=(8, 0))

    calculate_total()
    basket_canvas.update_idletasks()
    basket_canvas.configure(scrollregion=basket_canvas.bbox("all"))


# Refresh the visible menu cards when the category or search text changes.
def update_menu(event=None):
    search_text = search_entry.get().strip()
    if search_text == "Search dishes or categories...":
        search_text = ""
    search = search_text.casefold()
    category = selected_category_var.get()
    matching_products = [
        product for product in products
        if (category == "All" or product["category"] == category)
        and (
            not search
            or search in product["name"].casefold()
            or search in product["category"].casefold()
        )
    ]

    for product in products:
        product_cards[product["id"]].grid_remove()
    for index, product in enumerate(matching_products):
        product_cards[product["id"]].grid(
            row=index // 3,
            column=index % 3,
            padx=9,
            pady=9,
            sticky="nsew",
        )
    if not matching_products:
        no_results_label.grid(row=0, column=0, columnspan=3, padx=12, pady=20)
    else:
        no_results_label.grid_remove()

    for category_name, button in category_buttons.items():
        selected = category_name == category
        button.config(
            bg=NAV_COLOUR if selected else WHITE_COLOUR,
            fg=WHITE_COLOUR if selected else TEXT_COLOUR,
            activebackground=ACTIVE_COLOUR,
        )
    result_label.config(text=f"{len(matching_products)} dishes")
    product_frame.update_idletasks()
    menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))
    menu_canvas.yview_moveto(0)


# Create one menu card with a fixed-size picture. Clicking the picture opens the detail page.
def add_product_card(product):
    card = tk.Frame(
        product_frame,
        bg=WHITE_COLOUR,
        width=250,
        height=225,
        bd=1,
        relief="solid",
        padx=9,
        pady=9,
    )
    card.grid_propagate(False)

    # Show a fixed-size placeholder first. The actual photo is loaded later
    # in a separate Tkinter callback so the Menu page can appear immediately.
    image_holder = tk.Frame(card, width=MENU_PHOTO_SIZE[0], height=MENU_PHOTO_SIZE[1], bg=SECONDARY_COLOUR)
    image_holder.pack(pady=(0, 7))
    image_holder.pack_propagate(False)
    image_label = tk.Label(
        image_holder,
        text="Loading picture...",
        bg=SECONDARY_COLOUR,
        fg=TEXT_COLOUR,
        cursor="hand2",
    )
    image_label.pack(fill="both", expand=True)
    card.menu_image_label = image_label
    image_label.bind("<Button-1>", lambda _event, selected=product: open_food_detail(selected))
    name_label = tk.Label(
        card,
        text=product["name"],
        font=("Arial", 11, "bold"),
        bg=WHITE_COLOUR,
        fg=TEXT_COLOUR,
        wraplength=220,
        cursor="hand2",
    )
    name_label.pack(fill="x")
    name_label.bind("<Button-1>", lambda _event, selected=product: open_food_detail(selected))
    tk.Label(
        card,
        text=f'{product["category"]}  ·  {money(product["price"])}',
        font=("Arial", 9),
        bg=WHITE_COLOUR,
        fg=NAV_COLOUR,
        wraplength=220,
    ).pack(pady=(5, 0))
    return card


# Build the menu, food detail, basket and My Orders screens inside main.py.
def build_restaurant_ui(parent):
    global window, header, heading_label, page_area, pages, nav_basket_count_label
    global history_count_label
    global menu_canvas, menu_scrollbar, product_frame, no_results_label, result_label, search_entry
    global detail_image, detail_name, detail_description
    global detail_quantity_label, detail_add_button
    global basket_canvas, basket_items_frame, basket_count_label
    global subtotal_label, tax_label, service_label, total_label
    global customer_entry, dining_method, location_entry, payment_method
    global history_tree, selected_category_var, category_buttons, product_cards
    global image_references, active_page, show_page

    window = parent
    window.configure(bg=BG_COLOUR)

    # The Menu heading stays on the left, with Basket and My Orders on the right.
    header = tk.Frame(window, bg=BG_COLOUR)
    header.pack(fill="x", padx=22, pady=(16, 8))

    heading_area = tk.Frame(header, bg=BG_COLOUR)
    heading_area.pack(side="left", fill="x", expand=True)
    heading_label = tk.Label(
        heading_area,
        text="MENU",
        font=("Arial", 19, "bold"),
        bg=BG_COLOUR,
        fg=NAV_COLOUR,
    )
    heading_label.pack(anchor="w")
    tk.Label(
        heading_area,
        text="Explore our food and drinks.",
        font=("Arial", 10),
        bg=BG_COLOUR,
        fg=MUTED_COLOUR,
    ).pack(anchor="w", pady=(3, 0))

    nav = tk.Frame(header, bg=BG_COLOUR)
    nav.pack(side="right", anchor="e", pady=(4, 0))
    nav_basket_count_label = tk.Label(
        nav,
        text="0 item(s)",
        bg=BG_COLOUR,
        fg=NAV_COLOUR,
        font=("Arial", 9, "bold"),
    )
    nav_basket_count_label.pack(side="left", padx=(0, 6))
    basket_button = tk.Button(
        nav,
        text="Basket",
        command=lambda: show_page("Basket"),
        bg=SECONDARY_COLOUR,
        fg=NAV_COLOUR,
        activebackground=ACTIVE_COLOUR,
        activeforeground=WHITE_COLOUR,
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=14,
        pady=9,
        font=("Arial", 9, "bold"),
    )
    basket_button.pack(side="left", padx=(0, 7))
    orders_button = tk.Button(
        nav,
        text="My Orders",
        command=lambda: show_page("Orders"),
        bg=SECONDARY_COLOUR,
        fg=NAV_COLOUR,
        activebackground=ACTIVE_COLOUR,
        activeforeground=WHITE_COLOUR,
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=14,
        pady=9,
        font=("Arial", 9, "bold"),
    )
    orders_button.pack(side="left")

    page_area = tk.Frame(window, bg=BG_COLOUR)
    page_area.pack(fill="both", expand=True, padx=18, pady=(4, 16))
    pages = {}
    for page_name in ("Menu", "Detail", "Basket", "Orders"):
        page = tk.Frame(page_area, bg=BG_COLOUR)
        page.grid(row=0, column=0, sticky="nsew")
        pages[page_name] = page
    page_area.rowconfigure(0, weight=1)
    page_area.columnconfigure(0, weight=1)

    # Switch between the four restaurant screens. The food-detail page hides
    # the restaurant heading and its Basket/My Orders buttons. The shared
    # Caramel Hotel navigation in main.py remains visible.
    def show_page(page_name):
        global active_page
        active_page = page_name
        pages[page_name].tkraise()
        if page_name == "Detail":
            header.pack_forget()
        elif not header.winfo_manager():
            header.pack(before=page_area, fill="x", padx=22, pady=(16, 8))

        basket_button.config(
            bg=NAV_COLOUR if page_name == "Basket" else SECONDARY_COLOUR,
            fg=WHITE_COLOUR if page_name == "Basket" else NAV_COLOUR,
        )
        orders_button.config(
            bg=NAV_COLOUR if page_name == "Orders" else SECONDARY_COLOUR,
            fg=WHITE_COLOUR if page_name == "Orders" else NAV_COLOUR,
        )
        if page_name == "Basket":
            update_basket()
        elif page_name == "Orders":
            update_history()

    # Menu page: search, categories and a scrollable grid of food pictures.
    menu_page = pages["Menu"]
    menu_page.rowconfigure(0, weight=1)
    menu_page.columnconfigure(0, weight=1)
    menu_panel = tk.Frame(menu_page, bg=WHITE_COLOUR, padx=12, pady=12)
    menu_panel.grid(row=0, column=0, sticky="nsew")
    menu_panel.rowconfigure(2, weight=1)
    menu_panel.columnconfigure(0, weight=1)

    search_entry = ttk.Entry(menu_panel, font=("Arial", 10))
    search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 9))
    search_entry.insert(0, "Search dishes or categories...")
    search_entry.configure(foreground=MUTED_COLOUR)
    search_entry.bind(
        "<FocusIn>",
        lambda _event: (
            search_entry.delete(0, tk.END), search_entry.configure(foreground=TEXT_COLOUR)
        ) if search_entry.get() == "Search dishes or categories..." else None,
    )
    search_entry.bind(
        "<FocusOut>",
        lambda _event: (
            search_entry.insert(0, "Search dishes or categories..."),
            search_entry.configure(foreground=MUTED_COLOUR),
            update_menu(),
        ) if not search_entry.get().strip() else None,
    )
    search_entry.bind("<KeyRelease>", update_menu)

    selected_category_var = tk.StringVar(value="All")
    category_frame = tk.Frame(menu_panel, bg=WHITE_COLOUR)
    category_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    category_buttons = {}
    categories = ["All"] + list(dict.fromkeys(item["category"] for item in products))
    for index, category in enumerate(categories):
        button = tk.Button(
            category_frame,
            text=category,
            command=lambda value=category: (selected_category_var.set(value), update_menu()),
            bg=WHITE_COLOUR,
            fg=TEXT_COLOUR,
            activebackground=SECONDARY_COLOUR,
            relief="solid",
            bd=1,
            padx=10,
            pady=5,
            font=("Arial", 8),
        )
        button.grid(row=0, column=index, padx=3, sticky="ew")
        category_buttons[category] = button
        category_frame.columnconfigure(index, weight=1)

    menu_body = tk.Frame(menu_panel, bg=WHITE_COLOUR)
    menu_body.grid(row=2, column=0, sticky="nsew")
    menu_body.rowconfigure(0, weight=1)
    menu_body.columnconfigure(0, weight=1)
    menu_canvas = tk.Canvas(menu_body, bg=BG_COLOUR, highlightthickness=0)
    menu_scrollbar = ttk.Scrollbar(menu_body, orient="vertical", command=menu_canvas.yview)
    menu_canvas.configure(yscrollcommand=menu_scrollbar.set)
    menu_canvas.grid(row=0, column=0, sticky="nsew")
    menu_scrollbar.grid(row=0, column=1, sticky="ns")
    product_frame = tk.Frame(menu_canvas, bg=BG_COLOUR)
    canvas_window = menu_canvas.create_window((0, 0), window=product_frame, anchor="nw")
    product_frame.bind(
        "<Configure>",
        lambda _event: menu_canvas.configure(scrollregion=menu_canvas.bbox("all")),
    )
    menu_canvas.bind(
        "<Configure>",
        lambda event: menu_canvas.itemconfigure(canvas_window, width=event.width),
    )
    for column in range(3):
        product_frame.columnconfigure(column, weight=1, uniform="menu_cards")
    no_results_label = tk.Label(
        product_frame,
        text="No dishes found. Try another search or category.",
        bg=WHITE_COLOUR,
        fg=TEXT_COLOUR,
        font=("Arial", 11),
        padx=15,
        pady=18,
    )
    image_references = {}
    product_cards = {}
    for product in products:
        product_cards[product["id"]] = add_product_card(product)

    # Load only one food picture in each scheduled callback.
    # Tkinter can respond to clicks and scrolling between these callbacks.
    for image_index, product in enumerate(products):
        image_target = product_cards[product["id"]].menu_image_label
        after_id = parent.after(
            20 + image_index * 12,
            lambda selected=product, target=image_target: (
                setattr(target, "image", load_image(selected["image"], MENU_PHOTO_SIZE)),
                image_references.__setitem__(selected["id"], target.image),
                target.configure(
                    image=target.image,
                    text="" if target.image else "Picture unavailable",
                    bg=WHITE_COLOUR if target.image else SECONDARY_COLOUR,
                ),
            ) if target.winfo_exists() else None,
        )
        parent._image_after_ids.append(after_id)

    result_label = tk.Label(menu_panel, text="", bg=WHITE_COLOUR, fg=MUTED_COLOUR, font=("Arial", 8))
    result_label.grid(row=3, column=0, sticky="e", pady=(5, 0))
    update_menu()

    # Food detail page: only the selected food photo, name, quantity, description and Add button.
    detail_page = pages["Detail"]
    detail_page.columnconfigure(0, weight=1)
    detail_panel = tk.Frame(detail_page, bg=WHITE_COLOUR, padx=28, pady=18)
    detail_panel.pack(fill="both", expand=True, padx=45, pady=20)
    detail_image = tk.Label(detail_panel, bg=WHITE_COLOUR, text="Picture unavailable")
    detail_image.pack(fill="x", pady=(0, 12))
    detail_name = tk.Label(
        detail_panel, text="Food name", bg=WHITE_COLOUR, fg=TEXT_COLOUR,
        font=("Arial", 18, "bold"),
    )
    detail_name.pack(fill="x")
    detail_quantity_row = tk.Frame(detail_panel, bg=WHITE_COLOUR)
    detail_quantity_row.pack(pady=8)
    tk.Button(
        detail_quantity_row, text="−", command=lambda: change_detail_quantity(-1),
        bg=SECONDARY_COLOUR, fg=NAV_COLOUR, font=("Arial", 14, "bold"), width=3,
    ).pack(side="left", padx=10)
    detail_quantity_label = tk.Label(
        detail_quantity_row, text="1", bg=WHITE_COLOUR, fg=TEXT_COLOUR,
        font=("Arial", 12, "bold"), width=4,
    )
    detail_quantity_label.pack(side="left")
    tk.Button(
        detail_quantity_row, text="+", command=lambda: change_detail_quantity(1),
        bg=NAV_COLOUR, fg=WHITE_COLOUR, font=("Arial", 14, "bold"), width=3,
    ).pack(side="left", padx=10)
    detail_description = tk.Label(
        detail_panel, text="", bg=WHITE_COLOUR, fg=MUTED_COLOUR,
        font=("Arial", 9), justify="left", wraplength=760,
    )
    detail_description.pack(fill="x", pady=(8, 16))
    detail_add_button = tk.Button(
        detail_panel,
        text="Add to basket",
        command=lambda: (add_to_basket(detail_product, detail_quantity), show_page("Menu")),
        bg=NAV_COLOUR,
        fg=WHITE_COLOUR,
        activebackground=ACTIVE_COLOUR,
        font=("Arial", 11, "bold"),
        padx=18,
        pady=10,
    )
    detail_add_button.pack(fill="x")
    detail_page.bind("<Escape>", lambda _event: show_page("Menu"))

    # Basket page: product photos and details on the left; total and payment details on the right.
    basket_page = pages["Basket"]
    basket_page.rowconfigure(0, weight=1)
    basket_page.columnconfigure(0, weight=3)
    basket_page.columnconfigure(1, weight=2)
    basket_items_panel = tk.Frame(basket_page, bg=WHITE_COLOUR, padx=10, pady=10)
    basket_items_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
    basket_items_panel.rowconfigure(0, weight=1)
    basket_items_panel.columnconfigure(0, weight=1)
    basket_canvas = tk.Canvas(basket_items_panel, bg=WHITE_COLOUR, highlightthickness=0)
    basket_scrollbar = ttk.Scrollbar(basket_items_panel, orient="vertical", command=basket_canvas.yview)
    basket_canvas.configure(yscrollcommand=basket_scrollbar.set)
    basket_canvas.grid(row=0, column=0, sticky="nsew")
    basket_scrollbar.grid(row=0, column=1, sticky="ns")
    basket_items_frame = tk.Frame(basket_canvas, bg=WHITE_COLOUR)
    basket_canvas_window = basket_canvas.create_window((0, 0), window=basket_items_frame, anchor="nw")
    basket_items_frame.bind(
        "<Configure>",
        lambda _event: basket_canvas.configure(scrollregion=basket_canvas.bbox("all")),
    )
    basket_canvas.bind(
        "<Configure>",
        lambda event: basket_canvas.itemconfigure(basket_canvas_window, width=event.width),
    )

    checkout_panel = tk.Frame(
        basket_page, bg=WHITE_COLOUR, padx=17, pady=15,
        highlightthickness=1, highlightbackground=SECONDARY_COLOUR,
    )
    checkout_panel.grid(row=0, column=1, sticky="nsew")
    tk.Label(
        checkout_panel, text="Order Summary", bg=WHITE_COLOUR, fg=TEXT_COLOUR,
        font=("Arial", 14, "bold"),
    ).pack(anchor="w", pady=(0, 10))
    basket_count_label = tk.Label(checkout_panel, text="0 item(s)", bg=WHITE_COLOUR, fg=MUTED_COLOUR)
    basket_count_label.pack(anchor="w", pady=(0, 7))
    subtotal_label = tk.Label(checkout_panel, text="Subtotal: RM 0.00", bg=WHITE_COLOUR, fg=TEXT_COLOUR)
    subtotal_label.pack(anchor="w", pady=3)
    tax_label = tk.Label(checkout_panel, text="Tax (6%): RM 0.00", bg=WHITE_COLOUR, fg=TEXT_COLOUR)
    tax_label.pack(anchor="w", pady=3)
    service_label = tk.Label(checkout_panel, text="Service charge (10%): RM 0.00", bg=WHITE_COLOUR, fg=TEXT_COLOUR)
    service_label.pack(anchor="w", pady=3)
    total_label = tk.Label(
        checkout_panel, text="Total including charges: RM 0.00", bg=WHITE_COLOUR,
        fg=NAV_COLOUR, font=("Arial", 13, "bold"),
    )
    total_label.pack(anchor="w", pady=(5, 14))

    tk.Label(checkout_panel, text="Customer name", bg=WHITE_COLOUR, fg=TEXT_COLOUR).pack(anchor="w")
    customer_entry = tk.Entry(checkout_panel, font=("Arial", 10))
    customer_entry.pack(fill="x", pady=(3, 9), ipady=4)
    tk.Label(checkout_panel, text="Dining method", bg=WHITE_COLOUR, fg=TEXT_COLOUR).pack(anchor="w")
    dining_method = tk.StringVar(value="Restaurant dining")
    dining_box = ttk.Combobox(
        checkout_panel, textvariable=dining_method,
        values=("Restaurant dining", "Room delivery"), state="readonly",
    )
    dining_box.pack(fill="x", pady=(3, 9))
    tk.Label(checkout_panel, text="Table / Room number", bg=WHITE_COLOUR, fg=TEXT_COLOUR).pack(anchor="w")
    location_entry = tk.Entry(checkout_panel, font=("Arial", 10))
    location_entry.pack(fill="x", pady=(3, 9), ipady=4)
    tk.Label(checkout_panel, text="Payment method", bg=WHITE_COLOUR, fg=TEXT_COLOUR).pack(anchor="w")
    payment_method = tk.StringVar(value="Cash")
    ttk.Combobox(
        checkout_panel, textvariable=payment_method,
        values=("Cash", "Visa / Credit Card", "E-wallet"), state="readonly",
    ).pack(fill="x", pady=(3, 12))
    tk.Button(
        checkout_panel,
        text="PAY",
        command=place_order,
        bg=NAV_COLOUR,
        fg=WHITE_COLOUR,
        activebackground=ACTIVE_COLOUR,
        font=("Arial", 11, "bold"),
        padx=14,
        pady=10,
    ).pack(fill="x", pady=(5, 0))


    orders_page = pages["Orders"]
    orders_page.rowconfigure(0, weight=1)
    orders_page.columnconfigure(0, weight=1)

    orders_content = tk.Frame(orders_page, bg=BG_COLOUR)
    orders_content.pack(fill="both", expand=True)
    orders_top = tk.Frame(orders_content, bg=BG_COLOUR)
    orders_top.pack(fill="x", pady=(0, 10))
    tk.Label(
        orders_top, text="Order history", bg=BG_COLOUR, fg=TEXT_COLOUR,
        font=("Arial", 15, "bold"),
    ).pack(side="left")
    history_count_label = tk.Label(
        orders_top, text=f"{len(orders)} saved order(s) on this device",
        bg=BG_COLOUR, fg=MUTED_COLOUR, font=("Arial", 9),
    )
    history_count_label.pack(side="left", padx=(12, 0), pady=(4, 0))
    tk.Button(
        orders_top, text="Refresh", command=update_history,
        bg=SECONDARY_COLOUR, fg=NAV_COLOUR, activebackground=ACTIVE_COLOUR,
        activeforeground=WHITE_COLOUR, relief="flat", borderwidth=0,
        cursor="hand2", font=("Arial", 9, "bold"), padx=14, pady=9,
    ).pack(side="right")

    # Match the blue heading, alternating rows and scrollbars to the Caramel Hotel theme.
    table_shell = tk.Frame(orders_content, bg="#D0D9E0", padx=1, pady=1)
    table_shell.pack(fill="both", expand=True)
    history_frame = tk.Frame(table_shell, bg=WHITE_COLOUR)
    history_frame.pack(fill="both", expand=True)
    history_frame.grid_rowconfigure(0, weight=1)
    history_frame.grid_columnconfigure(0, weight=1)

    history_style = ttk.Style(window)
    history_style.configure(
        "Restaurant.Treeview", background=WHITE_COLOUR,
        fieldbackground=WHITE_COLOUR, foreground=TEXT_COLOUR,
        rowheight=34, font=("Arial", 10), borderwidth=0,
    )
    history_style.configure(
        "Restaurant.Treeview.Heading", background=NAV_COLOUR,
        foreground=WHITE_COLOUR, font=("Arial", 9, "bold"), padding=(8, 10),
    )
    history_style.map(
        "Restaurant.Treeview",
        background=[("selected", "#9497B6")],
        foreground=[("selected", WHITE_COLOUR)],
    )

    history_columns = (
        "order_id", "date", "customer", "dining", "location",
        "items", "total", "payment", "status",
    )
    history_tree = ttk.Treeview(
        history_frame, columns=history_columns, show="headings",
        style="Restaurant.Treeview",
    )
    history_headings = {
        "order_id": ("Order ID", 90),
        "date": ("Date", 145),
        "customer": ("Customer", 130),
        "dining": ("Dining method", 125),
        "location": ("Table / Room", 105),
        "items": ("Ordered items", 250),
        "total": ("Total price", 105),
        "payment": ("Payment method", 135),
        "status": ("Status", 95),
    }
    for column, (title, width) in history_headings.items():
        history_tree.heading(column, text=title)
        history_tree.column(
            column, width=width, minwidth=65,
            anchor="w" if column in ("customer", "items") else "center",
            stretch=True,
        )
    history_tree.tag_configure("even", background="#F7F9FA")
    history_tree.tag_configure("odd", background=WHITE_COLOUR)
    history_ybar = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
    history_xbar = ttk.Scrollbar(history_frame, orient="horizontal", command=history_tree.xview)
    history_tree.configure(
        yscrollcommand=history_ybar.set, xscrollcommand=history_xbar.set,
    )
    history_tree.grid(row=0, column=0, sticky="nsew")
    history_ybar.grid(row=0, column=1, sticky="ns")
    history_xbar.grid(row=1, column=0, sticky="ew")

    update_history()
    update_basket()
    show_page("Menu")


class RestaurantPage(tk.Frame):
    # Restaurant pages embedded in main.py's shared window.

    # Prepare the restaurant page and connect scrolling to the visible restaurant list.
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOUR)
        global products, image_references, product_cards, category_buttons
        global selected_category_var, detail_product, detail_quantity, detail_image_reference
        global subtotal, tax_amount, service_charge, total
        products = read_menu()
        image_references = {}
        product_cards = {}
        category_buttons = {}
        selected_category_var = None
        detail_product = None
        detail_quantity = 1
        detail_image_reference = None
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        service_charge = Decimal("0.00")
        total = Decimal("0.00")
        self._wheel_bindings = []
        self._image_after_ids = []  # Store pending photo callbacks so they can be cancelled safely.
        build_restaurant_ui(self)
        # bind_all lets the menu and basket scroll even when the pointer is over a photo or label.
        self._wheel_bindings.append(("<MouseWheel>", self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")))
        self._wheel_bindings.append(("<Button-4>", self.bind_all("<Button-4>", lambda event: self._on_linux_mousewheel(event, -1), add="+")))
        self._wheel_bindings.append(("<Button-5>", self.bind_all("<Button-5>", lambda event: self._on_linux_mousewheel(event, 1), add="+")))

    # Remove the global scrolling events when the Menu page is closed.
    def destroy(self):
        # Cancel food-photo callbacks if the user leaves Menu before loading finishes.
        for after_id in getattr(self, "_image_after_ids", []):
            try:
                self.after_cancel(after_id)
            except (tk.TclError, ValueError):
                pass
        self._image_after_ids = []
        for sequence, binding_id in getattr(self, "_wheel_bindings", []):
            if binding_id:
                try:
                    self._root()._unbind(("bind", "all", sequence), binding_id)
                except (tk.TclError, AttributeError):
                    pass
        self._wheel_bindings = []
        super().destroy()

    # Scroll the menu or basket only when the mouse pointer is inside that page.
    def _on_mousewheel(self, event):
        target = (
            menu_canvas if active_page == "Menu"
            else basket_canvas if active_page == "Basket"
            else history_tree if active_page == "Orders"
            else None
        )
        if target is None:
            return None
        left, top = target.winfo_rootx(), target.winfo_rooty()
        right, bottom = left + target.winfo_width(), top + target.winfo_height()
        if left <= event.x_root <= right and top <= event.y_root <= bottom:
            amount = int(-event.delta / 120)
            if amount == 0 and event.delta:
                amount = -1 if event.delta > 0 else 1
            target.yview_scroll(amount, "units")
            return "break"
        return None

    # Handle mouse-wheel scrolling on Linux computers.
    def _on_linux_mousewheel(self, event, direction):
        target = (
            menu_canvas if active_page == "Menu"
            else basket_canvas if active_page == "Basket"
            else history_tree if active_page == "Orders"
            else None
        )
        if target is None:
            return None
        left, top = target.winfo_rootx(), target.winfo_rooty()
        right, bottom = left + target.winfo_width(), top + target.winfo_height()
        if left <= event.x_root <= right and top <= event.y_root <= bottom:
            target.yview_scroll(direction, "units")
            return "break"
        return None
