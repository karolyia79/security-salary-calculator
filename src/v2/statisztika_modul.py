import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class StatisztikaModul:
    def __init__(self, parent, dolgozo_adatok):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Statisztika - {dolgozo_adatok['nev']}")
        self.window.state('zoomed')
        self.window.configure(bg="#F8FAFC")
        
        # Ablak prioritás
        self.window.attributes("-topmost", True)
        
        self.dolgozo = dolgozo_adatok
        self.db_path = "berszamitas.db"
        
        # --- ÁLLAPOTVÁLTOZÓK ---
        self.stat_tipus = tk.StringVar(value="ber")  
        self.diagram_tipus = tk.StringVar(value="bar") 
        self.elemzes_mod = tk.StringVar(value="pont") # pontszerű vagy intervallum
        self.idoszak_a = tk.StringVar()
        self.idoszak_b = tk.StringVar()
        self.chk_vars = {}
        
        self.setup_ui()
        self.load_months()

    def setup_ui(self):
        # Fejléc
        header = tk.Frame(self.window, bg="#1E293B", height=70)
        header.pack(fill="x")
        
        header_text = f"STATISZTIKAI ELEMZÉS: {self.dolgozo['nev']} | Szül: {self.dolgozo['szul_datum']}"
        tk.Label(header, text=header_text, fg="white", bg="#1E293B", 
                 font=("Segoe UI", 16, "bold")).pack(pady=15)

        # Bal oldali vezérlőpult
        sidebar = tk.Frame(self.window, bg="#F1F5F9", width=300, padx=20, pady=20)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="Elemzés fókusza:", bg="#F1F5F9", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Radiobutton(sidebar, text="Bér jellegű adatok", variable=self.stat_tipus, 
                       value="ber", command=self.refresh_checkboxes).pack(anchor="w", pady=2)
        ttk.Radiobutton(sidebar, text="Munkaügyi adatok", variable=self.stat_tipus, 
                       value="munka", command=self.refresh_checkboxes).pack(anchor="w", pady=2)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)

        # Elemzési mód választó
        tk.Label(sidebar, text="Elemzési mód:", bg="#F1F5F9", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Radiobutton(sidebar, text="Két időpont összehasonlítása", variable=self.elemzes_mod, value="pont").pack(anchor="w")
        ttk.Radiobutton(sidebar, text="Időszak (A és B között)", variable=self.elemzes_mod, value="intervallum").pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)

        # Diagram típus választó
        tk.Label(sidebar, text="Diagram típusa:", bg="#F1F5F9", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Radiobutton(sidebar, text="Oszlopdiagram", variable=self.diagram_tipus, value="bar").pack(anchor="w")
        ttk.Radiobutton(sidebar, text="Vonalgrafikon", variable=self.diagram_tipus, value="line").pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)

        # Időszak választók
        tk.Label(sidebar, text="Vizsgált időszak (A):", bg="#F1F5F9", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.cb_a = ttk.Combobox(sidebar, textvariable=self.idoszak_a, state="readonly")
        self.cb_a.pack(fill="x", pady=5)

        tk.Label(sidebar, text="Záró / Összehasonlító (B):", bg="#F1F5F9", font=("Segoe UI", 10)).pack(anchor="w")
        self.cb_b = ttk.Combobox(sidebar, textvariable=self.idoszak_b, state="readonly")
        self.cb_b.pack(fill="x", pady=5)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=15)

        self.chk_container = tk.Frame(sidebar, bg="#F1F5F9")
        self.chk_container.pack(fill="x", pady=5)
        self.refresh_checkboxes()

        ttk.Button(sidebar, text="📊 GRAFIKON GENERÁLÁSA", command=self.generate_plot).pack(fill="x", pady=25)
        
        ttk.Button(sidebar, text="Bezárás", command=self.window.destroy).pack(fill="x", side="bottom")

        # Jobb oldali tartalom
        self.main_content = tk.Frame(self.window, bg="white")
        self.main_content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.plot_frame = tk.Frame(self.main_content, bg="white")
        self.plot_frame.pack(fill="both", expand=True)

        self.summary_frame = tk.LabelFrame(self.main_content, text="Számszerűsített Összehasonlítás", 
                                          bg="white", font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        self.summary_frame.pack(fill="x", side="bottom")
        
        self.summary_text = tk.Label(self.summary_frame, text="Válasszon ki időszakokat az elemzéshez.", 
                                    bg="white", font=("Segoe UI", 11), justify="left")
        self.summary_text.pack(anchor="w")

    def refresh_checkboxes(self):
        for widget in self.chk_container.winfo_children():
            widget.destroy()
        
        self.chk_vars = {}
        if self.stat_tipus.get() == "ber":
            options = [("Nettó bér", "netto_ber"), ("Bruttó összesen", "brutto_osszesen"), 
                       ("Alapbér", "alap_osszeg"), ("Műszakpótlék", "muszakpotlek_osszeg")]
        else:
            options = [("Összes ledolgozott óra", "osszes_ledolgozott_ora"), 
                       ("Pótlékos órák", "potlekos_ora"), ("Szabadság óra", "szabadsag_ora")]

        for label, key in options:
            self.chk_vars[key] = tk.BooleanVar(value=True if "netto" in key or "osszes" in key else False)
            tk.Checkbutton(self.chk_container, text=label, variable=self.chk_vars[key], bg="#F1F5F9").pack(anchor="w")

    def load_months(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""SELECT DISTINCT ev, honap FROM berszamitas 
                              WHERE dolgozo_id = ? AND torles_ideje IS NULL 
                              ORDER BY ev ASC, honap ASC""", (self.dolgozo['id'],))
            
            rows = cursor.fetchall()
            evek_honapok = [f"{row[0]}.{row[1]:02d}" for row in rows]
            self.cb_a['values'] = evek_honapok[::-1] 
            self.cb_b['values'] = ["Nincs"] + evek_honapok[::-1]
            conn.close()
        except Exception as e:
            print(f"Hiba a hónapok betöltésekor: {e}")

    def get_data_by_period(self, period_str):
        if not period_str or period_str == "Nincs": return None
        try:
            ev, honap = map(int, period_str.split('.'))
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM berszamitas 
                              WHERE dolgozo_id = ? AND ev = ? AND honap = ? 
                              AND torles_ideje IS NULL""", (self.dolgozo['id'], ev, honap))
            res = cursor.fetchone()
            conn.close()
            return res
        except Exception as e:
            print(f"Lekérdezési hiba: {e}")
            return None

    def get_range_data(self, start_str, end_str):
        try:
            s_ev, s_honap = map(int, start_str.split('.'))
            e_ev, e_honap = map(int, end_str.split('.'))
            if (s_ev > e_ev) or (s_ev == e_ev and s_honap > e_honap):
                s_ev, e_ev = e_ev, s_ev
                s_honap, e_honap = e_honap, s_honap

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM berszamitas 
                              WHERE dolgozo_id = ? AND torles_ideje IS NULL 
                              AND (ev * 100 + honap) BETWEEN ? AND ?
                              ORDER BY ev ASC, honap ASC""", 
                           (self.dolgozo['id'], s_ev * 100 + s_honap, e_ev * 100 + e_honap))
            res = cursor.fetchall()
            conn.close()
            return res
        except: return []

    def generate_plot(self):
        active_keys = [k for k, v in self.chk_vars.items() if v.get()]
        if not active_keys: return

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Módosított méretezés és tight_layout a jobb illeszkedésért
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        report = ""
        suffix = " Ft" if self.stat_tipus.get() == "ber" else " óra"

        if self.elemzes_mod.get() == "pont" or self.idoszak_b.get() == "Nincs":
            data_a = self.get_data_by_period(self.idoszak_a.get())
            data_b = self.get_data_by_period(self.idoszak_b.get())
            if not data_a: return

            vals_a = [float(data_a[k] or 0) for k in active_keys]
            x_labels = [k.replace('_', ' ').capitalize() for k in active_keys]
            x = range(len(active_keys))

            if self.diagram_tipus.get() == "bar":
                width = 0.35
                rects1 = ax.bar([i - width/2 for i in x] if data_b else x, vals_a, width, label=self.idoszak_a.get(), color='#3B82F6')
                for r in rects1: ax.annotate(f'{r.get_height():,.0f}', xy=(r.get_x()+r.get_width()/2, r.get_height()), xytext=(0,3), textcoords="offset points", ha='center', fontweight='bold', fontsize=8)
                if data_b:
                    vals_b = [float(data_b[k] or 0) for k in active_keys]
                    rects2 = ax.bar([i + width/2 for i in x], vals_b, width, label=self.idoszak_b.get(), color='#94A3B8')
                    for r in rects2: ax.annotate(f'{r.get_height():,.0f}', xy=(r.get_x()+r.get_width()/2, r.get_height()), xytext=(0,3), textcoords="offset points", ha='center', fontweight='bold', fontsize=8)
            else:
                ax.plot(x_labels, vals_a, marker='o', label=self.idoszak_a.get(), color='#3B82F6')
                for i, v in enumerate(vals_a): ax.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontweight='bold', fontsize=8)
                if data_b:
                    vals_b = [float(data_b[k] or 0) for k in active_keys]
                    ax.plot(x_labels, vals_b, marker='s', label=self.idoszak_b.get(), color='#94A3B8')
                    for i, v in enumerate(vals_b): ax.text(i, v, f'{v:,.0f}', ha='center', va='top', fontweight='bold', fontsize=8)

            report = f"Összehasonlítás: {self.idoszak_a.get()}" + (f" vs {self.idoszak_b.get()}\n" if data_b else "\n")
            for k in active_keys:
                v_a = float(data_a[k] or 0)
                if data_b:
                    v_b = float(data_b[k] or 0)
                    diff = v_a - v_b
                    pc = (diff / v_b * 100) if v_b != 0 else 0
                    report += f"• {k.replace('_',' ').capitalize()}: {v_a:,.0f}{suffix} (Kül: {diff:+,.0f} | {pc:+,.1f}%)\n"
                else: report += f"• {k.replace('_',' ').capitalize()}: {v_a:,.0f}{suffix}\n"

        else:
            range_data = self.get_range_data(self.idoszak_a.get(), self.idoszak_b.get())
            if not range_data: return
            
            x_labels = [f"{d['ev']}.{d['honap']:02d}" for d in range_data]
            for key in active_keys:
                vals = [float(d[key] or 0) for d in range_data]
                label_name = key.replace('_', ' ').capitalize()
                if self.diagram_tipus.get() == "bar":
                    ax.bar(x_labels, vals, label=label_name, alpha=0.7)
                else:
                    ax.plot(x_labels, vals, marker='o', label=label_name)
                for i, v in enumerate(vals): ax.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
            
            report = f"Időszak elemzése: {x_labels[0]} - {x_labels[-1]}\n"
            for key in active_keys:
                vals = [float(d[key] or 0) for d in range_data]
                report += f"• {key.replace('_',' ').capitalize()}: Átlag: {sum(vals)/len(vals):,.0f}{suffix} | Max: {max(vals):,.0f}{suffix}\n"

        ax.set_title("Statisztikai Kimutatás")
        ax.legend()
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right") # Elforgatás a jobb olvashatóságért
        fig.tight_layout() # Automatizált elrendezés
        
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.summary_text.config(text=report)