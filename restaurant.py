import ast
import json
import tkinter as tk
from datetime import datetime
from decimal import Decimal, InvalidOperation
from decimal import ROUND_HALF_UP
from pathlib import Path
from tkinter import messagebox, ttk
from PIL import Image, ImageTk


# File locations, colors, and money charges 
FOLDER = Path(__file__).resolve().parent
MENU_FILE = FOLDER / "menu.txt"
IMAGE_FOLDER = FOLDER / "images"
ORDERS_FILE = FOLDER / "rorders.txt"

BG_COLOUR = "#DFE2E5"
NAV_COLOUR = "#486B92"
SELECTED_COLOUR = NAV_COLOUR
ACTIVE_COLOUR = "#7E93A9"
SECONDARY_COLOUR = "#C5D6E2"
TEXT_COLOUR = "#34465A"
WHITE_COLOUR = "#FFFFFF"
BUTTON_COLOUR = NAV_COLOUR
PURPLE_COLOUR = TEXT_COLOUR
MUTED_COLOUR = "#7E93A9"
TAX_RATE = Decimal("0.06")
SERVICE_CHARGE_RATE = Decimal("0.10")
CENT = Decimal("0.01")


# Menu loading and image
def normalize_image_path(filename):
    """Match a menu photo name to the local file, ignoring extension typos."""
    image_path = Path(filename)
    if image_path.is_absolute():
        return str(image_path)

    image_folder = IMAGE_FOLDER if len(image_path.parts) == 1 else FOLDER / image_path.parent
    requested_name = image_path.name.casefold()
    requested_stem = image_path.stem.casefold()
    if image_folder.is_dir():
        for candidate in image_folder.iterdir():
            if not candidate.is_file():
                continue
            if candidate.name.casefold() == requested_name or candidate.stem.casefold() == requested_stem:
                return candidate.relative_to(FOLDER).as_posix()
            extension = candidate.suffix.casefold()
            if (
                extension == ".jpg"
                and requested_name.endswith(extension[1:])
                and requested_name[:-len(extension) + 1] == candidate.stem.casefold()
            ):
                return candidate.relative_to(FOLDER).as_posix()

    if len(image_path.parts) == 1:
        image_path = Path("images") / image_path
    return image_path.as_posix()


def read_menu():
    """Read a menu_dict assignment or the pipe-separated menu file."""
    if not MENU_FILE.exists():
        raise FileNotFoundError(f"Menu file not found:\n{MENU_FILE}")

    text = MENU_FILE.read_text(encoding="utf-8-sig")
    if "menu_dict" in text:
        try:
            tree = ast.parse(text, filename=str(MENU_FILE))
            menu_assignment = next(
                node for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "menu_dict"
                    for target in node.targets
                )
            )
            menu_data = ast.literal_eval(menu_assignment.value)
        except (SyntaxError, StopIteration, ValueError) as error:
            raise ValueError(
                f"{MENU_FILE.name} must contain a valid menu_dict with literal menu data."
            ) from error

        if not isinstance(menu_data, dict):
            raise ValueError("menu_dict must be a dictionary.")

        products = []
        for item_id, details in menu_data.items():
            if not isinstance(details, dict):
                raise ValueError(f"Menu item {item_id} must contain a dictionary of details.")
            try:
                name = str(details["Name"]).strip()
                category = str(details["Category"]).strip()
                amount = Decimal(str(details["Price"]))
                image = str(details["Image"]).strip()
            except (KeyError, InvalidOperation) as error:
                raise ValueError(f"Menu item {item_id} is missing valid Name, Category, Price, or Image data.") from error
            if not amount.is_finite() or amount < 0:
                raise ValueError(f"Menu item {item_id} has an invalid price.")
            if not name or not category or not image:
                raise ValueError(f"Menu item {item_id} has an empty name, category, or image.")
            products.append({
                "id": str(item_id).strip(),
                "name": name,
                "category": category,
                "price": amount,
                "image": normalize_image_path(image),
            })

        if not products:
            raise ValueError("No menu items were found in menu_dict.")
        return products

    products = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue

        columns = line.split("|")
        if len(columns) != 5:
            raise ValueError(
                f"Menu line {line_number} must have five | separated values "
                "(ID|Name|Category|Price|Image)."
            )

        item_id, name, category, price, image = columns
        try:
            amount = Decimal(price)
        except InvalidOperation as error:
            raise ValueError(f"Menu line {line_number} has an invalid price.") from error

        products.append({
            "id": item_id.strip(),
            "name": name.strip(),
            "category": category.strip(),
            "price": amount,
            "image": normalize_image_path(image.strip()),
        })

    if not products:
        raise ValueError("No menu items were found in menu.txt.")
    return products


