import tkinter as tk

class PromotionsPageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caramel Hotel - Promotions")
        self.geometry("1180x780")
        self.configure(bg="#DFE2E5")
        
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

        tk.Label(self.body, text="Current Promotions", font=("Arial", 21, "bold"), bg="#C5D6E2", fg="#34465A").pack(fill="x", pady=(0, 6))
        tk.Frame(self.body, bg="#C5D6E2", height=2).pack(fill="x", pady=(0, 20))

        tk.Label(self.body, text="Take advantage of our limited-time offers.", font=("Helvetica", 12), fg="#34465A", bg="#DFE2E5").pack(pady=(0, 20))

        promos = [
            ("Weekend Getaway", "Stay 2 nights, get 20% off the second night.", "Valid Friday–Sunday • Until 31 Dec 2025"),
            ("Early Bird Breakfast", "Book 30 days in advance and enjoy complimentary breakfast.", "Valid for Deluxe and Superior rooms"),
            ("Family Package", "Two adjoining rooms + free kids' meals.", "Valid all year • Subject to availability"),
            ("Long Stay Discount", "Stay 5+ nights and save 15% on the total bill.", "Excludes public holidays"),
        ]

        for title, desc, note in promos:
            card = tk.Frame(self.body, bg="#FFFFFF", padx=22, pady=16, highlightbackground="#C9D2DC", highlightthickness=1)
            card.pack(pady=8, padx=60, fill="x")
            tk.Label(card, text=title, font=("Helvetica", 14, "bold"), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(0, 4))
            tk.Label(card, text=desc, font=("Helvetica", 12), fg="#34465A", bg="#FFFFFF", anchor="w", justify="left", wraplength=900).pack(fill="x", pady=(0, 6))
            tk.Label(card, text=note, font=("Helvetica", 10, "italic"), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x")

        tk.Label(self.body, text="For reservations, contact us at info@caramelhotel.com", font=("Helvetica", 12, "bold"), fg="#34465A", bg="#DFE2E5").pack(pady=30)

if __name__ == "__main__":
    app = PromotionsPageApp()
    app.mainloop()