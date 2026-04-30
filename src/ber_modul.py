import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class BerbeallitasokModul:
    def __init__(self, parent, aktualis_ceg_id, ceg_neve, current_user="Ismeretlen"):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Bérbeállítások - {ceg_neve}")
        self.window.geometry("1100x820")
        self.window.configure(bg="#F8FAFC")
        
        self.window.attributes("-topmost", True)
        
        self.ceg_id = aktualis_ceg_id
        self.ceg_neve = ceg_neve
        self.current_user = current_user
        
        self.init_db()
        self.create_ui()
        self.load_all_data()

    def init_db(self):
        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS berezes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                munkaltato_id TEXT,
                megnevezes TEXT,
                mertek REAL,
                tipus TEXT,
                user TEXT,
                rogzitve TEXT,
                ervenyes_tol TEXT,
                ervenyes_ig TEXT
            )
        """)

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings_ado'")
        if cursor.fetchone():
            cursor.execute("CREATE TABLE IF NOT EXISTS settings_temp (id INTEGER PRIMARY KEY AUTOINCREMENT, megnevezes TEXT, mertek REAL, ervenyes_tol TEXT, ervenyes_ig TEXT, tipus TEXT, user TEXT, rogzitve TEXT, munkaltato_id TEXT)")
            try:
                cursor.execute("INSERT INTO settings_temp (megnevezes, mertek, ervenyes_tol, ervenyes_ig, tipus, user, rogzitve, munkaltato_id) SELECT megnevezes, mertek, ervenyes_tol, ervenyes_ig, tipus, user, rogzitve, munkaltato_id FROM settings_ado")
                cursor.execute("DROP TABLE settings_ado")
                cursor.execute("ALTER TABLE settings_temp RENAME TO settings_ado")
            except:
                pass

        conn.commit()
        conn.close()

    def get_settings_data(self, tipus):
        db_map = {"adokedvezmeny": "Adókedvezmény", "cafeteria": "Cafeteria"}
        db_type = db_map.get(tipus, "")
        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT megnevezes, mertek, ervenyes_tol, ervenyes_ig FROM settings_ado WHERE tipus=?", (db_type,))
        data = cursor.fetchall()
        conn.close()
        return data

    def create_ui(self):
        header = tk.Frame(self.window, bg="#1E293B", height=60)
        header.pack(fill="x")
        tk.Label(header, text=f"BÉRBEÁLLÍTÁSOK: {self.ceg_neve.upper()}", fg="#3B82F6", bg="#1E293B", font=("Segoe UI", 14, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs = {}
        for t_id, t_name in [("alap", "Számítási alapok"), ("adokedvezmeny", "Adókedvezmény"), ("cafeteria", "Cafeteria")]:
            frame = tk.Frame(self.notebook, bg="#F8FAFC")
            self.notebook.add(frame, text=t_name)
            self.tabs[t_id] = self.setup_inline_tab(frame, t_id)

        footer = tk.Frame(self.window, bg="#F8FAFC")
        footer.pack(fill="x", side="bottom", pady=10)
        tk.Button(footer, text="❌ Bezárás", command=self.window.destroy, bg="#64748B", fg="white", font=("Segoe UI", 10, "bold"), padx=30, pady=8).pack()

    def setup_inline_tab(self, parent_frame, tipus):
        edit_frame = tk.LabelFrame(parent_frame, text="Adatkezelés", bg="#F8FAFC", padx=10, pady=10)
        edit_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(edit_frame, text="Megnevezés:", bg="#F8FAFC").grid(row=0, column=0, padx=5)
        if tipus in ["adokedvezmeny", "cafeteria"]:
            ent_nev = ttk.Combobox(edit_frame, width=32)
            ent_nev['values'] = list(set([r[0] for r in self.get_settings_data(tipus)]))
            ent_nev.bind("<<ComboboxSelected>>", lambda e: self.on_dropdown_select(tipus))
        else:
            ent_nev = ttk.Entry(edit_frame, width=35)
        ent_nev.grid(row=0, column=1, padx=5)

        tk.Label(edit_frame, text="Mérték:", bg="#F8FAFC").grid(row=0, column=2, padx=5)
        ent_mertek = ttk.Entry(edit_frame, width=15)
        ent_mertek.grid(row=0, column=3, padx=5)

        tk.Label(edit_frame, text="Érvényes tól:", bg="#F8FAFC").grid(row=1, column=0, padx=5, pady=5)
        ent_h_be = ttk.Entry(edit_frame, width=15)
        ent_h_be.grid(row=1, column=1, padx=5, sticky="w")

        tk.Label(edit_frame, text="Érvényes ig:", bg="#F8FAFC").grid(row=1, column=2, padx=5)
        ent_h_ki = ttk.Entry(edit_frame, width=15)
        ent_h_ki.grid(row=1, column=3, padx=5, sticky="w")

        btn_frame = tk.Frame(edit_frame, bg="#F8FAFC")
        btn_frame.grid(row=0, column=4, rowspan=2, padx=20)

        tk.Button(btn_frame, text="💾 Mentés / Új", command=lambda: self.save_inline(tipus), bg="#10B981", fg="white", width=15).pack(pady=2)
        tk.Button(btn_frame, text="🗑️ Törlés", command=lambda: self.delete_record(tipus), bg="#EF4444", fg="white", width=15).pack(pady=2)

        tree = ttk.Treeview(parent_frame, columns=("id", "megnevezes", "mertek", "h_be", "h_ki", "user"), show="headings", height=12)
        
        # OSZLOPSZÉLESSÉGEK BEÁLLÍTÁSA A KÉP ALAPJÁN
        col_configs = [
            ("id", "ID", 40),
            ("megnevezes", "Megnevezés", 450),
            ("mertek", "Mérték", 100),
            ("h_be", "Tól", 80),
            ("h_ki", "Ig", 80),
            ("user", "Felhasználó", 120)
        ]

        for col, head, width in col_configs:
            tree.heading(col, text=head)
            tree.column(col, anchor="center", width=width)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        tab_info = {"tree": tree, "ent_nev": ent_nev, "ent_mertek": ent_mertek, "ent_h_be": ent_h_be, "ent_h_ki": ent_h_ki, "selected_id": None}
        tree.bind("<<TreeviewSelect>>", lambda e: self.on_row_select(tipus))
        return tab_info

    def on_dropdown_select(self, tipus):
        tab = self.tabs[tipus]
        val = tab["ent_nev"].get()
        for r in self.get_settings_data(tipus):
            if r[0] == val:
                tab["ent_mertek"].delete(0, tk.END); tab["ent_mertek"].insert(0, r[1])
                tab["ent_h_be"].delete(0, tk.END); tab["ent_h_be"].insert(0, r[2] if r[2] else datetime.now().strftime("%Y.%m"))
                tab["ent_h_ki"].delete(0, tk.END); tab["ent_h_ki"].insert(0, r[3] if r[3] else "9999.12")
                break

    def on_row_select(self, tipus):
        tab = self.tabs[tipus]
        sel = tab["tree"].selection()
        if sel:
            d = tab["tree"].item(sel[0])['values']
            tab["selected_id"] = d[0]
            if isinstance(tab["ent_nev"], ttk.Combobox): tab["ent_nev"].set(d[1])
            else: tab["ent_nev"].delete(0, tk.END); tab["ent_nev"].insert(0, d[1])
            tab["ent_mertek"].delete(0, tk.END); tab["ent_mertek"].insert(0, d[2])
            tab["ent_h_be"].delete(0, tk.END); tab["ent_h_be"].insert(0, d[3])
            tab["ent_h_ki"].delete(0, tk.END); tab["ent_h_ki"].insert(0, d[4])

    def save_inline(self, tipus):
        tab = self.tabs[tipus]
        nev, hbe, hki = tab["ent_nev"].get().strip(), tab["ent_h_be"].get().strip(), tab["ent_h_ki"].get().strip()
        if not nev: return
        try: mertek = float(str(tab["ent_mertek"].get()).replace(',', '.'))
        except: return

        most = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target = "settings_ado" if tipus in ["adokedvezmeny", "cafeteria"] else "berezes"
        db_tipus = {"adokedvezmeny": "Adókedvezmény", "cafeteria": "Cafeteria"}.get(tipus, tipus)

        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        
        if tab["selected_id"] is None:
            cursor.execute(f"INSERT INTO {target} (megnevezes, mertek, ervenyes_tol, ervenyes_ig, tipus, user, rogzitve, munkaltato_id) VALUES (?,?,?,?,?,?,?,?)",
                           (nev, mertek, hbe, hki, db_tipus, self.current_user, most, self.ceg_id))
        else:
            cursor.execute(f"UPDATE {target} SET megnevezes=?, mertek=?, ervenyes_tol=?, ervenyes_ig=?, user=?, rogzitve=? WHERE id=?",
                           (nev, mertek, hbe, hki, self.current_user, most, tab["selected_id"]))
        
        conn.commit(); conn.close()
        self.clear_fields(tipus); self.load_data(tipus)

    def clear_fields(self, tipus):
        tab = self.tabs[tipus]
        tab["selected_id"] = None
        if isinstance(tab["ent_nev"], ttk.Combobox): tab["ent_nev"].set('')
        else: tab["ent_nev"].delete(0, tk.END)
        for e in ["ent_mertek", "ent_h_be", "ent_h_ki"]: tab[e].delete(0, tk.END)

    def load_all_data(self):
        for t in self.tabs: self.load_data(t)

    def load_data(self, tipus):
        tab = self.tabs[tipus]
        tab["tree"].delete(*tab["tree"].get_children())
        target = "settings_ado" if tipus in ["adokedvezmeny", "cafeteria"] else "berezes"
        db_tipus = {"adokedvezmeny": "Adókedvezmény", "cafeteria": "Cafeteria"}.get(tipus, tipus)
        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, megnevezes, mertek, ervenyes_tol, ervenyes_ig, user FROM {target} WHERE munkaltato_id=? AND tipus=?", (self.ceg_id, db_tipus))
        for r in cursor.fetchall(): tab["tree"].insert("", "end", values=r)
        conn.close()

    def delete_record(self, tipus):
        tab = self.tabs[tipus]
        sel = tab["tree"].selection()
        if not sel: return
        target = "settings_ado" if tipus in ["adokedvezmeny", "cafeteria"] else "berezes"
        conn = sqlite3.connect('berszamitas.db')
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {target} WHERE id=?", (tab["tree"].item(sel[0])['values'][0],))
        conn.commit(); conn.close()
        self.clear_fields(tipus); self.load_data(tipus)