import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class KapcsolatModul(tk.Toplevel):
    def __init__(self, parent, current_user_name="Ismeretlen", current_user_acc="user"):
        super().__init__(parent)
        self.parent = parent
        self.title("Üzenetek")
        self.geometry("800x700")
        self.configure(bg="#F1F5F9")
        self.resizable(False, False)
        
        # Ablak mindig felül logika alaphelyzetbe állítása
        self.attributes("-topmost", True)
        
        self.user_name = current_user_name
        self.user_acc = current_user_acc
        
        self.init_db()
        
        header = tk.Frame(self, bg="#1E293B", height=60)
        header.pack(fill="x")
        tk.Label(header, text="ÜZENETKEZELŐ", fg="white", bg="#1E293B", font=("Segoe UI", 14, "bold")).pack(pady=15)

        self.main_tabs = ttk.Notebook(self)
        self.tab_msg_container = tk.Frame(self.main_tabs, bg="white")
        self.tab_send = tk.Frame(self.main_tabs, bg="white")
        
        self.main_tabs.add(self.tab_msg_container, text="Üzenetek listája")
        self.main_tabs.add(self.tab_send, text="Új üzenet")
        self.main_tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.sub_tabs = ttk.Notebook(self.tab_msg_container)
        self.tab_inbox = tk.Frame(self.sub_tabs, bg="white")
        self.tab_outbox = tk.Frame(self.sub_tabs, bg="white")
        
        self.sub_tabs.add(self.tab_inbox, text="📥 Bejövő")
        self.sub_tabs.add(self.tab_outbox, text="📤 Kimenő")
        self.sub_tabs.pack(fill="both", expand=True)

        self.setup_list_tab(self.tab_inbox, "inbox")
        self.setup_list_tab(self.tab_outbox, "outbox")
        self.setup_send_tab()

    def init_db(self):
        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    recipient TEXT,
                    subject TEXT,
                    message TEXT,
                    priority INTEGER,
                    sent_at TEXT,
                    read_at TEXT,
                    replied_at TEXT
                )
            """)
            # ÚJ TÁBLA: a MINDENKI üzenetek egyéni olvasottságához
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_reads (
                    message_id INTEGER,
                    user_name TEXT,
                    read_at TEXT,
                    PRIMARY KEY (message_id, user_name)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Adatbázis hiba: {e}")

    def get_users(self):
        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, acc FROM users")
            rows = cursor.fetchall()
            conn.close()
            return [f"{row[0]} ({row[1]})" for row in rows if row[0] != self.user_name]
        except:
            return []

    def setup_list_tab(self, frame, mode):
        columns = ("id", "partner", "subject", "priority", "date", "status")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        tree.tag_configure("mindenki", foreground="#EF4444")
        
        partner_text = "Feladó" if mode == "inbox" else "Címzett"
        tree.heading("id", text="ID")
        tree.heading("partner", text=partner_text)
        tree.heading("subject", text="Tárgy")
        tree.heading("priority", text="Típus")
        tree.heading("date", text="Dátum")
        tree.heading("status", text="Állapot")
        
        tree.column("id", width=0, stretch=False)
        tree.column("partner", width=150)
        tree.column("subject", width=200)
        tree.column("priority", width=100)
        tree.column("date", width=130)
        tree.column("status", width=80)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # MÓDOSÍTÁS: Dupla kattintás esemény hozzáadása (Double-1)
        tree.bind("<Double-1>", lambda event: self.read_message(tree, mode))
        
        if mode == "inbox": self.inbox_tree = tree
        else: self.outbox_tree = tree
        
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="📖 Olvasás", bg="#3B82F6", fg="white", command=lambda: self.read_message(tree, mode), width=15).pack(side="left", padx=5)
        
        if mode != "outbox":
            tk.Button(btn_frame, text="🗑 Törlés", bg="#EF4444", fg="white", command=lambda: self.delete_message(tree), width=10).pack(side="left", padx=5)
            
        tk.Button(btn_frame, text="✖ Bezárás", bg="#64748B", fg="white", command=self.destroy, width=10).pack(side="right", padx=5)
        
        self.refresh_messages(tree, mode)
        
    def refresh_messages(self, tree, mode):
        for i in tree.get_children(): tree.delete(i)
        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            if mode == "inbox":
                cursor.execute("""
                    SELECT m.id, m.sender, m.subject, m.priority, m.sent_at, 
                           COALESCE(m.read_at, mr.read_at), m.replied_at, m.recipient
                    FROM messages m
                    LEFT JOIN message_reads mr ON m.id = mr.message_id AND mr.user_name = ?
                    WHERE m.recipient = ? OR m.recipient = 'MINDENKI'
                    ORDER BY m.sent_at DESC
                """, (self.user_name, self.user_name))
            else:
                cursor.execute("SELECT id, recipient, subject, priority, sent_at, read_at, replied_at FROM messages WHERE sender = ? ORDER BY sent_at DESC", (self.user_name,))
            
            rows = cursor.fetchall()
            prio_map = {1: "⚠ Hiba", 2: "⚙ Fejlesztés", 3: "✉ Üzenet"}
            for row in rows:
                # Alapértelmezett állapot és típus meghatározása
                if row[6]: status = "Válaszolva"
                elif row[5]: status = "Olvasott"
                else: status = "ÚJ" if mode == "inbox" else "Elküldve"
                
                display_prio = prio_map.get(row[3], "Üzenet")
                
                # MÓDOSÍTÁS: Ha a címzett MINDENKI (inbox esetén row[7]), alkalmazzuk a piros tag-et
                tags = ()
                if mode == "inbox" and row[7] == "MINDENKI":
                    tags = ("mindenki",)
                
                tree.insert("", "end", values=(row[0], row[1], row[2], display_prio, row[4], status), tags=tags)
            conn.close()
        except Exception as e:
            print(f"Lista hiba: {e}")

    def setup_send_tab(self, recipient_val=None, subject_val=None):
        for widget in self.tab_send.winfo_children(): widget.destroy()
        container = tk.Frame(self.tab_send, bg="white", padx=20, pady=10)
        container.pack(fill="both", expand=True)

        tk.Label(container, text=f"Bejelentkezve mint: {self.user_name}", bg="white", fg="#475569", font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 10))
        tk.Label(container, text="Címzett kiválasztása:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        
        # Címzettek listájának összeállítása: su vagy keyuser esetén "MINDENKI" opció hozzáadása
        user_list = self.get_users()
        if self.user_acc in ["su", "keyuser"]:
            user_list.insert(0, "MINDENKI")
            
        self.combo_recipient = ttk.Combobox(container, values=user_list, state="readonly")
        self.combo_recipient.pack(fill="x", pady=5)
        if recipient_val: self.combo_recipient.set(recipient_val)

        tk.Label(container, text="Üzenet tárgya:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_subject = ttk.Entry(container)
        self.ent_subject.pack(fill="x", pady=5)
        if subject_val: self.ent_subject.insert(0, subject_val)

        tk.Label(container, text="Kategória:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.combo_prio = ttk.Combobox(container, values=["1-Hibajelentés", "2-Fejlesztés kérése", "3-Általános üzenet"], state="readonly")
        self.combo_prio.set("3-Általános üzenet")
        self.combo_prio.pack(fill="x", pady=5)

        tk.Label(container, text="Üzenet szövege:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_body = tk.Text(container, height=10, bg="#F8FAFC", font=("Segoe UI", 10))
        self.txt_body.pack(fill="x", pady=5)

        # Piros magyarázó szöveg a gomb felett
        tk.Label(container, text="Üzenet tárgyát kötelező megadni!", bg="white", fg="#EF4444", font=("Segoe UI", 8, "bold")).pack(pady=(5, 0))

        self.btn_send_main = tk.Button(container, text="✉ ÜZENET ELKÜLDÉSE", bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"), command=self.send_message, pady=10)
        self.btn_send_main.pack(fill="x", pady=10)

    def send_message(self, reply_id=None):
        dest_full = self.combo_recipient.get()
        subj = self.ent_subject.get()
        body = self.txt_body.get("1.0", tk.END).strip()
        
        if not dest_full or not subj or not body:
            messagebox.showwarning("Figyelem", "Kérjük, töltsön ki minden mezőt!")
            return

        prio = int(self.combo_prio.get()[0])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            
            # Logika a "MINDENKI" opciónak: ha ki van választva, minden usernek elküldi
            if dest_full == "MINDENKI":
                cursor.execute("SELECT fullname FROM users WHERE fullname != ?", (self.user_name,))
                all_recipients = cursor.fetchall()
                for rec in all_recipients:
                    cursor.execute("INSERT INTO messages (sender, recipient, subject, message, priority, sent_at) VALUES (?, ?, ?, ?, ?, ?)", 
                                 (self.user_name, rec[0], subj, body, prio, now))
                dest_name = "Mindenki"
            else:
                dest_name = dest_full.split(" (")[0]
                cursor.execute("INSERT INTO messages (sender, recipient, subject, message, priority, sent_at) VALUES (?, ?, ?, ?, ?, ?)", 
                             (self.user_name, dest_name, subj, body, prio, now))
            
            if reply_id: 
                cursor.execute("UPDATE messages SET replied_at = ? WHERE id = ?", (now, reply_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Siker", f"Üzenet elküldve: {dest_name}")
            self.refresh_messages(self.inbox_tree, "inbox")
            self.refresh_messages(self.outbox_tree, "outbox")
            self.main_tabs.select(self.tab_msg_container)
            self.txt_body.delete("1.0", tk.END)
            self.ent_subject.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba: {e}")

    def send_message(self, reply_id=None):
        dest_full = self.combo_recipient.get()
        subj = self.ent_subject.get()
        body = self.txt_body.get("1.0", tk.END).strip()
        if not dest_full or not subj or not body:
            messagebox.showwarning("Figyelem", "Kérjük, töltsön ki minden mezőt!")
            return

        dest_name = dest_full.split(" (")[0]
        prio = int(self.combo_prio.get()[0])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (sender, recipient, subject, message, priority, sent_at) VALUES (?, ?, ?, ?, ?, ?)", (self.user_name, dest_name, subj, body, prio, now))
            if reply_id: cursor.execute("UPDATE messages SET replied_at = ? WHERE id = ?", (now, reply_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Siker", f"Üzenet elküldve: {dest_name}")
            self.refresh_messages(self.inbox_tree, "inbox")
            self.refresh_messages(self.outbox_tree, "outbox")
            self.main_tabs.select(self.tab_msg_container)
            self.txt_body.delete("1.0", tk.END)
            self.ent_subject.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba: {e}")

    def read_message(self, tree, mode):
        selected = tree.selection()
        if not selected: return
        msg_id = tree.item(selected)['values'][0]
        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("SELECT sender, subject, message, priority, sent_at, recipient FROM messages WHERE id = ?", (msg_id,))
            data = cursor.fetchone()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if data[5] == 'MINDENKI':
                # Egyéni olvasottság rögzítése a közös üzenethez
                cursor.execute("INSERT OR IGNORE INTO message_reads (message_id, user_name, read_at) VALUES (?, ?, ?)", (msg_id, self.user_name, now))
                conn.commit()
            elif data[5] == self.user_name:
                # Normál névre szóló üzenet frissítése
                cursor.execute("UPDATE messages SET read_at = ? WHERE id = ? AND read_at IS NULL", (now, msg_id))
                conn.commit()
                
            conn.close()
            self.refresh_messages(self.inbox_tree, "inbox")
            self.refresh_messages(self.outbox_tree, "outbox")
            self.show_message_window(msg_id, data)
        except Exception as e:
            print(f"Olvasás hiba: {e}")

    def show_message_window(self, msg_id, data):
        # Ideiglenesen kikapcsoljuk a főablak topmost állapotát, hogy a Toplevel ne kerüljön alá
        self.attributes("-topmost", False)
        
        win = tk.Toplevel(self)
        win.title(f"Üzenet megtekintése")
        win.geometry("500x650")
        win.configure(bg="white")
        win.transient(self)
        win.grab_set()

        # Ha bezárják a kis ablakot, visszakapcsoljuk a topmost-ot
        def on_close():
            win.destroy()
            self.attributes("-topmost", True)
        
        win.protocol("WM_DELETE_WINDOW", on_close)

        prio_colors = {"1": "#EF4444", "2": "#F59E0B", "3": "#3B82F6"}
        prio_names = {"1": "HIBAJELENTÉS", "2": "FEJLESZTÉSI KÉRÉS", "3": "ÁLTALÁNOS ÜZENET"}

        header = tk.Frame(win, bg="#F8FAFC", pady=15, padx=15)
        header.pack(fill="x", side="top")
        
        tk.Label(header, text=f"FELADÓ: {data[0]}", bg="#F8FAFC", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(header, text=f"TÁRGY: {data[1]}", bg="#F8FAFC", font=("Segoe UI", 10, "bold"), fg="#1E293B").pack(anchor="w")
        tk.Label(header, text=f"DÁTUM: {data[4]}", bg="#F8FAFC", font=("Segoe UI", 8), fg="#64748B").pack(anchor="w")
        tk.Label(header, text=prio_names.get(str(data[3])), fg="white", bg=prio_colors.get(str(data[3]), "grey"), font=("Segoe UI", 7, "bold"), padx=5, pady=2).pack(anchor="w", pady=5)

        body_frame = tk.Frame(win, bg="white", padx=15, pady=10)
        body_frame.pack(fill="both", expand=True)
        
        tk.Label(body_frame, text="Üzenet:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        txt = tk.Text(body_frame, bg="#FFFFFF", relief="flat", font=("Segoe UI", 10), padx=5, pady=5)
        txt.insert("1.0", data[2])
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)

        footer = tk.Frame(win, bg="#F1F5F9", pady=20, padx=15)
        footer.pack(fill="x", side="bottom")
        
        tk.Button(footer, text="✖ Bezárás", command=on_close, width=12, bg="#64748B", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)
        
        if str(data[0]) != str(self.user_name):
            btn_reply = tk.Button(footer, text="↩ VÁLASZADÁS", bg="#10B981", fg="white", font=("Segoe UI", 9, "bold"), width=15,
                                  command=lambda: [on_close(), self.open_reply(data[0], data[1], msg_id)])
            btn_reply.pack(side="right", padx=5)

    def open_reply(self, sender, subject, msg_id):
        self.main_tabs.select(self.tab_send)
        users = self.get_users()
        target = next((u for u in users if u.startswith(sender)), "")
        
        re_subject = f"Re: {subject}" if not str(subject).startswith("Re:") else subject
        self.setup_send_tab(recipient_val=target, subject_val=re_subject)
        self.btn_send_main.configure(command=lambda: self.send_message(reply_id=msg_id))
        self.txt_body.focus_set()

    def delete_message(self, tree):
        selected = tree.selection()
        if not selected: return
        
        # Lekérjük a kijelölt sor adatait
        item_values = tree.item(selected)['values']
        msg_id = item_values[0]
        recipient = item_values[1] # A Treeview-ban a partner oszlop
        
        # MÓDOSÍTÁS: Védelem a "MINDENKI" üzenetek törlése ellen
        # Megnézzük az adatbázisban, hogy ténylegesen MINDENKI-e a címzett
        try:
            conn = sqlite3.connect("berszamitas.db")
            cursor = conn.cursor()
            cursor.execute("SELECT recipient FROM messages WHERE id = ?", (msg_id,))
            real_recipient = cursor.fetchone()[0]
            conn.close()
            
            if real_recipient == "MINDENKI":
                messagebox.showwarning("Tiltott művelet", "A mindenki számára küldött központi üzenetek nem törölhetőek a listából!")
                return
        except:
            pass

        self.attributes("-topmost", False)
        if messagebox.askyesno("Megerősítés", "Biztosan törli az üzenetet?"):
            try:
                conn = sqlite3.connect("berszamitas.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
                # Töröljük az ehhez kapcsolódó egyéni olvasottsági adatokat is
                cursor.execute("DELETE FROM message_reads WHERE message_id = ?", (msg_id,))
                conn.commit()
                conn.close()
                self.refresh_messages(self.inbox_tree, "inbox")
                self.refresh_messages(self.outbox_tree, "outbox")
            except Exception as e:
                print(f"Törlési hiba: {e}")
        self.attributes("-topmost", True)