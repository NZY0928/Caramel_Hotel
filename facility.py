import tkinter as tk

class FacilityPageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caramel Hotel - Facility")
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

        tk.Label(self.body, text="Hotel Facilities", font=("Arial", 21, "bold"), bg="#C5D6E2", fg="#34465A").pack(fill="x", pady=(0, 6))
        tk.Frame(self.body, bg="#C5D6E2", height=2).pack(fill="x", pady=(0, 20))

        tk.Label(self.body, text="Enjoy our wide range of facilities designed for your comfort and relaxation.", font=("Helvetica", 12), fg="#34465A", bg="#DFE2E5", wraplength=900, justify="center").pack(pady=(0, 20))

        facilities = [
            ("Swimming Pool", "Outdoor pool open 7:00 AM – 10:00 PM.\nTowels and sun loungers provided."),
            ("Fitness Centre", "Fully equipped gym with cardio and weights.\nOpen 24 hours for hotel guests."),
            ("Spa & Wellness", "Massage, sauna and steam room.\nAdvance booking recommended."),
            ("Restaurant", "Local and international cuisine.\nBreakfast 6:30–10:30 AM, dinner from 6:00 PM."),
            ("Free Wi-Fi", "High-speed internet throughout the hotel.\nNo password required in public areas."),
            ("Airport Shuttle", "Complimentary shuttle service.\nPlease reserve at the front desk."),
        ]

        grid = tk.Frame(self.body, bg="#DFE2E5")
        grid.pack(padx=40, pady=10, fill="x")

        for i, (title, desc) in enumerate(facilities):
            card = tk.Frame(grid, bg="#FFFFFF", padx=18, pady=14, highlightbackground="#C9D2DC", highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, padx=12, pady=10, sticky="nsew")
            tk.Label(card, text=title, font=("Helvetica", 13, "bold"), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(0, 6))
            tk.Label(card, text=desc, font=("Helvetica", 11), fg="#34465A", bg="#FFFFFF", justify="left", anchor="w", wraplength=380).pack(fill="x")

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

if __name__ == "__main__":
    app = FacilityPageApp()
    app.mainloop()