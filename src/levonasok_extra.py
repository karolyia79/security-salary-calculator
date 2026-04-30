import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

class LevonasokExtraModul(tk.Toplevel):
    def __init__(self, parent, dolgozo_adatok, felhasznalo_nev):
        super().__init__(parent)
        self.parent = parent
        self.dolgozo = dolgozo_adatok
        self.szerkeszto = felhasznalo_nev
        
        self.title(f"Módosító tételek - {self.dolgozo['nev']}")
        self.geometry("1450x850")
        self.configure(bg="#F1F5F9")
        
        self.db_path = 'berszamitas.db'
        self.selected_id = None 
        
        # Figyelő változók az automatikus számításhoz
        self.var_osszeg = tk.StringVar()
        self.var_ismetles = tk.StringVar()
        self.var_osszeg.trace_add("write", self.update_total_amount)
        self.var_ismetles.trace_add("write", self.update_total_amount)

        self.init_db()
        self.setup_ui()
        self.adatok_betoltese()
        
        self.transient(parent)
        self.grab_set()

    def update_total_amount(self, *args):
        """Automatikusan kiszámolja a teljes összeget a havi összeg és az ismétlés alapján."""
        try:
            current_tab_idx = self.notebook.index(self.notebook.select())
            tipus = list(self.tabs_config.keys())[current_tab_idx]
            
            if tipus in ["EXTRA", "LEVONAS"]:
                o_str = self.var_osszeg.get().replace(" ", "").replace(",", "")
                havi = int(o_str) if o_str else 0
                
                i_str = self.var_ismetles.get().strip()
                # Megnézzük, hogy szám-e vagy dátum
                if i_str and i_str.isdigit():
                    ismetles = int(i_str)
                else:
                    ismetles = 1
                
                total = havi * ismetles
                f = self.fields[tipus]
                if 'total' in f['vars']:
                    f['vars']['total'].delete(0, tk.END)
                    if total > 0:
                        f['vars']['total'].insert(0, str(total))
        except:
            pass

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extra_tetelek (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dolgozo_id INTEGER NOT NULL,
                tipus TEXT,
                megnevezes TEXT,
                osszeg INTEGER,
                teljes_osszeg INTEGER DEFAULT 0,
                idoszak TEXT,
                lejarat TEXT,
                gyakorisag TEXT DEFAULT 'Eseti',
                ismetles_szam INTEGER DEFAULT 1,
                visszafizetes_reszlet INTEGER DEFAULT 0,
                rogzitve TEXT,
                szerkeszto_nev TEXT,
                modositas_ideje TEXT,
                torles_ideje TEXT,
                folyositas_ideje TEXT,
                adokoteles INTEGER DEFAULT 0,
                megjegyzes TEXT,
                lejarat_datum TEXT,
                FOREIGN KEY(dolgozo_id) REFERENCES munkavallalok(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    def setup_ui(self):
        header = tk.Frame(self, bg="#1E293B", height=70)
        header.pack(fill="x")
        
        display_name = f"{self.dolgozo['nev'].upper()}"
        if 'szuletesi_datum' in self.dolgozo:
            display_name += f" ({self.dolgozo['szuletesi_datum']})"
            
        tk.Label(header, text=f"MÓDOSÍTÓ TÉTELEK: {display_name}", 
                 fg="white", bg="#1E293B", font=("Segoe UI", 12, "bold")).pack(pady=15)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.tabs_config = {
            "EXTRA": {"text": "  EXTRÁK ÉS JUTALMAK  "},
            "ELOLEG": {"text": "  BÉRELŐLEG  "},
            "LEVONAS": {"text": "  LEVONÁSOK ÉS LETILTÁSOK  "}
        }

        self.fields = {}
        for key, cfg in self.tabs_config.items():
            frame = tk.Frame(self.notebook, bg="white")
            self.notebook.add(frame, text=cfg['text'])
            self.build_tab_content(frame, key)

    def _update_ui_and_limit(self, event, widget, label):
        content = widget.get("1.0", "end-1c")
        hossz = len(content)
        if hossz > 256:
            widget.delete("1.0 + 256 chars", tk.END)
            hossz = 256
        label.config(text=f"{hossz} / 256")
        label.config(fg="#EF4444" if hossz >= 240 else "#64748B")

    def build_tab_content(self, frame, tipus):
        main_input_f = tk.Frame(frame, bg="white", padx=25, pady=15)
        main_input_f.pack(fill="x")

        left_f = tk.Frame(main_input_f, bg="white")
        left_f.pack(side="left", fill="y")

        # Megnevezés
        tk.Label(left_f, text="Megnevezés:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ent_m = ttk.Entry(left_f, width=30)
        if tipus == "ELOLEG":
            ent_m.insert(0, "Bérelőleg"); ent_m.config(state="readonly")
        ent_m.grid(row=0, column=1, padx=10, pady=8)

        # Összeg mezők
        label_text = "Összeg (Ft):" if tipus == "ELOLEG" else "Havi összeg (Ft):"
        tk.Label(left_f, text=label_text, bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w")
        ent_o = ttk.Entry(left_f, width=20, textvariable=self.var_osszeg)
        ent_o.grid(row=0, column=3, padx=10, pady=8)

        ado_var = tk.IntVar(value=0)
        tk.Checkbutton(left_f, text="Adóköteles", variable=ado_var, bg="white").grid(row=0, column=4, padx=10)

        l_vars = {'ado': ado_var}
        
        if tipus == "ELOLEG":
            tk.Label(left_f, text="Folyósítás (ÉÉÉÉ-HH):", bg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w")
            ent_foly = ttk.Entry(left_f, width=30)
            ent_foly.insert(0, datetime.now().strftime("%Y-%m"))
            ent_foly.grid(row=1, column=1, padx=10, pady=8)

            tk.Label(left_f, text="Futamidő (hó):", bg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="w")
            cmb_v = ttk.Combobox(left_f, values=["1", "2", "3", "4", "5", "6"], state="readonly", width=17, textvariable=self.var_ismetles)
            cmb_v.current(0); cmb_v.grid(row=1, column=3, padx=10, pady=8)

            tk.Label(left_f, text="Törlesztés kezdete:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
            ent_i = ttk.Entry(left_f, width=30)
            ent_i.insert(0, (datetime.now() + relativedelta(months=1)).strftime("%Y-%m"))
            ent_i.grid(row=2, column=1, padx=10, pady=8)
            l_vars.update({'vissza': cmb_v, 'foly': ent_foly})
        else:
            tk.Label(left_f, text="Induló hó (ÉÉÉÉ-HH):", bg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w")
            ent_i = ttk.Entry(left_f, width=30)
            ent_i.insert(0, datetime.now().strftime("%Y-%m"))
            ent_i.grid(row=1, column=1, padx=10, pady=8)

            tk.Label(left_f, text="Gyakoriság:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="w")
            cmb_g = ttk.Combobox(left_f, values=["Eseti", "Ciklikus (hó)", "Dátumig"], state="readonly", width=17)
            cmb_g.current(0); cmb_g.grid(row=1, column=3, padx=10, pady=8)

            tk.Label(left_f, text="Teljes összeg:", bg="white", fg="#059669", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
            ent_total = ttk.Entry(left_f, width=30)
            ent_total.grid(row=2, column=1, padx=10, pady=8)

            tk.Label(left_f, text="Hónapok / Dátum:", bg="white").grid(row=2, column=2, sticky="w")
            ent_t = ttk.Entry(left_f, width=20, textvariable=self.var_ismetles)
            ent_t.grid(row=2, column=3, padx=10, pady=8)
            l_vars.update({'gyak': cmb_g, 'tartam': ent_t, 'total': ent_total})

        # Megjegyzés szekció - CSAK HA NEM ELŐLEG
        if tipus != "ELOLEG":
            right_f = tk.Frame(main_input_f, bg="white")
            right_f.pack(side="right", fill="both", expand=True, padx=(20, 0))
            tk.Label(right_f, text="Megjegyzés:", bg="white", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            txt_megj = tk.Text(right_f, height=4, width=40, font=("Segoe UI", 9), relief="solid", borderwidth=1)
            txt_megj.pack(fill="both", expand=True)
            lbl_szamlalo = tk.Label(right_f, text="0 / 256", bg="white", font=("Segoe UI", 7), fg="#64748B")
            lbl_szamlalo.pack(anchor="e")
            txt_megj.bind("<KeyRelease>", lambda e: self._update_ui_and_limit(e, txt_megj, lbl_szamlalo))
            l_vars.update({'megj_text': txt_megj, 'szamlalo': lbl_szamlalo})

        self.fields[tipus] = {'m': ent_m, 'o': ent_o, 'i': ent_i, 'vars': l_vars}

        # Treeview oszlopok - ELŐLEG esetén nincs megjegyzés oszlop
        cols = ["id", "megnevezes", "teljes_osszeg", "osszeg", "folyositas", "idoszak", "lejarat", "param", "ado", "megj"]
        if tipus == "ELOLEG":
            cols.remove("megj")
        else:
            cols.remove("folyositas")
        
        tree_f = tk.Frame(frame, bg="white", padx=20)
        tree_f.pack(fill="both", expand=True, pady=10)
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=10)
        
        titles = {"id":"ID", "megnevezes":"Megnevezés", "osszeg":"Összeg / Havi", "folyositas":"Folyósítás", "idoszak":"Indulás", "lejarat":"Lejárat", "param":"Paraméter", "ado":"Adó", "teljes_osszeg":"Teljes összeg", "megj": "Megj."}
        for c in cols:
            tree.heading(c, text=titles[c])
            tree.column(c, width=100, anchor="center")
        tree.column("megnevezes", width=180, anchor="w")
        tree.pack(fill="both", expand=True, side="left")
        tree.bind("<<TreeviewSelect>>", lambda e: self.betolt_szerkesztesre(tipus))
        setattr(self, f"tree_{tipus}", tree)

    def betolt_szerkesztesre(self, tipus):
        tree = getattr(self, f"tree_{tipus}")
        sel = tree.selection()
        if not sel: return
        d = dict(zip(tree["columns"], tree.item(sel[0])['values']))
        self.selected_id = d['id']
        f = self.fields[tipus]
        
        f['m'].config(state="normal")
        f['m'].delete(0, tk.END); f['m'].insert(0, d['megnevezes'])
        if tipus == "ELOLEG": f['m'].config(state="readonly")
            
        self.var_osszeg.set(str(d['osszeg']).replace(",", "").replace(" ", "").replace("Ft", ""))
        f['i'].delete(0, tk.END); f['i'].insert(0, d['idoszak'])
        f['vars']['ado'].set(1 if d['ado'] == "Igen" else 0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT megjegyzes, gyakorisag, ismetles_szam, folyositas_ideje, lejarat_datum, teljes_osszeg FROM extra_tetelek WHERE id=?", (self.selected_id,))
        db_r = cursor.fetchone()
        conn.close()

        if db_r:
            if tipus != "ELOLEG":
                f['vars']['megj_text'].delete("1.0", tk.END)
                if db_r[0]: f['vars']['megj_text'].insert("1.0", db_r[0])
                self._update_ui_and_limit(None, f['vars']['megj_text'], f['vars']['szamlalo'])
                
                f['vars']['gyak'].set(db_r[1])
                self.var_ismetles.set(db_r[4] if db_r[1] == "Dátumig" else str(db_r[2]))
                
                f['vars']['total'].delete(0, tk.END)
                if db_r[5] and db_r[5] > 0:
                    f['vars']['total'].insert(0, str(db_r[5]))
                else:
                    try:
                        havi = int(self.var_osszeg.get() or 0)
                        ism = int(db_r[2] or 1)
                        if havi * ism > 0: f['vars']['total'].insert(0, str(havi * ism))
                    except: pass
            else:
                f['vars']['foly'].delete(0, tk.END); f['vars']['foly'].insert(0, db_r[3] or "")
                self.var_ismetles.set(str(db_r[2]))

    def mentes_logic(self, tipus, is_update):
        f = self.fields[tipus]
        m, o_raw, i = f['m'].get().strip(), f['o'].get().strip(), f['i'].get().strip()
        megj = f['vars']['megj_text'].get("1.0", tk.END).strip()
        
        try:
            start_date = datetime.strptime(i, "%Y-%m")
            total_sum = 0
            
            # Alapértékek
            gyak = f['vars']['gyak'].get() if 'gyak' in f['vars'] else "Eseti"
            tartam = 1
            lejarat_str = i
            target_date_str = None
            folyositas = ""

            # Számítási logika
            if tipus == "ELOLEG":
                total_sum = int(o_raw.replace(" ", ""))
                tartam = int(f['vars']['vissza'].get())
                havi_osszeg = total_sum // tartam
                lejarat_dt = start_date + relativedelta(months=tartam-1)
                lejarat_str = lejarat_dt.strftime("%Y-%m")
                gyak, folyositas = "Ciklikus", f['vars']['foly'].get().strip()
            
            else:
                t_input = f['vars']['total'].get().strip()
                # Ha van megadva TELJES ÖSSZEG, akkor osztunk
                if t_input:
                    total_sum = int(t_input.replace(" ", ""))
                    if gyak == "Dátumig":
                        target_date_str = f['vars']['tartam'].get().strip()
                        lejarat_dt = datetime.strptime(target_date_str, "%Y-%m")
                        diff = relativedelta(lejarat_dt, start_date)
                        tartam = (diff.years * 12) + diff.months + 1
                        lejarat_str = target_date_str
                    elif gyak == "Ciklikus (hó)":
                        tartam = int(f['vars']['tartam'].get().strip() or 1)
                        lejarat_dt = start_date + relativedelta(months=tartam-1)
                        lejarat_str = lejarat_dt.strftime("%Y-%m")
                    
                    havi_osszeg = total_sum // tartam
                # Ha NINCS teljes összeg, akkor a Havi összeg fix
                else:
                    havi_osszeg = int(o_raw.replace(" ", "") or 0)
                    if gyak == "Dátumig":
                        target_date_str = f['vars']['tartam'].get().strip()
                        lejarat_str = target_date_str
                        diff = relativedelta(datetime.strptime(target_date_str, "%Y-%m"), start_date)
                        tartam = (diff.years * 12) + diff.months + 1
                    elif gyak == "Ciklikus (hó)":
                        tartam = int(f['vars']['tartam'].get().strip() or 1)
                        lejarat_dt = start_date + relativedelta(months=tartam-1)
                        lejarat_str = lejarat_dt.strftime("%Y-%m")

            conn = sqlite3.connect(self.db_path)
            q = """UPDATE extra_tetelek SET megnevezes=?, osszeg=?, teljes_osszeg=?, idoszak=?, lejarat=?, gyakorisag=?, 
                    ismetles_szam=?, folyositas_ideje=?, adokoteles=?, megjegyzes=?, modositas_ideje=?, lejarat_datum=? WHERE id=?""" if is_update else \
                """INSERT INTO extra_tetelek (dolgozo_id, tipus, megnevezes, osszeg, teljes_osszeg, idoszak, lejarat, gyakorisag, 
                   ismetles_szam, rogzitve, szerkeszto_nev, folyositas_ideje, adokoteles, megjegyzes, lejarat_datum) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
            
            params = (m, havi_osszeg, total_sum, i, lejarat_str, gyak, tartam, folyositas, f['vars']['ado'].get(), megj, 
                      datetime.now().strftime("%Y-%m-%d %H:%M"), target_date_str, self.selected_id) if is_update else \
                      (self.dolgozo['id'], tipus, m, havi_osszeg, total_sum, i, lejarat_str, gyak, tartam, 
                      datetime.now().strftime("%Y-%m-%d %H:%M"), self.szerkeszto, folyositas, f['vars']['ado'].get(), megj, target_date_str)
            
            conn.execute(q, params)
            conn.commit(); conn.close()
            self.adatok_betoltese(); self.selected_id = None
            messagebox.showinfo("Siker", "Adatok mentve.", parent=self)
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba: {str(e)}", parent=self)

    def adatok_betoltese(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for t in self.tabs_config.keys():
            tree = getattr(self, f"tree_{t}")
            for item in tree.get_children(): tree.delete(item)
            cursor.execute("""SELECT id, megnevezes, osszeg, idoszak, lejarat, gyakorisag, ismetles_szam, folyositas_ideje, adokoteles, teljes_osszeg, megjegyzes 
                              FROM extra_tetelek WHERE dolgozo_id=? AND tipus=? ORDER BY id DESC""", (self.dolgozo['id'], t))
            for r in cursor.fetchall():
                p = f"{r[6]} hó" if "Ciklikus" in r[5] else r[5]
                ado = "Igen" if r[8] else "Nem"
                tree.insert("", "end", values=(r[0], r[1], f"{r[9]:,}" if r[9]>0 else "-", f"{r[2]:,}", r[7] if t=="ELOLEG" else r[3], r[3] if t=="ELOLEG" else r[4], r[4] if t=="ELOLEG" else p, ado, "VAN" if r[10] else "NINCS"))
        conn.close()

    def torles_logic(self, tipus):
        tree = getattr(self, f"tree_{tipus}")
        sel = tree.selection()
        if not sel: return
        if messagebox.askyesno("Törlés", "Biztosan törli?", parent=self):
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM extra_tetelek WHERE id=?", (tree.item(sel[0])['values'][0],))
            conn.commit(); conn.close()
            self.adatok_betoltese()