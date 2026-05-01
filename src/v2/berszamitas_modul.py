import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from ber_logika import szamitas_vegrehajtasa
from annual_report import AnnualReportGenerator

# --- KONFIGURÁCIÓ ---
DB_PATH = 'berszamitas.db'

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

class BerszamitasModul(tk.Toplevel):
    def __init__(self, parent, dolgozo_adatok):
        super().__init__(parent)
        self.dolgozo_id = dolgozo_adatok.get('id')
        self.dolgozo_nev = dolgozo_adatok.get('nev', "Ismeretlen")
        self.valasztott_ev = tk.IntVar(value=datetime.now().year)
        
        self.szuletesi_datum = self.get_dolgozo_szuldat()
        
        self.title(f"Security Bérkalkulátor - {self.dolgozo_nev}")
        
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = int(sw*0.85), int(sh*0.85)
        x, y = (sw-w)//2, (sh-h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.configure(bg="#F8FAFC")
        self.attributes("-topmost", True)
        
        self.init_db()
        self.setup_ui()

    def get_dolgozo_szuldat(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT szul_ido FROM munkavallalok WHERE id=?", (self.dolgozo_id,))
            res = cursor.fetchone()
            conn.close()
            return res[0] if res and res[0] else "Nincs megadva"
        except:
            return "N/A"

    def init_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS berszamitas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dolgozo_id INTEGER NOT NULL,
                    ev INTEGER NOT NULL,
                    honap INTEGER NOT NULL,
                    letrehozas_datuma TEXT,
                    utolso_modositas TEXT,
                    torles_ideje TEXT,
                    FOREIGN KEY(dolgozo_id) REFERENCES munkavallalok(id)
                )
            """)
            # Bővített oszloplista (Új extra tételekkel kiegészítve)
            szukseges_oszlopok = {
                "beosztas_kori": "TEXT", "alapber_oradij": "REAL", "alapber_osszeg": "REAL",
                "adhato_oradij": "REAL", "adhato_osszeg": "REAL", "alap_oradij": "REAL", "alap_osszeg": "REAL",
                "muszakpotlek_oradij": "REAL", "muszakpotlek_osszeg": "REAL",
                "munkaszuneti_munkavegzes_oradij": "REAL", "munkaszuneti_munkavegzes_osszeg": "REAL",
                "unnepnap_munkaber_oradij": "REAL", "unnepnapi_munkaber_osszeg": "REAL",
                "fizetett_unnep_oradij": "REAL", "fizetett_unnep_osszeg": "REAL",
                "szabadsag_oradij": "REAL", "szabadsag_osszeg": "REAL",
                "beteg_70_oradij": "REAL", "beteg_70_osszeg": "REAL",
                "beteg_60_oradij": "REAL", "beteg_60_osszeg": "REAL",
                "utibaleset_90_oradij": "REAL", "utibaleset_90_osszeg": "REAL",
                "mhbaleset_100_oradij": "REAL", "mhbaleset_100_osszeg": "REAL",
                "munkabajaras_osszeg": "REAL", "brutto_osszesen": "REAL", 
                "szja": "REAL", "tb_jarulek": "REAL", "netto_ber": "REAL",
                "tulora50_ora": "REAL", "tulora50_osszeg": "REAL", 
                "tulora100_ora": "REAL", "tulora100_osszeg": "REAL",
                "keszenlet_ora": "REAL", "keszenlet_osszeg": "REAL",
                "extra_plusz_adokoteles": "REAL", "extra_plusz_adomentes": "REAL",
                "extra_minusz_adokoteles": "REAL", "extra_minusz_adomentes": "REAL"
            }
            cursor.execute("PRAGMA table_info(berszamitas)")
            letezo = [sor[1] for sor in cursor.fetchall()]
            for col, dtype in szukseges_oszlopok.items():
                if col not in letezo:
                    cursor.execute(f"ALTER TABLE berszamitas ADD COLUMN {col} {dtype} DEFAULT 0")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB hiba: {e}")

    def setup_ui(self):
        for w in self.winfo_children(): w.destroy()
        
        header = tk.Frame(self, bg="#1E293B", pady=20)
        header.pack(fill="x")
        tk.Label(header, text=f"{self.dolgozo_nev.upper()}  |  Született: {self.szuletesi_datum}", 
                 font=("Segoe UI", 14, "bold"), fg="white", bg="#1E293B").pack()

        nav = tk.Frame(self, bg="#F8FAFC", pady=20)
        nav.pack()
        tk.Button(nav, text=" ◀ ", command=lambda: [self.valasztott_ev.set(self.valasztott_ev.get()-1), self.setup_ui()], 
                  font=("Segoe UI", 12, "bold")).pack(side="left", padx=20)
        tk.Label(nav, text=str(self.valasztott_ev.get()), font=("Segoe UI", 24, "bold"), bg="#F8FAFC").pack(side="left")
        tk.Button(nav, text=" ▶ ", command=lambda: [self.valasztott_ev.set(self.valasztott_ev.get()+1), self.setup_ui()],
                  font=("Segoe UI", 12, "bold")).pack(side="left", padx=20)

        racs_cont = tk.Frame(self, bg="#F8FAFC")
        racs_cont.pack(expand=True, fill="both", padx=40, pady=10)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        h_nevek = ["Január", "Február", "Március", "Április", "Május", "Június", "Július", "Augusztus", "Szeptember", "Október", "November", "December"]

        for idx in range(1, 13):
            month_pattern = f"{self.valasztott_ev.get()}.{idx:02d}.%"
            cursor.execute("SELECT statusz FROM jelenleti_adatok WHERE dolgozo_id=? AND datum LIKE ? LIMIT 1", (self.dolgozo_id, month_pattern))
            j_res = cursor.fetchone()
            
            if not j_res or j_res[0] not in ["kesz", "mentve"]: continue

            statusz = j_res[0]
            cursor.execute("SELECT * FROM berszamitas WHERE dolgozo_id=? AND ev=? AND honap=? AND torles_ideje IS NULL", 
                           (self.dolgozo_id, self.valasztott_ev.get(), idx))
            ber_res = cursor.fetchone()

            bg_c, fg_c = ("#DCFCE7", "#166534") if ber_res else (("#FEF9C3", "#854D0E") if statusz == "kesz" else ("#F1F5F9", "#64748B"))
            
            f = tk.Frame(racs_cont, bg="#F8FAFC")
            f.grid(row=(idx-1)//4, column=(idx-1)%4, padx=10, pady=10, sticky="nsew")
            racs_cont.grid_columnconfigure((idx-1)%4, weight=1)

            box = tk.Frame(f, bg=bg_c, highlightbackground="#CBD5E1", highlightthickness=1)
            box.pack(fill="both", expand=True)

            tk.Label(box, text=h_nevek[idx-1].upper(), font=("Segoe UI", 11, "bold"), bg=bg_c, fg=fg_c, pady=5).pack()
            
            info_text = f"Állapot: {statusz.upper()}"
            if ber_res:
                info_text += f"\nNettó: {int(ber_res['netto_ber']):,} Ft".replace(",", " ")
            
            tk.Label(box, text=info_text, font=("Segoe UI", 8), bg=bg_c, fg="#1E293B", pady=5, justify="center").pack()

            btn_zone = tk.Frame(f, bg="#F8FAFC", pady=5)
            btn_zone.pack(fill="x")

            if statusz == "kesz":
                if ber_res:
                    tk.Button(btn_zone, text="VÁZLAT", command=lambda m=idx: self.mutat_osszesito(m), bg="white", font=("Segoe UI", 8, "bold")).pack(fill="x", pady=1)
                    tk.Button(btn_zone, text="ÚJRASZÁMOL", command=lambda m=idx: self.ujraszamolas(m), bg="#E0F2FE", font=("Segoe UI", 8)).pack(fill="x", pady=1)
                    tk.Button(btn_zone, text="TÖRÖL", command=lambda m=idx: self.torol_szamitas(m), bg="#FEE2E2", fg="#991B1B", font=("Segoe UI", 8)).pack(fill="x", pady=1)
                else:
                    tk.Button(btn_zone, text="SZÁMFEJTÉS", command=lambda m=idx: self.indit_szamitas(m), bg="#1E293B", fg="white", font=("Segoe UI", 9, "bold")).pack(fill="x", pady=5)
            else:
                tk.Label(btn_zone, text="Lezáratlan ív", font=("Segoe UI", 7, "italic"), bg="#F8FAFC", fg="#64748B").pack()

        conn.close()
        
        footer_bar = tk.Frame(self, bg="#F1F5F9", pady=15, highlightbackground="#CBD5E1", highlightthickness=1)
        footer_bar.pack(side="bottom", fill="x")
        
        def megnyit_eves_jelentesek():
            # Példányosítjuk a generátort az adatbázis elérési útjával
            generator = AnnualReportGenerator(DB_PATH)
            # Meghívjuk a GUI-val rendelkező ablakkezelőt
            # Átadjuk: (szülő_ablak, dolgozó_id, választott_év)
            generator.open_management_window(self, self.dolgozo_id, self.valasztott_ev.get())

        tk.Button(footer_bar, 
                  text="📊  ÉVES BÉRÜGYI KIMUTATÁSOK ÉS ARCHÍVUM", 
                  command=megnyit_eves_jelentesek,
                  bg="#0F172A", 
                  fg="white", 
                  font=("Segoe UI", 11, "bold"), 
                  padx=40, 
                  pady=10,
                  cursor="hand2",
                  relief="flat").pack(anchor="center")

    def get_szabi_status(self, db_path, dolgozo_id, ev, honap):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT alapszabi, gyerekszabi FROM munkavallalok WHERE id=?", (dolgozo_id,))
            m = cursor.fetchone()
            eves_keret_ora = ((m[0] or 0) + (m[1] or 0)) * 8
            
            cursor.execute("""
                SELECT SUM(szabadsag_ora) FROM berszamitas 
                WHERE dolgozo_id=? AND ev=? AND honap < ? AND torles_ideje IS NULL
            """, (dolgozo_id, ev, honap))
            korabbi_felhasznalt = cursor.fetchone()[0] or 0
            
            minta = f"{ev}.{honap:02d}.%"
            cursor.execute("""
                SELECT COUNT(*) FROM jelenleti_adatok 
                WHERE dolgozo_id=? AND datum LIKE ? AND tipus='Szabadság'
            """, (dolgozo_id, minta))
            targyi_ora = (cursor.fetchone()[0] or 0) * 8
            
            nyito_egyenleg = eves_keret_ora - korabbi_felhasznalt
            zaro_egyenleg = nyito_egyenleg - targyi_ora
            conn.close()
            return float(targyi_ora), float(zaro_egyenleg)
        except Exception as e:
            print(f"Hiba a szabadság lekérdezésekor: {e}")
            return 0.0, 0.0
    
    def indit_szamitas(self, honap):
        try:
            szamitas_vegrehajtasa(DB_PATH, self.dolgozo_id, self.valasztott_ev.get(), honap, self.get_szabi_status)
            esemeny_naplozas(f"Bérszámfejtés: {honap}. hó", self.dolgozo_nev)
            self.setup_ui()
        except Exception as e:
            self.attributes("-topmost", False)
            messagebox.showerror("Hiba", str(e))
            self.attributes("-topmost", True)

    def ujraszamolas(self, honap):
        self.attributes("-topmost", False)
        if messagebox.askyesno("Megerősítés", f"Biztosan újra szeretné számolni a {honap}. havi bért?"):
            self.indit_szamitas(honap)
        self.attributes("-topmost", True)

    def torol_szamitas(self, honap):
        self.attributes("-topmost", False)
        if messagebox.askyesno("Megerősítés", f"Biztosan törli a {honap}. havi számítást?"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
                cursor.execute("UPDATE berszamitas SET torles_ideje=? WHERE dolgozo_id=? AND ev=? AND honap=? AND torles_ideje IS NULL",
                               (most, self.dolgozo_id, self.valasztott_ev.get(), honap))
                conn.commit()
                conn.close()
                self.setup_ui()
            except Exception as e:
                messagebox.showerror("Hiba", str(e))
        self.attributes("-topmost", True)

    def mutat_osszesito(self, honap):
        self.attributes("-topmost", False)
        top = tk.Toplevel(self)
        top.title(f"Összesítő - {self.valasztott_ev.get()}. {honap}. hó")
        top.geometry("750x920")
        top.configure(bg="white")
        top.protocol("WM_DELETE_WINDOW", lambda: [self.attributes("-topmost", True), top.destroy()])

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Biztonsági ellenőrzés az új oszlopra
        cursor.execute("PRAGMA table_info(berszamitas)")
        cols = [info['name'] for info in cursor.fetchall()]
        if 'extra_tetelek_reszletezve' not in cols:
            cursor.execute("ALTER TABLE berszamitas ADD COLUMN extra_tetelek_reszletezve TEXT")
            conn.commit()

        cursor.execute("SELECT * FROM berszamitas WHERE dolgozo_id=? AND ev=? AND honap=? AND torles_ideje IS NULL", 
                       (self.dolgozo_id, self.valasztott_ev.get(), honap))
        r = cursor.fetchone()
        
        if not r:
            conn.close()
            top.destroy()
            return

        tk.Label(top, text=self.dolgozo_nev.upper(), font=("Segoe UI", 14, "bold"), bg="white", pady=15).pack()
        
        h_frame = tk.Frame(top, bg="#F1F5F9", height=35)
        h_frame.pack(fill="x", padx=40, pady=(10, 5))
        headers = [("MEGNEVEZÉS", 30, "w"), ("IDŐ (óra)", 12, "c"), ("EGYSÉGDÍJ", 12, "c"), ("ÖSSZEG", 18, "e")]
        for t, w, a in headers:
            tk.Label(h_frame, text=t, font=("Segoe UI", 9, "bold"), bg="#F1F5F9", width=w, anchor=a).pack(side="left", padx=2)

        # Alap szekciók (Az Extra tételeket kivettük innen, mert lentebb tételesezzük)
        szekciok = [
            ("MUNKABÉR ÉS PÓTLÉKOK", [
                ("Alapbér", "alapber_ora", "alapber_oradij", "alapber_osszeg"),
                ("Készenlét", "keszenlet_ora", "keszenlet_oradij", "keszenlet_osszeg"),
                ("FIX/Adható bérkieg.", None, "adhato_oradij", "adhato_osszeg"),
                ("Műszakpótlék (30%)", "potlekos_ora", "muszakpotlek_oradij", "muszakpotlek_osszeg"),
                ("Túlóra (50%)", "tulora50_ora", "tulora50_oradij", "tulora50_osszeg"),
                ("Túlóra (100%)", "tulora100_ora", "tulora100_oradij", "tulora100_osszeg"),
            ]),
            ("TÁVOLLÉTEK ÉS ÜNNEPEK", [
                ("Szabadság", "szabadsag_ora", "szabadsag_oradij", "szabadsag_osszeg"),
                ("Fizetett ünnep", "fizetett_unnep_ora", "fizetett_unnep_oradij", "fizetett_unnep_osszeg"),
                ("Ünnepnapi munkavégzés", "unnep_ledolgozott_ora", "unnepnap_munkaber_oradij", "unnepnapi_munkaber_osszeg"),
                ("Ünnepnapi pótlék (100%)", "unnep_ledolgozott_ora", "munkaszuneti_munkavegzes_oradij", "munkaszuneti_munkavegzes_osszeg"),
            ]),
            ("BETEGSÉG ÉS BALESET", [
                ("Betegszabadság (70%)", "beteg_70_ora", "beteg_70_oradij", "beteg_70_osszeg"),
                ("Táppénz (60%)", "beteg_60_ora", "beteg_60_oradij", "beteg_60_osszeg"),
                ("Útibaleset (90%)", "utibaleset_90_ora", "utibaleset_90_oradij", "utibaleset_90_osszeg"),
                ("MHBaleset (100%)", "mhbaleset_100_ora", "mhbaleset_100_oradij", "mhbaleset_100_osszeg"),
            ])
        ]

        for cim, elemek in szekciok:
            szekcio_latszik = False
            for _, _, _, s_kulcs in elemek:
                if s_kulcs in r.keys() and r[s_kulcs] and r[s_kulcs] != 0:
                    szekcio_latszik = True
                    break
            
            if szekcio_latszik:
                tk.Label(top, text=cim, font=("Segoe UI", 8, "bold"), bg="#F8FAFC", fg="#64748B", anchor="w", padx=45).pack(fill="x", pady=(10, 2))
                for nev, m_kulcs, e_kulcs, s_kulcs in elemek:
                    osszeg = r[s_kulcs] if s_kulcs and s_kulcs in r.keys() and r[s_kulcs] else 0
                    if osszeg == 0: continue
                    
                    egyseg = r[e_kulcs] if e_kulcs and e_kulcs in r.keys() and r[e_kulcs] else 0
                    mennyiseg = r[m_kulcs] if m_kulcs and m_kulcs in r.keys() and r[m_kulcs] else 0
                    if not mennyiseg and egyseg > 0: mennyiseg = osszeg / egyseg

                    f = tk.Frame(top, bg="white")
                    f.pack(fill="x", padx=45, pady=2)
                    tk.Label(f, text=nev, bg="white", font=("Segoe UI", 10), width=30, anchor="w").pack(side="left")
                    tk.Label(f, text=f"{float(mennyiseg):.1f}" if mennyiseg else "", bg="white", font=("Segoe UI", 10), width=12).pack(side="left")
                    tk.Label(f, text=f"{int(egyseg):,}".replace(",", " ") if egyseg else "", bg="white", font=("Segoe UI", 10), width=12).pack(side="left")
                    tk.Label(f, text=f"{int(osszeg):,}".replace(",", " "), bg="white", font=("Segoe UI", 10, "bold"), width=18, anchor="e").pack(side="right")

        # --- DINAMIKUS EXTRA TÉTELEK MEGJELENÍTÉSE ---
        reszletezes = r["extra_tetelek_reszletezve"]
        if reszletezes:
            tk.Label(top, text="EXTRA TÉTELEK ÉS LEVONÁSOK (TÉTELES)", font=("Segoe UI", 8, "bold"), bg="#F8FAFC", fg="#64748B", anchor="w", padx=45).pack(fill="x", pady=(10, 2))
            
            tetelek = reszletezes.split(";")
            for tetel in tetelek:
                if not tetel or "|" not in tetel: continue
                # Szétszedés: Megnevezés|Típus|Összeg|Adóköteles(1/0)
                adatok = tetel.split("|")
                if len(adatok) >= 3:
                    nev_megj = adatok[0]
                    t_tipus = adatok[1]
                    t_osszeg = float(adatok[2])
                    is_adomentes = " (Adómentes)" if len(adatok) > 3 and adatok[3] == "0" else ""
                    
                    prefix = "-" if t_tipus == "LEVONAS" else "+"
                    szin = "#991B1B" if t_tipus == "LEVONAS" else "#166534"

                    f = tk.Frame(top, bg="white")
                    f.pack(fill="x", padx=45, pady=2)
                    tk.Label(f, text=f"{nev_megj}{is_adomentes}", bg="white", font=("Segoe UI", 10), width=30, anchor="w").pack(side="left")
                    tk.Label(f, text="", bg="white", width=12).pack(side="left")
                    tk.Label(f, text="", bg="white", width=12).pack(side="left")
                    tk.Label(f, text=f"{prefix} {int(t_osszeg):,}".replace(",", " "), bg="white", font=("Segoe UI", 10, "bold"), fg=szin, width=18, anchor="e").pack(side="right")

        # --- SZABADSÁG-EGYENLEG ---
        try:
            cursor.execute("SELECT alapszabi, gyerekszabi FROM munkavallalok WHERE id=?", (self.dolgozo_id,))
            m_adat = cursor.fetchone()
            eves_keret_ora = ((m_adat[0] or 0) + (m_adat[1] or 0)) * 8
            cursor.execute("SELECT SUM(szabadsag_ora) FROM berszamitas WHERE dolgozo_id=? AND ev=? AND honap < ? AND torles_ideje IS NULL", (self.dolgozo_id, self.valasztott_ev.get(), honap))
            korabbi_felhasznalt = cursor.fetchone()[0] or 0
            aktualis_felhasznalt = r["szabadsag_ora"] or 0
            nyito_ora = eves_keret_ora - korabbi_felhasznalt
            zaro_ora = nyito_ora - aktualis_felhasznalt
        except:
            nyito_ora = aktualis_felhasznalt = zaro_ora = 0
        finally:
            conn.close()

        f_szabi_keret = tk.Frame(top, bg="#F8FAFC", pady=10, highlightbackground="#CBD5E1", highlightthickness=1)
        f_szabi_keret.pack(fill="x", padx=40, pady=(15, 10))
        tk.Label(f_szabi_keret, text="SZABADSÁG ELSZÁMOLÁS", font=("Segoe UI", 8, "bold"), bg="#F8FAFC", fg="#64748B").pack()
        
        for c, v, s in [("Hó eleji nyitó egyenleg:", f"{nyito_ora/8:.1f} nap", "#475569"), ("Tárgyhavi felhasználás:", f"- {aktualis_felhasznalt/8:.1f} nap", "#991B1B"), ("Hó végi záró egyenleg:", f"{zaro_ora/8:.1f} nap", "#166534")]:
            fs = tk.Frame(f_szabi_keret, bg="#F8FAFC")
            fs.pack(fill="x", padx=20, pady=1)
            tk.Label(fs, text=c, bg="#F8FAFC", font=("Segoe UI", 9)).pack(side="left")
            tk.Label(fs, text=v, bg="#F8FAFC", font=("Segoe UI", 9, "bold"), fg=s).pack(side="right")

        # --- ÖSSZESÍTŐK ---
        tk.Frame(top, height=2, bg="#F1F5F9").pack(fill="x", padx=40, pady=5)
        totals = [
            ("Munkábajárás támogatás", r["munkabajaras_osszeg"] or 0, "black"),
            ("BRUTTÓ JÁRANDÓSÁG", r["brutto_osszesen"] or 0, "#1E293B"),
            ("SZJA levonás (15%)", r["szja"] or 0, "#991B1B"),
            ("TB járulék (18.5%)", r["tb_jarulek"] or 0, "#991B1B"),
            ("NETTÓ KIFIZETENDŐ", r["netto_ber"] or 0, "#166534")
        ]
        
        for nev, ertek, szin in totals:
            f = tk.Frame(top, bg="white")
            f.pack(fill="x", padx=40, pady=3)
            is_netto = "NETTÓ" in nev
            tk.Label(f, text=nev, bg="white", font=("Segoe UI", 11, "bold"), fg=szin).pack(side="left")
            tk.Label(f, text=f"{int(ertek):,}".replace(",", " ") + " Ft", bg="white", font=("Segoe UI", 14 if is_netto else 11, "bold"), fg=szin).pack(side="right")
            
        tk.Button(top, text="BEZÁRÁS", command=lambda: [self.attributes("-topmost", True), top.destroy()], bg="#1E293B", fg="white", font=("Segoe UI", 11, "bold"), pady=12).pack(side="bottom", fill="x", padx=40, pady=20)