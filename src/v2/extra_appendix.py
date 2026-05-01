import sqlite3
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4

# Betűtípusok beállítása (a berlapok.py-val azonosan)
try:
    FONT_NORMAL = "Arial"
    FONT_BOLD = "Arial-Bold"
except:
    FONT_NORMAL = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

class ExtraAppendixGenerator:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_kifizetett_osszeg(self, dolgozo_id, tetel_nev):
        """Kiszámolja a múltbéli adatokat a JSON cellák alapján."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        osszegzes = 0
        try:
            cursor.execute("SELECT extra_tetelek_reszletezve FROM berszamitas WHERE dolgozo_id = ?", (dolgozo_id,))
            for (json_adat,) in cursor.fetchall():
                if not json_adat: continue
                reszletek = json_adat.split(';')
                for reszlet in reszletek:
                    if '|' not in reszlet: continue
                    adatok = reszlet.split('|')
                    if len(adatok) < 4: continue
                    
                    m_nev = adatok[0]
                    m_tipus = adatok[1]
                    try:
                        m_ertek = int(adatok[2])
                        m_statusz = adatok[3]
                    except: continue
                    
                    if tetel_nev in m_nev:
                        if m_tipus == "LEVONAS":
                            osszegzes += m_ertek
                        elif m_tipus == "EXTRA" and m_statusz == "1":
                            osszegzes += m_ertek
            return osszegzes
        finally:
            conn.close()

    def general_appendix(self, c, dolgozo_id, aktualis_ev, honap_nev, honap_szam):
        """Új oldalra generálja a függeléket, de csak ha van rögzített mozgás az adott hónapban."""
        if isinstance(dolgozo_id, dict):
            dolgozo_id = dolgozo_id.get('id')

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. ELLENŐRZÉS: Csak az adott évi és hónapi számfejtést nézzük
        # Az utolsó (legnagyobb ID-jú) számítást vesszük figyelembe
        cursor.execute("""
            SELECT extra_tetelek_reszletezve 
            FROM berszamitas 
            WHERE dolgozo_id = ? AND ev = ? AND honap = ?
            ORDER BY id DESC LIMIT 1
        """, (dolgozo_id, aktualis_ev, honap_szam))
        
        havi_sor = cursor.fetchone()
        
        if not havi_sor:
            conn.close()
            return False

        # 2. TARTALMI SZŰRÉS: Van-e benne tényleges összeg?
        havi_adat = str(havi_sor['extra_tetelek_reszletezve'] or "").strip()
        van_aktiv_tetel = False
        
        if havi_adat and '|' in havi_adat:
            reszletek = havi_adat.split(';')
            for r in reszletek:
                darabok = r.split('|')
                if len(darabok) >= 3:
                    try:
                        # Ha bármelyik tétel értéke > 0, akkor kell a függelék
                        if int(darabok[2]) > 0:
                            van_aktiv_tetel = True
                            break
                    except:
                        continue

        if not van_aktiv_tetel:
            conn.close()
            return False

        # 3. HA IDÁIG ELJUTOTT, AKKOR GENERÁLUNK
        cursor.execute("SELECT * FROM munkavallalok WHERE id = ?", (dolgozo_id,))
        mv = cursor.fetchone()
        
        cursor.execute("SELECT ceg_nev, szekhely FROM global_beallitasok LIMIT 1")
        ceg = cursor.fetchone()
        ceg_nev = ceg['ceg_nev'] if ceg else "A-WAY ZRT."
        ceg_cim = ceg['szekhely'] if ceg else "Újhartyán"

        # Törzs adatok a hátralékokhoz
        datum_iso = f"{aktualis_ev}-{honap_szam:02d}-01"
        cursor.execute("""
            SELECT tipus, megnevezes, teljes_osszeg, osszeg 
            FROM extra_tetelek 
            WHERE dolgozo_id = ? AND (lejarat >= ? OR lejarat IS NULL OR lejarat = '')
        """, (dolgozo_id, datum_iso))
        tetelek = [dict(row) for row in cursor.fetchall()]
        
        if not tetelek:
            conn.close()
            return False

        tetelek.sort(key=lambda x: (0 if x['tipus'] == "EXTRA" else 1, x['megnevezes'].lower()))

        c.showPage()
        szelt, magt = A4
        c.setFont(FONT_BOLD, 12)
        c.drawString(50, magt - 40, ceg_nev)
        c.setFont(FONT_NORMAL, 9)
        c.drawString(50, magt - 52, ceg_cim)
        c.drawRightString(szelt - 50, magt - 40, f"BÉRLAP FÜGGELÉK: {aktualis_ev}. {honap_nev}")

        c.setStrokeColor(colors.black)
        c.roundRect(50, magt - 110, 500, 45, 4, stroke=1)
        c.setFont(FONT_BOLD, 10)
        c.drawString(60, magt - 82, f"Név: {mv['nev']}")
        c.setFont(FONT_NORMAL, 9)
        c.drawString(60, magt - 98, f"Szül: {mv['szul_ido'] or '-'}")
        c.drawString(170, magt - 98, f"D.szám: {mv['dolgozoszam'] or '-'}")
        c.drawString(280, magt - 98, f"Beosztás: {mv['beosztas'] or '-'}")
        c.drawString(420, magt - 98, f"Adó: {mv['adoszam'] or '-'}")

        data = [["MEGNEVEZÉS", "TÍPUS", "TELJES Ö.", "HAVI", "RENDEZVE", "HÁTRALÉK", "MÚLT", "HÁTRA"]]
        import math
        for t in tetelek:
            nev = t['megnevezes']
            raw_tipus = t['tipus']
            t_osszeg = t['teljes_osszeg'] or 0
            havi = t['osszeg'] or 0
            megjelenitett_tipus = "Kifizetés" if raw_tipus == "EXTRA" else "Levonás"
            rendezve = self.get_kifizetett_osszeg(dolgozo_id, nev)
            hatralek = max(0, t_osszeg - rendezve)
            mult_ho = int(rendezve / havi) if havi > 0 else 0
            hatra_ho = math.ceil(hatralek / havi) if havi > 0 else 0
            
            data.append([
                nev.upper(), megjelenitett_tipus,
                f"{int(t_osszeg):,}".replace(',', ' '),
                f"{int(havi):,}".replace(',', ' '),
                f"{int(rendezve):,}".replace(',', ' '),
                f"{int(hatralek):,}".replace(',', ' '),
                f"{mult_ho} hó", f"{hatra_ho} hó"
            ])

        t_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (5,-1), 'RIGHT'),
            ('ALIGN', (6,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTNAME', (0,1), (-1,-1), FONT_NORMAL),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ])

        table = Table(data, colWidths=[130, 60, 65, 45, 65, 65, 35, 35])
        table.setStyle(t_style)
        tabla_magassag = len(data) * 20
        y_pos = magt - 130 - tabla_magassag
        table.wrapOn(c, 50, 400)
        table.drawOn(c, 50, y_pos)

        c.setFont(FONT_NORMAL, 7)
        c.drawCentredString(szelt/2, 30, "Ez a dokumentum a Security Bérkalkulátor hátralékkezelő függeléke.")

        conn.close()
        return True