def load_image(filename, size):
    """Open and resize one menu photo for display in a Tkinter label."""
    image_path = Path(filename)
    if not image_path.is_absolute():
        image_path = FOLDER / image_path

    candidates = [image_path]
    wanted_stem = image_path.stem.casefold()
    if image_path.suffix.lower() != ".jpg":
        for extension in (".jpg",):
            candidates.append(image_path.with_suffix(extension))
            if image_path.name.casefold().endswith(extension[1:]):
                candidates.append(image_path.with_name(image_path.name[:-len(extension) + 1] + extension))
    if IMAGE_FOLDER.exists():
        candidates.extend(
            candidate for candidate in IMAGE_FOLDER.iterdir()
            if candidate.is_file()
            and candidate.suffix.lower() == ".jpg"
            and candidate.stem.casefold() == wanted_stem
        )

    for candidate in candidates:
        try:
            picture = Image.open(candidate)
            picture.thumbnail(size, Image.Resampling.LANCZOS)
            picture = picture.convert("RGB")
            return ImageTk.PhotoImage(picture)
        except (FileNotFoundError, OSError):
            continue
    return None


def money(amount):
    """Format an amount as Malaysian Ringgit."""
    return f"RM {Decimal(str(amount)):.2f}"


# NOTE: Shared menu, basket, and order totals used by the screens.
products = read_menu()
orders = []
try:
    ORDERS_FILE.write_text("[]\n", encoding="utf-8")
except OSError as error:
    raise SystemExit(f"Could not reset order history: {error}") from error

quantity_entries = {}
basket = {}
image_references = {}
product_cards = {}
category_buttons = {}
selected_category = "All"
menu_columns = 3
subtotal = Decimal("0.00")
tax_amount = Decimal("0.00")
service_charge = Decimal("0.00")
total = Decimal("0.00")
detail_product = None
detail_quantity = 1
detail_image_reference = None


