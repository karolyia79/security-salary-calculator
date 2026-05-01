import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sys
import sqlite3
import hashlib
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ModernBerszamfejtoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Security Bérkalkulátor 2026")
        
        self.version = "v0.9d"
        self.db_status = "Adatbázis rendben betöltve"
        self.aktualis_dolgozo = None
        self.aktualis_ceg_id = None
        self.current_user_acc = "user" 
        self.current_user_fullname = "Ismeretlen"
        self.pulse_state = False
        self.session_file = ".session_data"
        self.session_start_time = None
        
        min_width = 650  
        min_height = 800 
        self.root.minsize(min_width, min_height)
        self.root.state('zoomed') 
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)

        self.colors = {
            "bg": "#F8FAFC",
            "header": "#1E293B",
            "accent": "#3B82F6",
            "exit": "#EF4444",
            "text_light": "#F8FAFC",
            "info": "#10B981",
            "warning": "#F59E0B",
            "su_red": "#EF4444",
            "ku_blue": "#2563EB"
        }

        self.root.configure(bg=self.colors["bg"])
        self.setup_styles()
        self.create_main_ui()
        self.update_clock()
        self.frissit_db_statisztika()
        self.pulse_button() 
        
        self.init_auth_system()
        # Automatikus belépés és cég betöltés ellenőrzése
        self.root.after(100, self.check_auto_login)

    def init_auth_system(self):
        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                fullname TEXT,
                password_hash TEXT,
                acc TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('session_timeout_hours', '24')")
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'acc' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN acc TEXT")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        if user_count == 0:
            self.show_superuser_creation()

    def get_session_timeout(self):
        try:
            conn = sqlite3.connect('berszamitas.db')
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'session_timeout_hours'")
            result = cursor.fetchone()
            conn.close()
            return int(result[0]) * 3600 if result else 86400
        except:
            return 86400

    def save_session(self, username, fullname, acc, timestamp, ceg_id=None):
        """Munkamenet adatok mentése fájlba."""
        session_data = {
            "username": username,
            "fullname": fullname,
            "acc": acc,
            "timestamp": timestamp,
            "last_ceg_id": ceg_id
        }
        with open(self.session_file, "w") as f:
            json.dump(session_data, f)

    def check_auto_login(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                
                timeout = self.get_session_timeout()
                saved_time = data.get("timestamp", 0)
                if time.time() - saved_time < timeout:
                    self.session_start_time = saved_time
                    self.current_user_fullname = data["fullname"]
                    self.current_user_acc = data["acc"]
                    
                    # Korábban mentett cég visszaállítása
                    saved_ceg_id = data.get("last_ceg_id")
                    if saved_ceg_id:
                        self.aktualis_ceg_id = str(saved_ceg_id)
                    
                    self.user_label_var.set(f"Bejelentkezve: {data['username']} ({data['fullname']}) | Jogosultság: {data['acc']}")
                    self.update_ui_by_access(data['username'], data['fullname'], data['acc'])
                    self.frissit_fejlecet(None) # Fejléc frissítése a cég nevével
                    return 
            except:
                pass
        self.show_login_window()

    def show_login_window(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Bejelentkezés")
        width, height = 350, 420
        x = (self.login_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.login_win.winfo_screenheight() // 2) - (height // 2)
        self.login_win.geometry(f"{width}x{height}+{x}+{y}")
        self.login_win.configure(bg=self.colors["header"])
        self.login_win.transient(self.root)
        self.login_win.grab_set()
        self.login_win.protocol("WM_DELETE_WINDOW", self.exit_program)

        tk.Label(self.login_win, text="BEJELENTKEZÉS", fg="white", bg=self.colors["header"], font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        tk.Label(self.login_win, text="Felhasználónév:", fg="white", bg=self.colors["header"], font=("Segoe UI", 10)).pack()
        un_entry = ttk.Entry(self.login_win)
        un_entry.pack(pady=5)
        un_entry.focus_set()

        tk.Label(self.login_win, text="Jelszó:", fg="white", bg=self.colors["header"], font=("Segoe UI", 10)).pack()
        pw_entry = ttk.Entry(self.login_win, show="*")
        pw_entry.pack(pady=5)

        self.remember_var = tk.BooleanVar(value=False)
        cb_stay = tk.Checkbutton(self.login_win, text="Maradjak bejelentkezve", variable=self.remember_var,
                                 fg="white", bg=self.colors["header"], selectcolor=self.colors["header"],
                                 activebackground=self.colors["header"], activeforeground="white",
                                 font=("Segoe UI", 9))
        cb_stay.pack(pady=10)

        def attempt_login():
            un, pw = un_entry.get(), pw_entry.get()
            pwd_hash = hashlib.sha256(pw.encode()).hexdigest()
            
            conn = sqlite3.connect('berszamitas.db')
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, acc FROM users WHERE username=? AND password_hash=?", (un, pwd_hash))
            user = cursor.fetchone()
            conn.close()
        
            if user:
                fullname, acc = user[0], user[1]
                now_ts = time.time()
                self.session_start_time = now_ts
                
                if self.remember_var.get():
                    self.save_session(un, fullname, acc, now_ts, self.aktualis_ceg_id)

                self.current_user_fullname = fullname 
                self.current_user_acc = acc 
                self.login_win.destroy()
                self.user_label_var.set(f"Bejelentkezve: {un} ({fullname}) | Jogosultság: {acc}")
                self.update_ui_by_access(un, fullname, acc)
                messagebox.showinfo("Üdvözlet", f"Üdvözöljük, {fullname}!")
            else:
                messagebox.showerror("Hiba", "Érvénytelen felhasználónév vagy jelszó!")
        
        ttk.Button(self.login_win, text="Belépés", command=attempt_login).pack(pady=10)
        self.login_win.bind('<Return>', lambda e: attempt_login())

        copyright_text = f"Security Bérkalkulátor  | © 2026 Károlyi András\nVerzió: {self.version}"
        tk.Label(self.login_win, text=copyright_text, fg="#eeffee", bg=self.colors["header"], font=("Segoe UI", 8)).pack(side="bottom", pady=5)

    def logout(self):
        if messagebox.askyesno("Kijelentkezés", "Biztosan ki szeretne jelentkezni?"):
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            self.session_start_time = None
            self.current_user_acc = "user"
            self.current_user_fullname = "Ismeretlen"
            self.login_info_label.config(text="Kérem jelentkezzen be")
            self.user_label_var.set("Nincs bejelentkezett felhasználó")
            self.session_timer_var.set("")
            self.btn_logout.pack_forget()
            self.header.configure(bg=self.colors["header"])
            for widget in self.header.winfo_children():
                if isinstance(widget, (tk.Label, tk.Frame)):
                    widget.configure(bg=self.colors["header"])
            self.show_login_window()

    def show_superuser_creation(self):
        self.super_win = tk.Toplevel(self.root)
        self.super_win.title("Első indítás - Superuser létrehozása")
        self.super_win.geometry("400x450")
        self.super_win.configure(bg=self.colors["header"])
        self.super_win.transient(self.root)
        self.super_win.grab_set()
        self.super_win.protocol("WM_DELETE_WINDOW", self.exit_program)
        tk.Label(self.super_win, text="SUPERUSER LÉTREHOZÁSA", fg="white", bg=self.colors["header"], font=("Segoe UI", 14, "bold")).pack(pady=20)
        tk.Label(self.super_win, text="Felhasználónév:", fg="white", bg=self.colors["header"]).pack()
        un_entry = ttk.Entry(self.super_win); un_entry.pack(pady=5)
        tk.Label(self.super_win, text="Teljes név:", fg="white", bg=self.colors["header"]).pack()
        fn_entry = ttk.Entry(self.super_win); fn_entry.pack(pady=5)
        tk.Label(self.super_win, text="Jelszó:", fg="white", bg=self.colors["header"]).pack()
        p1_entry = ttk.Entry(self.super_win, show="*"); p1_entry.pack(pady=5)
        tk.Label(self.super_win, text="Jelszó újra:", fg="white", bg=self.colors["header"]).pack()
        p2_entry = ttk.Entry(self.super_win, show="*"); p2_entry.pack(pady=5)
        def save_superuser():
            un, fn, p1, p2 = un_entry.get(), fn_entry.get(), p1_entry.get(), p2_entry.get()
            if not all([un, fn, p1, p2]) or p1 != p2:
                messagebox.showerror("Hiba", "Hiba az adatokban!"); return
            pwd_hash = hashlib.sha256(p1.encode()).hexdigest()
            conn = sqlite3.connect('berszamitas.db'); cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, fullname, password_hash, acc) VALUES (?,?,?,?)", (un, fn, pwd_hash, "su"))
                conn.commit(); self.super_win.destroy(); self.show_login_window()
            except: messagebox.showerror("Hiba", "Foglalt név!")
            finally: conn.close()
        ttk.Button(self.super_win, text="Létrehozás", command=save_superuser).pack(pady=20)

    def update_ui_by_access(self, username, fullname, acc):
        header_color = self.colors["header"]
        if acc == "su": header_color = self.colors["su_red"]
        elif acc == "ku": header_color = self.colors["ku_blue"]
        self.header.configure(bg=header_color)
        for widget in self.header.winfo_children():
            if isinstance(widget, (tk.Label, tk.Frame)):
                widget.configure(bg=header_color)
                if isinstance(widget, tk.Frame):
                    for sub in widget.winfo_children():
                        if isinstance(sub, (tk.Label, tk.Button)): sub.configure(bg=header_color)
        self.login_info_label.config(text=f"User: {username} ({fullname}) | Access: {acc}")
        self.btn_logout.pack(side="top", pady=(0, 5))

    def setup_styles(self):
        self.style = ttk.Style(); self.style.theme_use('clam')
        self.style.configure("Modern.TButton", font=("Segoe UI", 13, "bold"), background=self.colors["accent"], foreground="white", padding=18, borderwidth=0)
        self.style.map("Modern.TButton", background=[('active', '#2563EB')])
        self.style.configure("Warning.TButton", font=("Segoe UI", 13, "bold"), background=self.colors["warning"], foreground="white", padding=18, borderwidth=0)
        self.style.map("Warning.TButton", background=[('active', '#D97706')])
        self.style.configure("Info.TButton", font=("Segoe UI", 13, "bold"), background=self.colors["info"], foreground="white", padding=18, borderwidth=0)
        self.style.map("Info.TButton", background=[('active', '#059669')])
        self.style.configure("Pulse1.TButton", font=("Segoe UI", 13, "bold"), background="#10B981", foreground="white", padding=18)
        self.style.configure("Pulse2.TButton", font=("Segoe UI", 13, "bold"), background="#EF4444", foreground="white", padding=18)
        self.style.configure("Exit.TButton", font=("Segoe UI", 13, "bold"), background=self.colors["exit"], foreground="white", padding=18, borderwidth=0)
        self.style.map("Exit.TButton", background=[('active', '#DC2626')])

    def create_main_ui(self):
        self.header = tk.Frame(self.root, bg=self.colors["header"], height=120); self.header.pack(fill="x"); self.header.pack_propagate(False)
        tk.Label(self.header, text="BÉRSZÁMFEJTÉS", fg="white", bg=self.colors["header"], font=("Segoe UI", 20, "bold")).pack(side="left", padx=40)
        self.user_section = tk.Frame(self.header, bg=self.colors["header"]); self.user_section.pack(side="left", padx=10)
        self.login_info_label = tk.Label(self.user_section, text="Kérem jelentkezzen be", fg="white", bg=self.colors["header"], font=("Segoe UI", 10, "bold")); self.login_info_label.pack(side="top")
        self.btn_logout = tk.Button(self.user_section, text="Kijelentkezés", bg=self.colors["header"], fg="#CBD5E1", font=("Segoe UI", 8, "underline"), command=self.logout, relief="flat", bd=0, cursor="hand2")
        self.time_label = tk.Label(self.header, text="", fg="white", bg=self.colors["header"], font=("Segoe UI", 12)); self.time_label.pack(side="right", padx=40)
        self.ceg_frame = tk.Frame(self.header, bg=self.colors["header"]); self.ceg_frame.place(relx=0.5, rely=0.35, anchor="center")
        self.company_name_label = tk.Label(self.ceg_frame, text="Nincs kiválasztott munkáltató", fg=self.colors["accent"], bg=self.colors["header"], font=("Segoe UI", 16, "bold")); self.company_name_label.pack(side="left")
        self.btn_clear_ceg = tk.Button(self.ceg_frame, text="X", bg=self.colors["exit"], fg="white", font=("Arial", 8, "bold"), command=self.clear_ceg, relief="flat", bd=0, padx=5)
        self.dolgozo_frame = tk.Frame(self.header, bg=self.colors["header"]); self.dolgozo_frame.place(relx=0.5, rely=0.65, anchor="center")
        self.selected_worker_label = tk.Label(self.dolgozo_frame, text="Nincs kiválasztott dolgozó", fg="#94A3B8", bg=self.colors["header"], font=("Segoe UI", 14, "italic")); self.selected_worker_label.pack(side="left")
        self.btn_clear_worker = tk.Button(self.dolgozo_frame, text="X", bg=self.colors["exit"], fg="white", font=("Arial", 8, "bold"), command=self.clear_worker, relief="flat", bd=0, padx=5)
        self.instruction_label = tk.Label(self.root, text="A munka megkezdéséhez válasszon ki egy munkáltatót!", fg=self.colors["exit"], bg=self.colors["bg"], font=("Segoe UI", 12, "bold")); self.instruction_label.pack(pady=(20, 0))
        self.container = tk.Frame(self.root, bg=self.colors["bg"], padx=20, pady=20); self.container.pack(expand=True)
        self.left_buttons_dict = {}
        col1 = [("💸 Levonások és Extra", self.megnyit_extrak), ("➕ Jelenléti kezelés", self.megnyit_jelenleti_bevitel), ("🧮 Bérszámfejtés", self.megnyit_berszamitas), ("📄 Bérlapok", self.megnyit_berlapok), ("📊 Statisztika", self.megnyit_statisztika)]
        for i, (text, cmd) in enumerate(col1):
            btn = ttk.Button(self.container, text=text, style="Warning.TButton", width=35, command=cmd); btn.grid(row=i, column=0, padx=15, pady=10); self.left_buttons_dict[text] = btn
        col2 = [("👤 Dolgozók", self.megnyit_adatlapok), ("🏢 Munkáltató", self.megnyit_ceg_valaszto), ("⚙️ Beállítások", self.megnyit_beallitasok), ("💰 Bérbeállítások", self.megnyit_berbeallitasok), ("✉️ Üzenetek", self.megnyit_kapcsolat)]
        for i, (text, cmd) in enumerate(col2):
            style = "Warning.TButton" if text in ["👤 Dolgozók", "💰 Bérbeállítások"] else "Modern.TButton"
            if text == "✉️ Üzenetek": style = "Info.TButton"
            btn = ttk.Button(self.container, text=text, style=style, width=35, command=cmd); btn.grid(row=i, column=1, padx=15, pady=10)
            if text == "👤 Dolgozók": self.worker_select_btn = btn
            if text == "💰 Bérbeállítások": self.ber_beall_btn = btn
            if text == "✉️ Üzenetek": self.messages_btn = btn
        self.exit_btn = ttk.Button(self.container, text="❌ Kilépés a programból", style="Exit.TButton", command=self.exit_program); self.exit_btn.grid(row=5, column=0, columnspan=2, padx=15, pady=30, sticky="ew")
        
        self.info_frame = tk.Frame(self.root, bg=self.colors["bg"]); self.info_frame.pack(side="bottom", fill="x", pady=10)
        self.user_label_var = tk.StringVar(value="Nincs bejelentkezett felhasználó")
        tk.Label(self.info_frame, textvariable=self.user_label_var, fg=self.colors["header"], bg=self.colors["bg"], font=("Segoe UI", 9, "bold")).pack()
        
        self.session_timer_var = tk.StringVar(value="")
        tk.Label(self.info_frame, textvariable=self.session_timer_var, fg="#475569", bg=self.colors["bg"], font=("Segoe UI", 8, "bold")).pack()

        self.status_text_var = tk.StringVar(value=self.db_status); self.db_label = tk.Label(self.info_frame, textvariable=self.status_text_var, fg="#64748B", bg=self.colors["bg"], font=("Segoe UI", 8, "italic")); self.db_label.pack()
        tk.Label(self.info_frame, text=f"Verzió: {self.version} | Security Bérkalkulátor 2026", fg="#94A3B8", bg=self.colors["bg"], font=("Segoe UI", 8)).pack()

    def pulse_button(self):
        unread_count = 0
        try:
            conn = sqlite3.connect('berszamitas.db'); cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read_at IS NULL", (self.current_user_fullname,))
            unread_count = cursor.fetchone()[0]; conn.close()
        except: pass
        if unread_count > 0:
            self.pulse_state = not self.pulse_state
            self.messages_btn.configure(style="Pulse1.TButton" if self.pulse_state else "Pulse2.TButton")
        else: self.messages_btn.configure(style="Info.TButton")
        self.root.after(400, self.pulse_button)

    def clear_ceg(self):
        self.company_name_label.config(text="Nincs kiválasztott munkáltató"); self.btn_clear_ceg.pack_forget()
        self.aktualis_ceg_id = None; self.frissit_fejlecet({'nev': 'Nincs kiválasztott'})
        # Frissítjük a session fájlt is
        self.update_session_ceg(None)

    def clear_worker(self): self.frissit_fejlecet({'nev': 'Nincs kiválasztott'})

    def update_session_ceg(self, ceg_id):
        """Kiválasztott cég ID-jának frissítése a session fájlban, ha be van állítva auto-login."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                data["last_ceg_id"] = ceg_id
                with open(self.session_file, "w") as f:
                    json.dump(data, f)
            except: pass

    def frissit_db_statisztika(self):
        try:
            conn = sqlite3.connect('berszamitas.db'); cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cegek"); c_szam = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM munkavallalok"); d_szam = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM berszamitas"); b_szam = cursor.fetchone()[0]
            conn.close()
            self.status_text_var.set(f"Adatbázis | {c_szam} cég | {d_szam} dolgozó | {b_szam} bérszámfejtés"); self.db_label.config(fg="#10B981")
        except: self.status_text_var.set("Hiba a betöltéskor"); self.db_label.config(fg="#EF4444")

    def megnyit_ceg_valaszto(self):
        try: from ceg_modul import CegModul; CegModul(self.root, self.frissit_fejlecet)
        except Exception as e: messagebox.showerror("Hiba", f"Sikertelen modul: {e}")

    def megnyit_berbeallitasok(self):
        if not self.aktualis_ceg_id: messagebox.showwarning("Figyelem", "Válasszon munkáltatót!"); return
        try:
            from ber_modul import BerbeallitasokModul; ceg_neve = self.company_name_label.cget("text")
            BerbeallitasokModul(self.root, self.aktualis_ceg_id, ceg_neve, current_user=self.current_user_fullname)
        except Exception as e: messagebox.showerror("Hiba", f"Sikertelen modul: {e}")

    def megnyit_statisztika(self):
        if not self.aktualis_dolgozo: return
        try: from statisztika_modul import StatisztikaModul; StatisztikaModul(self.root, self.aktualis_dolgozo)
        except: pass

    def megnyit_berlapok(self):
        if not self.aktualis_dolgozo: return
        try: from berlapok import BerlapModul; BerlapModul(self.root, self.aktualis_dolgozo)
        except: pass

    def megnyit_kapcsolat(self):
        try: from kapcsolat_modul import KapcsolatModul; KapcsolatModul(self.root, current_user_name=self.current_user_fullname, current_user_acc=self.current_user_acc)
        except: pass
        
    def megnyit_beallitasok(self):
        try: from beallitasok_modul import BeallitasokModul; BeallitasokModul(self.root, current_user_acc=self.current_user_acc)
        except: messagebox.showerror("Hiba", "Sikertelen modul!")

    def megnyit_extrak(self):
        if not self.aktualis_dolgozo: messagebox.showwarning("Figyelem", "Válasszon dolgozót!"); return
        try: from levonasok_extra import LevonasokExtraModul; LevonasokExtraModul(self.root, self.aktualis_dolgozo, self.current_user_fullname)
        except Exception as e: messagebox.showerror("Hiba", f"Hiba: {e}")
    
    def megnyit_adatlapok(self):
        if not self.aktualis_ceg_id: messagebox.showwarning("Figyelem", "Válasszon munkáltatót!"); return
        try: from dolgozo_adatlapok import DolgozoAdatlapok; DolgozoAdatlapok(self.root, munkaltato_id=self.aktualis_ceg_id, user_nev=self.current_user_fullname, callback=self.frissit_fejlecet); self.frissit_db_statisztika()
        except Exception as e: messagebox.showerror("Hiba", f"Hiba: {e}")

    def megnyit_jelenleti_bevitel(self):
        if not self.aktualis_dolgozo: return
        try: from jelenleti_bevitel import JelenletiModul; JelenletiModul(self.root, self.aktualis_dolgozo)
        except: pass

    def megnyit_berszamitas(self):
        if not self.aktualis_dolgozo: return
        try: from berszamitas_modul import BerszamitasModul; BerszamitasModul(self.root, self.aktualis_dolgozo); self.frissit_db_statisztika()
        except: pass
    
    def frissit_fejlecet(self, adatok):
        is_worker_selected = adatok and adatok.get('nev') != 'Nincs kiválasztott'
        if adatok:
            self.aktualis_dolgozo = adatok if is_worker_selected else None
            bejovo_c_id = adatok.get('ID_ceg') or adatok.get('id_ceg')
            if bejovo_c_id: 
                self.aktualis_ceg_id = str(bejovo_c_id)
                self.update_session_ceg(self.aktualis_ceg_id)

        is_ceg_selected = self.aktualis_ceg_id is not None
        if not is_ceg_selected: self.instruction_label.config(text="A munka megkezdéséhez válasszon ki egy munkáltatót!", fg=self.colors["exit"])
        elif not is_worker_selected: self.instruction_label.config(text="Munkaidőrögzítéshez válasszon ki egy dolgozót!", fg=self.colors["warning"])
        else: self.instruction_label.config(text="")
        
        if is_ceg_selected and is_worker_selected:
            for btn in self.left_buttons_dict.values(): btn.configure(style="Modern.TButton")
            self.worker_select_btn.configure(style="Modern.TButton"); self.ber_beall_btn.configure(style="Modern.TButton")
        else:
            style = "Modern.TButton" if is_ceg_selected else "Warning.TButton"
            for btn in self.left_buttons_dict.values(): btn.configure(style="Warning.TButton")
            self.worker_select_btn.configure(style=style); self.ber_beall_btn.configure(style=style)
        
        try:
            if is_ceg_selected:
                from ceg_modul import CegModul; cegek = CegModul.betolt_cegek()
                ceg_neve = next((c.get('ceg_neve', "") for c in cegek if str(c.get('ID_ceg') or c.get('id_ceg')) == self.aktualis_ceg_id), "")
                if ceg_neve: 
                    self.company_name_label.config(text=ceg_neve.upper())
                    self.btn_clear_ceg.pack(side="left", padx=10)
        except: pass
        
        if not is_worker_selected:
            self.selected_worker_label.config(text="Nincs kiválasztott dolgozó", fg="#94A3B8", font=("Segoe UI", 14, "italic"))
            self.btn_clear_worker.pack_forget()
        else:
            self.selected_worker_label.config(text=f"{adatok['nev']} ({adatok['szul_datum']})", font=("Segoe UI", 13, "bold"), fg="white")
            self.btn_clear_worker.pack(side="left", padx=10)
        self.root.update_idletasks()

    def update_clock(self):
        now_dt = datetime.now()
        self.time_label.config(text=now_dt.strftime("%Y.%m.%d | %H:%M:%S"))
        
        if self.session_start_time:
            elapsed = time.time() - self.session_start_time
            timeout = self.get_session_timeout()
            remaining = max(0, timeout - elapsed)
            
            if remaining > 0:
                h = int(remaining // 3600)
                m = int((remaining % 3600) // 60)
                s = int(remaining % 60)
                duration_h = timeout // 3600
                self.session_timer_var.set(f"Session: {duration_h}ó | Hátralévő: {h:02d}:{m:02d}:{s:02d}")
            else:
                self.session_timer_var.set("SESSION LEJÁRT!")
        else:
            self.session_timer_var.set("")

        self.root.after(1000, self.update_clock)

    def exit_program(self):
        if messagebox.askyesno("Megerősítés", "Bezárja a programot?"):
            self.root.destroy(); sys.exit()

if __name__ == "__main__":
    root = tk.Tk(); app = ModernBerszamfejtoApp(root); root.mainloop()