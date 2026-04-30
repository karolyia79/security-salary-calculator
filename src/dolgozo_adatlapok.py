import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import os
import shutil
from datetime import datetime

# --- KONFIGURÁCIÓ ÉS NAPLÓZÁS ---
DB_PATH = 'berszamitas.db'
BASE_DOCS_PATH = "Munkavallalo_Dokumentumok"

def esemeny_naplozas(esemeny, dolgozo_adat="N/A"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS esemeny_naplo 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           datum TEXT, esemeny TEXT, dolgozo TEXT)''')
        most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        cursor.execute("INSERT INTO esemeny_naplo (datum, esemeny, dolgozo) VALUES (?, ?, ?)", 
                       (most, esemeny, dolgozo_adat))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Naplózási hiba: {e}")

def hiba_naplozas(modul, hiba):
    hiba_szoveg = f"HIBA: {str(hiba)}"
    print(f"[{modul}] {hiba_szoveg}")
    esemeny_naplozas(f"ERROR: {modul}", hiba_szoveg)

try:
    from tkcalendar import DateEntry
except ImportError:
    print("Hiba: pip install tkcalendar szükséges!")

class DolgozoAdatlapok(tk.Toplevel):
    def __init__(self, parent, munkaltato_id=None, user_nev="Ismeretlen", callback=None):
        super().__init__(parent)
        self.munkaltato_id = munkaltato_id
        self.user_nev = user_nev
        self.callback = callback
        
        self.title("Munkavállalók Nyilvántartása - Security Bérkalkulátor")
        self.geometry("1100x700")
        self.configure(bg="#F8FAFC")
        
        self.btn_style = {"bg": "#64748B", "fg": "white", "font": ("Segoe UI", 9, "bold"), "relief": "flat", "padx": 10, "pady": 5}
        self.sel_style = {"bg": "#1E293B", "fg": "white", "font": ("Segoe UI", 9, "bold"), "relief": "flat", "padx": 15, "pady": 5}
        self.del_style = {"bg": "#EF4444", "fg": "white", "font": ("Segoe UI", 9, "bold"), "relief": "flat", "padx": 10, "pady": 5}
        
        self.grab_set()
        self.setup_db()
        self.setup_ui()
        self.frissit_listat()

    def setup_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS munkavallalok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dolgozoszam TEXT UNIQUE,
                    nev TEXT,
                    szul_ido TEXT,
                    belep_ido TEXT,
                    ber_adatok TEXT,
                    gyermek_adatok TEXT,
                    kedvezmenyek TEXT,
                    alapszabi INTEGER,
                    gyerekszabi INTEGER,
                    munkabajaras_km INTEGER DEFAULT 0,
                    beosztas TEXT DEFAULT '',
                    adoszam TEXT DEFAULT '',
                    iranyitoszam TEXT DEFAULT '',
                    varos TEXT DEFAULT '',
                    utca_hazszam TEXT DEFAULT '',
                    telefonszam TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    munkaltato_id TEXT DEFAULT '',
                    rogzito_user TEXT DEFAULT ''
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            hiba_naplozas("setup_db", e)

    def setup_ui(self):
        header = tk.Frame(self, bg="#1E293B", height=50)
        header.pack(fill="x")
        tk.Label(header, text="DOLGOZÓI ADATBÁZIS", fg="white", bg="#1E293B", font=("Segoe UI", 12, "bold")).pack(pady=10)

        container = tk.Frame(self, bg="#F8FAFC", padx=20, pady=10)
        container.pack(fill="both", expand=True)

        self.cols = ("id", "dszam", "nev", "szul", "beosztas", "alap_sz", "gyerek_sz", "kedv_caf")
        self.tree = ttk.Treeview(container, columns=self.cols, show='headings')
        
        heads = [
            ("id", "ID", 40), 
            ("dszam", "D.szám", 80), 
            ("nev", "Név", 200), 
            ("szul", "Születés", 100), 
            ("beosztas", "Beosztás", 120), 
            ("alap_sz", "Alap szabi", 80), 
            ("gyerek_sz", "Gyerek szabi", 80),
            ("kedv_caf", "Adókedvezmény/Cafeteria", 250)
        ]
        
        for col_id, head_text, col_width in heads:
            self.tree.heading(col_id, text=head_text)
            self.tree.column(col_id, width=col_width, anchor="center")
            
        self.tree.pack(fill="both", expand=True)

        btn_f = tk.Frame(self, bg="#F8FAFC", pady=10)
        btn_f.pack(fill="x")
        
        tk.Button(btn_f, text="✅ KIVÁLASZTÁS", **self.sel_style, 
                  command=self.valasztas_vegrehajtasa).pack(side="left", padx=10)
        
        tk.Button(btn_f, text="ÚJ DOLGOZÓ", **self.btn_style, 
                  command=lambda: EditorAblak(self, self.frissit_listat, munkaltato_id=self.munkaltato_id, user_nev=self.user_nev)).pack(side="left", padx=5)
        
        tk.Button(btn_f, text="SZERKESZTÉS", **self.btn_style, 
                  command=self.szerkeszt).pack(side="left", padx=5)
        
        tk.Button(btn_f, text="TÖRLÉS", **self.del_style, 
                  command=self.torol).pack(side="left", padx=5)
        
        tk.Button(btn_f, text="BEZÁRÁS", **self.btn_style, 
                  command=self.destroy).pack(side="right", padx=20)

    def valasztas_vegrehajtasa(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Figyelem", "Válasszon ki egy dolgozót a listából!")
            return
        
        item_data = self.tree.item(selected[0])['values']
        adatok = {
            "id": item_data[0],
            "nev": item_data[2],
            "szul_datum": item_data[3]
        }
        
        if self.callback:
            self.callback(adatok)
            self.destroy()
        else:
            messagebox.showinfo("Infó", f"Kiválasztva: {adatok['nev']}\n(Callback nincs megadva)")

    def frissit_listat(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if self.munkaltato_id is not None:
                query = "SELECT id, dolgozoszam, nev, szul_ido, beosztas, alapszabi, gyerekszabi, kedvezmenyek FROM munkavallalok WHERE munkaltato_id = ? ORDER BY nev ASC"
                cursor.execute(query, (str(self.munkaltato_id),))
                rows = cursor.fetchall()
                for row in rows:
                    kedv_json = row[7]
                    stat_str = "NINCS"
                    if kedv_json:
                        try:
                            lista = json.loads(kedv_json)
                            ado_db = sum(1 for item in lista if isinstance(item, dict) and item.get('t') == "Adókedvezmény")
                            caf_db = sum(1 for item in lista if isinstance(item, dict) and item.get('t') == "Cafeteria")
                            res = []
                            if ado_db > 0: res.append(f"{ado_db}db Adó")
                            if caf_db > 0: res.append(f"{caf_db}db Caf")
                            if res: stat_str = ", ".join(res)
                        except: pass
                    
                    display_row = list(row[:7]) + [stat_str]
                    self.tree.insert("", "end", values=display_row)
            conn.close()
        except Exception as e: 
            hiba_naplozas("frissit_listat", e)

    def szerkeszt(self):
        sel = self.tree.selection()
        if not sel: return
        d_id = self.tree.item(sel[0])['values'][0]
        EditorAblak(self, self.frissit_listat, d_id, munkaltato_id=self.munkaltato_id, user_nev=self.user_nev)

    def torol(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        if messagebox.askyesno("Törlés", f"Biztosan törli {item['values'][2]} adatait?"):
            d_id = item['values'][0]
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM munkavallalok WHERE id=?", (d_id,))
            conn.commit(); conn.close()
            self.frissit_listat()

# --- EDITOR ABLAK OSZTÁLY ---
class EditorAblak(tk.Toplevel):
    def __init__(self, parent, callback, dolgozo_id=None, munkaltato_id=None, user_nev="Ismeretlen"):
        super().__init__(parent)
        self.title("Dolgozó Adatlap")
        self.geometry("850x750")
        self.callback = callback
        self.dolgozo_id = dolgozo_id
        self.munkaltato_id = munkaltato_id
        self.user_nev = user_nev
        
        self.btn_style = {"bg": "#64748B", "fg": "white", "font": ("Segoe UI", 9, "bold"), "relief": "flat"}
        self.save_style = {"bg": "#059669", "fg": "white", "font": ("Segoe UI", 10, "bold"), "relief": "flat"}
        self.del_style = {"bg": "#EF4444", "fg": "white", "font": ("Segoe UI", 9, "bold"), "relief": "flat"}
        
        self.grab_set()
        self.ber_lista, self.gyerek_lista, self.kedv_lista = [], [], []

        self.setup_db_docs()

        bottom_f = tk.Frame(self, pady=15, padx=20)
        bottom_f.pack(side="bottom", fill="x")
        
        tk.Button(bottom_f, text="MINDEN ADAT MENTÉSE", **self.save_style, width=25, height=2, command=self.mentes).pack(side="left")
        tk.Button(bottom_f, text="KILÉPÉS MENTÉS NÉLKÜL", **self.btn_style, width=25, height=2, command=self.destroy).pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.setup_tabs()
        if self.dolgozo_id: self.adatok_betoltese()

    def setup_db_docs(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dokumentumok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dolgozo_id INTEGER,
                    fajlnev TEXT,
                    eredeti_nev TEXT,
                    jelleg TEXT,
                    feltoltes_ideje TEXT,
                    feltolto_user TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            hiba_naplozas("setup_db_docs", e)

    def setup_tabs(self):
        # 1. Alapadatok fül
        t1 = ttk.Frame(self.nb); self.nb.add(t1, text=" Alapadatok ")
        c1 = tk.Frame(t1, padx=20, pady=15); c1.pack(fill="both")
        self.ent = {}
        
        beosztasok_lista = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT beosztasok FROM cegek WHERE ID_ceg = ?", (self.munkaltato_id,))
            res = cursor.fetchone()
            if res and res[0]:
                beosztasok_lista = json.loads(res[0])
            conn.close()
        except: pass

        fields = [("Dolgozószám:", "dszam"), ("Név:", "nev"), ("Születési d.:", "szul"), ("Adószám:", "adoszam"), 
                  ("Belépés:", "belep"), ("Beosztás:", "beosztas"), ("Munkábajárás (km):", "km")]
        
        for i, (txt, key) in enumerate(fields):
            tk.Label(c1, text=txt, font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=5)
            if key in ["szul", "belep"]: 
                e = DateEntry(c1, date_pattern='yyyy.mm.dd', width=27)
            elif key == "beosztas": 
                e = ttk.Combobox(c1, values=beosztasok_lista, width=27)
            else: 
                e = ttk.Entry(c1, width=30)
            e.grid(row=i, column=1, pady=5, padx=10)
            self.ent[key] = e

        # 2. Elérhetőség fül
        t_el = ttk.Frame(self.nb); self.nb.add(t_el, text=" Elérhetőség ")
        c_el = tk.Frame(t_el, padx=20, pady=15); c_el.pack(fill="both")
        el_fields = [("Irányítószám:", "iranyitoszam"), ("Város:", "varos"), ("Utca, házszám:", "utca_hazszam"), ("Telefonszám:", "telefonszam"), ("Email:", "email")]
        for i, (txt, key) in enumerate(el_fields):
            tk.Label(c_el, text=txt, font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(c_el, width=40)
            e.grid(row=i, column=1, pady=5, padx=10)
            self.ent[key] = e

        # 3. Bérezés fül
        t2 = ttk.Frame(self.nb); self.nb.add(t2, text=" Bérezés ")
        c2 = tk.Frame(t2, padx=20, pady=15); c2.pack(fill="both")
        input_f = tk.LabelFrame(c2, text=" Új bér tétel ", padx=10, pady=5); input_f.pack(fill="x", pady=5)
        
        tk.Label(input_f, text="Érvényesség:").grid(row=0, column=0, sticky="w")
        ev_f = tk.Frame(input_f); ev_f.grid(row=0, column=1, sticky="w", pady=2)
        curr_y = datetime.now().year
        self.e_ber_ev = ttk.Combobox(ev_f, values=[str(y) for y in range(curr_y-2, curr_y+5)], width=8); self.e_ber_ev.set(str(curr_y)); self.e_ber_ev.pack(side="left")
        self.e_ber_ho = ttk.Combobox(ev_f, values=[f"{i:02d}" for i in range(1, 13)], width=6, state="readonly"); self.e_ber_ho.set("01"); self.e_ber_ho.pack(side="left", padx=5)
        
        tk.Label(input_f, text="Típus:").grid(row=1, column=0, sticky="w")
        self.ber_tipus = ttk.Combobox(input_f, values=["Alapbér", "Bérkiegészítés", "Pótlék"], width=30); self.ber_tipus.current(0); self.ber_tipus.grid(row=1, column=1, pady=2, sticky="w")
        
        tk.Label(input_f, text="Összeg:").grid(row=2, column=0, sticky="w")
        self.e_bo = ttk.Entry(input_f, width=33); self.e_bo.grid(row=2, column=1, pady=2, sticky="w")
        
        opt_f = tk.Frame(input_f); opt_f.grid(row=3, column=1, sticky="w", pady=2)
        self.is_oraber, self.is_eseti = tk.BooleanVar(), tk.BooleanVar()
        tk.Checkbutton(opt_f, text="Órabér?", variable=self.is_oraber).pack(side="left")
        tk.Checkbutton(opt_f, text="Eseti", variable=self.is_eseti).pack(side="left", padx=10)
        
        tk.Button(input_f, text="+ Hozzáadás", **self.btn_style, command=self.add_ber).grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.ber_tree = ttk.Treeview(c2, columns=("idő", "tipus", "osszeg", "jelleg"), show="headings", height=5)
        for c, h in [("idő", "Dátum"), ("tipus", "Típus"), ("osszeg", "Összeg"), ("jelleg", "Jelleg")]: self.ber_tree.heading(c, text=h)
        self.ber_tree.pack(fill="both", expand=True, pady=5)
        tk.Button(c2, text="TÖRLÉS", **self.del_style, command=self.del_ber).pack(fill="x")

        # 4. Gyermekek fül
        t3 = ttk.Frame(self.nb); self.nb.add(t3, text=" Gyermekek ")
        c3 = tk.Frame(t3, padx=20, pady=15); c3.pack(fill="both")
        tk.Label(c3, text="Gyermek neve:").pack(anchor="w")
        self.e_gy_n = ttk.Entry(c3, width=40); self.e_gy_n.pack(pady=2)
        tk.Label(c3, text="Születési dátum:").pack(anchor="w")
        self.e_gy_sz = DateEntry(c3, date_pattern='yyyy.mm.dd', width=27); self.e_gy_sz.pack(pady=2)
        tk.Button(c3, text="+ Gyermek hozzáadása", **self.btn_style, command=self.add_gyerek).pack(pady=10)
        self.gy_tree = ttk.Treeview(c3, columns=("n", "sz"), show="headings", height=5)
        self.gy_tree.heading("n", text="Név"); self.gy_tree.heading("sz", text="Születés"); self.gy_tree.pack(fill="x")
        tk.Button(c3, text="TÖRLÉS", **self.del_style, command=self.del_gyerek).pack(pady=5, fill="x")

        # 5. Adókedv./Cafeteria fül
        t4 = ttk.Frame(self.nb); self.nb.add(t4, text=" Adókedv./Cafeteria ")
        c4 = tk.Frame(t4, padx=20, pady=15); c4.pack(fill="both")
        
        lista_elemek = []
        self.kedv_adatok_map = {}
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            query = "SELECT megnevezes, tipus, mertek FROM settings_ado WHERE munkaltato_id = ? ORDER BY megnevezes ASC"
            cursor.execute(query, (str(self.munkaltato_id),))
            for r in cursor.fetchall():
                megjelenes = f"{r[0]} ({r[1]})"
                lista_elemek.append(megjelenes)
                self.kedv_adatok_map[megjelenes] = {"n": r[0], "t": r[1], "m": r[2]}
            conn.close()
        except: pass

        self.kedv_valaszto = ttk.Combobox(c4, values=lista_elemek, width=60, state="readonly")
        self.kedv_valaszto.pack(pady=5, anchor="w")
        tk.Button(c4, text="Sor hozzáadása", **self.btn_style, command=self.add_kedv).pack(pady=10, anchor="w")
        
        self.kedv_tree = ttk.Treeview(c4, columns=("megnevezes", "tipus", "mertek"), show="headings", height=5)
        self.kedv_tree.heading("megnevezes", text="Megnevezés"); self.kedv_tree.heading("tipus", text="Típus"); self.kedv_tree.heading("mertek", text="Mérték")
        self.kedv_tree.pack(fill="x", pady=5)
        tk.Button(c4, text="KIJELÖLT TÖRLÉSE", **self.del_style, command=self.del_kedv).pack(pady=10, fill="x")

        # 6. Dokumentumok fül
        self.t_docs = ttk.Frame(self.nb)
        self.nb.add(self.t_docs, text=" Dokumentumok ")
        self.setup_docs_tab()

    def setup_docs_tab(self):
        container = tk.Frame(self.t_docs, padx=20, pady=15)
        container.pack(fill="both", expand=True)

        upload_f = tk.LabelFrame(container, text=" Dokumentum feltöltése ", padx=10, pady=10)
        upload_f.pack(fill="x", pady=(0, 10))

        tk.Label(upload_f, text="Jelleg:").grid(row=0, column=0, sticky="w")
        self.doc_type_var = tk.StringVar()
        self.doc_type_combo = ttk.Combobox(upload_f, textvariable=self.doc_type_var, width=20, state="readonly")
        self.doc_type_combo['values'] = ("személyes", "hivatalos", "szerződés", "temetés", "fizetéselőleg", "egyéb")
        self.doc_type_combo.current(0)
        self.doc_type_combo.grid(row=0, column=1, padx=10, sticky="w")

        tk.Button(upload_f, text="📁 Fájl feltöltése", bg="#3B82F6", fg="white", 
                  font=("Segoe UI", 9, "bold"), relief="flat", command=self.upload_file).grid(row=0, column=2, padx=10)

        self.doc_tree = ttk.Treeview(container, columns=("nev", "jelleg", "user"), show="headings", height=10)
        self.doc_tree.heading("nev", text="Fájlnév")
        self.doc_tree.heading("jelleg", text="Dokumentum jellege")
        self.doc_tree.heading("user", text="Feltöltő felhasználó")
        self.doc_tree.pack(fill="both", expand=True)

        btn_f = tk.Frame(container)
        btn_f.pack(fill="x", pady=5)
        tk.Button(btn_f, text="TÖRLÉS", **self.del_style, command=self.delete_file).pack(side="left")

    def get_munkaltato_nev(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            res = conn.execute("SELECT ceg_neve FROM cegek WHERE ID_ceg=?", (self.munkaltato_id,)).fetchone()
            conn.close()
            return res[0].replace(" ", "_") if res else "Ismeretlen_Ceg"
        except: return "Ismeretlen_Ceg"

    def upload_file(self):
        if not self.dolgozo_id:
            messagebox.showwarning("Figyelem", "Előbb mentse el a dolgozót!")
            return
        source_path = filedialog.askopenfilename()
        if not source_path: return
        try:
            munkaltato = self.get_munkaltato_nev()
            dolgozo = self.ent["nev"].get().replace(" ", "_")
            most = datetime.now()
            f_datum = most.strftime("%Y%m%d")
            f_ido = most.strftime("%H%M%S")
            jelleg = self.doc_type_var.get()
            
            orig_name_only = os.path.splitext(os.path.basename(source_path))[0]
            ext = os.path.splitext(source_path)[1]
            
            # Formátum: eredetifajlnev_YYYYMMDD_hhmmss_jelleg.kiterjesztés
            target_filename = f"{orig_name_only}_{f_datum}_{f_ido}_{jelleg}{ext}"
            
            target_dir = os.path.join(BASE_DOCS_PATH, munkaltato, dolgozo)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, target_filename)
            
            shutil.copy2(source_path, target_path)
            
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO dokumentumok (dolgozo_id, fajlnev, eredeti_nev, jelleg, feltoltes_ideje, feltolto_user) VALUES (?,?,?,?,?,?)",
                         (self.dolgozo_id, target_filename, os.path.basename(source_path), jelleg, most.strftime("%Y.%m.%d %H:%M:%S"), self.user_nev))
            conn.commit(); conn.close()
            self.refresh_docs_list()
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def refresh_docs_list(self):
        for i in self.doc_tree.get_children(): self.doc_tree.delete(i)
        if not self.dolgozo_id: return
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("SELECT fajlnev, jelleg, feltolto_user, id FROM dokumentumok WHERE dolgozo_id=?", (self.dolgozo_id,))
            for row in cursor.fetchall():
                self.doc_tree.insert("", "end", values=row[:3], tags=(row[3],))
            conn.close()
        except: pass

    def delete_file(self):
        sel = self.doc_tree.selection()
        if not sel: return
        item = self.doc_tree.item(sel[0])
        f_nev = item['values'][0]
        db_id = self.doc_tree.item(sel[0], "tags")[0]
        if messagebox.askyesno("Törlés", "Biztosan törli a fájlt?"):
            try:
                m = self.get_munkaltato_nev()
                d = self.ent["nev"].get().replace(" ", "_")
                p = os.path.join(BASE_DOCS_PATH, m, d, f_nev)
                if os.path.exists(p): os.remove(p)
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM dokumentumok WHERE id=?", (db_id,))
                conn.commit(); conn.close()
                self.refresh_docs_list()
            except Exception as e: messagebox.showerror("Hiba", str(e))

    def add_ber(self):
        idopont, tipus, osszeg = f"{self.e_ber_ev.get()}.{self.e_ber_ho.get()}", self.ber_tipus.get(), self.e_bo.get().strip()
        jelleg = "Eseti" if self.is_eseti.get() else "Normál"
        if osszeg:
            self.ber_tree.insert("", "end", values=(idopont, tipus, f"{osszeg} {'(óra)' if self.is_oraber.get() else ''}", jelleg))
            self.ber_lista.append({"ev": self.e_ber_ev.get(), "ho": self.e_ber_ho.get(), "t": tipus, "o": osszeg, "h": self.is_oraber.get(), "eseti": self.is_eseti.get()})
            self.e_bo.delete(0, tk.END)

    def del_ber(self):
        sel = self.ber_tree.selection()
        if sel: idx = self.ber_tree.index(sel[0]); del self.ber_lista[idx]; self.ber_tree.delete(sel[0])

    def add_gyerek(self):
        n, sz = self.e_gy_n.get().strip(), self.e_gy_sz.get()
        if n: self.gy_tree.insert("", "end", values=(n, sz)); self.gyerek_lista.append({"nev": n, "szul": sz}); self.e_gy_n.delete(0, tk.END)

    def del_gyerek(self):
        sel = self.gy_tree.selection()
        if sel: idx = self.gy_tree.index(sel[0]); del self.gyerek_lista[idx]; self.gy_tree.delete(sel[0])

    def add_kedv(self):
        val = self.kedv_valaszto.get()
        if val and val in self.kedv_adatok_map:
            info = self.kedv_adatok_map[val]
            self.kedv_tree.insert("", "end", values=(info["n"], info["t"], info["m"]))
            self.kedv_lista.append({"n": info["n"], "t": info["t"], "m": info["m"]})

    def del_kedv(self):
        sel = self.kedv_tree.selection()
        if sel: idx = self.kedv_tree.index(sel[0]); del self.kedv_lista[idx]; self.kedv_tree.delete(sel[0])

    def adatok_betoltese(self):
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(munkavallalok)")
            cols = {c[1]: i for i, c in enumerate(cursor.fetchall())}
            r = cursor.execute("SELECT * FROM munkavallalok WHERE id=?", (self.dolgozo_id,)).fetchone()
            if r:
                map = {"dszam": "dolgozoszam", "nev": "nev", "adoszam": "adoszam", "beosztas": "beosztas", "km": "munkabajaras_km", "iranyitoszam": "iranyitoszam", "varos": "varos", "utca_hazszam": "utca_hazszam", "telefonszam": "telefonszam", "email": "email"}
                for k, c in map.items():
                    if k == "beosztas": self.ent[k].set(r[cols[c]] or "")
                    else: self.ent[k].delete(0, tk.END); self.ent[k].insert(0, str(r[cols[c]] or ""))
                self.ent["szul"].set_date(r[cols["szul_ido"]]); self.ent["belep"].set_date(r[cols["belep_ido"]])
                self.ber_lista = json.loads(r[cols["ber_adatok"]] or "[]")
                for b in self.ber_lista: self.ber_tree.insert("", "end", values=(f"{b.get('ev')}.{b.get('ho')}", b['t'], b['o'], "Eseti" if b.get('eseti') else "Normál"))
                self.gyerek_lista = json.loads(r[cols["gyermek_adatok"]] or "[]")
                for g in self.gyerek_lista: self.gy_tree.insert("", "end", values=(g['nev'], g['szul']))
                self.kedv_lista = json.loads(r[cols["kedvezmenyek"]] or "[]")
                for k in self.kedv_lista: 
                    if isinstance(k, dict): self.kedv_tree.insert("", "end", values=(k["n"], k["t"], k.get("m", "")))
            conn.close()
            self.refresh_docs_list()
        except Exception as e: hiba_naplozas("betoltes", e)

    def mentes(self):
        try:
            dszam, nev = self.ent["dszam"].get().strip(), self.ent["nev"].get().strip()
            if not dszam or not nev: messagebox.showwarning("Hiba", "Név és dolgozószám kötelező!"); return
            szul_ev = int(self.ent["szul"].get()[:4]); kor = datetime.now().year - szul_ev
            alap_sz = 20 + next((p for k,p in {45:10, 43:9, 41:8, 39:7, 37:6, 35:5, 33:4, 31:3, 28:2, 25:1}.items() if kor >= k), 0)
            gz = {1:2, 2:4}.get(len(self.gyerek_lista), 7 if len(self.gyerek_lista)>=3 else 0)
            conn = sqlite3.connect(DB_PATH)
            vals = (dszam, nev, self.ent["szul"].get(), self.ent["belep"].get(), json.dumps(self.ber_lista), 
                    json.dumps(self.gyerek_lista), json.dumps(self.kedv_lista), alap_sz, gz, int(self.ent["km"].get() or 0), 
                    self.ent["beosztas"].get(), self.ent["adoszam"].get(), self.ent["iranyitoszam"].get(), 
                    self.ent["varos"].get(), self.ent["utca_hazszam"].get(), self.ent["telefonszam"].get(), 
                    self.ent["email"].get(), str(self.munkaltato_id), str(self.user_nev))
            if self.dolgozo_id:
                conn.execute("""UPDATE munkavallalok SET dolgozoszam=?, nev=?, szul_ido=?, belep_ido=?, ber_adatok=?, 
                                gyermek_adatok=?, kedvezmenyek=?, alapszabi=?, gyerekszabi=?, munkabajaras_km=?, 
                                beosztas=?, adoszam=?, iranyitoszam=?, varos=?, utca_hazszam=?, telefonszam=?, 
                                email=?, munkaltato_id=?, rogzito_user=? WHERE id=?""", vals + (self.dolgozo_id,))
            else:
                conn.execute("""INSERT INTO munkavallalok (dolgozoszam, nev, szul_ido, belep_ido, ber_adatok, 
                                gyermek_adatok, kedvezmenyek, alapszabi, gyerekszabi, munkabajaras_km, 
                                beosztas, adoszam, iranyitoszam, varos, utca_hazszam, telefonszam, 
                                email, munkaltato_id, rogzito_user) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
            conn.commit(); conn.close(); self.callback(); self.destroy()
        except Exception as e: hiba_naplozas("mentes", e); messagebox.showerror("Hiba", str(e))

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw()
    def sample_cb(data): print("Kiválasztott:", data)
    DolgozoAdatlapok(root, munkaltato_id=1, user_nev="Gipsz Jakab", callback=sample_cb)
    root.mainloop()