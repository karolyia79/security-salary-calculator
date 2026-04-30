import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import calendar
from datetime import datetime, date, timedelta

# --- KONFIGURÁCIÓ ---
DB_PATH = 'berszamitas.db'
SQL_TIMEOUT = 20  # Másodperc, amíg vár az adatbázisra, ha foglalt

# --- 1. NAPLÓZÓ ÉS HIBAKEZELŐ RENDSZER ---
def esemeny_naplozas(esemeny, dolgozo_adat="N/A"):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=SQL_TIMEOUT)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS esemeny_naplo 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           datum TEXT, esemeny TEXT, dolgozo TEXT)''')
        most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        cursor.execute("INSERT INTO esemeny_naplo (datum, esemeny, dolgozo) VALUES (?, ?, ?)", 
                       (most, esemeny, dolgozo_adat))
        conn.commit()
    except Exception as e:
        print(f"Naplózási hiba: {e}")
    finally:
        if conn: conn.close()

def hiba_naplozas(modul, hiba):
    hiba_szoveg = f"HIBA: {str(hiba)}"
    print(f"[{modul}] {hiba_szoveg}")
    esemeny_naplozas(f"ERROR: {modul}", hiba_szoveg)

# --- 2. ÜNNEPNAP KALKULÁTOR ---
def get_all_unnepek(ev):
    unnepek = {
        date(ev, 1, 1): "Újév", date(ev, 3, 15): "Nemzeti ünnep",
        date(ev, 5, 1): "Munka ünnepe", date(ev, 8, 20): "Államalapítás",
        date(ev, 10, 23): "56-os forradalom", date(ev, 11, 1): "Mindenszentek",
        date(ev, 12, 25): "Karácsony", date(ev, 12, 26): "Karácsony"
    }
    # Gauss-algoritmus húsvéthoz
    a, b, c = ev % 19, ev % 4, ev % 7
    m, n = 24, 5
    d = (19 * a + m) % 30
    e = (2 * b + 4 * c + 6 * d + n) % 7
    nap = 22 + d + e
    h = 3
    if nap > 31: nap -= 31; h = 4
    h_vas = date(ev, h, nap)
    unnepek.update({
        h_vas - timedelta(days=2): "Nagypéntek",
        h_vas: "Húsvétvasárnap", h_vas + timedelta(days=1): "Húsvéthétfő",
        h_vas + timedelta(days=49): "Pünkösdvasárnap", h_vas + timedelta(days=50): "Pünkösdhétfő"
    })
    return unnepek
    
def adatbazis_ellenorzes():
    print("\n[DB-CHECK] Adatbázis struktúra ellenőrzése...")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=SQL_TIMEOUT)
        cursor = conn.cursor()
        
        # Alap tábla létrehozása (ha még nincs)
        cursor.execute("CREATE TABLE IF NOT EXISTS jelenleti_adatok (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        
        # Minden szükséges oszlop listája és típusa
        szukseges_oszlopok = {
            "dolgozo_id": "INTEGER",
            "datum": "TEXT",
            "tipus": "TEXT",
            "m_ora": "REAL", "m_kez": "TEXT", "m_veg": "TEXT",
            "t_ora": "REAL", "t_kez": "TEXT", "t_veg": "TEXT",
            "k_ora": "REAL", "k_kez": "TEXT", "k_veg": "TEXT",
            "megj": "TEXT", "statusz": "TEXT",
            "unnepnapi_munkavegzes": "INTEGER DEFAULT 0",
            "unnep": "INTEGER DEFAULT 0"
        }
        
        cursor.execute("PRAGMA table_info(jelenleti_adatok)")
        letezo_oszlopok = [row[1] for row in cursor.fetchall()]
        
        for oszlop, tipus in szukseges_oszlopok.items():
            if oszlop not in letezo_oszlopok:
                print(f"[DB-MIGRATE] Oszlop hozzáadása: {oszlop} ({tipus})")
                cursor.execute(f"ALTER TABLE jelenleti_adatok ADD COLUMN {oszlop} {tipus}")
        
        conn.commit()
        print("[DB-CHECK] Adatbázis kész.\n")
    except Exception as e:
        print(f"[DB-ERROR] Hiba az ellenőrzésnél: {e}")
    finally:
        if conn: conn.close()

# Indításnál hívd meg:
adatbazis_ellenorzes()

# --- 3. JELENLÉTI MODUL ---
class JelenletiModul(tk.Toplevel):
    def __init__(self, parent, dolgozo_adatok):
        super().__init__(parent)
        self.dolgozo_id = dolgozo_adatok.get('id', 1)
        self.dolgozo_nev = dolgozo_adatok.get('nev', "Ismeretlen")
        self.dolgozo_szul = dolgozo_adatok.get('szul_datum', "N/A")
        
        self.valasztott_ev = datetime.now().year
        self.title(f"Security Bérkalkulátor - {self.dolgozo_nev}")
        self.geometry("1450x900")
        self.configure(bg="#F8FAFC")
        
        # Ablak rétegkezelés: Felül legyen alapértelmezetten, de engedje maga elé az alablakokat
        self.attributes("-topmost", True)
        self.bind("<FocusIn>", lambda e: self.attributes("-topmost", True))
        self.bind("<FocusOut>", lambda e: self.attributes("-topmost", False))

        self.center_window()
        self.setup_valaszto_ui()

    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = (self.winfo_screenwidth() // 2) - (w // 2), (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

    def get_statusz_info(self, ev, honap):
        minta = f"{ev}.{honap:02d}.%"
        res = {"statusz": "ures", "mentve": None, "kesz": None, "torolve": None, "utolso_tipus": None}
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=SQL_TIMEOUT)
            cursor = conn.cursor()
            cursor.execute("SELECT statusz FROM jelenleti_adatok WHERE dolgozo_id=? AND datum LIKE ? LIMIT 1", (self.dolgozo_id, minta))
            row = cursor.fetchone()
            if row: res["statusz"] = row[0]
            
            naplo_kulcs = f"{self.dolgozo_nev} | {ev}. év {honap:02d}. hónap"
            cursor.execute("SELECT datum, esemeny FROM esemeny_naplo WHERE dolgozo=? ORDER BY id DESC", (naplo_kulcs,))
            naplo_adatok = cursor.fetchall()
            
            if naplo_adatok:
                legfrissebb = naplo_adatok[0][1].lower()
                if "kiürítve" in legfrissebb:
                    res["utolso_tipus"] = "torolve"
                    res["torolve"] = naplo_adatok[0][0]
                else:
                    res["utolso_tipus"] = "adat"
                    for d, e in naplo_adatok:
                        e_l = e.lower()
                        if "mentve" in e_l and not res["mentve"]: res["mentve"] = d
                        if "véglegesítve" in e_l and not res["kesz"]: res["kesz"] = d
                        if "kiürítve" in e_l: break
        except Exception as e: hiba_naplozas("STATUSZ_INFO", e)
        finally:
            if conn: conn.close()
        return res

    def setup_valaszto_ui(self):
        for w in self.winfo_children(): w.destroy()
        
        header = tk.Frame(self, bg="#1E293B", pady=20); header.pack(fill="x")
        tk.Label(header, text=f"{self.dolgozo_nev}  |  Született: {self.dolgozo_szul}", font=("Segoe UI", 14, "bold"), bg="#1E293B", fg="white").pack()

        nav = tk.Frame(self, bg="#F8FAFC", pady=20); nav.pack()
        tk.Button(nav, text=" ◀ ", command=lambda: [setattr(self, 'valasztott_ev', self.valasztott_ev-1), self.setup_valaszto_ui()]).pack(side="left", padx=20)
        tk.Label(nav, text=str(self.valasztott_ev), font=("Segoe UI", 24, "bold"), bg="#F8FAFC").pack(side="left")
        tk.Button(nav, text=" ▶ ", command=lambda: [setattr(self, 'valasztott_ev', self.valasztott_ev+1), self.setup_valaszto_ui()]).pack(side="left", padx=20)

        racs = tk.Frame(self, bg="#F8FAFC"); racs.pack(expand=True, fill="both", padx=50)
        h_nevek = ["Január", "Február", "Március", "Április", "Május", "Június", "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        for i, nev in enumerate(h_nevek):
            info = self.get_statusz_info(self.valasztott_ev, i+1)
            bg_c, fg_c = ("#BBF7D0", "#166534") if info["statusz"] == "kesz" else (("#FEF08A", "#854D0E") if info["statusz"] == "mentve" else ("#E2E8F0", "#64748B"))
            
            # Külső keret nélküli konténer, ami rácshoz igazodik
            f = tk.Frame(racs, bg="#F8FAFC"); f.grid(row=i//4, column=i%4, padx=15, pady=15, sticky="nsew")
            racs.grid_columnconfigure(i%4, weight=1)
            racs.grid_rowconfigure(i//4, weight=1)
            
            # Gomb konténer, amin csak a keret van (highlightthickness)
            btn_frame = tk.Frame(f, bg="#CBD5E1", highlightbackground="#CBD5E1", highlightthickness=1)
            btn_frame.pack()

            # Gomb (20%-al nagyobb méretben)
            tk.Button(btn_frame, text=nev.upper(), bg=bg_c, fg=fg_c, font=("Segoe UI", 10, "bold"), width=26, height=4, relief="flat", command=lambda m=i+1: self.megnyit_tablazat(m)).pack()
            
            # Feliratok a kereten kívül, a doboz alatt
            if info["utolso_tipus"] == "torolve":
                tk.Label(f, text=f"Törölve: {info['torolve']}", font=("Segoe UI", 7, "bold"), bg="#F8FAFC", fg="#E11D48").pack(pady=(2,0))
            else:
                if info["mentve"]: tk.Label(f, text=f"Mentve: {info['mentve']}", font=("Segoe UI", 7), bg="#F8FAFC", fg="#64748B").pack(pady=(2,0))
                if info["kesz"]: tk.Label(f, text=f"Kész: {info['kesz']}", font=("Segoe UI", 7, "bold"), bg="#F8FAFC", fg="#166534").pack()

    def megnyit_tablazat(self, honap):
        for w in self.winfo_children(): w.destroy()
        nav = tk.Frame(self, bg="#F1F5F9", pady=10); nav.pack(fill="x")
        tk.Button(nav, text="⬅ VISSZA", font=("Segoe UI", 9, "bold"), command=self.setup_valaszto_ui).pack(side="left", padx=20)
        
        btns = tk.Frame(nav, bg="#F1F5F9"); btns.pack(side="right", padx=20)
        tk.Button(btns, text="🗑 KIÜRÍTÉS", bg="#E11D48", fg="white", font=("Segoe UI", 9, "bold"), command=lambda: self.megerosit(honap, "kiurites")).pack(side="left", padx=5)
        tk.Button(btns, text="💾 MENTÉS", bg="#64748B", fg="white", font=("Segoe UI", 9, "bold"), command=lambda: self.megerosit(honap, "mentve")).pack(side="left", padx=5)
        tk.Button(btns, text="✅ VÉGLEGESÍTÉS", bg="#059669", fg="white", font=("Segoe UI", 9, "bold"), command=lambda: self.megerosit(honap, "kesz")).pack(side="left", padx=5)

        main_cont = tk.Frame(self, bg="white"); main_cont.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canv = tk.Canvas(main_cont, bg="white", highlightthickness=0); scr = ttk.Scrollbar(main_cont, orient="vertical", command=canv.yview)
        self.scroll_frame = tk.Frame(canv, bg="white")
        self.scroll_frame.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canv.configure(yscrollcommand=scr.set); canv.pack(side="left", fill="both", expand=True); scr.pack(side="right", fill="y")

        headers = ["Nap", "Típus", "Jogcím", "M.óra", "Kezd", "Vége", "T.óra", "T.Kezd", "T.Vége", "K.óra", "K.Kezd", "K.Vége", "Megjegyzés"]
        for c, h in enumerate(headers):
            self.scroll_frame.grid_columnconfigure(c, weight=1, uniform="g1")
            tk.Label(self.scroll_frame, text=h, font=("Segoe UI", 8, "bold"), bg="#1E293B", fg="white", pady=10).grid(row=0, column=c, sticky="nsew", padx=1)

        mentett = {}
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=SQL_TIMEOUT); cursor = conn.cursor()
            minta = f"{self.valasztott_ev}.{honap:02d}.%"
            cursor.execute("SELECT * FROM jelenleti_adatok WHERE dolgozo_id=? AND datum LIKE ?", (self.dolgozo_id, minta))
            cols = [d[0] for d in cursor.description]
            for r in cursor.fetchall():
                d_row = dict(zip(cols, r))
                mentett[d_row['datum']] = d_row
        except Exception as e: hiba_naplozas("BETOLTES", e)
        finally:
            if conn: conn.close()

        unnepek = get_all_unnepek(self.valasztott_ev)
        self.sorok = []
        _, n_szam = calendar.monthrange(self.valasztott_ev, honap)
        for n in range(1, n_szam + 1):
            curr_d = date(self.valasztott_ev, honap, n); ds = curr_d.strftime("%Y.%m.%d")
            u_nev = unnepek.get(curr_d, "")
            bg = "#FFF1F2" if u_nev else ("#F1F5F9" if curr_d.weekday() >= 5 else "white")
            ad = mentett.get(ds, {})

            tk.Label(self.scroll_frame, text=f"{n}.", bg=bg, font=("Segoe UI", 9, "bold")).grid(row=n, column=0, sticky="nsew", pady=1)
            inf = tk.Frame(self.scroll_frame, bg=bg); inf.grid(row=n, column=1, sticky="nsew")
            tk.Label(inf, text=["H","K","Sze","Cs","P","Szo","V"][curr_d.weekday()], bg=bg, font=("Segoe UI", 7)).pack()
            if u_nev: tk.Label(inf, text=u_nev, bg=bg, fg="red", font=("Segoe UI", 6, "bold")).pack()

            cb = ttk.Combobox(self.scroll_frame, values=["Ledolgozott", "Szabadság", "Beteg", "MHBaleset", "Uti baleset", "Ünnep"], width=10)
            cb.grid(row=n, column=2, padx=2); cb.set(ad.get('tipus', ""))

            m = self.create_grp(n, 3, bg, ad.get('m_ora'), ad.get('m_kez'), ad.get('m_veg'))
            t = self.create_grp(n, 6, bg, ad.get('t_ora'), ad.get('t_kez'), ad.get('t_veg'))
            k = self.create_grp(n, 9, bg, ad.get('k_ora'), ad.get('k_kez'), ad.get('k_veg'))
            mj = ttk.Entry(self.scroll_frame, width=8); mj.insert(0, ad.get('megj', "")); mj.grid(row=n, column=12, padx=2)
            self.sorok.append({'datum': ds, 'is_u': u_nev!="", 'cb': cb, 'm': m, 't': t, 'k': k, 'mj': mj})

    def create_grp(self, r, col, bg, ov="", kv="", vv="--:--"):
        eo = ttk.Entry(self.scroll_frame, width=4, justify="center"); eo.insert(0, str(ov) if ov and ov!=0 else ""); eo.grid(row=r, column=col, padx=1)
        ek = ttk.Entry(self.scroll_frame, width=5, justify="center"); ek.insert(0, kv if kv else ""); ek.grid(row=r, column=col+1, padx=1)
        lv = tk.Label(self.scroll_frame, text=vv if vv else "--:--", width=5, bg=bg, font=("Segoe UI", 8, "bold"), fg="#0369A1"); lv.grid(row=r, column=col+2)
        def upd(e=None):
            k = self.ido_formal(ek.get()); ek.delete(0, tk.END); ek.insert(0, k)
            try:
                h, m = map(int, k.split(':'))
                dt = datetime(2000, 1, 1, h, m) + timedelta(hours=float(eo.get().replace(',','.') or 0))
                lv.config(text=dt.strftime("%H:%M"))
            except: lv.config(text="--:--")
        eo.bind("<FocusOut>", upd); ek.bind("<FocusOut>", upd); return eo, ek, lv

    def megerosit(self, honap, stat):
        msg = "KIÜRÍTI a hónapot?" if stat=="kiurites" else "Menti a piszkozatot?" if stat=="mentve" else "VÉGLEGESÍTI?"
        if messagebox.askyesno("Megerősítés", msg): self.vegrehajtas(honap, stat)

    def vegrehajtas(self, honap, stat):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=SQL_TIMEOUT)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jelenleti_adatok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dolgozo_id INTEGER, datum TEXT, tipus TEXT, 
                    m_ora REAL, m_kez TEXT, m_veg TEXT, 
                    t_ora REAL, t_kez TEXT, t_veg TEXT, 
                    k_ora REAL, k_kez TEXT, k_veg TEXT, 
                    megj TEXT, statusz TEXT, 
                    unnepnapi_munkavegzes INTEGER,
                    unnep INTEGER
                )
            """)

            minta = f"{self.valasztott_ev}.{honap:02d}.%"
            cursor.execute("DELETE FROM jelenleti_adatok WHERE dolgozo_id=? AND datum LIKE ?", (self.dolgozo_id, minta))
            
            if stat != "kiurites":
                for s in self.sorok:
                    jog = s['cb'].get()
                    try:
                        m_o_ertek = float(str(s['m'][0].get()).replace(',', '.') or 0)
                        t_o_ertek = float(str(s['t'][0].get()).replace(',', '.') or 0)
                        k_o_ertek = float(str(s['k'][0].get()).replace(',', '.') or 0)
                    except ValueError:
                        m_o_ertek = t_o_ertek = k_o_ertek = 0.0
                
                    is_naptari_unnep = 1 if s.get('is_u') else 0
                    u_m = 1 if (is_naptari_unnep == 1 and (m_o_ertek > 0 or t_o_ertek > 0 or k_o_ertek > 0)) else 0
                
                    if jog or m_o_ertek > 0 or t_o_ertek > 0 or k_o_ertek > 0 or is_naptari_unnep == 1:
                        cursor.execute("""
                            INSERT INTO jelenleti_adatok (
                                dolgozo_id, datum, tipus, 
                                m_ora, m_kez, m_veg, 
                                t_ora, t_kez, t_veg, 
                                k_ora, k_kez, k_veg, 
                                megj, statusz, unnepnapi_munkavegzes, unnep
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                            (self.dolgozo_id, s['datum'], jog, 
                             m_o_ertek, s['m'][1].get(), s['m'][2].cget("text"), 
                             t_o_ertek, s['t'][1].get(), s['t'][2].cget("text"), 
                             k_o_ertek, s['k'][1].get(), s['k'][2].cget("text"), 
                             s['mj'].get(), stat, u_m, is_naptari_unnep))
                            
            conn.commit()
                            
            if stat == "kiurites":
                esem_tipus = "Jelenléti ív KIÜRÍTVE"
            elif stat == "mentve":
                esem_tipus = "Jelenléti ív MENTVE (piszkozat)"
            elif stat == "kesz":
                esem_tipus = "Jelenléti ív VÉGLEGESÍTVE"
            else:
                esem_tipus = f"Jelenléti művelet: {stat}"

            reszletek = f"{self.valasztott_ev}. év {honap:02d}. hónap"
            naplo_beegyzes = f"{self.dolgozo_nev} | {reszletek}"
            esemeny_naplozas(esem_tipus, naplo_beegyzes)
            
            messagebox.showinfo("Siker", f"A művelet végrehajtva: {esem_tipus}\nIdőszak: {reszletek}")
            self.setup_valaszto_ui()
            
        except Exception as e:
            hiba_naplozas("VEGREHAJTAS", e)
            messagebox.showerror("Hiba", f"Nem sikerült a művelet: {e}")
        finally:
            if conn: conn.close()

    def ido_formal(self, v):
        if not v: return ""
        v = v.strip().replace(',', '.')
        try:
            if ":" in v: return v
            f = float(v); return f"{int(f):02d}:{int((f % 1) * 60):02d}"
        except: return v