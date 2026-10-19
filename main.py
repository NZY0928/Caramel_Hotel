import tkinter as tk
from tkinter import ttk, messagebox

class HotelApp(tk.Tk):
    def __init__(self):

        self.title("Caramel Hotel")
        self.geometry("1180*780")

        # Navigation panel
        self.nav_frame = tk.Frame(self, bg="#3E2723", width=200)
        self.nav_frame.pack(side="top", fill="x")

        tk.Label(
            self.nav_frame,
            text = "CARAMEL HOTEL",
            bg="#3E2723",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=20, pady=20)

        # Navigation buttons on the right
        self.button_frame = tk.Frame(
            self.nav_frame, bg="3E2723"
        )
        self.button_frame.pack(side="right", padx=10)

        pages = [
            "Home",
            "Accommodation",
            "Menu",
            "Facility",
            "Promotions",
            "Gallery",
            "Contact Us"
        ]

        for page in pages:
            tk.Button(
                self.button_frame,
                text=page,
                command=lambda p=page: self.show_page(p),
                bg="#3E2723",
                fg="white",
                activebackground="#795548",
                activeforeground="white",
                relief="flat",
                font=("Arial", 10, "bold") if page == self.current_page else ("Arial", 10),
                padx=8,
                pady=5
            ).pack(side="left", padx=2)

            # Main content are
            self.content_frame = tk.Frame(self, bg="white")
            self.content_frame.pack(
                side="top", fill="both", expand=True
            )

            self.show_page("Home")

        def show_page(self, page):
            # Clear the old page
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            # Display the selected page
            if page == "Accommodation":
                pass
                
            else:
                tk.Lable(
                    self.content_frame,
                    text=page,
                    font=("Arial", 24, "bold"),
                    bg="white"
                ).pack(pady=30)

if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()