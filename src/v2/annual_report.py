import sqlite3
import os
import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

class AnnualReportGenerator:
    def __init__(self, db_path):
        self.db_path = db_path
        self.base_dir = "Munkavallalo_Dokumentumok"

    def _get_save_path(self, ceg_nev, dolgozo_nev):
        """
        Szigorú útvonal: Munkavallo_Dokumentumok / Cégnév / Dolgozó_neve / Kimutatasok
        A szóközöket mindenhol "_" karakterre cseréljük.
        """
        ceg_mappa = ceg_nev.replace(" ", "_")
        dolgozo_mappa = dolgozo_nev.replace(" ", "_")
        kimutatasok_mappa = "Kimutatások"
        
        path = os.path.join(self.base_dir, ceg_mappa, dolgozo_mappa, kimutatasok_mappa)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def open_management_window(self, parent, dolgozo_id, ev):
        """Megnyitja a jelentéskezelő ablakot listával és funkciókkal."""
        top = tk.Toplevel(parent)
        top.title(f"Éves összesítők kezelése - {ev}")
        top.geometry("750x500")
        top.configure(bg="white")
        top.transient(parent)
        top.grab_set()

        # Adatok lekérése a korábban rögzített adatbázis-struktúra szerint
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.nev, c.ceg_neve 
            FROM munkavallalok m 
            LEFT JOIN cegek c ON m.munkaltato_id = c.ID_ceg 
            WHERE m.id=?
        """, (dolgozo_id,))
        info = cursor.fetchone()
        conn.close()

        ceg_nev = info['ceg_neve'] if info and info['ceg_neve'] else "Ismeretlen_Ceg"
        d_nev = info['nev'] if info else "Ismeretlen_Dolgozo"
        mentesi_hely = self._get_save_path(ceg_nev, d_nev)

        tk.Label(top, text=f"ÉVES ÖSSZESÍTŐK: {d_nev} ({ev})", 
                 font=("Segoe UI", 12, "bold"), bg="white", fg="#1E293B").pack(pady=10)

        # Táblázatos listázás
        columns = ("file_name", "date", "full_path")
        tree = ttk.Treeview(top, columns=columns, show="headings", height=12)
        tree.heading("file_name", text="Fájlnév")
        tree.heading("date", text="Létrehozva")
        tree.column("file_name", width=450)
        tree.column("date", width=150)
        tree.column("full_path", width=0, stretch=tk.NO)
        tree.pack(padx=20, pady=10, fill="both", expand=True)

        def frissit_lista():
            for item in tree.get_children():
                tree.delete(item)
            if os.path.exists(mentesi_hely):
                for f in sorted(os.listdir(mentesi_hely), reverse=True):
                    if f.endswith(".pdf") and f.startswith(str(ev)):
                        full_p = os.path.join(mentesi_hely, f)
                        ctime = os.path.getctime(full_p)
                        dt = datetime.fromtimestamp(ctime).strftime('%Y.%m.%d %H:%M')
                        tree.insert("", "end", values=(f, dt, full_p))

        def fajat_megnyit(event=None):
            selected = tree.selection()
            if selected:
                fpath = tree.item(selected[0])['values'][2]
                if os.path.exists(fpath):
                    os.startfile(fpath)

        def fajl_torles():
            """A kijelölt PDF fájl törlése a meghajtóról és a listából."""
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Figyelem", "Válassz ki egy fájlt a törléshez!", parent=top)
                return
            
            fajl_nev = tree.item(selected[0])['values'][0]
            fpath = tree.item(selected[0])['values'][2]
            
            if messagebox.askyesno("Megerősítés", f"Biztosan törölni szeretnéd ezt a fájlt?\n\n{fajl_nev}", parent=top):
                try:
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        frissit_lista()
                except Exception as e:
                    messagebox.showerror("Hiba", f"Nem sikerült a törlés: {e}", parent=top)

        tree.bind("<Double-1>", fajat_megnyit)

        def uj_generalas_es_frissites():
            # Itt is parent=top-ot használunk majd a generáló metóduson belül
            path = self.generate_annual_pdf(dolgozo_id, ev, ceg_nev, d_nev, top)
            if path:
                frissit_lista()
                for item in tree.get_children():
                    if tree.item(item)['values'][0] == os.path.basename(path):
                        tree.selection_set(item)
                        fajat_megnyit()
                        break

        # Gombok kezelése
        btn_frame = tk.Frame(top, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=20)

        tk.Button(btn_frame, text="➕ ÚJ ÉVES ÖSSZESÍTŐ GENERÁLÁSA", 
                  command=uj_generalas_es_frissites, 
                  bg="#166534", fg="white", font=("Segoe UI", 9, "bold"), padx=15).pack(side="left")
        
        tk.Button(btn_frame, text="📂 MEGNYITÁS", 
                  command=fajat_megnyit, 
                  bg="#1E293B", fg="white", font=("Segoe UI", 9), padx=15).pack(side="left", padx=10)

        tk.Button(btn_frame, text="🗑️ TÖRLÉS", 
                  command=fajl_torles, 
                  bg="#991B1B", fg="white", font=("Segoe UI", 9), padx=15).pack(side="right")

        frissit_lista()

    def generate_annual_pdf(self, dolgozo_id, ev, ceg_nev, d_nev, top_window):
        """Kiszámolja az éves bérösszeget és PDF-et generál a kért könyvtárba."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(brutto_osszesen) as ossz_brutto, 
                   SUM(netto_ber) as ossz_netto 
            FROM berszamitas 
            WHERE dolgozo_id=? AND ev=? AND torles_ideje IS NULL
        """, (dolgozo_id, ev))
        res = cursor.fetchone()
        conn.close()

        if not res or res['ossz_brutto'] is None:
            messagebox.showwarning("Hiba", f"Nincs rögzített bérszámítás a {ev} year-ben!", parent=top_window)
            return None

        mentesi_utvonal = self._get_save_path(ceg_nev, d_nev)
        most = datetime.now()
        idobelyeg = most.strftime('%Y%m%d_%H%M')
        base_name = f"{ev}_{ceg_nev}_{d_nev}_{idobelyeg}".replace(" ", "_")
        
        version = 1
        full_path = os.path.join(mentesi_utvonal, f"{base_name}_v{version}.pdf")
        
        # Felülírási metódus verziókezeléssel
        while os.path.exists(full_path):
            valasz = messagebox.askyesnocancel(
                "Fájl létezik", 
                f"A fájl már létezik: {os.path.basename(full_path)}\n\n"
                "IGEN: Felülírás\n"
                "NEM: Új verzió mentése (v2, v3...)\n"
                "MÉGSE: Megszakítás",
                parent=top_window
            )
            
            if valasz is True:
                break
            elif valasz is False:
                version += 1
                full_path = os.path.join(mentesi_utvonal, f"{base_name}_v{version}.pdf")
            else:
                return None

        # PDF elkészítése csak az éves bruttó/nettó adatokkal
        c = canvas.Canvas(full_path, pagesize=A4)
        szelt, magt = A4

        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(szelt/2, magt - 60, f"ÉVES KERESETI ÖSSZESÍTŐ - {ev}")
        
        c.setFont("Helvetica", 12)
        c.drawString(70, magt - 110, f"Munkáltató: {ceg_nev}")
        c.drawString(70, magt - 130, f"Munkavállaló: {d_nev}")
        
        c.setLineWidth(1)
        c.rect(60, magt - 230, 480, 75)
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(80, magt - 190, "Éves teljes BRUTTÓ bér:")
        c.drawRightString(520, magt - 190, f"{int(res['ossz_brutto']):,} Ft".replace(",", " "))
        
        c.drawString(80, magt - 215, "Éves teljes NETTÓ kifizetés:")
        c.drawRightString(520, magt - 215, f"{int(res['ossz_netto']):,} Ft".replace(",", " "))
        
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(60, magt - 260, f"Generálás időpontja: {most.strftime('%Y.%m.%d %H:%M')}")
        
        c.save()
        return full_path