# Order totals and local order history
def calculate_order_totals(item_subtotal):
    """Return subtotal, tax, service charge, and total rounded to cents."""
    item_subtotal = Decimal(str(item_subtotal)).quantize(CENT, rounding=ROUND_HALF_UP)
    tax = (item_subtotal * TAX_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    service = (item_subtotal * SERVICE_CHARGE_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    return item_subtotal, tax, service, item_subtotal + tax + service


def calculate_total():
    """Calculate totals for the items currently in the basket."""
    global subtotal, tax_amount, service_charge, total

    if not basket:
        messagebox.showinfo("Empty basket", "Add a dish to your basket first.", parent=window)
        return False

    new_subtotal = sum(
        (row["product"]["price"] * row["quantity"] for row in basket.values()),
        Decimal("0.00"),
    )
    subtotal, tax_amount, service_charge, total = calculate_order_totals(new_subtotal)
    subtotal_label.config(text=f"Subtotal: {money(subtotal)}")
    tax_label.config(text=f"Tax ({TAX_RATE * 100}%): {money(tax_amount)}")
    service_label.config(
        text=f"Service charge ({SERVICE_CHARGE_RATE * 100}%): {money(service_charge)}"
    )
    total_label.config(text=f"Total to Pay: {money(total)}")
    return True


def update_history():
    """Refresh the recent order list."""
    history_list.delete(0, tk.END)
    for order in reversed(orders[-10:]):
        history_list.insert(
            tk.END,
            f'{order.get("date", "")} — {order.get("customer", "")} — '
            f'{money(order.get("total", "0"))}',
        )


def place_order():
    """Save the basket as a completed local order."""
    if not calculate_total():
        return

    customer = customer_entry.get().strip()
    location = location_entry.get().strip()
    if not customer or not location:
        messagebox.showwarning(
            "Order details",
            "Enter the customer's name and table or room number.",
            parent=window,
        )
        return

    order = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "customer": customer,
        "dining": dining_method.get(),
        "location": location,
        "payment": payment_method.get(),
        "items": [
            {
                "id": row["product"]["id"],
                "name": row["product"]["name"],
                "quantity": row["quantity"],
                "price": str(row["product"]["price"]),
                "note": row.get("note", ""),
            }
            for row in basket.values()
        ],
        "subtotal": str(subtotal),
        "tax_rate": str(TAX_RATE),
        "tax": str(tax_amount),
        "service_charge_rate": str(SERVICE_CHARGE_RATE),
        "service_charge": str(service_charge),
        "total": str(total),
    }

    orders.append(order)
    try:
        ORDERS_FILE.write_text(
            json.dumps(orders, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as error:
        orders.pop()
        messagebox.showerror("Could not save order", str(error), parent=window)
        return

    basket.clear()
    for entry in quantity_entries.values():
        entry.delete(0, tk.END)
        entry.insert(0, "0")

    update_basket()
    customer_entry.delete(0, tk.END)
    total_label.config(text="Total to Pay: RM 0.00")
    subtotal_label.config(text="Subtotal: RM 0.00")
    tax_label.config(text=f"Tax ({TAX_RATE * 100}%): RM 0.00")
    service_label.config(text=f"Service charge ({SERVICE_CHARGE_RATE * 100}%): RM 0.00")
    update_history()
    show_page("Orders")
    messagebox.showinfo(
        "Order placed",
        "Your order was saved on this computer.",
        parent=window,
    )


def add_to_basket(product, quantity=None, note=""):
    """Add a dish and quantity to the customer's basket."""
    if quantity is None:
        try:
            quantity = int(quantity_entries[product["id"]].get())
            if not 1 <= quantity <= 50:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Quantity",
                "Enter a whole number between 1 and 50 before adding this dish.",
                parent=window,
            )
            return

    item_id = product["id"]
    if item_id in basket:
        basket[item_id]["quantity"] = min(basket[item_id]["quantity"] + quantity, 50)
        existing_note = basket[item_id].get("note", "")
        if note and note not in existing_note:
            basket[item_id]["note"] = "\n".join(
                value for value in (existing_note, note) if value
            )
    else:
        basket[item_id] = {"product": product, "quantity": quantity, "note": note}

    if item_id in quantity_entries:
        quantity_entries[item_id].delete(0, tk.END)
        quantity_entries[item_id].insert(0, "0")
    update_basket()
    reset_payment_totals()


def open_food_detail(product):
    """Show the selected dish on its own detail screen."""
    global detail_product, detail_quantity, detail_image_reference
    detail_product = product
    detail_quantity = 1
    detail_note.delete("1.0", tk.END)
    detail_note.configure(fg=TEXT_COLOUR)
    photo = load_image(
        product["image"],
        (max(320, window_width - 100), max(120, min(280, window_height // 3))),
    )
    detail_image_reference = photo
    if photo:
        detail_image.configure(image=photo, text="")
    else:
        detail_image.configure(image="", text="Picture unavailable")
    detail_name.configure(text=product["name"])
    detail_price.configure(text=money(product["price"]))
    detail_quantity_label.configure(text=str(detail_quantity))
    update_detail_button()
    show_page("Detail")


def change_detail_quantity(amount):
    """Change the quantity on the dish detail screen."""
    global detail_quantity
    detail_quantity = max(1, min(50, detail_quantity + amount))
    detail_quantity_label.configure(text=str(detail_quantity))
    update_detail_button()


def update_detail_button():
    if detail_product is not None:
        detail_add_button.configure(
            text=f"Add to basket · {money(detail_product['price'] * detail_quantity)}"
        )


def add_detail_to_basket():
    """Add the selected dish, quantity, and optional request to the basket."""
    if detail_product is None:
        return
    note = detail_note.get("1.0", "end-1c").strip()
    add_to_basket(detail_product, detail_quantity, note)
    show_page("Basket")


# NOTE: Basket removal, checkout reset, and basket display.
def remove_from_basket():
    """Remove the selected dish from the basket."""
    selection = basket_list.curselection()
    if not selection:
        messagebox.showinfo("Choose a dish", "Select a basket item to remove.", parent=window)
        return

    item_id = list(basket.keys())[selection[0]]
    del basket[item_id]
    update_basket()
    reset_payment_totals()


def reset_payment_totals():
    """Clear the displayed checkout totals after the basket changes."""
    global subtotal, tax_amount, service_charge, total
    subtotal = Decimal("0.00")
    tax_amount = Decimal("0.00")
    service_charge = Decimal("0.00")
    total = Decimal("0.00")
    subtotal_label.config(text="Subtotal: RM 0.00")
    tax_label.config(text=f"Tax ({TAX_RATE * 100}%): RM 0.00")
    service_label.config(text=f"Service charge ({SERVICE_CHARGE_RATE * 100}%): RM 0.00")
    total_label.config(text="Total to Pay: RM 0.00")


def update_basket():
    """Refresh the basket list and item count."""
    basket_list.delete(0, tk.END)
    for row in basket.values():
        product = row["product"]
        line_total = product["price"] * row["quantity"]
        note = f' · Note: {row["note"]}' if row.get("note") else ""
        basket_list.insert(
            tk.END,
            f'{product["name"]} x {row["quantity"]} — {money(line_total)}{note}',
        )
    item_count = sum(row["quantity"] for row in basket.values())
    basket_count_label.config(text=f"{item_count} item(s)")
    nav_basket_count_label.config(text=f"{item_count} items")
    basket_total_label.config(
        text=f'Basket subtotal: {money(sum((row["product"]["price"] * row["quantity"] for row in basket.values()), Decimal("0.00")))}'
    )


def select_category(category):
    """Choose one menu category and refresh the visible food cards."""
    global selected_category
    selected_category = category
    update_menu()


# NOTE: Search and category filtering for the food menu.
def update_menu(event=None):
    """Filter the menu cards by the selected category and search text."""
    search_text = search_entry.get().strip()
    if search_text == "Search dishes or categories...":
        search_text = ""
    search = search_text.casefold()
    matching_products = [
        product for product in products
        if (selected_category == "All" or product["category"] == selected_category)
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
            row=index // menu_columns,
            column=index % menu_columns,
            padx=7,
            pady=7,
            sticky="nsew",
        )

    if matching_products:
        no_results_label.grid_remove()
    else:
        no_results_label.grid(row=0, column=0, columnspan=menu_columns, padx=12, pady=20)

    for category, button in category_buttons.items():
        is_selected = category == selected_category
        button.config(
            bg=SELECTED_COLOUR if is_selected else WHITE_COLOUR,
            fg=WHITE_COLOUR if is_selected else TEXT_COLOUR,
            activebackground=SELECTED_COLOUR if is_selected else SECONDARY_COLOUR,
            relief="flat",
        )

    result_label.config(text=f"{len(matching_products)} dishes")
    product_frame.update_idletasks()
    menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))
    menu_canvas.yview_moveto(0)


def add_product_card(product):
    """Create one menu card with its photo, price, and quantity entry."""
    card = tk.Frame(
        product_frame,
        bg=WHITE_COLOUR,
        bd=1,
        relief="solid",
        padx=8,
        pady=7,
    )

    photo = load_image(product["image"], (140, 95))
    if photo:
        image_references[product["id"]] = photo
        image_label = tk.Label(card, image=photo, bg=WHITE_COLOUR, cursor="hand2")
        image_label.pack(pady=3)
        image_label.bind("<Button-1>", lambda event, selected=product: open_food_detail(selected))
    else:
        image_label = tk.Label(
            card,
            text="Picture unavailable",
            width=18,
            height=5,
            bg=SECONDARY_COLOUR,
            fg=TEXT_COLOUR,
            cursor="hand2",
        )
        image_label.pack(pady=3)
        image_label.bind("<Button-1>", lambda event, selected=product: open_food_detail(selected))

    name_label = tk.Label(
        card,
        text=product["name"],
        font=("Arial", 11, "bold"),
        bg=WHITE_COLOUR,
        wraplength=155,
        cursor="hand2",
    )
    name_label.pack()
    name_label.bind("<Button-1>", lambda event, selected=product: open_food_detail(selected))
    tk.Label(
        card,
        text=f'{product["category"]} · {money(product["price"])}',
        font=("Arial", 9),
        bg=WHITE_COLOUR,
        fg=NAV_COLOUR,
        wraplength=155,
    ).pack(pady=3)
    tk.Label(card, text="Quantity:", bg=WHITE_COLOUR).pack()

    entry = tk.Entry(card, width=8, justify="center")
    entry.insert(0, "0")
    entry.pack(pady=(2, 4))
    quantity_entries[product["id"]] = entry
    tk.Button(
        card,
        text="Add to basket",
        command=lambda selected=product: add_to_basket(selected),
        bg=BUTTON_COLOUR,
        fg=WHITE_COLOUR,
        activebackground=ACTIVE_COLOUR,
        activeforeground=WHITE_COLOUR,
        font=("Arial", 9, "bold"),
        padx=8,
        pady=3,
    ).pack(fill="x", pady=(3, 0))
    return card


# Main window scales , screen resolution
try:
    window = tk.Tk()
except tk.TclError as error:
    raise SystemExit(f"Could not open the restaurant window: {error}") from error

window.title("Caramel Restaurant")
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window_width = min(1000, max(620, screen_width - 60))
window_height = min(700, max(480, screen_height - 90))
window.geometry(
    f"{window_width}x{window_height}+"
    f"{max(0, (screen_width - window_width) // 2)}+"
    f"{max(0, (screen_height - window_height) // 2)}"
)
window.minsize(min(620, screen_width), min(480, screen_height))
window.configure(bg=BG_COLOUR)
window.option_add("*Font", "Arial 10")
style = ttk.Style(window)
style.theme_use("clam")
style.configure(
    "TCombobox",
    fieldbackground=WHITE_COLOUR,
    background=WHITE_COLOUR,
    foreground=TEXT_COLOUR,
    bordercolor=SECONDARY_COLOUR,
    padding=6,
)
style.configure(
    "Vertical.TScrollbar",
    background=SECONDARY_COLOUR,
    troughcolor=BG_COLOUR,
    bordercolor=BG_COLOUR,
    arrowcolor=TEXT_COLOUR,
)

header = tk.Frame(
    window,
    bg=WHITE_COLOUR,
    padx=18,
    pady=9,
    highlightthickness=1,
    highlightbackground=SECONDARY_COLOUR,
)
header.pack(fill="x")
tk.Label(
    header,
    text="Caramel Restaurant",
    font=("Arial", 17, "bold"),
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
).pack(side="left")

page_area = tk.Frame(window, bg=BG_COLOUR)
page_area.pack(fill="both", expand=True, padx=18, pady=12)
page_area.rowconfigure(0, weight=1)
page_area.columnconfigure(0, weight=1)

pages = {}
for page_name in ("Food", "Detail", "Basket", "Payment", "Orders"):
    page = tk.Frame(page_area, bg=BG_COLOUR)
    page.grid(row=0, column=0, sticky="nsew")
    pages[page_name] = page

nav = tk.Frame(header, bg=WHITE_COLOUR)
nav.pack(side="right")
nav_buttons = {}


def show_page(page_name):
    """Raise one of the app's separate ordering screens."""
    pages[page_name].tkraise()
    for name, button in nav_buttons.items():
        button.configure(
            bg=NAV_COLOUR if name == page_name else WHITE_COLOUR,
            fg=WHITE_COLOUR if name == page_name else TEXT_COLOUR,
        )


def open_payment():
    """Open checkout only when there are items in the basket."""
    if calculate_total():
        show_page("Payment")


# Header navigation buttons and basket item count
for page_name in ("Food", "Basket", "Payment", "Orders"):
    nav_text = {
        "Food": "Menu",
        "Basket": "Basket",
        "Payment": "Payment",
        "Orders": "My orders",
    }[page_name]
    button = tk.Button(
        nav,
        text=nav_text,
        command=open_payment if page_name == "Payment" else lambda name=page_name: show_page(name),
        bg=WHITE_COLOUR,
        fg=TEXT_COLOUR,
        activebackground=SECONDARY_COLOUR,
        activeforeground=WHITE_COLOUR,
        relief="flat",
        padx=7,
        pady=6,
    )
    button.pack(side="left", padx=2)
    nav_buttons[page_name] = button

nav_basket_count_label = tk.Label(
    nav,
    text="0 items",
    bg=WHITE_COLOUR,
    fg=NAV_COLOUR,
    font=("Arial", 8, "bold"),
)
nav_basket_count_label.pack(side="left", padx=(8, 2))

# NOTE: Food page - search, categories, image cards, and menu scrolling.
food_page = pages["Food"]
food_page.columnconfigure(0, weight=1)
food_page.rowconfigure(0, weight=1)

menu_area = tk.LabelFrame(
    food_page,
    text="  Our menu  ",
    font=("Arial", 12, "bold"),
    fg=TEXT_COLOUR,
    bg=WHITE_COLOUR,
    padx=10,
    pady=9,
    bd=0,
    highlightthickness=1,
    highlightbackground=SECONDARY_COLOUR,
)
menu_area.grid(row=0, column=0, sticky="nsew")
menu_area.rowconfigure(2, weight=1)
menu_area.columnconfigure(0, weight=1)

search_frame = tk.Frame(menu_area, bg=WHITE_COLOUR)
search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
search_frame.columnconfigure(0, weight=1)
search_entry = ttk.Entry(search_frame, font=("Arial", 10))
search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))


def clear_search_placeholder(event):
    if search_entry.get() == "Search dishes or categories...":
        search_entry.delete(0, tk.END)
        search_entry.configure(foreground=TEXT_COLOUR)


def restore_search_placeholder(event):
    if not search_entry.get().strip():
        search_entry.insert(0, "Search dishes or categories...")
        search_entry.configure(foreground=MUTED_COLOUR)


search_entry.insert(0, "Search dishes or categories...")
search_entry.configure(foreground=MUTED_COLOUR)
search_entry.bind("<FocusIn>", clear_search_placeholder)
search_entry.bind("<FocusOut>", restore_search_placeholder)
search_entry.bind("<Return>", update_menu)
search_entry.bind("<KeyRelease>", update_menu)
tk.Button(
    search_frame,
    text="Search",
    command=update_menu,
    bg=BUTTON_COLOUR,
    fg=WHITE_COLOUR,
    activebackground=ACTIVE_COLOUR,
    activeforeground=WHITE_COLOUR,
    font=("Arial", 9, "bold"),
    padx=10,
).grid(row=0, column=1)

category_frame = tk.Frame(menu_area, bg=WHITE_COLOUR)
category_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))
categories = ["All"] + list(dict.fromkeys(product["category"] for product in products))
for column, category in enumerate(categories):
    button = tk.Button(
        category_frame,
        text=category,
        command=lambda value=category: select_category(value),
        bg=WHITE_COLOUR,
        fg=TEXT_COLOUR,
        activebackground=ACTIVE_COLOUR,
        activeforeground=WHITE_COLOUR,
        font=("Arial", 8),
        padx=7,
        pady=4,
        relief="flat",
        bd=1,
    )
    button.grid(row=column // 5, column=column % 5, padx=3, pady=3, sticky="ew")
    category_buttons[category] = button
for column in range(5):
    category_frame.columnconfigure(column, weight=1)

result_label = tk.Label(
    category_frame,
    text="",
    bg=WHITE_COLOUR,
    fg=MUTED_COLOUR,
    font=("Arial", 9),
)
result_label.grid(row=2, column=0, columnspan=5, sticky="e", padx=6)

menu_canvas = tk.Canvas(menu_area, bg=BG_COLOUR, highlightthickness=0)
menu_scrollbar = ttk.Scrollbar(
    menu_area,
    orient="vertical",
    command=menu_canvas.yview,
)
menu_canvas.configure(yscrollcommand=menu_scrollbar.set)
menu_scrollbar.grid(row=2, column=1, sticky="ns")
menu_canvas.grid(row=2, column=0, sticky="nsew")
product_frame = tk.Frame(menu_canvas, bg=BG_COLOUR)
canvas_window = menu_canvas.create_window((0, 0), window=product_frame, anchor="nw")
no_results_label = tk.Label(
    product_frame,
    text="No dishes found. Try another search or category.",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 11),
    padx=15,
    pady=15,
)


