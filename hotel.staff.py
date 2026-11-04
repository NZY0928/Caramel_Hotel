import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os


User = {
    "ADMIN": "admin123",
    "CHIN YANG LIANG": "105820999",
    "NG ZHI YING": "105817373",
    "TAN YUAN": "105821552",
    "PUI YI XUAN": "105819201"
}

CURRENT_USER = ""
BOOKING_FILE = "booking.txt"


ROOM_TYPES = {
    "Superior Twin": {"price": 160},
    "Superior Triple": {"price": 200},
    "Superior Queen": {"price": 160},
    "Deluxe Suite": {"price": 350}
}

bookings, arrivals, departures = [], [], []

COLORS = {
    "bg": "#F0F2F5", "nav": "#3A5F7E", "nav_text": "#FFFFFF", 
    "card": "#FFFFFF", "text": "#1A2A3A", "muted": "#5F7080", 
    "accent": "#3A5F7E", "accent_hover": "#2B4A63", "line": "#D0D8E0", 
    "banner": "#D9E4EE", "red": "#A85248"
}

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_data():
    if not os.path.exists(BOOKING_FILE): 
        return
    bookings.clear()
    with open(BOOKING_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("name|"):
                continue
            
            parts = line.split("|")
            if len(parts) >= 16: 
                try:
                    total = float(parts[13]) if parts[13] else 0.0
                except:
                    total = 0.0
                    
                bookings.append({
                    "name": parts[0], "email": parts[1], "hp": parts[2], "ic": parts[3],
                    "room_type": parts[4], "room_number": parts[5], "check_in": parts[6], 
                    "check_out": parts[7], "amount_of_room": parts[8], "adults": parts[9],
                    "children": parts[10], "special_requests": parts[11], "promo_code": parts[12],
                    "total_price": total, 
                    "payment_method": parts[14], "status": parts[15]
                })
    print(f"Loaded {len(bookings)} bookings from {BOOKING_FILE}")

def save_data():
    with open(BOOKING_FILE, "w", encoding="utf-8") as f:
        f.write("# \nname|email|hp|ic|room_type|room_number|check_in|check_out|amount_of_room|adults|children|special_requests|promo_code|total_price|payment_method|status\n")
        for b in bookings:
            f.write(f"{b['name']}|{b['email']}|{b['hp']}|{b['ic']}|{b['room_type']}|{b['room_number']}|{b['check_in']}|{b['check_out']}|{b['amount_of_room']}|{b['adults']}|{b['children']}|{b['special_requests']}|{b['promo_code']}|{b['total_price']:.2f}|{b['payment_method']}|{b['status']}\n")

def execute_login(login_win):
    global CURRENT_USER
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if username in User and User[username] == password:
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        CURRENT_USER = username
        login_win.destroy()      
        init_main_window()       
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

def sign_out(win):
    if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
        win.destroy()
        start_login()


def clear_content():
    for w in content_area.winfo_children(): w.destroy()

def create_table(parent, columns, col_widths):
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Custom.Treeview", background=COLORS["card"], fieldbackground=COLORS["card"], foreground=COLORS["text"], rowheight=35, font=("Segoe UI", 10), borderwidth=1, relief="solid")
    style.configure("Custom.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=COLORS["banner"], foreground=COLORS["accent"], padding=10)
    
    frame = tk.Frame(parent, bg=COLORS["card"])
    frame.pack(fill="x", pady=10)
    tree = ttk.Treeview(frame, columns=columns, show="headings", style="Custom.Treeview", height=8)
    
    for i, col in enumerate(columns):
        tree.heading(col, text=col.upper())
        tree.column(col, width=col_widths[i], anchor="w")
        
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="x", expand=True)
    scroll.pack(side="right", fill="y")
    return tree


def show_dashboard():
    clear_content()
    banner = tk.Frame(content_area, bg=COLORS["banner"], height=80)
    banner.pack(fill="x", pady=(0, 20))
    tk.Label(banner, text="Overview Dashboard", font=("Georgia", 22, "bold"), bg=COLORS["banner"], fg=COLORS["accent"]).pack(side="left", padx=20, pady=20)
    
    tk.Label(content_area, text=f"Good day, {CURRENT_USER}.", font=("Georgia", 20), bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 15))
    
    stats_frame = tk.Frame(content_area, bg=COLORS["bg"])
    stats_frame.pack(fill="x", pady=(0, 20))
    
    cards = [
        ("Total Bookings", str(len(bookings)), "Reservations recorded"),
        ("Guests In-House", str(len(arrivals)), "Currently checked in"),
        ("Total Check-outs", str(len(departures)), "Completed stays")
    ]
    
    for title, value, sub in cards:
        card = tk.Frame(stats_frame, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=(0, 15))
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(padx=20, pady=20, fill="x")
        tk.Label(inner, text=title, font=("Segoe UI", 10, "bold"), bg=COLORS["card"], fg=COLORS["muted"]).pack(anchor="w")
        tk.Label(inner, text=value, font=("Georgia", 28), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(5, 0))
        tk.Label(inner, text=sub, font=("Segoe UI", 9), bg=COLORS["card"], fg=COLORS["muted"]).pack(anchor="w")

    p = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    p.pack(fill="x")
    tk.Label(p, text="Recent Room Bookings", font=("Georgia", 16), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 0))
    
    tree = create_table(p, ["Guest", "Room Type", "Check-in", "Status"], [150, 150, 120, 120])
    for b in bookings[-5:][::-1]:
        tree.insert("", "end", values=(b["name"], b["room_type"], b["check_in"], b["status"]))

