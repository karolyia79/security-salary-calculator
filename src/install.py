import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import importlib
import os

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Security Bérkalkulátor 2026 - Telepítő")
        self.root.geometry("600x500") # Kicsit szélesebb ablak a biztonság kedvéért

        # Adatok
        self.external_libs = {"fpdf": "fpdf"}
        self.standard_libs = ["sqlite3", "tkinter", "hashlib", "json", "datetime", "math"]

        self.setup_ui()
        self.check_initial_state()

    def setup_ui(self):
        # Fő konténer
        self.main_container = tk.Frame(self.root, bg="#f0f0f0")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Címsor
        header = tk.Label(self.main_container, text="Rendszerösszetevők Ellenőrzése", 
                          font=("Segoe UI", 16, "bold"), bg="#f0f0f0")
        header.pack(pady=(0, 20))

        # Lista keret
        self.list_frame = tk.LabelFrame(self.main_container, text=" Modulok állapota ", 
                                       font=("Segoe UI", 10, "bold"), bg="#f0f0f0", padx=10, pady=10)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # Gombok kerete (Fix hely az ablak alján)
        btn_frame = tk.Frame(self.main_container, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        # Gombok egységes stílussal
        btn_config = {"font": ("Segoe UI", 10), "width": 18, "height": 2}

        self.install_btn = tk.Button(btn_frame, text="Szükséges telepítése", 
                                     command=self.run_installation, state=tk.DISABLED, **btn_config)
        self.install_btn.pack(side=tk.LEFT, padx=5)

        self.start_btn = tk.Button(btn_frame, text="Program indítása", 
                                   command=self.start_program, state=tk.DISABLED, **btn_config)
        self.start_btn.pack(side=tk.RIGHT, padx=5)

        self.exit_btn = tk.Button(btn_frame, text="Kilépés", 
                                  command=self.root.destroy, **btn_config)
        self.exit_btn.pack(side=tk.RIGHT, padx=5)

    def add_item(self, name, status, color):
        row = tk.Frame(self.list_frame, bg="#f0f0f0")
        row.pack(fill=tk.X, pady=5)
        
        tk.Label(row, text=name, font=("Segoe UI", 10), bg="#f0f0f0", width=40, anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=status, font=("Segoe UI", 10, "bold"), bg="#f0f0f0", fg=color).pack(side=tk.RIGHT)

    def check_initial_state(self):
        needs_install = False
        
        # Alapmodulok
        for lib in self.standard_libs:
            try:
                importlib.import_module(lib)
                self.add_item(f"Python alaprendszer: {lib}", "✓ Rendben", "green")
            except ImportError:
                self.add_item(f"Python alaprendszer: {lib}", "✗ HIÁNYZIK", "red")

        # Külső könyvtárak (fpdf)
        for mod, pkg in self.external_libs.items():
            try:
                importlib.import_module(mod)
                self.add_item(f"Külső könyvtár: {pkg}", "✓ Telepítve", "green")
            except ImportError:
                self.add_item(f"Külső könyvtár: {pkg}", "! Nincs telepítve", "#cc6600")
                needs_install = True

        if needs_install:
            self.install_btn.config(state=tk.NORMAL, bg="#e1e1e1")
        else:
            self.start_btn.config(state=tk.NORMAL, bg="#4CAF50", fg="white")
            status_lbl = tk.Label(self.main_container, text="Minden összetevő naprakész!", 
                                  font=("Segoe UI", 10, "italic"), fg="blue", bg="#f0f0f0")
            status_lbl.pack(pady=5)

    def run_installation(self):
        self.install_btn.config(state=tk.DISABLED)
        success = True
        
        for mod, pkg in self.external_libs.items():
            try:
                importlib.import_module(mod)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                except:
                    success = False
        
        if success:
            messagebox.showinfo("Kész", "A telepítés sikeresen befejeződött!")
            # Ablak frissítése a gombok állapota miatt
            for widget in self.list_frame.winfo_children():
                widget.destroy()
            self.check_initial_state()
        else:
            messagebox.showerror("Hiba", "Hiba történt a telepítés során. Próbálja rendszergazdaként!")
            self.install_btn.config(state=tk.NORMAL)

    def start_program(self):
        start_file = "start.py"
        if os.path.exists(start_file):
            self.root.destroy()
            subprocess.Popen([sys.executable, start_file])
        else:
            messagebox.showerror("Hiba", f"A(z) {start_file} nem található!")

if __name__ == "__main__":
    root = tk.Tk()
    # Ablak középre helyezése
    window_width = 600
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = InstallerGUI(root)
    root.mainloop()