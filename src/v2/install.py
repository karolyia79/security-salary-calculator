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
        self.root.geometry("600x580")
        self.root.configure(bg="#f0f0f0")

        # Bővített külső könyvtárak listája
        self.external_libs = {
            "fpdf": "fpdf",
            "matplotlib": "matplotlib",
            "reportlab": "reportlab"  # Az éves összesítőhöz szükséges
        }
        
        self.standard_libs = ["sqlite3", "tkinter", "hashlib", "json", "datetime", "math"]

        self.setup_ui()
        self.check_initial_state()

    def setup_ui(self):
        self.main_container = tk.Frame(self.root, bg="#f0f0f0")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)

        header = tk.Label(self.main_container, text="Rendszerösszetevők Ellenőrzése", 
                          font=("Segoe UI", 18, "bold"), bg="#f0f0f0", fg="#333")
        header.pack(pady=(0, 20))

        self.list_frame = tk.LabelFrame(self.main_container, text=" Modulok állapota ", 
                                       font=("Segoe UI", 10, "bold"), bg="#f0f0f0", padx=15, pady=15)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.main_container, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=(25, 0))

        btn_style = {"font": ("Segoe UI", 10, "bold"), "width": 18, "height": 2, "bd": 1}

        self.install_btn = tk.Button(btn_frame, text="Telepítés", 
                                     command=self.run_installation, state=tk.DISABLED, bg="#d1d1d1", **btn_style)
        self.install_btn.pack(side=tk.LEFT, padx=5)

        self.start_btn = tk.Button(btn_frame, text="Program indítása", 
                                   command=self.start_program, state=tk.DISABLED, bg="#d1d1d1", **btn_style)
        self.start_btn.pack(side=tk.RIGHT, padx=5)

        self.exit_btn = tk.Button(btn_frame, text="Kilépés", 
                                  command=self.root.destroy, bg="#ff9999", **btn_style)
        self.exit_btn.pack(side=tk.RIGHT, padx=5)

    def add_item(self, name, status, color):
        row = tk.Frame(self.list_frame, bg="#f0f0f0")
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, text=name, font=("Segoe UI", 10), bg="#f0f0f0", width=35, anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=status, font=("Segoe UI", 10, "bold"), bg="#f0f0f0", fg=color).pack(side=tk.RIGHT)

    def check_initial_state(self):
        needs_install = False
        for lib in self.standard_libs:
            try:
                importlib.import_module(lib)
                self.add_item(f"Rendszermodul: {lib}", "✓ Elérhető", "#2e7d32")
            except ImportError:
                self.add_item(f"Rendszermodul: {lib}", "✗ HIÁNYZIK", "#c62828")

        for mod, pkg in self.external_libs.items():
            try:
                importlib.import_module(mod)
                self.add_item(f"Speciális modul: {pkg}", "✓ Telepítve", "#2e7d32")
            except ImportError:
                self.add_item(f"Speciális modul: {pkg}", "! Hiányzik", "#ef6c00")
                needs_install = True

        if needs_install:
            self.install_btn.config(state=tk.NORMAL, bg="#0277bd", fg="white")
        else:
            self.start_btn.config(state=tk.NORMAL, bg="#43a047", fg="white")

    def run_installation(self):
        self.install_btn.config(state=tk.DISABLED, text="Telepítés...")
        success = True
        for mod, pkg in self.external_libs.items():
            try:
                importlib.import_module(mod)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                except: success = False
        
        if success:
            messagebox.showinfo("Siker", "Minden összetevő (FPDF, Matplotlib, ReportLab) telepítve!")
            for widget in self.list_frame.winfo_children(): widget.destroy()
            self.check_initial_state()
        else:
            messagebox.showerror("Hiba", "Hiba a telepítés során!")

    def start_program(self):
        if os.path.exists("start.py"):
            self.root.destroy()
            subprocess.Popen([sys.executable, "start.py"])
        else:
            messagebox.showerror("Hiba", "start.py nem található!")

if __name__ == "__main__":
    root = tk.Tk()
    w, h = 600, 580
    sx, sy = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f'{w}x{h}+{int(sx/2-w/2)}+{int(sy/2-h/2)}')
    InstallerGUI(root).root.mainloop()