import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import unicodedata
import json

# PDF generáláshoz szükséges importok
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from extra_appendix import ExtraAppendixGenerator

# Betűtípus regisztrálása az ékezetes karakterekhez
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Italic', 'ariali.ttf'))
    FONT_NORMAL = "Arial"
    FONT_BOLD = "Arial-Bold"
    FONT_ITALIC = "Arial-Italic"
except:
    FONT_NORMAL = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_ITALIC = "Helvetica-Oblique"

class BerlapModul:
    def __init__(self, parent, dolgozo_adatok):
        print("\n" + "="*60)
        print(f"DEBUG: BerlapModul inicializálása")
        print(f"DEBUG: Dolgozó adatok: {dolgozo_adatok}")
        print("="*60)
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Bérlap generálása - {dolgozo_adatok['nev']}")
        self.window.geometry("1050x850")
        self.window.configure(bg="#F1F5F9")
        
        self.window.attributes("-topmost", True)
        
        self.dolgozo = dolgozo_adatok
        self.dolgozo_id = dolgozo_adatok['id']
        self.valasztott_ev = tk.IntVar(value=datetime.now().year)
        self.aktualis_ev_ertek = self.valasztott_ev.get()

        # Fejléc
        self.header_frame = tk.Frame(self.window, bg="#1E293B", height=80)
        self.header_frame.pack(fill="x")
        
        header_text = f"Bérlap: {self.dolgozo['nev']} | Szül: {self.dolgozo['szul_datum']}"
        tk.Label(self.header_frame, text=header_text, fg="white", bg="#1E293B", 
                 font=("Segoe UI", 14, "bold")).pack(pady=15)

        # Évválasztó
        self.filter_frame = tk.Frame(self.window, bg="#F1F5F9", pady=10)
        self.filter_frame.pack(fill="x")
        
        tk.Label(self.filter_frame, text="Válasszon évet:", bg="#F1F5F9", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(40, 10))
        
        self.btn_prev = tk.Button(self.filter_frame, text="◀", bg="#64748B", fg="white", 
                                  relief="flat", command=self.elozo_ev)
        self.btn_prev.pack(side="left", padx=5)
        
        self.ev_label = tk.Label(self.filter_frame, text=str(self.aktualis_ev_ertek), 
                                  bg="white", font=("Segoe UI", 11, "bold"), width=6, relief="sunken")
        self.ev_label.pack(side="left", padx=5)
        
        self.btn_next = tk.Button(self.filter_frame, text="▶", bg="#64748B", fg="white", 
                                  relief="flat", command=self.kovetkezo_ev)
        self.btn_next.pack(side="left", padx=5)

        self.info_label = tk.Label(self.window, text="Ha KÉSZ a bérlap státusza, dupla kattintással megnyitható!", 
                                   fg="#3B82F6", bg="#F1F5F9", font=("Segoe UI", 10, "italic bold"))
        self.info_label.pack(fill="x", padx=40, pady=(10, 0))

        # Táblázat
        self.table_container = tk.Frame(self.window, bg="white", relief="ridge", borderwidth=1)
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(5, 20))

        columns = ("honap", "netto", "brutto", "kivalaszthato", "berlap")
        self.tree = ttk.Treeview(self.table_container, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("honap", text="Hónap")
        self.tree.heading("netto", text="Nettó bér")
        self.tree.heading("brutto", text="Bruttó bér")
        self.tree.heading("kivalaszthato", text="Kiválasztható")
        self.tree.heading("berlap", text="Bérlap")

        self.tree.tag_configure("ervenyes", background="#DCFCE7") 
        self.tree.tag_configure("nincs_adat", background="#F1F5F9", foreground="#94A3B8") 
        self.tree.tag_configure("egyeb", background="#FEF9C3") 

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.pdf_megnyitasa_dupla_kattintassal)
        
        self.tablazat_frissitese()

        # Alsó gombok
        self.button_bar = tk.Frame(self.window, bg="#F1F5F9", padx=20, pady=20)
        self.button_bar.pack(fill="x", side="bottom")

        self.btn_torles = tk.Button(self.button_bar, text="🗑️ Törlés", bg="#64748B", fg="white",
                                    font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                    relief="flat", cursor="hand2", command=self.adatok_torlese)
        self.btn_torles.pack(side="left")

        self.btn_osszes_ujra = tk.Button(self.button_bar, text="🔄 Összes újragenerálása", bg="#F59E0B", fg="white",
                                         font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                         relief="flat", cursor="hand2", command=self.osszes_ujrageneralsa)
        self.btn_osszes_ujra.pack(side="left", padx=(10, 0))

        self.btn_bezaras = tk.Button(self.button_bar, text="Bezárás", bg="#EF4444", fg="white",
                                     font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                     relief="flat", cursor="hand2", command=self.window.destroy)
        self.btn_bezaras.pack(side="right", padx=(10, 0))

        self.btn_pdf = tk.Button(self.button_bar, text="📄 PDF generálása", bg="#3B82F6", fg="white",
                                 font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                 relief="flat", cursor="hand2", command=self.pdf_generalas)
        self.btn_pdf.pack(side="right")

        self.btn_nyomtatas = tk.Button(self.button_bar, text="🖨️ Nyomtatás", bg="#10B981", fg="white",
                                       font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                       relief="flat", cursor="hand2", command=self.pdf_nyomtatas)
        self.btn_nyomtatas.pack(side="right", padx=(10, 0))

    def ekezentmentesit(self, szoveg):
        if not szoveg: return ""
        nfkd_form = unicodedata.normalize('NFKD', szoveg)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace(" ", "_")

    def get_munkaltato_nev(self):
        try:
            conn = sqlite3.connect('berszamitas.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.ceg_neve 
                FROM cegek c 
                JOIN munkavallalok m ON c.ID_ceg = m.munkaltato_id 
                WHERE m.id = ?
            """, (self.dolgozo['id'],))
            res = cursor.fetchone()
            conn.close()
            if res:
                return self.ekezentmentesit(res[0])
            return "Ismeretlen_Ceg"
        except Exception as e:
            print(f"DEBUG: Hiba a munkáltató lekérésekor: {e}")
            return "Ismeretlen_Ceg"

    def get_mentes_utvonal(self):
        munkaltato = self.get_munkaltato_nev()
        dolgozo = self.ekezentmentesit(self.dolgozo['nev'])
        path = os.path.join("Munkavallalo_Berlapok", munkaltato, dolgozo)
        return path

    def elozo_ev(self):
        self.aktualis_ev_ertek -= 1
        self.ev_label.config(text=str(self.aktualis_ev_ertek))
        self.tablazat_frissitese()

    def kovetkezo_ev(self):
        self.aktualis_ev_ertek += 1
        self.ev_label.config(text=str(self.aktualis_ev_ertek))
        self.tablazat_frissitese()

    def tablazat_frissitese(self):
        print(f"DEBUG: Táblázat frissítése - Év: {self.aktualis_ev_ertek}, ID: {self.dolgozo['id']}")
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        honapok = ["Január", "Február", "Március", "Április", "Május", "Június", 
                   "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        
        try:
            conn = sqlite3.connect('berszamitas.db')
            cursor = conn.cursor()
            
            for index, honap_nev in enumerate(honapok, start=1):
                cursor.execute("""SELECT netto_ber, brutto_osszesen, torles_ideje, letrehozas_datuma, utolso_modositas 
                                  FROM berszamitas 
                                  WHERE dolgozo_id = ? AND ev = ? AND honap = ?""", 
                               (self.dolgozo['id'], self.aktualis_ev_ertek, index))
                
                adat = cursor.fetchone()
                statusz = ""
                tag = ""
                netto_megjelenit = "-"
                brutto_megjelenit = "-"
                
                pdf_mappa = self.get_mentes_utvonal()
                berlap_statusz = "NINCS"
                if os.path.exists(pdf_mappa):
                    fajlok = os.listdir(pdf_mappa)
                    honap_prefix = f"{self.aktualis_ev_ertek}_{index:02d}"
                    if any(fajl.endswith(".pdf") and f"_{honap_prefix}_" in self.ekezentmentesit(fajl) for fajl in fajlok):
                        berlap_statusz = "KÉSZ"

                if adat:
                    netto, brutto, torles, letrehozas, modositas = adat
                    if not torles and (letrehozas or modositas):
                        statusz = "IGEN"
                        tag = "ervenyes"
                        netto_megjelenit = f"{int(round(netto)):,} Ft" if netto is not None else "0 Ft"
                        brutto_megjelenit = f"{int(round(brutto)):,} Ft" if brutto is not None else "0 Ft"
                    else:
                        statusz = "NEM"
                        tag = "egyeb"
                else:
                    statusz = "NINCS BÉRSZÁMFEJTVE"
                    tag = "nincs_adat"

                self.tree.insert("", "end", values=(honap_nev, netto_megjelenit, brutto_megjelenit, statusz, berlap_statusz), tags=(tag,))

            conn.close()
        except sqlite3.Error as e:
            print(f"DEBUG: SQL hiba a frissítésnél: {e}")
            self.window.attributes("-topmost", False)
            messagebox.showerror("Adatbázis hiba", f"Nem sikerült az adatok lekérése: {e}")
            self.window.attributes("-topmost", True)

    def pdf_motor(self, honap_szam, honap_nev, open_file=True):
        print("\n" + "#"*40)
        print(f"DEBUG: PDF GENERÁLÁS INDÍTÁSA - {honap_nev}")
        print("#"*40)
        try:
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
                f_norm, f_bold = 'DejaVuSans', 'DejaVuSans-Bold'
            except:
                f_norm, f_bold = 'Helvetica', 'Helvetica-Bold'

            mentes_utvonal = self.get_mentes_utvonal()
            honap_prefix = f"{self.aktualis_ev_ertek}_{honap_szam:02d}"
            
            # Régi fájlok törlése
            if os.path.exists(mentes_utvonal):
                fajlok = os.listdir(mentes_utvonal)
                for f in fajlok:
                    if f.endswith(".pdf") and f"_{honap_prefix}_" in self.ekezentmentesit(f):
                        try: 
                            os.remove(os.path.join(mentes_utvonal, f))
                        except Exception as e: 
                            print(f"DEBUG: Törlési hiba: {e}")

            conn = sqlite3.connect('berszamitas.db')
            conn.row_factory = sqlite3.Row # Ez fontos, hogy névvel érjük el az oszlopokat
            cursor = conn.cursor()
            
            # Cég adatok (global_beallitasok-ból)
            cursor.execute("SELECT ceg_nev, szekhely FROM global_beallitasok LIMIT 1")
            g_adat = cursor.fetchone()
            ceg_nev = g_adat['ceg_nev'] if g_adat else "Cégnév"
            ceg_cim = g_adat['szekhely'] if g_adat else "Székhely"

            # Dolgozó adatok
            cursor.execute("SELECT nev, szul_ido, dolgozoszam, beosztas, adoszam FROM munkavallalok WHERE id = ?", (self.dolgozo['id'],))
            mv_dict = cursor.fetchone()

            # 1. Lekérjük az adatokat az adatbázisból
            cursor.execute("""
                SELECT * FROM berszamitas 
                WHERE dolgozo_id = ? AND ev = ? AND honap = ? 
                AND torles_ideje IS NULL
            """, (self.dolgozo['id'], self.aktualis_ev_ertek, honap_szam))
            
            # Ez a sor hozza létre a 'res' változót!
            res = cursor.fetchone()

            # Ellenőrizzük, hogy találtunk-e adatot
            if not res:
                print(f"DEBUG: Nem található béradat: ID:{self.dolgozo['id']}, {self.aktualis_ev_ertek}.{honap_szam}")
                return False
            
            # Most már definiálva van a 'res', így a konverzió működni fog
            # Ez csinál valódi szótárat (dict), amin már működik a .get() metódus
            ber_dict = dict(zip([d[0] for d in cursor.description], res))
            
            # Szabadság számítás
            cursor.execute("SELECT alapszabi, gyerekszabi FROM munkavallalok WHERE id=?", (self.dolgozo['id'],))
            m_adat = cursor.fetchone()
            eves_keret_ora = ((m_adat['alapszabi'] or 0) + (m_adat['gyerekszabi'] or 0)) * 8

            cursor.execute("""
                SELECT SUM(szabadsag_ora) FROM berszamitas 
                WHERE dolgozo_id=? AND ev=? AND honap < ? AND torles_ideje IS NULL
            """, (self.dolgozo['id'], self.aktualis_ev_ertek, honap_szam))
            korabbi_felhasznalt = cursor.fetchone()[0] or 0
            aktualis_szabi_felhasznalt = ber_dict["szabadsag_ora"] or 0
            nyito_szabi_ora = eves_keret_ora - korabbi_felhasznalt
            zaro_szabi_ora = nyito_szabi_ora - aktualis_szabi_felhasznalt

            def format_pdf_szabi(ora):
                nap = round(ora / 8, 1)
                return f"{float(ora):.1f} óra ({nap} nap)"

            # Jelenléti adatok kigyűjtése a naptárhoz
            naptar_adatok = {}
            beteg_ora_osszesen = 0
            datum_kereses = f"{self.aktualis_ev_ertek}.{honap_szam:02d}%"
            cursor.execute("""
                SELECT datum, m_ora, tipus, t_ora, k_ora, unnep, m_kez, m_veg 
                FROM jelenleti_adatok 
                WHERE dolgozo_id = ? AND datum LIKE ?
            """, (self.dolgozo['id'], datum_kereses))
            
            for row in cursor.fetchall():
                d_str = row['datum']
                reszek = [r for r in d_str.split('.') if r]
                if len(reszek) >= 3:
                    nap = int(reszek[2])
                    info = {"alap": "-", "tul": "-", "kesz": "-", "un": ""}
                    potlek_jelzo = ""
                    if row['m_kez'] and row['m_veg']:
                        try:
                            k_ora = int(row['m_kez'].split(':')[0])
                            v_ora = int(row['m_veg'].split(':')[0])
                            if k_ora >= 18 or v_ora > 18 or v_ora < k_ora: potlek_jelzo = "P"
                        except: pass
                    if row['m_ora'] and row['m_ora'] > 0:
                        rov = {"Ledolgozott": "L", "Szabadság": "SZ", "Beteg": "B", "MHBaleset": "MHB", "Uti baleset": "UTB", "Ünnep": "Ü"}.get(row['tipus'], "L")
                        if row['unnep'] == 1 and row['tipus'] == "Ledolgozott": rov = "ÜL"
                        info["alap"] = f"{int(row['m_ora'])}{rov}{potlek_jelzo}"
                        if row['tipus'] == 'Beteg': beteg_ora_osszesen += row['m_ora']
                    if row['t_ora'] and row['t_ora'] > 0: info["tul"] = f"{int(row['t_ora'])}T"
                    if row['k_ora'] and row['k_ora'] > 0: info["kesz"] = f"{int(row['k_ora'])}K"
                    if row['unnep'] == 1: info["un"] = "ÜNN"
                    naptar_adatok[nap] = info
            conn.close()

            if not os.path.exists(mentes_utvonal): os.makedirs(mentes_utvonal)
            most = datetime.now()
            tiszta_nev = self.ekezentmentesit(self.dolgozo['nev'])
            file_path = os.path.join(mentes_utvonal, f"{tiszta_nev}_{self.aktualis_ev_ertek}_{honap_szam:02d}_{most.strftime('%Y%m%d_%H%M%S')}.pdf")

            c = canvas.Canvas(file_path, pagesize=A4)
            szelt, magt = A4
            c.setFont(f_bold, 12); c.drawString(50, magt - 40, ceg_nev)
            c.setFont(f_norm, 9); c.drawString(50, magt - 52, ceg_cim)
            c.drawRightString(szelt - 50, magt - 40, f"BÉRJEGYZÉK: {self.aktualis_ev_ertek}. {honap_nev}")
            
            # Dolgozó adatok keret
            c.roundRect(50, magt - 110, 500, 45, 4, stroke=1)
            c.setFont(f_bold, 10); c.drawString(60, magt - 82, f"Név: {mv_dict['nev']}")
            c.setFont(f_norm, 9)
            c.drawString(60, magt - 98, f"Szül: {mv_dict['szul_ido'] or '-'}")
            c.drawString(170, magt - 98, f"D.szám: {mv_dict['dolgozoszam'] or '-'}")
            c.drawString(280, magt - 98, f"Beosztás: {mv_dict['beosztas'] or '-'}")
            c.drawString(420, magt - 98, f"Adó: {mv_dict['adoszam'] or '-'}")

            # --- TÉTELES FELSOROLÁS ÖSSZEÁLLÍTÁSA ---
            data = [["MEGNEVEZÉS", "ÓRA / ALAP", "EGYSÉGDÍJ", "ÖSSZEG"]]
            
            # 1. FIX TÉTELEK (Ezek maradnak felül)
            fix_tetelek = [
                ("Alapbér", "osszes_ledolgozott_ora", "alapber_oradij", "alapber_osszeg"),
                ("FIX/Adható bérkieg.", "alap_ora_korrigalt", "adhato_oradij", "adhato_osszeg"),
                ("Műszakpótlék (30%)", "potlekos_ora", "muszakpotlek_oradij", "muszakpotlek_osszeg"),
                ("Készenlét", "keszenlet_ora", "keszenlet_oradij", "keszenlet_osszeg"),
                ("Túlóra (50%)", "tulora50_ora", "tulora50_oradij", "tulora50_osszeg"),
                ("Túlóra (100%)", "tulora100_ora", "tulora100_oradij", "tulora100_osszeg"),
                ("Fizetett ünnep", "fizetett_unnep_ora", "fizetett_unnep_oradij", "fizetett_unnep_osszeg"),
                ("Ünnepnapi munkavégzés", "unnep_ledolgozott_ora", "unnepnap_munkaber_oradij", "unnepnapi_munkaber_osszeg"),
                ("Ünnepnapi pótlék (100%)", "unnep_ledolgozott_ora", "munkaszuneti_munkavegzes_oradij", "munkaszuneti_munkavegzes_osszeg"),
                ("Szabadság", "szabadsag_ora", "szabadsag_oradij", "szabadsag_osszeg"),
                ("Betegszabadság (70%)", "beteg_70_ora", "beteg_70_oradij", "beteg_70_osszeg"),
                ("Táppénz (60%)", "beteg_60_ora", "beteg_60_oradij", "beteg_60_osszeg"),
                ("Munkábajárás", None, None, "munkabajaras_osszeg")
            ]
            
            for nev, o_kulcs, d_kulcs, s_kulcs in fix_tetelek:
                osszeg = ber_dict.get(s_kulcs, 0)
                if osszeg and float(osszeg) != 0:
                    o_val = ber_dict.get(o_kulcs) if o_kulcs else None
                    ora = f"{float(o_val):.1f}" if o_val is not None and str(o_val).strip() != "" and float(o_val) != 0 else "-"
                    d_val = ber_dict.get(d_kulcs) if d_kulcs else None
                    dij = f"{int(float(d_val)):,} Ft" if d_val is not None and str(d_val).strip() != "" and float(d_val) != 0 else "-"
                    data.append([nev, ora, dij, f"{int(float(osszeg)):,} Ft"])

            # 2. EXTRA TÉTELEK SZÉTVÁLOGATÁSA (Pozitív vs Negatív)
            pozitiv_extrak = []
            negativ_extrak = []
            
            reszletezes_raw = ber_dict.get('extra_tetelek_reszletezve', "")
            if reszletezes_raw:
                try:
                    entries = [e.strip() for e in str(reszletezes_raw).split(';') if e.strip()]
                    for entry in entries:
                        if '|' in entry:
                            resz = entry.split('|')
                            if len(resz) >= 3:
                                nev_ex = resz[0].strip()
                                tipus_ex = resz[1].strip() # LEVONAS vagy EXTRA
                                try:
                                    ertek_ex = float(resz[2].strip())
                                    if ertek_ex == 0: continue
                                    
                                    # Az 'ÓRA / ALAP' oszlopba (sor[1]) kerül a típus megnevezése
                                    megjelenitett_irany = "Kifizetés" if tipus_ex == "EXTRA" else "Levonás"
                                    
                                    # Adózási info (ha a 4. paraméter tartalmazza, pl. 1 vagy 0)
                                    # Alapértelmezés: ha nincs megadva, EXTRA -> Adózott, LEVONAS -> Adómentes
                                    ado_info = "Adóköteles" if tipus_ex == "EXTRA" else "Adómentes"
                                    if len(resz) >= 4:
                                        ado_info = "Adóköteles" if resz[3].strip() == "1" else "Adómentes"

                                    sor = [nev_ex, megjelenitett_irany, ado_info, f"{'-' if tipus_ex == 'LEVONAS' else ''}{int(abs(ertek_ex)):,} Ft"]                                    
                                    if tipus_ex == "LEVONAS":
                                        negativ_extrak.append(sor)
                                    else:
                                        pozitiv_extrak.append(sor)
                                except: continue
                except Exception as e:
                    print(f"DEBUG: Hiba az extra tételek feldolgozásakor: {e}")

            # Sorrend összeállítása: Fixek -> Pozitív extra -> Negatív extra -> SZJA/TB
            for s in pozitiv_extrak:
                data.append(s)
            
            for s in negativ_extrak:
                data.append(s)

            idx_kifizetesek_vege = len(data)
            
            # Kormányzati levonások (SZJA, TB)
            szja = ber_dict['szja'] or 0
            tb = ber_dict['tb_jarulek'] or 0
            data.append(["SZJA levonás (15%)", "", "", f"-{int(szja):,} Ft"])
            data.append(["Társadalombiztosítás (18.5%)", "", "", f"-{int(tb):,} Ft"])
            
            idx_osszesitok = len(data)
            data.append(["BRUTTÓ ÖSSZESEN", "", "", f"{int(ber_dict['brutto_osszesen']):,} Ft"])
            data.append(["NETTÓ KIFIZETENDŐ", "", "", f"{int(ber_dict['netto_ber']):,} Ft"])

            # Táblázat formázása
            t1 = Table(data, colWidths=[180, 80, 110, 130])
            
            munkabajaras_index = 0
            for i, row in enumerate(data):
                if row[0] == "Munkábajárás":
                    munkabajaras_index = i
                    break
            
            t1.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (3,0), (3,-1), 'RIGHT'),
                ('GRID', (0,0), (-1, idx_kifizetesek_vege - 1), 0.5, colors.grey),
                ('LINEBELOW', (0, munkabajaras_index), (-1, munkabajaras_index), 1.5, colors.black),
                ('LINEABOVE', (0, idx_kifizetesek_vege), (-1, idx_kifizetesek_vege), 1.5, colors.black),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('FONTNAME', (0,0), (-1,-1), f_norm),
                ('FONTNAME', (0, idx_osszesitok), (-1, -1), f_bold),
                ('TEXTCOLOR', (3, idx_kifizetesek_vege), (3, idx_osszesitok-1), colors.red),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
            ]))

            tabla_magassag = len(data) * 18
            y_pos = magt - 130 - tabla_magassag
            t1.wrapOn(c, 50, 400); t1.drawOn(c, 50, y_pos)

            # --- SZABADSÁG RÉSZ ---
            y_pos -= 65 # Kisebb helykihagyás a fenti táblázat után
            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            c.setFillColor(colors.HexColor("#F8FAFC"))
            # Szélesség 500-ról 350-re csökkentve, középre igazítva (125-nél kezdődik)
            c.roundRect(125, y_pos, 350, 60, 4, fill=1)
            
            c.setFillColor(colors.HexColor("#64748B"))
            c.setFont(f_bold, 8)
            c.drawCentredString(300, y_pos + 48, "SZABADSÁG ELSZÁMOLÁS")
            
            c.setFont(f_norm, 9); c.setFillColor(colors.HexColor("#1E293B"))
            c.drawString(140, y_pos + 32, "Hó eleji nyitó egyenleg:")
            c.drawRightString(460, y_pos + 32, format_pdf_szabi(nyito_szabi_ora))
            c.drawString(140, y_pos + 20, "Tárgyhavi felhasználás:")
            c.drawRightString(460, y_pos + 20, f"- {format_pdf_szabi(aktualis_szabi_felhasznalt)}")
            c.drawString(140, y_pos + 8, "Hó végi záró egyenleg:")
            c.setFillColor(colors.HexColor("#166534")); c.setFont(f_bold, 9)
            c.drawRightString(460, y_pos + 8, format_pdf_szabi(zaro_szabi_ora))

            # --- NAPTÁR RÉSZ (FEJLÉC NÉLKÜL ÉS SŰRŰBBEN) ---
            y_pos -= 15 # Minimális szünet a szabadság blokk után
            
            def create_detail_cal(start, end):
                num_days = (end - start + 1)
                h_nap = ["Nap"] + [str(i) for i in range(start, end + 1)]
                h_munka = ["Alap"] + [naptar_adatok.get(i, {}).get("alap", "-") for i in range(start, end + 1)]
                h_tul = ["Túlóra"] + [naptar_adatok.get(i, {}).get("tul", "-") for i in range(start, end + 1)]
                h_kesz = ["Kész."] + [naptar_adatok.get(i, {}).get("kesz", "-") for i in range(start, end + 1)]
                h_un = ["Ünnep"] + [naptar_adatok.get(i, {}).get("un", "-") for i in range(start, end + 1)]
                col_w = [40] + [460/num_days] * num_days
                t = Table([h_nap, h_munka, h_tul, h_kesz, h_un], colWidths=col_w, rowHeights=[15]*5)
                t.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTSIZE', (0,0), (-1,-1), 7), ('FONTNAME', (0,0), (-1,-1), f_norm),
                    ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F1F5F9")),
                    ('BACKGROUND', (1,0), (-1,0), colors.HexColor("#CBD5E1")),
                    ('TEXTCOLOR', (1,4), (-1,4), colors.red), ('FONTNAME', (0,0), (-1,0), f_bold)
                ]))
                return t
            
            # Táblázatok elhelyezése (y_pos csökkentés mértéke kisebb lett a sűrítéshez)
            y_pos -= 75
            t_c1 = create_detail_cal(1, 10)
            t_c1.wrap(460, 100); t_c1.drawOn(c, 50, y_pos)
            
            y_pos -= 80
            t_c2 = create_detail_cal(11, 20)
            t_c2.wrap(460, 100); t_c2.drawOn(c, 50, y_pos)
            
            y_pos -= 80
            t_c3 = create_detail_cal(21, 31)
            t_c3.wrap(460, 100); t_c3.drawOn(c, 50, y_pos)
            
            # Lábléc maradhat a helyén
            c.setFont(f_norm, 6); c.drawString(50, y_pos - 15, "Jelmagyarázat: L: Ledolgozott, ÜL: Ünnepi munka, Ü: Fizetett ünnep, SZ: Szabi, B: Beteg, MHB/UTB: Baleset, T: Túlóra, K: Készenlét, P: Műszakpótlék")
            
            # Lábléc
            c.setFont(f_norm, 6); c.drawString(50, y_pos - 15, "Jelmagyarázat: L: Ledolgozott, ÜL: Ünnepi munka, Ü: Fizetett ünnep, SZ: Szabi, B: Beteg, MHB/UTB: Baleset, T: Túlóra, K: Készenlét, P: Műszakpótlék")
            c.setFont(f_norm, 7); c.drawCentredString(szelt/2, 30, "Ez a bérlap a 'Security Bérkalkulátor' rendszerrel készült.")
            c.drawRightString(szelt - 50, 20, f"Készítés ideje: {most.strftime('%Y.%m.%d %H:%M:%S')}")
            self.db_path = 'berszamitas.db'
            app_gen = ExtraAppendixGenerator(self.db_path)
            app_gen.general_appendix(c, self.dolgozo, self.aktualis_ev_ertek, honap_nev, honap_szam)
            c.save()
            
            if open_file: os.startfile(file_path)
            return True
        except Exception as e:
            print(f"DEBUG: KRITIKUS HIBA A PDF MOTORBAN: {e}")
            import traceback
            traceback.print_exc()
            return False

    def pdf_generalas(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.window.attributes("-topmost", False)
            messagebox.showwarning("Figyelem", "Kérjük, válasszon ki egy hónapot a listából!")
            self.window.attributes("-topmost", True)
            return

        values = self.tree.item(selected_item)['values']
        if values[3] != "IGEN":
            self.window.attributes("-topmost", False)
            messagebox.showwarning("Figyelem", f"A(z) {values[0]} hónap nincs bérszámfejtve!")
            self.window.attributes("-topmost", True)
            return

        honap_nev = values[0]
        honapok_lista = ["Január", "Február", "Március", "Április", "Május", "Június", 
                         "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        honap_szam = honapok_lista.index(honap_nev) + 1

        if values[4] == "KÉSZ":
            self.window.attributes("-topmost", False)
            if not messagebox.askyesno("Megerősítés", f"Ehhez a hónaphoz ({honap_nev}) már készült PDF. Felülírja?"):
                self.window.attributes("-topmost", True)
                return
            self.window.attributes("-topmost", True)

        self.pdf_motor(honap_szam, honap_nev, open_file=True)
        self.tablazat_frissitese()

    def osszes_ujrageneralsa(self):
        igen_sorok = []
        for child in self.tree.get_children():
            values = self.tree.item(child)['values']
            if values[3] == "IGEN":
                igen_sorok.append(values)

        if not igen_sorok:
            self.window.attributes("-topmost", False)
            messagebox.showinfo("Információ", "Nincs bérszámfejtett hónap ezen az oldalon.")
            self.window.attributes("-topmost", True)
            return

        self.window.attributes("-topmost", False)
        kerdes = messagebox.askyesno("Megerősítés", 
            f"Biztosan újra szeretné generálni az összes ({len(igen_sorok)} db) bérszámfejtett bérlapot?\n\n"
            "A korábbi PDF verziók törlésre kerülnek!")
        
        if kerdes:
            honapok_lista = ["Január", "Február", "Március", "Április", "Május", "Június", 
                             "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
            sikeres = 0
            for sor in igen_sorok:
                honap_nev = sor[0]
                honap_szam = honapok_lista.index(honap_nev) + 1
                if self.pdf_motor(honap_szam, honap_nev, open_file=False):
                    sikeres += 1
            
            self.tablazat_frissitese()
            messagebox.showinfo("Kész", f"Generálás befejeződött.\nSikeres: {sikeres}/{len(igen_sorok)}")
        
        self.window.attributes("-topmost", True)

    def pdf_megnyitasa_dupla_kattintassal(self, event):
        selected_item = self.tree.selection()
        if not selected_item: return
        values = self.tree.item(selected_item)['values']
        if values[4] != "KÉSZ": return
        honap_nev = values[0]
        honapok_lista = ["Január", "Február", "Március", "Április", "Május", "Június", 
                         "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        honap_szam = honapok_lista.index(honap_nev) + 1
        try:
            mentes_utvonal = self.get_mentes_utvonal()
            if os.path.exists(mentes_utvonal):
                honap_prefix = f"{self.aktualis_ev_ertek}_{honap_szam:02d}"
                fajlok = os.listdir(mentes_utvonal)
                for fajl in fajlok:
                    if fajl.endswith(".pdf") and f"_{honap_prefix}_" in self.ekezentmentesit(fajl):
                        os.startfile(os.path.normpath(os.path.join(mentes_utvonal, fajl)))
                        return
        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült megnyitni: {e}")

    def adatok_torlese(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.window.attributes("-topmost", False)
            messagebox.showwarning("Figyelem", "Válasszon ki egy bérlapot!")
            self.window.attributes("-topmost", True)
            return
        values = self.tree.item(selected_item)['values']
        honap_nev = values[0]
        honapok_lista = ["Január", "Február", "Március", "Április", "Május", "Június", 
                         "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        honap_szam = honapok_lista.index(honap_nev) + 1
        self.window.attributes("-topmost", False)
        if messagebox.askyesno("Megerősítés", f"Törli a(z) {honap_nev} havi PDF-et?"):
            try:
                mentes_utvonal = self.get_mentes_utvonal()
                if os.path.exists(mentes_utvonal):
                    honap_prefix = f"{self.aktualis_ev_ertek}_{honap_szam:02d}"
                    for f in os.listdir(mentes_utvonal):
                        if f.endswith(".pdf") and f"_{honap_prefix}_" in self.ekezentmentesit(f):
                            os.remove(os.path.join(mentes_utvonal, f))
                self.tablazat_frissitese()
            except Exception as e:
                messagebox.showerror("Hiba", f"Hiba: {e}")
        self.window.attributes("-topmost", True)

    def pdf_nyomtatas(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.window.attributes("-topmost", False)
            messagebox.showwarning("Figyelem", "Válasszon ki egy bérlapot!")
            self.window.attributes("-topmost", True)
            return
        values = self.tree.item(selected_item)['values']
        if values[4] != "KÉSZ": return
        honap_nev = values[0]
        honapok_lista = ["Január", "Február", "Március", "Április", "Május", "Június", 
                         "Július", "Augusztus", "Szeptember", "Október", "November", "December"]
        honap_szam = honapok_lista.index(honap_nev) + 1
        try:
            mentes_utvonal = self.get_mentes_utvonal()
            if os.path.exists(mentes_utvonal):
                honap_prefix = f"{self.aktualis_ev_ertek}_{honap_szam:02d}"
                for fajl in os.listdir(mentes_utvonal):
                    if fajl.endswith(".pdf") and f"_{honap_prefix}_" in self.ekezentmentesit(fajl):
                        full_path = os.path.normpath(os.path.join(mentes_utvonal, fajl))
                        try: os.startfile(full_path, "print")
                        except: os.startfile(full_path)
                        return
        except Exception as e:
            self.window.attributes("-topmost", False)
            messagebox.showerror("Hiba", f"Hiba: {str(e)}")
            self.window.attributes("-topmost", True)
    