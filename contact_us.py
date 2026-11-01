import tkinter as tk

class ContactPageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caramel Hotel - Contact Us")
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

        tk.Label(self.body, text="Contact Us", font=("Arial", 21, "bold"), bg="#C5D6E2", fg="#34465A").pack(fill="x", pady=(0, 6))
        tk.Frame(self.body, bg="#C5D6E2", height=2).pack(fill="x", pady=(0, 20))

        info_card = tk.Frame(self.body, bg="#FFFFFF", padx=24, pady=20, highlightbackground="#C9D2DC", highlightthickness=1)
        info_card.pack(pady=10, padx=60, fill="x")
        tk.Label(info_card, text="Get in Touch", font=("Helvetica", 14, "bold"), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(0, 10))

        rows = [("Address", "123 Main Street, City, Country"), ("Phone", "+1234567890"), ("Email", "info@caramelhotel.com"), ("Front Desk Hours", "24 hours")]
        for label, value in rows:
            row = tk.Frame(info_card, bg="#FFFFFF")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", font=("Helvetica", 11, "bold"), fg="#34465A", bg="#FFFFFF", width=16, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=("Helvetica", 11), fg="#34465A", bg="#FFFFFF", anchor="w").pack(side="left")

        form_card = tk.Frame(self.body, bg="#FFFFFF", padx=24, pady=20, highlightbackground="#C9D2DC", highlightthickness=1)
        form_card.pack(pady=14, padx=60, fill="x")
        tk.Label(form_card, text="Send Us a Message", font=("Helvetica", 14, "bold"), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(0, 10))

        tk.Label(form_card, text="Name", font=("Helvetica", 11), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x")
        name_entry = tk.Entry(form_card, font=("Helvetica", 11), relief="solid", borderwidth=1, highlightthickness=0)
        name_entry.pack(fill="x", pady=(2, 10), ipady=4)

        tk.Label(form_card, text="Email", font=("Helvetica", 11), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x")
        email_entry = tk.Entry(form_card, font=("Helvetica", 11), relief="solid", borderwidth=1, highlightthickness=0)
        email_entry.pack(fill="x", pady=(2, 10), ipady=4)

        tk.Label(form_card, text="Message", font=("Helvetica", 11), fg="#34465A", bg="#FFFFFF", anchor="w").pack(fill="x")
        message_text = tk.Text(form_card, font=("Helvetica", 11), height=5, relief="solid", borderwidth=1, highlightthickness=0)
        message_text.pack(fill="x", pady=(2, 12))

        status = tk.Label(form_card, text="", font=("Helvetica", 10, "italic"), fg="#486B92", bg="#FFFFFF")

        def submit():
            name, email, msg = name_entry.get().strip(), email_entry.get().strip(), message_text.get("1.0", "end").strip()
            if not name or not email or not msg:
                status.config(text="Please fill in all fields.", fg="#B23A48")
            else:
                status.config(text="Thank you! We will get back to you soon.", fg="#486B92")
                name_entry.delete(0, "end")
                email_entry.delete(0, "end")
                message_text.delete("1.0", "end")
            status.pack(pady=(4, 0))

        tk.Button(form_card, text="Send Message", command=submit, bg="#486B92", fg="#FFFFFF", relief="flat", activebackground="#7E93A9", activeforeground="#FFFFFF", font=("Arial", 11), padx=18, pady=6, cursor="hand2").pack(pady=(0, 6))

if __name__ == "__main__":
    app = ContactPageApp()
    app.mainloop()