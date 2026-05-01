import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import shutil
import os
import traceback
import hashlib
from datetime import datetime

# --- GLOBÁLIS SEGÉDFÜGGVÉNY ---
def hiba_logolas(modul_neve, hiba_obj):
    conn = None
    try:
        conn = sqlite3.connect("berszamitas.db", timeout=20)
        cursor = conn.cursor()
        most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        teljes_traceback = traceback.format_exc()
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS hiba_naplo (
            id INTEGER PRIMARY KEY AUTOINCREMENT, datum TEXT, modul TEXT, hiba_uzenet TEXT, traceback TEXT)""")
        
        cursor.execute("""INSERT INTO hiba_naplo (datum, modul, hiba_uzenet, traceback) 
                          VALUES (?, ?, ?, ?)""", 
                       (most, modul_neve, str(hiba_obj), teljes_traceback))
        conn.commit()
    except:
        print("Kritikus hiba: A hibanaplózás nem sikerült!")
    finally:
        if conn: conn.close()

class BeallitasokModul(tk.Toplevel):
    def __init__(self, parent, current_user_acc="user"):
        super().__init__(parent)
        self.title("Rendszerbeállítások")
        self.geometry("1100x900")
        self.configure(bg="#F1F5F9")
        
        self.current_user_acc = current_user_acc
        self.db_offset = 0 
        self.db_order_by = "1"
        self.db_order_dir = "ASC"
        self.selected_ado_id = None 
        
        self.valasztott_munkaltato_id = getattr(parent, 'valasztott_munkaltato_id', None)
        
        self.setup_db_tables()
        
        header = tk.Frame(self, bg="#0F172A", height=60)
        header.pack(fill="x")
        tk.Label(header, text="GLOBÁLIS RENDSZERBEÁLLÍTÁSOK", fg="white", bg="#0F172A", 
                 font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_ceg = tk.Frame(self.notebook, bg="white", padx=30, pady=20)
        self.tab_szamitas = tk.Frame(self.notebook, bg="white", padx=30, pady=20)
        self.tab_ado = tk.Frame(self.notebook, bg="white", padx=30, pady=20)
        self.tab_rendszer = tk.Frame(self.notebook, bg="white", padx=30, pady=20)

        self.notebook.add(self.tab_ceg, text="  Cégadatok  ")
        self.notebook.add(self.tab_szamitas, text="  Számítási alapok  ")
        self.notebook.add(self.tab_ado, text="  Adókedvezmény és Cafeteria  ")
        self.notebook.add(self.tab_rendszer, text="  Biztonsági mentés  ")

        self.entries = {}
        self._setup_ceg_tab()
        self._setup_szamitas_tab()
        self._setup_ado_tab()
        self._setup_rendszer_tab()

        if self.current_user_acc == "su":
            self.tab_naplok = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
            self.tab_konzol = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
            self.tab_db_kezelo = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
            self.tab_users = tk.Frame(self.notebook, bg="white", padx=20, pady=20)

            self.notebook.add(self.tab_naplok, text="  Naplózás  ")
            self.notebook.add(self.tab_konzol, text="  SQL Konzol  ")
            self.notebook.add(self.tab_db_kezelo, text="  Adatbázis kezelés  ")
            self.notebook.add(self.tab_users, text="  Felhasználó kezelés  ")

            self._setup_naplok_tab()
            self._setup_konzol_tab()
            self._setup_db_kezelo_tab()
            self._setup_users_tab()
        
        self.adatok_betoltese()

        footer = tk.Frame(self, bg="#F1F5F9", pady=20)
        footer.pack(fill="x", side="bottom")
        
        tk.Button(footer, text="✖ BEZÁRÁS", bg="#64748B", fg="white", font=("Segoe UI", 10, "bold"), 
                  padx=25, pady=10, relief="flat", command=self.destroy).pack(side="left", padx=40)

        tk.Button(footer, text="💾 MENTÉS", bg="#059669", fg="white", font=("Segoe UI", 10, "bold"), 
                  padx=35, pady=10, relief="flat", command=self.mentes).pack(side="right", padx=40)

    def _setup_users_tab(self):
        form_f = tk.LabelFrame(self.tab_users, text="Új felhasználó / Szerkesztés", bg="white", padx=10, pady=10)
        form_f.pack(fill="x", pady=(0, 10))
        grid_params = {'padx': 5, 'pady': 2, 'sticky': 'w'}
        tk.Label(form_f, text="Felhasználónév:", bg="white").grid(row=0, column=0, **grid_params)
        self.user_name_ent = ttk.Entry(form_f, width=20)
        self.user_name_ent.grid(row=0, column=1, **grid_params)
        tk.Label(form_f, text="Teljes név:", bg="white").grid(row=0, column=2, **grid_params)
        self.user_full_ent = ttk.Entry(form_f, width=30)
        self.user_full_ent.grid(row=0, column=3, **grid_params)
        tk.Label(form_f, text="Jogosultság:", bg="white").grid(row=0, column=4, **grid_params)
        self.user_acc_cb = ttk.Combobox(form_f, values=["keyuser", "user"], state="readonly", width=10)
        self.user_acc_cb.grid(row=0, column=5, **grid_params)
        self.user_acc_cb.set("user")
        tk.Label(form_f, text="Jelszó:", bg="white").grid(row=1, column=0, **grid_params)
        self.user_pw1_ent = ttk.Entry(form_f, width=20, show="*")
        self.user_pw1_ent.grid(row=1, column=1, **grid_params)
        tk.Label(form_f, text="Jelszó újra:", bg="white").grid(row=1, column=2, **grid_params)
        self.user_pw2_ent = ttk.Entry(form_f, width=20, show="*")
        self.user_pw2_ent.grid(row=1, column=3, **grid_params)
        self.selected_user_id = None
        tree_f = tk.Frame(self.tab_users, bg="white")
        tree_f.pack(fill="both", expand=True)
        self.user_tree = ttk.Treeview(tree_f, columns=("id", "un", "fn", "acc"), show="headings", height=15)
        self.user_tree.heading("id", text="ID"); self.user_tree.heading("un", text="Felhasználónév")
        self.user_tree.heading("fn", text="Teljes név"); self.user_tree.heading("acc", text="Jogosultság")
        self.user_tree.column("id", width=50); self.user_tree.pack(side="left", fill="both", expand=True)
        sc = ttk.Scrollbar(tree_f, orient="vertical", command=self.user_tree.yview)
        sc.pack(side="right", fill="y"); self.user_tree.configure(yscrollcommand=sc.set)
        btn_f = tk.Frame(self.tab_users, bg="white", pady=10)
        btn_f.pack(fill="x")
        tk.Button(btn_f, text="➕ HOZZÁADÁS", bg="#10B981", fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self.user_add).pack(side="left", padx=5)
        tk.Button(btn_f, text="📝 SZERKESZTÉS KIVÁLASZTÁSA", bg="#3B82F6", fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self.user_select_for_edit).pack(side="left", padx=5)
        tk.Button(btn_f, text="💾 MÓDOSÍTÁS MENTÉSE", bg="#F59E0B", fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self.user_update).pack(side="left", padx=5)
        tk.Button(btn_f, text="🗑 TÖRLÉS", bg="#EF4444", fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self.user_delete).pack(side="right", padx=5)
        self.user_listazas()

    def user_listazas(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        try:
            conn = sqlite3.connect("berszamitas.db")
            for r in conn.execute("SELECT id, username, fullname, acc FROM users").fetchall():
                self.user_tree.insert("", "end", values=r)
            conn.close()
        except: pass

    def user_add(self):
        un, fn, acc = self.user_name_ent.get(), self.user_full_ent.get(), self.user_acc_cb.get()
        p1, p2 = self.user_pw1_ent.get(), self.user_pw2_ent.get()
        if not all([un, fn, acc, p1, p2]): messagebox.showerror("Hiba", "Minden mező kitöltése kötelező!"); return
        if p1 != p2: messagebox.showerror("Hiba", "A jelszavak nem egyeznek!"); return
        pwd_hash = hashlib.sha256(p1.encode()).hexdigest()
        try:
            conn = sqlite3.connect("berszamitas.db")
            conn.execute("INSERT INTO users (username, fullname, password_hash, acc) VALUES (?,?,?,?)", (un, fn, pwd_hash, acc))
            conn.commit(); conn.close(); messagebox.showinfo("Siker", "Felhasználó hozzáadva!"); self.user_listazas()
        except sqlite3.IntegrityError: messagebox.showerror("Hiba", "Ez a felhasználónév már létezik!")
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def user_select_for_edit(self):
        sel = self.user_tree.selection()
        if not sel: return
        item = self.user_tree.item(sel[0])['values']
        self.selected_user_id = item[0]
        self.user_name_ent.delete(0, tk.END); self.user_name_ent.insert(0, item[1])
        self.user_full_ent.delete(0, tk.END); self.user_full_ent.insert(0, item[2])
        self.user_acc_cb.set(item[3])

    def user_update(self):
        if not self.selected_user_id: return
        un, fn, acc = self.user_name_ent.get(), self.user_full_ent.get(), self.user_acc_cb.get()
        p1, p2 = self.user_pw1_ent.get(), self.user_pw2_ent.get()
        try:
            conn = sqlite3.connect("berszamitas.db")
            if p1:
                if p1 != p2: messagebox.showerror("Hiba", "A jelszavak nem egyeznek!"); return
                pwd_hash = hashlib.sha256(p1.encode()).hexdigest()
                conn.execute("UPDATE users SET username=?, fullname=?, acc=?, password_hash=? WHERE id=?", (un, fn, acc, pwd_hash, self.selected_user_id))
            else:
                conn.execute("UPDATE users SET username=?, fullname=?, acc=? WHERE id=?", (un, fn, acc, self.selected_user_id))
            conn.commit(); conn.close(); messagebox.showinfo("Siker", "Felhasználó frissítve!"); self.selected_user_id = None; self.user_listazas()
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def user_delete(self):
        sel = self.user_tree.selection()
        if not sel: return
        item = self.user_tree.item(sel[0])['values']
        if messagebox.askyesno("Megerősítés", f"Biztosan törli a '{item[1]}' felhasználót?"):
            try:
                conn = sqlite3.connect("berszamitas.db")
                conn.execute("DELETE FROM users WHERE id=?", (item[0],))
                conn.commit(); conn.close(); self.user_listazas()
            except Exception as e: messagebox.showerror("Hiba", str(e))

    def _setup_db_kezelo_tab(self):
        ctrl_f = tk.Frame(self.tab_db_kezelo, bg="white"); ctrl_f.pack(fill="x", pady=5)
        tk.Label(ctrl_f, text="Tábla:", bg="white").pack(side="left", padx=5)
        self.db_table_cb = ttk.Combobox(ctrl_f, state="readonly", width=25); self.db_table_cb.pack(side="left", padx=5)
        tk.Label(ctrl_f, text="Sorok:", bg="white").pack(side="left", padx=5)
        self.db_limit_cb = ttk.Combobox(ctrl_f, values=["20", "50", "100", "500"], state="readonly", width=5); self.db_limit_cb.set("50"); self.db_limit_cb.pack(side="left", padx=5)
        tk.Button(ctrl_f, text="🔍 BETÖLTÉS", command=self._db_reset_and_load, bg="#3B82F6", fg="white", font=("Segoe UI", 8, "bold")).pack(side="left", padx=10)
        self.lbl_row_count = tk.Label(ctrl_f, text="Sorok száma: 0", bg="white", font=("Segoe UI", 8, "italic")); self.lbl_row_count.pack(side="left", padx=5)
        self.btn_next = tk.Button(ctrl_f, text="KÖVETKEZŐ ▶", state="disabled", command=self.db_next_page); self.btn_next.pack(side="right", padx=5)
        self.btn_prev = tk.Button(ctrl_f, text="◀ ELŐZŐ", state="disabled", command=self.db_prev_page); self.btn_prev.pack(side="right", padx=5)
        self.db_list_frame = tk.Frame(self.tab_db_kezelo, bg="white"); self.db_list_frame.pack(fill="both", expand=True, pady=10)
        self.db_canvas = tk.Canvas(self.db_list_frame, bg="white")
        self.db_v_scroll = ttk.Scrollbar(self.db_list_frame, orient="vertical", command=self.db_canvas.yview)
        self.db_h_scroll = ttk.Scrollbar(self.tab_db_kezelo, orient="horizontal", command=self.db_canvas.xview)
        self.db_scroll_frame = tk.Frame(self.db_canvas, bg="white")
        self.db_scroll_frame.bind("<Configure>", lambda e: self.db_canvas.configure(scrollregion=self.db_canvas.bbox("all")))
        self.db_canvas.create_window((0, 0), window=self.db_scroll_frame, anchor="nw")
        self.db_canvas.configure(yscrollcommand=self.db_v_scroll.set, xscrollcommand=self.db_h_scroll.set)
        self.db_v_scroll.pack(side="right", fill="y"); self.db_canvas.pack(side="left", fill="both", expand=True); self.db_h_scroll.pack(fill="x")
        self.db_footer = tk.Frame(self.tab_db_kezelo, bg="white"); self.db_footer.pack(fill="x", pady=5)
        self.select_all_var = tk.BooleanVar()
        tk.Checkbutton(self.db_footer, text="Összes kijelölése", variable=self.select_all_var, bg="white", command=self.db_toggle_all).pack(side="left", padx=10)
        self.btn_bulk_delete = tk.Button(self.db_footer, text="🗑 KIJELÖLTEK TÖRLÉSE", bg="#EF4444", fg="white", font=("Segoe UI", 9, "bold"), state="disabled", command=self.db_csoportos_torles)
        self.btn_bulk_delete.pack(side="left", padx=20)
        self.db_tablak_frissitese()

    def _db_reset_and_load(self): self.db_offset = 0; self.db_order_by = "1"; self.db_order_dir = "ASC"; self.db_tabla_betoltes()
    def db_next_page(self): self.db_offset += int(self.db_limit_cb.get()); self.db_tabla_betoltes()
    def db_prev_page(self): self.db_offset = max(0, self.db_offset - int(self.db_limit_cb.get())); self.db_tabla_betoltes()
    def db_set_sort(self, col_name):
        if self.db_order_by == col_name: self.db_order_dir = "ASC" if self.db_order_dir == "DESC" else "DESC"
        else: self.db_order_by = col_name; self.db_order_dir = "DESC"
        self.db_tabla_betoltes()
    def db_toggle_all(self):
        state = self.select_all_var.get()
        for var in self.db_check_vars.values(): var.set(state)
        self.db_check_status_update()
    def db_tablak_frissitese(self):
        try:
            conn = sqlite3.connect("berszamitas.db")
            tablak = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
            self.db_table_cb["values"] = tablak
            if tablak: self.db_table_cb.set(tablak[0])
            conn.close()
        except Exception as e: hiba_logolas("db_kezelo", e)
    def db_tabla_betoltes(self):
        for widget in self.db_scroll_frame.winfo_children(): widget.destroy()
        tabla, limit = self.db_table_cb.get(), int(self.db_limit_cb.get())
        if not tabla: return
        self.db_check_vars, self.db_row_entries = {}, {}
        try:
            conn = sqlite3.connect("berszamitas.db"); cursor = conn.cursor()
            total_rows = cursor.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            self.lbl_row_count.config(text=f"Sorok száma: {total_rows}")
            cursor.execute(f"PRAGMA table_info({tabla})"); cols = [c[1] for c in cursor.fetchall()]
            tk.Label(self.db_scroll_frame, text="Kijelöl", font=("Segoe UI", 9, "bold"), bg="#E2E8F0", borderwidth=1, relief="solid", padx=5).grid(row=0, column=0, sticky="nsew")
            for j, col in enumerate(cols, start=1):
                lbl = tk.Label(self.db_scroll_frame, text=col, font=("Segoe UI", 9, "bold"), bg="#E2E8F0", borderwidth=1, relief="solid", padx=5, cursor="hand2")
                lbl.grid(row=0, column=j, sticky="nsew"); lbl.bind("<Button-1>", lambda e, c=col: self.db_set_sort(c))
            cursor.execute(f"SELECT * FROM {tabla} ORDER BY {self.db_order_by} {self.db_order_dir} LIMIT ? OFFSET ?", (limit, self.db_offset))
            for i, row in enumerate(cursor.fetchall(), start=1):
                rid, var = row[0], tk.BooleanVar()
                tk.Checkbutton(self.db_scroll_frame, variable=var, bg="white", command=self.db_check_status_update).grid(row=i, column=0)
                self.db_check_vars[rid] = var
                entries = []
                for j, val in enumerate(row):
                    ent = ttk.Entry(self.db_scroll_frame, width=15); ent.insert(0, str(val) if val is not None else ""); ent.grid(row=i, column=j+1, padx=2, pady=2); entries.append(ent)
                self.db_row_entries[rid] = entries
                btn_f = tk.Frame(self.db_scroll_frame, bg="white"); btn_f.grid(row=i, column=len(cols)+1, padx=5)
                tk.Button(btn_f, text="💾", bg="#10B981", fg="white", command=lambda r=rid: self.db_sor_mentes(tabla, cols, r)).pack(side="left", padx=2)
                tk.Button(btn_f, text="🗑", bg="#EF4444", fg="white", command=lambda r=rid: self.db_sor_torles(tabla, cols[0], r)).pack(side="left", padx=2)
            self.btn_prev.config(state="normal" if self.db_offset > 0 else "disabled")
            self.btn_next.config(state="normal" if self.db_offset + limit < total_rows else "disabled")
            conn.close(); self.db_check_status_update()
        except Exception as e: messagebox.showerror("Hiba", str(e))
    def db_check_status_update(self): self.btn_bulk_delete.config(state="normal" if any(v.get() for v in self.db_check_vars.values()) else "disabled")
    def db_sor_mentes(self, tabla, cols, row_id):
        try:
            values = [e.get() for e in self.db_row_entries[row_id]]
            set_clause = ", ".join([f"{col}=?" for col in cols])
            conn = sqlite3.connect("berszamitas.db"); conn.execute(f"UPDATE {tabla} SET {set_clause} WHERE {cols[0]}=?", values + [row_id]); conn.commit(); conn.close(); messagebox.showinfo("Siker", "Sor frissítve!")
        except Exception as e: messagebox.showerror("Mentési hiba", str(e))
    def db_sor_torles(self, tabla, id_col, row_id):
        if messagebox.askyesno("Megerősítés", "Biztosan törli?"):
            try: conn = sqlite3.connect("berszamitas.db"); conn.execute(f"DELETE FROM {tabla} WHERE {id_col}=?", (row_id,)); conn.commit(); conn.close(); self.db_tabla_betoltes()
            except Exception as e: messagebox.showerror("Hiba", str(e))
    def db_csoportos_torles(self):
        tabla = self.db_table_cb.get(); selected_ids = [rid for rid, var in self.db_check_vars.items() if var.get()]
        if not selected_ids: return
        if messagebox.askyesno("FIGYELEM", "Biztosan törli a kijelölteket?"):
            try:
                conn = sqlite3.connect("berszamitas.db"); cursor = conn.cursor(); cursor.execute(f"PRAGMA table_info({tabla})"); id_col = cursor.fetchone()[1]
                for rid in selected_ids: conn.execute(f"DELETE FROM {tabla} WHERE {id_col}=?", (rid,))
                conn.commit(); conn.close(); self.db_tabla_betoltes()
            except Exception as e: messagebox.showerror("Hiba", str(e))

    def _setup_konzol_tab(self):
        tk.Label(self.tab_konzol, text="SQL Lekérdező Konzol", font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 10))
        input_f = tk.Frame(self.tab_konzol, bg="white"); input_f.pack(fill="x", pady=5)
        self.sql_entry = ttk.Entry(input_f, font=("Consolas", 10)); self.sql_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.sql_entry.insert(0, "SELECT * FROM global_beallitasok"); self.sql_entry.bind("<Return>", lambda e: self.sql_futtatas())
        tk.Button(input_f, text="⚡ FUTTATÁS", bg="#4F46E5", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, command=self.sql_futtatas).pack(side="right")
        tree_f = tk.Frame(self.tab_konzol); tree_f.pack(fill="both", expand=True, pady=10)
        self.sql_tree = ttk.Treeview(tree_f, show="headings"); self.sql_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(tree_f, orient="vertical", command=self.sql_tree.yview); scroll.pack(side="right", fill="y"); self.sql_tree.configure(yscrollcommand=scroll.set)

    def sql_futtatas(self):
        query = self.sql_entry.get().strip()
        if not query: return
        try:
            conn = sqlite3.connect("berszamitas.db", timeout=20); cursor = conn.cursor(); cursor.execute(query)
            if any(x in query.upper() for x in ["UPDATE", "INSERT", "DELETE", "DROP", "CREATE"]): conn.commit(); messagebox.showinfo("Siker", f"{cursor.rowcount} sor érintett.")
            else:
                rows = cursor.fetchall(); colnames = [d[0] for d in cursor.description]
                self.sql_tree.delete(*self.sql_tree.get_children()); self.sql_tree["columns"] = colnames
                for col in colnames: self.sql_tree.heading(col, text=col); self.sql_tree.column(col, width=120)
                for r in rows: self.sql_tree.insert("", "end", values=r)
            conn.close()
        except Exception as e: messagebox.showerror("SQL Hiba", str(e))

    def setup_db_tables(self):
        try:
            conn = sqlite3.connect("berszamitas.db", timeout=20); cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS global_beallitasok (id INTEGER PRIMARY KEY CHECK (id = 1), ceg_nev TEXT, szekhely TEXT, szja REAL, tb REAL, betegszab_70 REAL, tappenz_60 REAL, baleseti_100 REAL, km_dij INTEGER, muszak_potlek REAL, ev_kezdet TEXT, smtp_pass TEXT)""")
            cursor.execute("CREATE TABLE IF NOT EXISTS settings_ado (id INTEGER PRIMARY KEY AUTOINCREMENT, tipus TEXT, megnevezes TEXT, mertek INTEGER, ervenyes_tol TEXT, ervenyes_ig TEXT)")
            conn.commit(); conn.close()
        except Exception as e: hiba_logolas("beallitasok_modul.py", e)

    def create_input(self, parent, label):
        tk.Label(parent, text=label, bg="white", fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 0))
        ent = ttk.Entry(parent, width=55); ent.pack(anchor="w", pady=2); return ent

    def _setup_ceg_tab(self):
        self.entries["ceg_nev"] = self.create_input(self.tab_ceg, "Cégnév:")
        self.entries["szekhely"] = self.create_input(self.tab_ceg, "Székhely / Telephely:")
        tk.Label(self.tab_ceg, text="Pénzügyi év kezdete (hónap):", bg="white").pack(anchor="w", pady=(10,0))
        self.ev_kezdet_cb = ttk.Combobox(self.tab_ceg, values=[f"{i:02d}" for i in range(1, 13)], state="readonly", width=10); self.ev_kezdet_cb.pack(anchor="w", pady=5); self.ev_kezdet_cb.set("01")

    def _setup_szamitas_tab(self):
        params = [("szja", "SZJA mértéke (%)"), ("tb", "TB járulék (%)"), ("betegszab_70", "Betegszabadság mértéke (%)"), ("tappenz_60", "Táppénz mértéke (%)"), ("baleseti_100", "Baleseti táppénz (%)"), ("km_dij", "Munkába járás (Ft/km)"), ("muszak_potlek", "Műszakpótlék (%)")]
        for k, v in params: self.entries[k] = self.create_input(self.tab_szamitas, v)

    def _setup_ado_tab(self):
        tk.Label(self.tab_ado, text="Adókedvezmények és Cafeteria", font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w", pady=(0,15))
        input_f = tk.Frame(self.tab_ado, bg="white"); input_f.pack(fill="x", pady=5)
        tk.Label(input_f, text="Típus:", bg="white", fg="#64748B", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, sticky="w")
        tk.Label(input_f, text="Megnevezés:", bg="white", fg="#64748B", font=("Segoe UI", 9)).grid(row=0, column=1, padx=5, sticky="w")
        tk.Label(input_f, text="Mérték (Ft):", bg="white", fg="#64748B", font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, sticky="w")
        tk.Label(input_f, text="Hatálybalépés (ÉÉÉÉ.HH):", bg="white", fg="#64748B", font=("Segoe UI", 9)).grid(row=0, column=3, padx=5, sticky="w")
        tk.Label(input_f, text="Hatályvesztés (ÉÉÉÉ.HH):", bg="white", fg="#64748B", font=("Segoe UI", 9)).grid(row=0, column=4, padx=5, sticky="w")
        self.ent_ado_tipus = ttk.Combobox(input_f, values=["Adókedvezmény", "Cafeteria"], state="readonly", width=15)
        self.ent_ado_tipus.set("Adókedvezmény"); self.ent_ado_tipus.grid(row=1, column=0, padx=5)
        self.ent_ado_nev = ttk.Entry(input_f, width=25); self.ent_ado_nev.grid(row=1, column=1, padx=5)
        self.ent_ado_mertek = ttk.Entry(input_f, width=12); self.ent_ado_mertek.grid(row=1, column=2, padx=5)
        evek = [str(i) for i in range(2020, 2036)]; honapok = [f"{i:02d}" for i in range(1, 13)]
        date_tol_f = tk.Frame(input_f, bg="white"); date_tol_f.grid(row=1, column=3, padx=5)
        self.cb_tol_e = ttk.Combobox(date_tol_f, values=evek, width=6, state="readonly"); self.cb_tol_e.pack(side="left")
        tk.Label(date_tol_f, text=".", bg="white").pack(side="left")
        self.cb_tol_h = ttk.Combobox(date_tol_f, values=honapok, width=4, state="readonly"); self.cb_tol_h.pack(side="left")
        date_ig_f = tk.Frame(input_f, bg="white"); date_ig_f.grid(row=1, column=4, padx=5)
        self.cb_ig_e = ttk.Combobox(date_ig_f, values=evek, width=6, state="readonly"); self.cb_ig_e.pack(side="left")
        tk.Label(date_ig_f, text=".", bg="white").pack(side="left")
        self.cb_ig_h = ttk.Combobox(date_ig_f, values=honapok, width=4, state="readonly"); self.cb_ig_h.pack(side="left")
        btn_action_f = tk.Frame(input_f, bg="white"); btn_action_f.grid(row=1, column=5, padx=5)
        tk.Button(btn_action_f, text="➕", command=self.ado_mentes, bg="#10B981", fg="white", width=3).pack(side="left", padx=2)
        tk.Button(btn_action_f, text="💾", command=self.ado_frissites, bg="#3B82F6", fg="white", width=3).pack(side="left", padx=2)
        cols = ("id", "tipus", "nev", "mertek", "tol", "ig")
        self.ado_tree = ttk.Treeview(self.tab_ado, columns=cols, show="headings", height=10)
        for c, t, w in zip(cols, ["ID", "Típus", "Megnevezés", "Ft", "Hatálybalépés", "Hatályvesztés"], [40, 120, 200, 80, 120, 120]):
            self.ado_tree.heading(c, text=t); self.ado_tree.column(c, width=w)
        self.ado_tree.pack(fill="both", expand=True, pady=10)
        self.ado_tree.bind("<<TreeviewSelect>>", self.ado_sor_betoltes)
        tk.Button(self.tab_ado, text="🗑 KIJELÖLT SOR TÖRLÉSE", bg="#EF4444", fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self.ado_sor_torles).pack(anchor="e")

    def ado_sor_betoltes(self, event):
        sel = self.ado_tree.selection()
        if not sel: return
        item = self.ado_tree.item(sel[0])['values']
        self.selected_ado_id = item[0]
        self.ent_ado_tipus.set(item[1])
        self.ent_ado_nev.delete(0, tk.END); self.ent_ado_nev.insert(0, item[2])
        self.ent_ado_mertek.delete(0, tk.END); self.ent_ado_mertek.insert(0, item[3])
        if item[4] and "." in str(item[4]):
            p = str(item[4]).split("."); self.cb_tol_e.set(p[0]); self.cb_tol_h.set(p[1])
        else: self.cb_tol_e.set(""); self.cb_tol_h.set("")
        if item[5] and "." in str(item[5]):
            p = str(item[5]).split("."); self.cb_ig_e.set(p[0]); self.cb_ig_h.set(p[1])
        else: self.cb_ig_e.set(""); self.cb_ig_h.set("")

    def ado_frissites(self):
        if not self.selected_ado_id:
            messagebox.showwarning("Figyelem", "Nincs kijelölt sor a módosításhoz!"); return
        try:
            tol = f"{self.cb_tol_e.get()}.{self.cb_tol_h.get()}" if self.cb_tol_e.get() else ""
            ig = f"{self.cb_ig_e.get()}.{self.cb_ig_h.get()}" if self.cb_ig_e.get() else ""
            conn = sqlite3.connect("berszamitas.db")
            conn.execute("UPDATE settings_ado SET tipus=?, megnevezes=?, mertek=?, ervenyes_tol=?, ervenyes_ig=? WHERE id=?", 
                         (self.ent_ado_tipus.get(), self.ent_ado_nev.get(), int(self.ent_ado_mertek.get() or 0), tol, ig, self.selected_ado_id))
            conn.commit(); conn.close(); self.ado_listazas(); messagebox.showinfo("Siker", "Módosítás mentve!")
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def ado_sor_torles(self):
        sel = self.ado_tree.selection()
        if not sel: return
        item = self.ado_tree.item(sel[0])['values']
        if messagebox.askyesno("Megerősítés", f"Törli: {item[2]}?"):
            try:
                conn = sqlite3.connect("berszamitas.db"); conn.execute("DELETE FROM settings_ado WHERE id=?", (item[0],)); conn.commit(); conn.close(); self.ado_listazas()
                self.selected_ado_id = None
            except Exception as e: messagebox.showerror("Hiba", str(e))

    def ado_mentes(self):
        try:
            tol = f"{self.cb_tol_e.get()}.{self.cb_tol_h.get()}" if self.cb_tol_e.get() else ""
            ig = f"{self.cb_ig_e.get()}.{self.cb_ig_h.get()}" if self.cb_ig_e.get() else ""
            conn = sqlite3.connect("berszamitas.db")
            conn.execute("INSERT INTO settings_ado (tipus, megnevezes, mertek, ervenyes_tol, ervenyes_ig) VALUES (?, ?, ?, ?, ?)", (self.ent_ado_tipus.get(), self.ent_ado_nev.get(), int(self.ent_ado_mertek.get() or 0), tol, ig))
            conn.commit(); conn.close(); self.ado_listazas()
        except Exception as e: messagebox.showerror("Hiba", f"Hiba: {e}")

    def ado_listazas(self):
        for i in self.ado_tree.get_children(): self.ado_tree.delete(i)
        try:
            conn = sqlite3.connect("berszamitas.db")
            for r in conn.execute("SELECT id, tipus, megnevezes, mertek, ervenyes_tol, ervenyes_ig FROM settings_ado").fetchall(): self.ado_tree.insert("", "end", values=r)
            conn.close()
        except: pass

    def _setup_rendszer_tab(self):
        # Biztonsági mentés rész (SMTP jelszó mező törölve)
        backup_f = tk.LabelFrame(self.tab_rendszer, text="Biztonsági mentések kezelése", bg="white", padx=10, pady=10)
        backup_f.pack(fill="both", expand=True)

        btn_top = tk.Frame(backup_f, bg="white")
        btn_top.pack(fill="x", pady=5)
        tk.Button(btn_top, text="📂 ÚJ BIZTONSÁGI MENTÉS KÉSZÍTÉSE", command=self.db_mentes, 
                  bg="#0F172A", fg="white", font=("Segoe UI", 9, "bold"), padx=20, pady=5).pack(side="left")
        tk.Button(btn_top, text="🔄 LISTA FRISSÍTÉSE", command=self.backup_listazas, 
                  bg="#64748B", fg="white", font=("Segoe UI", 8)).pack(side="right")

        cols = ("file", "date")
        self.backup_tree = ttk.Treeview(backup_f, columns=cols, show="headings", height=15)
        self.backup_tree.heading("file", text="Fájlnév")
        self.backup_tree.heading("date", text="Mentés dátuma")
        self.backup_tree.column("file", width=400)
        self.backup_tree.column("date", width=200)
        self.backup_tree.pack(fill="both", expand=True, pady=10)

        tk.Button(backup_f, text="⏪ KIJELÖLT MENTÉS VISSZAÁLLÍTÁSA", command=self.db_visszaallitas_kerdes, 
                  bg="#E11D48", fg="white", font=("Segoe UI", 10, "bold"), pady=8).pack(fill="x")
        
        self.backup_listazas()

    def backup_listazas(self):
        for i in self.backup_tree.get_children(): self.backup_tree.delete(i)
        if not os.path.exists("backup"):
            os.makedirs("backup")
        files = [f for f in os.listdir("backup") if f.endswith(".bak")]
        files.sort(reverse=True)
        for f in files:
            fpath = os.path.join("backup", f)
            mtime = os.path.getmtime(fpath)
            dt = datetime.fromtimestamp(mtime).strftime("%Y.%m.%d %H:%M:%S")
            self.backup_tree.insert("", "end", values=(f, dt))

    def db_mentes(self):
        try:
            if not os.path.exists("backup"):
                os.makedirs("backup")
            fname = f"backup_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.bak"
            target = os.path.join("backup", fname)
            shutil.copy2("berszamitas.db", target)
            messagebox.showinfo("Siker", f"Biztonsági mentés elkészült:\n{fname}")
            self.backup_listazas()
            return True
        except Exception as e:
            messagebox.showerror("Hiba", f"Mentési hiba: {e}")
            return False

    def db_visszaallitas_kerdes(self):
        sel = self.backup_tree.selection()
        if not sel:
            messagebox.showwarning("Figyelem", "Válasszon ki egy mentést a listából!")
            return
        fname = self.backup_tree.item(sel[0])['values'][0]
        msg = f"Biztosan visszaállítja a(z) {fname} mentést?\n\nA jelenlegi adatok felülírásra kerülnek!"
        custom_box = tk.Toplevel(self)
        custom_box.title("Visszaállítás megerősítése")
        custom_box.geometry("450x200")
        custom_box.configure(padx=20, pady=20)
        custom_box.grab_set()
        tk.Label(custom_box, text=msg, wraplength=400, justify="center").pack(pady=10)
        btn_f = tk.Frame(custom_box); btn_f.pack(pady=10)
        def proceed(save_current=False):
            if save_current:
                if self.db_mentes(): self._vegleges_visszaallitas(fname)
            else: self._vegleges_visszaallitas(fname)
            custom_box.destroy()
        tk.Button(btn_f, text="Jelenlegi mentése és betöltés", bg="#059669", fg="white", 
                  command=lambda: proceed(True)).pack(side="left", padx=5)
        tk.Button(btn_f, text="Csak betöltés", bg="#3B82F6", fg="white", 
                  command=lambda: proceed(False)).pack(side="left", padx=5)
        tk.Button(btn_f, text="Mégse", command=custom_box.destroy).pack(side="left", padx=5)

    def _vegleges_visszaallitas(self, backup_file):
        try:
            source = os.path.join("backup", backup_file)
            if not os.path.exists(source): raise FileNotFoundError("A mentési fájl nem található!")
            shutil.copy2(source, "berszamitas.db")
            messagebox.showinfo("Siker", "Az adatbázis visszaállítása sikeresen megtörtént!")
            self.adatok_betoltese()
        except Exception as e:
            messagebox.showerror("Hiba", f"Visszaállítási hiba (A jelenlegi adatbázis sértetlen maradt): {e}")

    def _setup_naplok_tab(self):
        btn_f = tk.Frame(self.tab_naplok, bg="white"); btn_f.pack(fill="x", pady=5)
        tk.Button(btn_f, text="🔄 FRISSÍTÉS", command=self.naplok_frissitese).pack(side="left")
        self.txt_munka = tk.Text(self.tab_naplok, height=10); self.txt_munka.pack(fill="both", expand=True, pady=5)
        self.txt_hiba = tk.Text(self.tab_naplok, height=8, bg="#1E293B", fg="#FCA5A5"); self.txt_hiba.pack(fill="both", expand=True, pady=5)

    def naplok_frissitese(self):
        self.txt_munka.delete("1.0", tk.END); self.txt_hiba.delete("1.0", tk.END)
        try:
            conn = sqlite3.connect("berszamitas.db")
            for r in conn.execute("SELECT datum, esemeny FROM esemeny_naplo ORDER BY id DESC LIMIT 50").fetchall(): self.txt_munka.insert(tk.END, f"{r[0]} | {r[1]}\n")
            for r in conn.execute("SELECT datum, hiba_uzenet FROM hiba_naplo ORDER BY id DESC LIMIT 30").fetchall(): self.txt_hiba.insert(tk.END, f"{r[0]} | {r[1]}\n")
            conn.close()
        except: pass

    def mentes(self):
        try:
            conn = sqlite3.connect("berszamitas.db")
            # A tuple végén az smtp_pass helyett üres sztringet küldünk, ha a mező már nem létezik az entries-ben
            smtp_val = self.entries["smtp_pass"].get() if "smtp_pass" in self.entries else ""
            vals = (self.entries["ceg_nev"].get(), self.entries["szekhely"].get(), float(self.entries["szja"].get().replace(',','.') or 0), float(self.entries["tb"].get().replace(',','.') or 0), float(self.entries["betegszab_70"].get().replace(',','.') or 0), float(self.entries["tappenz_60"].get().replace(',','.') or 0), float(self.entries["baleseti_100"].get().replace(',','.') or 0), int(self.entries["km_dij"].get() or 0), float(self.entries["muszak_potlek"].get().replace(',','.') or 0), self.ev_kezdet_cb.get(), smtp_val)
            conn.execute("INSERT OR REPLACE INTO global_beallitasok (id, ceg_nev, szekhely, szja, tb, betegszab_70, tappenz_60, baleseti_100, km_dij, muszak_potlek, ev_kezdet, smtp_pass) VALUES (1,?,?,?,?,?,?,?,?,?,?,?)", vals)
            conn.commit(); conn.close(); messagebox.showinfo("Siker", "Mentve!")
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def adatok_betoltese(self):
        try:
            conn = sqlite3.connect("berszamitas.db")
            row = conn.execute("SELECT * FROM global_beallitasok WHERE id = 1").fetchone()
            if row:
                mapping = ["id", "ceg_nev", "szekhely", "szja", "tb", "betegszab_70", "tappenz_60", "baleseti_100", "km_dij", "muszak_potlek", "ev_kezdet", "smtp_pass"]
                for i, key in enumerate(mapping):
                    if key in self.entries: self.entries[key].delete(0, tk.END); self.entries[key].insert(0, str(row[i]) if row[i] is not None else "")
                    if key == "ev_kezdet": self.ev_kezdet_cb.set(row[i])
            conn.close()
        except: pass
        self.ado_listazas()
        if hasattr(self, 'txt_munka'): self.naplok_frissitese()

if __name__ == "__main__":
    root = tk.Tk(); app = BeallitasokModul(root, current_user_acc="su"); root.mainloop()