def update_scroll_region(event):
    menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))


def resize_product_frame(event):
    global menu_columns
    menu_canvas.itemconfigure(canvas_window, width=event.width)
    for column in range(5):
        product_frame.columnconfigure(column, weight=1, uniform="menu")
    new_columns = max(1, min(5, event.width // 180))
    if new_columns != menu_columns:
        menu_columns = new_columns
        update_menu()


product_frame.bind("<Configure>", update_scroll_region)
menu_canvas.bind("<Configure>", resize_product_frame)
for product in products:
    product_cards[product["id"]] = add_product_card(product)
update_menu()

# NOTE: Food detail page - photo, optional restaurant note, quantity, and add button.
detail_page = pages["Detail"]
detail_page.columnconfigure(0, weight=1)
detail_page.rowconfigure(1, weight=1)
tk.Button(
    detail_page,
    text="Back to menu",
    command=lambda: show_page("Food"),
    bg=WHITE_COLOUR,
    fg=NAV_COLOUR,
    activebackground=SECONDARY_COLOUR,
    relief="flat",
    padx=12,
    pady=7,
).grid(row=0, column=0, sticky="w", pady=(0, 8))

detail_panel = tk.Frame(
    detail_page,
    bg=WHITE_COLOUR,
    padx=14,
    pady=12,
    highlightthickness=1,
    highlightbackground=SECONDARY_COLOUR,
)
detail_panel.grid(row=1, column=0, sticky="nsew")
detail_panel.columnconfigure(0, weight=1)
detail_panel.rowconfigure(0, weight=1)
detail_image = tk.Label(
    detail_panel,
    text="Choose a dish from the menu",
    bg=SECONDARY_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 12),
)
detail_image.grid(row=0, column=0, sticky="nsew")

detail_info = tk.Frame(detail_panel, bg=WHITE_COLOUR)
detail_info.grid(row=1, column=0, sticky="ew", pady=(10, 4))
detail_info.columnconfigure(0, weight=1)
detail_name = tk.Label(
    detail_info,
    text="",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 16, "bold"),
    anchor="w",
)
detail_name.grid(row=0, column=0, sticky="ew")
detail_price = tk.Label(
    detail_info,
    text="",
    bg=WHITE_COLOUR,
    fg=NAV_COLOUR,
    font=("Arial", 15, "bold"),
)
detail_price.grid(row=0, column=1, sticky="e", padx=(12, 0))