def show_bookings():
    clear_content()
    tk.Label(content_area, text="Room Bookings", font=("Georgia", 24, "bold"), bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w")
    tk.Label(content_area, text="Create a reservation. Data auto-saves to booking.txt.", font=("Segoe UI", 10), bg=COLORS["bg"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 15))

    card = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    card.pack(fill="x", pady=(0, 20))
    f = tk.Frame(card, bg=COLORS["card"])
    f.pack(padx=20, pady=20, fill="x")

    tk.Label(f, text="Guest Name *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
    name_e = tk.Entry(f, font=("Segoe UI", 11), width=15, relief="solid", bd=1); name_e.grid(row=1, column=0, pady=(5, 15), padx=(0, 10))

    tk.Label(f, text="IC / Passport *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w")
    ic_e = tk.Entry(f, font=("Segoe UI", 11), width=15, relief="solid", bd=1); ic_e.grid(row=1, column=1, pady=(5, 15), padx=(0, 10))

    tk.Label(f, text="Room Type *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w")
    room_cb = ttk.Combobox(f, values=list(ROOM_TYPES.keys()), state="readonly", width=15, font=("Segoe UI", 11))
    room_cb.current(0); room_cb.grid(row=1, column=2, pady=(5, 15), padx=(0, 10))

    tk.Label(f, text="Check-in *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky="w")
    checkin_e = tk.Entry(f, font=("Segoe UI", 11), width=12, relief="solid", bd=1); checkin_e.insert(0, "2026-10-25"); checkin_e.grid(row=1, column=3, pady=(5, 15), padx=(0, 10))

    tk.Label(f, text="Check-out *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).grid(row=0, column=4, sticky="w")
    checkout_e = tk.Entry(f, font=("Segoe UI", 11), width=12, relief="solid", bd=1); checkout_e.insert(0, "2026-10-26"); checkout_e.grid(row=1, column=4, pady=(5, 15), padx=(0, 10))

    total_lbl = tk.Label(f, text="Total: RM 160.00", font=("Georgia", 14, "bold"), fg=COLORS["accent"], bg=COLORS["card"])
    total_lbl.grid(row=1, column=5, padx=(10, 0))

    def add_booking():
        name, ic = name_e.get().strip(), ic_e.get().strip()
        if not name or not ic: return messagebox.showwarning("Missing", "Please fill in Name and IC.")
        room_type = room_cb.get()
        price = ROOM_TYPES[room_type]["price"]
        
        bookings.append({
            "name": name, "email": "-", "hp": "-", "ic": ic,
            "room_type": room_type, "room_number": "-", 
            "check_in": checkin_e.get(), "check_out": checkout_e.get(), 
            "amount_of_room": "1", "adults": "1", "children": "0", 
            "special_requests": "", "promo_code": "", 
            "total_price": price, "payment_method": "Cash", 
            "status": "Confirmed"
        })
        save_data()
        messagebox.showinfo("Success", "Booking saved successfully!")
        show_bookings()

    tk.Button(f, text="Confirm →", font=("Segoe UI", 10, "bold"), bg=COLORS["accent"], fg="white", relief="flat", padx=15, pady=6, command=add_booking).grid(row=1, column=6, padx=10)

    p = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    p.pack(fill="x")
    tk.Label(p, text=f"All Bookings ({len(bookings)})", font=("Georgia", 16), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 0))
    
    tree = create_table(p, ["Guest", "Email", "Room Type", "Room No.", "Check-in", "Total", "Status"], 
                        [120, 150, 120, 80, 100, 90, 100])
    for b in bookings[::-1]:
        tree.insert("", "end", values=(b["name"], b["email"], b["room_type"], b["room_number"], b["check_in"], f"RM {b['total_price']:.2f}", b["status"]))

def show_checkin():
    clear_content()
    tk.Label(content_area, text="Guest Check-in", font=("Georgia", 24, "bold"), bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w")
    
    card = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    card.pack(fill="x", pady=(15, 20))
    f = tk.Frame(card, bg=COLORS["card"]); f.pack(padx=20, pady=20, anchor="w")

    tk.Label(f, text="Guest Name *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack(side="left")
    name_e = tk.Entry(f, font=("Segoe UI", 11), width=25, relief="solid", bd=1); name_e.pack(side="left", padx=10)

    def do_checkin():
        name = name_e.get().strip()
        if not name: return
        found = False
        for i, b in enumerate(bookings):
            if b["name"].lower() == name.lower() and b["status"] == "Confirmed":
                b["status"] = "Checked In" 
                arrivals.append(b)
                save_data()
                found = True
                break
        if found:
            messagebox.showinfo("Success", "Checked in successfully!")
        else:
            messagebox.showerror("Error", "Booking not found or already checked in.")
        show_checkin()

    tk.Button(f, text="Confirm Check-in →", font=("Segoe UI", 10, "bold"), bg=COLORS["accent"], fg="white", relief="flat", padx=15, pady=6, command=do_checkin).pack(side="left", padx=10)

    p = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    p.pack(fill="x")
    tk.Label(p, text="Currently Checked-in", font=("Georgia", 16), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 0))
    
    tree = create_table(p, ["Guest", "Room Type", "Check-in", "Check-out", "Status"], [150, 150, 120, 120, 100])
    for a in arrivals:
        tree.insert("", "end", values=(a["name"], a["room_type"], a["check_in"], a["check_out"], a["status"]))

def show_checkout():
    clear_content()
    tk.Label(content_area, text="Guest Check-out", font=("Georgia", 24, "bold"), bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w")
    
    card = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    card.pack(fill="x", pady=(15, 20))
    f = tk.Frame(card, bg=COLORS["card"]); f.pack(padx=20, pady=20, anchor="w")

    tk.Label(f, text="Guest Name *", bg=COLORS["card"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack(side="left")
    name_e = tk.Entry(f, font=("Segoe UI", 11), width=25, relief="solid", bd=1); name_e.pack(side="left", padx=10)

    def do_checkout():
        name = name_e.get().strip()
        if not name: return
        for i, a in enumerate(arrivals):
            if a["name"].lower() == name.lower():
                a["status"] = "Checked Out"
                departures.append(arrivals.pop(i))
                save_data()
                messagebox.showinfo("Success", "Checked out successfully!")
                show_checkout()
                return
        messagebox.showerror("Error", "Guest not found in active check-ins.")

    tk.Button(f, text="Confirm Check-out →", font=("Segoe UI", 10, "bold"), bg=COLORS["accent"], fg="white", relief="flat", padx=15, pady=6, command=do_checkout).pack(side="left", padx=10)

    p = tk.Frame(content_area, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
    p.pack(fill="x")
    tk.Label(p, text="Recent Check-outs", font=("Georgia", 16), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 0))
    
    tree = create_table(p, ["Guest", "Room Type", "Check-in", "Status"], [150, 150, 120, 100])
    for d in departures[::-1]:
        tree.insert("", "end", values=(d["name"], d["room_type"], d["check_in"], d["status"]))


def build_menu():
    menu = tk.Frame(main_window, bg=COLORS["nav"], width=220)
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)
    
    logo_frame = tk.Frame(menu, bg=COLORS["nav"])
    logo_frame.pack(fill="x", padx=20, pady=(30, 20))
    tk.Label(logo_frame, text="CARAMEL", fg=COLORS["nav_text"], bg=COLORS["nav"], font=("Georgia", 16, "bold")).pack(anchor="w")
    tk.Label(logo_frame, text="HOTEL", fg=COLORS["nav_text"], bg=COLORS["nav"], font=("Georgia", 16, "bold")).pack(anchor="w")
    tk.Label(logo_frame, text="STAFF PORTAL", fg="#A8C0D6", bg=COLORS["nav"], font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))
    
    for name, func in [("Overview", show_dashboard), ("Bookings", show_bookings), ("Check-in", show_checkin), ("Check-out", show_checkout)]:
        tk.Button(menu, text=name, bg=COLORS["nav"], fg="white", activebackground=COLORS["accent_hover"], activeforeground="white", relief="flat", anchor="w", padx=20, pady=12, font=("Segoe UI", 11), command=func).pack(fill="x")
    
    tk.Button(menu, text="Sign Out", bg=COLORS["nav"], fg="#FFB4B4", activebackground=COLORS["red"], activeforeground="white", relief="flat", anchor="w", padx=20, pady=12, font=("Segoe UI", 11, "bold"), command=lambda: sign_out(main_window)).pack(fill="x", side="bottom", pady=20)

def init_main_window():
    global main_window, content_area
    main_window = tk.Tk()
    main_window.title("Caramel Hotel · Staff System")
    main_window.geometry("1150x750")
    main_window.configure(bg=COLORS["bg"])
    
    build_menu()
    content_area = tk.Frame(main_window, bg=COLORS["bg"])
    content_area.pack(side="left", fill="both", expand=True, padx=30, pady=30)

    load_data()
    show_dashboard()
    main_window.mainloop()

def start_login():
    global username_entry, password_entry
    login_win = tk.Tk()
    login_win.title("Caramel Hotel Staff Login")
    login_win.geometry("1180x720")
    login_win.configure(bg="#C5D6E2") 

    tk.Label(login_win, text="Caramel Hotel Staff Login", font=("Helvetica", 16, "bold"), fg=COLORS["nav"], bg="#C5D6E2").pack(pady=80)

    frame = tk.Frame(login_win, bg="#FFFFFF", highlightbackground=COLORS["line"], highlightthickness=1)
    frame.place(x=390, y=200, width=400, height=300)

    tk.Label(frame, text="Please enter your name (eg.ADMIN):", font=("Helvetica", 11), fg=COLORS["text"], bg="#FFFFFF").pack(pady=(30, 5))
    username_entry = tk.Entry(frame, font=("Helvetica", 12), relief="solid", bd=1)
    username_entry.pack(pady=(0, 15), ipady=4)

    tk.Label(frame, text="Password:", font=("Helvetica", 11), fg=COLORS["text"], bg="#FFFFFF").pack(pady=5)
    password_entry = tk.Entry(frame, font=("Helvetica", 12), show="*", relief="solid", bd=1)
    password_entry.pack(pady=(0, 20), ipady=4)

    tk.Button(frame, text="Login", font=("Helvetica", 12, "bold"), bg=COLORS["accent"], fg="white", relief="flat", width=20, command=lambda: execute_login(login_win)).pack(pady=10, ipady=5)

    login_win.mainloop()

if __name__ == "__main__":
    start_login()