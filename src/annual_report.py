import sqlite3
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class AnnualReportGenerator:
    def __init__(self, db_path):
        self.db_path = db_path

    def generate_annual_pdf(self, dolgozo_id, ev, mentési_utvonal):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Adatok lekérése
        cursor.execute("SELECT * FROM munkavallalok WHERE id=?", (dolgozo_id,))
        mv = cursor.fetchone()
        
        cursor.execute("""
            SELECT * FROM berszamitas 
            WHERE dolgozo_id=? AND ev=? AND torles_ideje IS NULL 
            ORDER BY honap ASC
        """, (dolgozo_id, ev))
        havi_adatok = cursor.fetchall()

        if not havi_adatok:
            conn.close()
            return False

        file_name = f"Eves_Elszamolas_{ev}_{mv['nev'].replace(' ', '_')}.pdf"
        full_path = f"{mentési_utvonal}/{file_name}"
        
        c = canvas.Canvas(full_path, pagesize=A4)
        szelt, magt = A4

        # Fejléc
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(szelt/2, magt - 50, f"ÉVES BÉRÜGYI ÖSSZESÍTŐ - {ev}")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, magt - 80, f"Munkavállaló: {mv['nev']}")
        c.drawString(50, magt - 95, f"Adóazonosító: {mv['adoszam'] or '-'}")

        # Táblázat adatai
        headers = ["Hónap", "Ledolg. óra", "Bruttó bér", "SZJA", "TB", "Nettó kifizetés"]
        data = [headers]
        
        t_ora, t_brutto, t_szja, t_tb, t_netto = 0, 0, 0, 0, 0
        h_nevek = ["Jan", "Feb", "Már", "Ápr", "Máj", "Jún", "Júl", "Aug", "Szep", "Okt", "Nov", "Dec"]

        for r in havi_adatok:
            h_idx = r['honap'] - 1
            brutto = r['brutto_osszesen'] or 0
            netto = r['netto_ber'] or 0
            szja = r['szja'] or 0
            tb = r['tb_jarulek'] or 0
            ora = (r['alapber_ora'] or 0) + (r['tulora50_ora'] or 0) + (r['tulora100_ora'] or 0)

            data.append([
                h_nevek[h_idx],
                f"{ora:.1f}",
                f"{int(brutto):,}".replace(",", " "),
                f"{int(szja):,}".replace(",", " "),
                f"{int(tb):,}".replace(",", " "),
                f"{int(netto):,}".replace(",", " ")
            ])
            t_ora += ora
            t_brutto += brutto
            t_szja += szja
            t_tb += tb
            t_netto += netto

        # Összesen sor
        data.append(["ÖSSZESEN", f"{t_ora:.1f}", f"{int(t_brutto):,}", f"{int(t_szja):,}", f"{int(t_tb):,}", f"{int(t_netto):,}"])

        table = Table(data, colWidths=[60, 80, 90, 80, 80, 100])
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ])
        table.setStyle(style)
        
        table.wrapOn(c, 50, 400)
        table.drawOn(c, 50, magt - 150 - (len(data)*20))

        c.save()
        conn.close()
        return full_path