note_heading = tk.Frame(detail_panel, bg=WHITE_COLOUR)
note_heading.grid(row=2, column=0, sticky="ew", pady=(8, 4))
tk.Label(
    note_heading,
    text="Note",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 11, "bold"),
).pack(side="left")
detail_note = tk.Text(
    detail_panel,
    height=3,
    wrap="word",
    font=("Arial", 10),
    relief="solid",
    bd=1,
    highlightthickness=1,
    highlightbackground=SECONDARY_COLOUR,
    padx=8,
    pady=7,
)
detail_note.grid(row=3, column=0, sticky="ew")
quantity_controls = tk.Frame(detail_panel, bg=WHITE_COLOUR)
quantity_controls.grid(row=4, column=0, pady=10)
tk.Button(
    quantity_controls,
    text="−",
    command=lambda: change_detail_quantity(-1),
    bg=SECONDARY_COLOUR,
    fg=NAV_COLOUR,
    activebackground=ACTIVE_COLOUR,
    font=("Arial", 15, "bold"),
    width=3,
    relief="flat",
).pack(side="left", padx=12)
detail_quantity_label = tk.Label(
    quantity_controls,
    text="1",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 12, "bold"),
    width=4,
)
detail_quantity_label.pack(side="left")
tk.Button(
    quantity_controls,
    text="+",
    command=lambda: change_detail_quantity(1),
    bg=NAV_COLOUR,
    fg=WHITE_COLOUR,
    activebackground=ACTIVE_COLOUR,
    font=("Arial", 15, "bold"),
    width=3,
    relief="flat",
).pack(side="left", padx=12)

