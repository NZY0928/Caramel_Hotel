import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

class HomePageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caramel Hotel - Home")
        self.geometry("1180x780")
        self.configure(bg="#DFE2E5")
        
        # 滚动容器
        canvas = tk.Canvas(self, bg="#DFE2E5", highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(canvas, bg="#DFE2E5")
        body_id = canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(body_id, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 标题
        tk.Label(self.body, text="Caramel Hotel Information", font=("Arial", 21, "bold"), bg="#C5D6E2", fg="#34465A").pack(fill="x", pady=(0, 6))
        tk.Frame(self.body, bg="#C5D6E2", height=2).pack(fill="x", pady=(0, 20))

        # 欢迎卡片
        welcome = tk.Frame(self.body, bg="#FFFFFF", highlightbackground="#C9D2DC", highlightthickness=1)
        welcome.pack(pady=10, padx=40, fill="x")
        tk.Label(welcome, text="Welcome to Caramel Hotel!", font=("Helvetica", 14, "bold"), fg="#34465A", bg="#FFFFFF").pack(pady=(14, 4))
        tk.Label(welcome, text="We offer the best services for your comfort.", font=("Helvetica", 12), fg="#34465A", bg="#FFFFFF").pack(pady=2)
        tk.Label(welcome, text="Check-in: 3:00 PM  |  Check-out: 12:00 PM", font=("Helvetica", 12), fg="#34465A", bg="#FFFFFF").pack(pady=(2, 14))

        # 房型展示
        tk.Label(self.body, text="We look forward to welcoming you!", font=("Helvetica", 14, "bold"), fg="#34465A", bg="#C5D6E2").pack(pady=14, fill="x")
        img_frame = tk.Frame(self.body, bg="#C5D6E2")
        img_frame.pack(pady=10, padx=20, fill="x")
        
        rooms = [("Deluxe_Twin.png", "Deluxe Twin"), ("Superior_Twin.png", "Superior Twin"), ("Deluxe_Queen.png", "Deluxe Queen")]
        for col, (fn, name) in enumerate(rooms):
            card = tk.Frame(img_frame, bg="#FFFFFF", padx=10, pady=10, highlightbackground="#C9D2DC", highlightthickness=1)
            card.grid(row=0, column=col, padx=12, pady=8, sticky="n")
            try:
                img = Image.open(fn).resize((360, 270), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            except:
                photo = ImageTk.PhotoImage(Image.new("RGB", (360, 270), (220, 220, 220)))
            lbl = tk.Label(card, image=photo, bg="#FFFFFF")
            lbl.image = photo
            lbl.pack()
            tk.Label(card, text=name, font=("Helvetica", 11, "bold"), fg="#34465A", bg="#FFFFFF").pack(pady=(6, 0))
        for c in range(3): img_frame.grid_columnconfigure(c, weight=1)

        # 联系方式
        contact = tk.Frame(self.body, bg="#FFFFFF", highlightbackground="#C9D2DC", highlightthickness=1)
        contact.pack(pady=14, padx=40, fill="x")
        tk.Label(contact, text="For more information, please contact us:", font=("Helvetica", 12, "bold"), fg="#34465A", bg="#FFFFFF").pack(pady=(14, 6))
        tk.Label(contact, text="Address: 123 Main Street, City, Country\nPhone: +1234567890\nEmail: info@caramelhotel.com", font=("Helvetica", 12), fg="#34465A", bg="#FFFFFF", justify="center").pack(pady=(0, 14))

if __name__ == "__main__":
    app = HomePageApp()
    app.mainloop()