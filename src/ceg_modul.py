import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

class CegModul:
    def __init__(self, parent, callback=None): # Hozzáadva: callback paraméter
        self.window = tk.Toplevel(parent)
        self.window.title("Cég kiválasztása")
        self.window.geometry("800x500")
        self.window.grab_set()
        
        self.callback = callback # Mentjük a callback függvényt
        self.window.configure(bg="#F8FAFC")
        
        # A kiválasztott cég ID-ja
        self.selected_id = None
        
        # Adatbázis inicializálása
        self.init_db()
        
        # Cím
        tk.Label(self.window, text="Válassza ki a bérszámfejtendő céget", 
                 font=("Segoe UI", 14, "bold"), bg="#F8FAFC", fg="#1E293B").pack(pady=15)
        
        # Táblázat konténer
        table_frame = tk.Frame(self.window, bg="#F8FAFC")
        table_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.columns = ("id", "cegnev", "cim", "adoszam", "cegjegyzekszam", "teljes_nev", "dolgozok")
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("cegnev", text="Cégnév")
        self.tree.heading("cim", text="Cím")
        self.tree.heading("adoszam", text="Adószám")
        self.tree.heading("cegjegyzekszam", text="Cégjegyzékszám")
        self.tree.heading("teljes_nev", text="Teljes név")
        self.tree.heading("dolgozok", text="Dolgozók")
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("cegnev", width=150)
        self.tree.column("dolgozok", width=80, anchor="center")
        
        self.tree.pack(expand=True, fill="both")
        
        # Gombok konténere
        btn_frame = tk.Frame(self.window, bg="#F8FAFC")
        btn_frame.pack(fill="x", side="bottom", pady=20)
        
        self.close_btn = ttk.Button(btn_frame, text="Bezárás", width=15, command=self.window.destroy)
        self.close_btn.pack(side="left", padx=10)

        self.add_btn = ttk.Button(btn_frame, text="Hozzáadás", width=15, command=self.add_ceg)
        self.add_btn.pack(side="left", padx=10)

        self.edit_btn = ttk.Button(btn_frame, text="Szerkesztés", width=15, command=self.edit_ceg)
        self.edit_btn.pack(side="left", padx=10)

        # Kiválasztás gomb
        self.select_btn = ttk.Button(btn_frame, text="Kiválasztás", width=15, command=self.confirm_selection)
        self.select_btn.pack(side="right", padx=20)

        self.load_data()

    def init_db(self):
        conn = sqlite3.connect("berszamitas.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cegek (
                ID_ceg INTEGER PRIMARY KEY AUTOINCREMENT,
                ceg_neve TEXT,
                cim TEXT,
                adoszam TEXT,
                cegjegyzekszam TEXT,
                teljes_nev TEXT
            )
        """)
        
        # Ellenőrizzük, hogy létezik-e a beosztasok oszlop
        cursor.execute("PRAGMA table_info(cegek)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'beosztasok' not in columns:
            cursor.execute("ALTER TABLE cegek ADD COLUMN beosztasok TEXT")
        
        conn.commit()
        conn.close()

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = sqlite3.connect("berszamitas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT ID_ceg, ceg_neve, cim, adoszam, cegjegyzekszam, teljes_nev FROM cegek")
        rows = cursor.fetchall()
        
        for row in rows:
            self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5], 0))
        conn.close()

    @staticmethod
    def betolt_cegek():
        try:
            conn = sqlite3.connect("berszamitas.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cegek")
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []

    def confirm_selection(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Figyelem", "Kérem, válasszon ki egy céget a listából!")
            return
        
        item_values = self.tree.item(selected[0])['values']
        self.selected_id = item_values[0]
        ceg_neve = item_values[1]

        if self.callback:
            adatok = {
                'ID_ceg': self.selected_id,
                'ceg_neve': ceg_neve,
                'nev': 'Nincs kiválasztott',
                'szul_datum': '-'
            }
            self.callback(adatok)

        self.window.destroy()

    def open_editor(self, data=None):
        editor = tk.Toplevel(self.window)
        editor.title("Cég adatai")
        editor.geometry("500x500")
        editor.grab_set()
        
        notebook = ttk.Notebook(editor)
        notebook.pack(expand=True, fill="both", padx=5, pady=5)
        
        # --- ALAPADATOK FÜL ---
        tab_alapadatok = tk.Frame(notebook)
        notebook.add(tab_alapadatok, text="Alapadatok")
        
        fields = ["Cég neve", "Cím", "Adószám", "Cégjegyzékszám", "Teljes név"]
        entries = {}

        for i, field in enumerate(fields):
            tk.Label(tab_alapadatok, text=field).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(tab_alapadatok, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry
            if data:
                entry.insert(0, data[i+1])

        # --- BEOSZTÁSOK FÜL ---
        tab_beosztasok = tk.Frame(notebook)
        notebook.add(tab_beosztasok, text="Beosztások")
        
        input_frame = tk.Frame(tab_beosztasok)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        beosztas_entry = ttk.Entry(input_frame)
        beosztas_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        beosztasok_list = []
        if data:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("SELECT beosztasok FROM cegek WHERE ID_ceg=?", (data[0],))
            res = cursor.fetchone()
            if res and res[0]:
                try:
                    beosztasok_list = json.loads(res[0])
                except:
                    beosztasok_list = []
            conn.close()

        def refresh_beosztas_table():
            for item in beosztas_tree.get_children():
                beosztas_tree.delete(item)
            for b in beosztasok_list:
                beosztas_tree.insert("", "end", values=(b,))

        def add_beosztas():
            val = beosztas_entry.get().strip()
            if val and val not in beosztasok_list:
                beosztasok_list.append(val)
                refresh_beosztas_table()
                beosztas_entry.delete(0, tk.END)

        ttk.Button(input_frame, text="Hozzáadás", command=add_beosztas).pack(side="right")
        
        beosztas_tree = ttk.Treeview(tab_beosztasok, columns=("megnevezes",), show="headings", height=8)
        beosztas_tree.heading("megnevezes", text="Beosztás megnevezése")
        beosztas_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        def delete_beosztas():
            sel = beosztas_tree.selection()
            if sel:
                val = beosztas_tree.item(sel[0])['values'][0]
                if val in beosztasok_list:
                    beosztasok_list.remove(val)
                refresh_beosztas_table()

        ttk.Button(tab_beosztasok, text="Törlés", command=delete_beosztas).pack(pady=5)
        refresh_beosztas_table()

        def save():
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            # Mentés JSON formátumban
            beosztasok_json = json.dumps(beosztasok_list, ensure_ascii=False)
            
            vals = (entries["Cég neve"].get(), entries["Cím"].get(), entries["Adószám"].get(), 
                    entries["Cégjegyzékszám"].get(), entries["Teljes név"].get(), beosztasok_json)
            
            if data:
                cursor.execute("""UPDATE cegek SET ceg_neve=?, cim=?, adoszam=?, 
                                  cegjegyzekszam=?, teljes_nev=?, beosztasok=? WHERE ID_ceg=?""", vals + (data[0],))
            else:
                cursor.execute("""INSERT INTO cegek (ceg_neve, cim, adoszam, cegjegyzekszam, teljes_nev, beosztasok) 
                                  VALUES (?, ?, ?, ?, ?, ?)""", vals)
            
            conn.commit()
            conn.close()
            self.load_data()
            editor.destroy()

        btn_container = tk.Frame(editor)
        btn_container.pack(fill="x", side="bottom", pady=10)
        ttk.Button(btn_container, text="Mentés", command=save).pack(side="left", padx=10)
        ttk.Button(btn_container, text="Kilépés", command=editor.destroy).pack(side="left", padx=10)

    def add_ceg(self):
        self.open_editor()

    def edit_ceg(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Figyelem", "Válasszon ki egy céget a szerkesztéshez!")
            return
        item_data = self.tree.item(selected[0])['values']
        self.open_editor(item_data)