detail_add_button = tk.Button(
    detail_panel,
    text="Add to basket",
    command=add_detail_to_basket,
    bg=NAV_COLOUR,
    fg=WHITE_COLOUR,
    activebackground=ACTIVE_COLOUR,
    activeforeground=WHITE_COLOUR,
    font=("Arial", 12, "bold"),
    pady=10,
)
detail_add_button.grid(row=5, column=0, sticky="ew", pady=(2, 0))

# Basket page (selected items, removal, and checkout navigation)
basket_page = pages["Basket"]
basket_page.columnconfigure(0, weight=1)
basket_page.rowconfigure(1, weight=1)
tk.Label(
    basket_page,
    text="Your basket",
    font=("Arial", 20, "bold"),
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
).grid(row=0, column=0, sticky="w", pady=(0, 10))
basket_panel = tk.Frame(basket_page, bg=WHITE_COLOUR, padx=18, pady=16)
basket_panel.grid(row=1, column=0, sticky="nsew")
basket_panel.columnconfigure(0, weight=1)
basket_panel.rowconfigure(1, weight=1)
basket_count_label = tk.Label(
    basket_panel,
    text="0 item(s)",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
)
basket_count_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
basket_list = tk.Listbox(
    basket_panel,
    height=12,
    font=("Arial", 11),
    selectmode=tk.SINGLE,
)
basket_list.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
basket_buttons = tk.Frame(basket_panel, bg=WHITE_COLOUR)
basket_buttons.grid(row=2, column=0, sticky="ew")
tk.Button(
    basket_buttons,
    text="Remove selected",
    command=remove_from_basket,
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    activebackground=SECONDARY_COLOUR,
    font=("Arial", 10),
).pack(side="left")
basket_total_label = tk.Label(
    basket_panel,
    text="Basket subtotal: RM 0.00",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    font=("Arial", 12, "bold"),
)
basket_total_label.grid(row=3, column=0, sticky="w", pady=(10, 5))
basket_actions = tk.Frame(basket_panel, bg=WHITE_COLOUR)
basket_actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
tk.Button(
    basket_actions,
    text="Back to menu",
    command=lambda: show_page("Food"),
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    activebackground=SECONDARY_COLOUR,
    font=("Arial", 10, "bold"),
    padx=12,
    pady=7,
).pack(side="left")
tk.Button(
    basket_actions,
    text="Go to payment",
    command=open_payment,
    bg=BUTTON_COLOUR,
    fg=WHITE_COLOUR,
    activebackground=ACTIVE_COLOUR,
    activeforeground=WHITE_COLOUR,
    font=("Arial", 10, "bold"),
    padx=16,
    pady=7,
).pack(side="right")

