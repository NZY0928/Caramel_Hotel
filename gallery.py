import tkinter as tk
from PIL import Image, ImageTk

class GalleryPageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caramel Hotel - Gallery")
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

        tk.Label(self.body, text="Gallery", font=("Arial", 21, "bold"), bg="#C5D6E2", fg="#34465A").pack(fill="x", pady=(0, 6))
        tk.Frame(self.body, bg="#C5D6E2", height=2).pack(fill="x", pady=(0, 20))

        tk.Label(self.body, text="A glimpse of the Caramel Hotel experience.", font=("Helvetica", 12), fg="#34465A", bg="#DFE2E5").pack(pady=(0, 20))

        items = [
            ("lobby.png", "Lobby"), ("pool.png", "Swimming Pool"), ("restaurant.png", "Restaurant"),
            ("Deluxe_Twin.png", "Room View"), ("spa.png", "Spa"), ("garden.png", "Garden"),
        ]

        grid = tk.Frame(self.body, bg="#DFE2E5")
        grid.pack(padx=40, pady=10, fill="x")

        for i, (fn, caption) in enumerate(items):
            card = tk.Frame(grid, bg="#FFFFFF", padx=8, pady=8, highlightbackground="#C9D2DC", highlightthickness=1)
            card.grid(row=i // 3, column=i % 3, padx=12, pady=12, sticky="n")
            try:
                img = Image.open(fn).resize((320, 220), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            except: 
                photo = ImageTk.PhotoImage(Image.new("RGB", (320, 220), (220, 220, 220)))
            lbl = tk.Label(card, image=photo, bg="#FFFFFF")
            lbl.image = photo
            lbl.pack()
            tk.Label(card, text=caption, font=("Helvetica", 11, "bold"), fg="#34465A", bg="#FFFFFF").pack(pady=(6, 0))

        for c in range(3): grid.grid_columnconfigure(c, weight=1)

if __name__ == "__main__":
    app = GalleryPageApp()
    app.mainloop()