# Payment page (order details, item totals, and local demo submission)
payment_page = pages["Payment"]
payment_page.columnconfigure(0, weight=1)
payment_page.rowconfigure(1, weight=1)
tk.Label(
    payment_page,
    text="Your order",
    font=("Arial", 20, "bold"),
    bg=BG_COLOUR,
    fg=TEXT_COLOUR,
).grid(row=0, column=0, sticky="w", pady=(0, 10))
payment_panel = tk.Frame(payment_page, bg=WHITE_COLOUR, padx=14, pady=10)
payment_panel.grid(row=1, column=0, sticky="nsew")
payment_panel.columnconfigure(0, weight=1)
payment_panel.columnconfigure(1, weight=1)

tk.Label(
    payment_panel,
    text="Order total",
    font=("Arial", 14, "bold"),
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
subtotal_label = tk.Label(payment_panel, text="Subtotal: RM 0.00", bg=WHITE_COLOUR, fg=TEXT_COLOUR)
subtotal_label.grid(row=1, column=0, columnspan=2, sticky="w")
tax_label = tk.Label(
    payment_panel,
    text=f"Tax ({TAX_RATE * 100}%): RM 0.00",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
)
tax_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
service_label = tk.Label(
    payment_panel,
    text=f"Service charge ({SERVICE_CHARGE_RATE * 100}%): RM 0.00",
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
)
service_label.grid(row=3, column=0, columnspan=2, sticky="w")
total_label = tk.Label(
    payment_panel,
    text="Total to Pay: RM 0.00",
    font=("Arial", 14, "bold"),
    bg=WHITE_COLOUR,
    fg=NAV_COLOUR,
)
total_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 14))

tk.Label(payment_panel, text="Your name", bg=WHITE_COLOUR).grid(row=5, column=0, sticky="w", pady=3)
customer_entry = tk.Entry(payment_panel)
customer_entry.grid(row=6, column=0, sticky="ew", padx=(0, 12))
tk.Label(payment_panel, text="Dining method", bg=WHITE_COLOUR).grid(row=5, column=1, sticky="w", pady=3)
dining_method = tk.StringVar(value="Restaurant dining")
ttk.Combobox(
    payment_panel,
    textvariable=dining_method,
    values=("Restaurant dining", "Room delivery"),
    state="readonly",
).grid(row=6, column=1, sticky="ew")
tk.Label(payment_panel, text="Table or room number", bg=WHITE_COLOUR).grid(row=7, column=0, sticky="w", pady=3)
location_entry = tk.Entry(payment_panel)
location_entry.grid(row=8, column=0, sticky="ew", padx=(0, 12))
tk.Label(payment_panel, text="Payment method", bg=WHITE_COLOUR).grid(row=7, column=1, sticky="w", pady=3)
payment_method = tk.StringVar(value="Cash")
ttk.Combobox(
    payment_panel,
    textvariable=payment_method,
    values=("Cash", "Visa / Credit Card", "E-wallet"),
    state="readonly",
).grid(row=8, column=1, sticky="ew")
payment_actions = tk.Frame(payment_panel, bg=WHITE_COLOUR)
payment_actions.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))
tk.Button(
    payment_actions,
    text="Back to basket",
    command=lambda: show_page("Basket"),
    bg=WHITE_COLOUR,
    fg=TEXT_COLOUR,
    activebackground=SECONDARY_COLOUR,
    font=("Arial", 10, "bold"),
    padx=12,
    pady=7,
).pack(side="left")
tk.Button(
    payment_actions,
    text="Place order",
    command=place_order,
    bg=BUTTON_COLOUR,
    fg=WHITE_COLOUR,
    activebackground=ACTIVE_COLOUR,
    activeforeground=WHITE_COLOUR,
    font=("Arial", 10, "bold"),
    padx=16,
    pady=7,
).pack(side="right")

# Order history page (displays the latest locally saved orders)
orders_page = pages["Orders"]
orders_page.columnconfigure(0, weight=1)
orders_page.rowconfigure(1, weight=1)
tk.Label(
    orders_page,
    text="Order history",
    font=("Arial", 20, "bold"),
    bg=BG_COLOUR,
    fg=TEXT_COLOUR,
).grid(row=0, column=0, sticky="w", pady=(0, 10))
history_list = tk.Listbox(orders_page, height=14, font=("Arial", 11))
history_list.grid(row=1, column=0, sticky="nsew")
update_history()
update_basket()
show_page("Food")

window.mainloop()
