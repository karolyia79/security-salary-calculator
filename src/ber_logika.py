import sqlite3
from datetime import datetime
from ber_oradijak import ber_valtozok_kiszamitasa
from ber_oraszamok import oraszamok_osszesitese

def esemeny_naplozas(db_path, esemeny, dolgozo_adat="N/A"):
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute('''CREATE TABLE IF NOT EXISTS esemeny_naplo 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, datum TEXT, esemeny TEXT, dolgozo TEXT)''')
        most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        cursor.execute("INSERT INTO esemeny_naplo (datum, esemeny, dolgozo) VALUES (?, ?, ?)", (most, esemeny, dolgozo_adat))
        conn.commit()
    except Exception as e:
        print(f"Naplózási hiba: {e}")
    finally:
        if conn: conn.close()

def hiba_naplozas(db_path, modul, hiba):
    hiba_szoveg = f"HIBA: {str(hiba)}"
    print(f"[{modul}] {hiba_szoveg}")
    esemeny_naplozas(db_path, f"ERROR: {modul}", hiba_szoveg)

def szamitas_vegrehajtasa(db_path, dolgozo_id, ev, honap, get_szabi_callback):
    print(f"\n" + "="*80)
    print(f" SZÁMÍTÁSI LEVEZETÉS | {ev}.{honap:02d} | Dolgozó: {dolgozo_id}")
    print("="*80)

    try:
        # 1. ADATOK BEKÉRÉSE ÉS TÁBLA ELLENŐRZÉSE
        conn_temp = sqlite3.connect(db_path)
        conn_temp.row_factory = sqlite3.Row
        cursor_temp = conn_temp.cursor()
        
        # Hiányzó oszlopok automatikus létrehozása a jelenléti táblában
        cursor_temp.execute("PRAGMA table_info(jelenleti_adatok)")
        cols = [info['name'] for info in cursor_temp.fetchall()]
        if 'tipus' not in cols:
            cursor_temp.execute("ALTER TABLE jelenleti_adatok ADD COLUMN tipus TEXT")
        if 't_ora' not in cols:
            cursor_temp.execute("ALTER TABLE jelenleti_adatok ADD COLUMN t_ora REAL DEFAULT 0")
        if 'k_ora' not in cols:
            cursor_temp.execute("ALTER TABLE jelenleti_adatok ADD COLUMN k_ora REAL DEFAULT 0")
        
        # Munkábajáráshoz szükséges adatok lekérése
        cursor_temp.execute("SELECT km_dij FROM global_beallitasok LIMIT 1")
        row_global = cursor_temp.fetchone()
        km_dij = row_global["km_dij"] if row_global else 0

        cursor_temp.execute("SELECT munkabajaras_km FROM munkavallalok WHERE id = ?", (dolgozo_id,))
        row_dolgozo = cursor_temp.fetchone()
        munkabajaras_km = row_dolgozo["munkabajaras_km"] if row_dolgozo else 0

        # Ledolgozott napok száma
        h_kotojel = f"{ev}-{str(honap).zfill(2)}%"
        h_pontos = f"{ev}.{str(honap).zfill(2)}%"

        cursor_temp.execute("""
            SELECT COUNT(DISTINCT datum) as napok_szama 
            FROM jelenleti_adatok
            WHERE dolgozo_id = ? 
            AND (datum LIKE ? OR datum LIKE ?)
            AND (tipus = 'Ledolgozott' OR (t_ora IS NOT NULL AND t_ora > 0))
        """, (dolgozo_id, h_kotojel, h_pontos))
        
        row_napok = cursor_temp.fetchone()
        ledolgozott_napok_szama = row_napok["napok_szama"] if row_napok else 0

        # --- EXTRA TÉTELEK KISZÁMÍTÁSA + RÉSZLETES MONITOROZÁS ---
        extra_plusz_adokoteles = 0
        extra_plusz_adomentes = 0
        extra_minusz_adokoteles = 0
        extra_minusz_adomentes = 0
        extra_tetelek_reszletezo = []
        
        print(f"\n[MONITOR] Extra tételek feldolgozása ({ev}.{honap:02d}):")
        print("-" * 80)
        
        cursor_temp.execute("SELECT * FROM extra_tetelek WHERE dolgozo_id = ?", (dolgozo_id,))
        extra_rows = cursor_temp.fetchall()
        
        akt_datum = datetime(ev, honap, 1)
        
        if not extra_rows:
            print("   > Nincsenek rögzített extra tételek ehhez a dolgozóhoz.")
        
        for row in extra_rows:
            t_id = row["id"]
            tipus = row["tipus"]
            osszeg = row["osszeg"] or 0
            t_osszeg = row["teljes_osszeg"] or 0
            adokoteles = row["adokoteles"]
            gyakorisag = row["gyakorisag"]
            megnevezes = row["megnevezes"] or "Névtelen tétel"
            
            # JAVÍTOTT RUGALMAS DÁTUMKEZELÉS
            try:
                def datum_normalizalas(d_str):
                    if not d_str: return None
                    tiszta = str(d_str).replace("-", ".").strip()
                    if len(tiszta) <= 7: # pl. 2026.04 -> 2026.04.01
                        return datetime.strptime(tiszta, "%Y.%m")
                    else: # pl. 2026.04.15
                        return datetime.strptime(tiszta, "%Y.%m.%d")

                idoszak_dt = datum_normalizalas(row["idoszak"])
                lejarat_dt = datum_normalizalas(row["lejarat"])
                
                f_nyers = row["folyositas_ideje"]
                foly_dt = datum_normalizalas(f_nyers) if f_nyers else None
                    
            except Exception as d_err:
                print(f"   ! KRITIKUS DÁTUM HIBA (ID:{t_id}): {d_err}")
                continue
                
            print(f"   > Ellenőrzés [ID:{t_id} | {tipus}]: {megnevezes}")
        
            # ELOLEG LOGIKA
            if tipus == "ELOLEG":
                if foly_dt and foly_dt.year == ev and foly_dt.month == honap:
                    print(f"     [!] FOLYÓSÍTÁS AKTÍV: +{t_osszeg} Ft")
                    extra_tetelek_reszletezo.append(f"{megnevezes} (Kifizetés)|EXTRA|{t_osszeg}|{adokoteles}")
                    if adokoteles == 1: extra_plusz_adokoteles += t_osszeg
                    else: extra_plusz_adomentes += t_osszeg
                
                if idoszak_dt and lejarat_dt and idoszak_dt <= akt_datum <= lejarat_dt:
                    print(f"     [!] TÖRLESZTÉS AKTÍV: -{osszeg} Ft")
                    extra_tetelek_reszletezo.append(f"{megnevezes} (Törlesztés)|LEVONAS|{osszeg}|{adokoteles}")
                    if adokoteles == 1: extra_minusz_adokoteles += osszeg
                    else: extra_minusz_adomentes += osszeg
        
            # EXTRA ÉS LEVONÁS LOGIKA
            elif tipus in ["EXTRA", "LEVONAS"]:
                ervenyes = False
                if gyakorisag == "Eseti":
                    if idoszak_dt and idoszak_dt.year == ev and idoszak_dt.month == honap:
                        ervenyes = True
                else:
                    if idoszak_dt and lejarat_dt and idoszak_dt <= akt_datum <= lejarat_dt:
                        ervenyes = True
                
                if ervenyes:
                    print(f"     [!] TÉTEL AKTÍV: {'+' if tipus=='EXTRA' else '-'}{osszeg} Ft")
                    extra_tetelek_reszletezo.append(f"{megnevezes}|{tipus}|{osszeg}|{adokoteles}")
                    if tipus == "EXTRA":
                        if adokoteles == 1: extra_plusz_adokoteles += osszeg
                        else: extra_plusz_adomentes += osszeg
                    else:
                        if adokoteles == 1: extra_minusz_adokoteles += osszeg
                        else: extra_minusz_adomentes += osszeg
        
        print("-" * 80)
        print(f"   ÖSSZESÍTETT EXTRA PLUSZ:  {extra_plusz_adokoteles + extra_plusz_adomentes:,.0f} Ft")
        print(f"   ÖSSZESÍTETT EXTRA MÍNUSZ: {extra_minusz_adokoteles + extra_minusz_adomentes:,.0f} Ft")
        print("-" * 80)
        
        conn_temp.close()

        datum_str = f"{ev}-{str(honap).zfill(2)}-01"
        rates = ber_valtozok_kiszamitasa(db_path, dolgozo_id, datum_str)
        if not rates: raise Exception("Óradíjak nem találhatók!")

        o = oraszamok_osszesitese(db_path, dolgozo_id, ev, honap, get_szabi_callback)
        
        # --- BEMENŐ ADATOK MONITOROZÁSA ---
        print(f"\n[MONITOR] Bemenő változók ellenőrzése:")
        print("-" * 50)
        print("A) ÓRADÍJAK (ber_oradijak.py):")
        for kulcs, ertek in rates.items():
            print(f"   > {kulcs:<30}: {ertek:>8} Ft")
        
        print("\nB) ÖSSZESÍTETT ÓRASZÁMOK (ber_oraszamok.py):")
        for kulcs, ertek in o.items():
            print(f"   > {kulcs:<30}: {ertek:>8} óra")
        
        print(f"\nC) MUNKÁBAJÁRÁS ALAPADATOK:")
        print(f"   > ledolgozott_napok_szama:       {ledolgozott_napok_szama:>8} nap")
        print("-" * 50)

        # 2. PÉNZÜGYI SZÁMÍTÁSOK
        alapber_osszeg = o["alap_ora_korrigalt"] * rates["alapber_oradij"]
        alap_elszamolas_osszeg = o["alap_ora_korrigalt"] * rates["alap_oradij"]
        adhato_osszeg = o["osszes_ledolgozott_ora"] * rates["adhato_oradij"]
        
        t50_osszeg = o["tulora50_ora"] * rates["tulora50"]
        t100_osszeg = o["tulora100_ora"] * rates["tulora100"]
        keszenlet_osszeg = o["keszenlet_ora"] * rates.get("keszenlet_oradij", 0)

        b70_osszeg = o["beteg_70_ora"] * rates["beteg_70_oradij"]
        b60_osszeg = o["beteg_60_ora"] * rates["beteg_60_oradij"]
        ut90_osszeg = o["utibaleset_90_ora"] * rates["utibaleset_90_oradij"]
        mh100_osszeg = o["mhbaleset_100_ora"] * rates["mhbaleset_100_oradij"]
        
        u_munkaber = o["unnep_ledolgozott_ora"] * rates["unnepnap_munkaber_oradij"]
        u_potlek = o["unnep_ledolgozott_ora"] * rates["munkaszuneti_munkavegzes_oradij"]
        f_unnep_osszeg = o["fizetett_unnep_ora"] * rates["fizetett_unnep_oradij"]
        m_potlek_ertek = o["potlekos_ora"] * rates["muszakpotlek_oradij"]
        szabadsag_osszeg = o["szabi_ora"] * rates['szabadsag_oradij']
        
        munkabajaras_osszeg = ledolgozott_napok_szama * munkabajaras_km * km_dij

        brutto = (alapber_osszeg + adhato_osszeg + u_munkaber + u_potlek + 
                  f_unnep_osszeg + m_potlek_ertek + szabadsag_osszeg + 
                  b70_osszeg + b60_osszeg + ut90_osszeg + mh100_osszeg + 
                  munkabajaras_osszeg + t50_osszeg + t100_osszeg + keszenlet_osszeg +
                  extra_plusz_adokoteles + extra_plusz_adomentes - 
                  extra_minusz_adokoteles - extra_minusz_adomentes)
        
        szja_alap = (brutto - ut90_osszeg - mh100_osszeg - munkabajaras_osszeg - 
                     extra_plusz_adomentes + extra_minusz_adomentes)
        
        tb_alap = szja_alap - b60_osszeg
        szja = round(szja_alap * 0.15)
        tb = round(tb_alap * 0.185)
        netto = brutto - szja - tb

        # --- KIMENŐ VÁLTOZÓK ÉS KÉPLETEK ---
        print(f"\n[MONITOR] Kalkuláció levezetése:")
        print("-" * 80)
        print(f"alapber_osszeg:      {alapber_osszeg:,.0f} Ft")
        print(f"tulora 50% össz:     {t50_osszeg:,.0f} Ft")
        print(f"tulora 100% össz:    {t100_osszeg:,.0f} Ft")
        print(f"Extra (+) adóköt:    {extra_plusz_adokoteles:,.0f} Ft")
        print(f"Extra (-) adóköt:    {extra_minusz_adokoteles:,.0f} Ft")
        print("-" * 80)
        print(f"BRUTTÓ: {brutto:,.0f} | SZJA: {szja:,.0f} | TB: {tb:,.0f} | NETTÓ: {netto:,.0f} Ft")

        # 3. MENTÉSI ADATOK ÖSSZEÁLLÍTÁSA (Bővített szótár)
        final_data = {
            "dolgozo_id": dolgozo_id, "ev": ev, "honap": honap,
            "alap_oradij": rates["alap_oradij"], "alap_osszeg": alap_elszamolas_osszeg,
            "alapber_oradij": rates["alapber_oradij"], "alapber_osszeg": alapber_osszeg,
            "adhato_oradij": rates["adhato_oradij"], "adhato_osszeg": adhato_osszeg,
            "tulora50_ora": o["tulora50_ora"], "tulora50_osszeg": t50_osszeg,
            "tulora100_ora": o["tulora100_ora"], "tulora100_osszeg": t100_osszeg,
            "dolgozo_id": dolgozo_id, # megjegyzés: ez a mező az eredetiben nem volt, de ha a táblában kell, itt van
            "keszenlet_ora": o["keszenlet_ora"], "keszenlet_osszeg": keszenlet_osszeg,
            "szabadsag_oradij": rates["szabadsag_oradij"], "szabadsag_osszeg": szabadsag_osszeg,
            "muszakpotlek_oradij": rates["muszakpotlek_oradij"], "muszakpotlek_osszeg": m_potlek_ertek,
            "munkaszuneti_munkavegzes_oradij": rates["munkaszuneti_munkavegzes_oradij"], "munkaszuneti_munkavegzes_osszeg": u_potlek,
            "unnepnap_munkaber_oradij": rates["unnepnap_munkaber_oradij"], "unnepnapi_munkaber_osszeg": u_munkaber,
            "fizetett_unnep_oradij": rates["fizetett_unnep_oradij"], "fizetett_unnep_osszeg": f_unnep_osszeg,
            "beteg_70_oradij": rates["beteg_70_oradij"], "beteg_70_osszeg": b70_osszeg,
            "beteg_60_oradij": rates["beteg_60_oradij"], "beteg_60_osszeg": b60_osszeg,
            "utibaleset_90_oradij": rates["utibaleset_90_oradij"], "utibaleset_90_osszeg": ut90_osszeg,
            "mhbaleset_100_oradij": rates["mhbaleset_100_oradij"], "mhbaleset_100_osszeg": mh100_osszeg,
            "extra_plusz_adokoteles": extra_plusz_adokoteles, "extra_plusz_adomentes": extra_plusz_adomentes,
            "extra_minusz_adokoteles": extra_minusz_adokoteles, "extra_minusz_adomentes": extra_minusz_adomentes,
            "extra_tetelek_reszletezve": ";".join(extra_tetelek_reszletezo),
            "munkabajaras_osszeg": munkabajaras_osszeg,
            "brutto_osszesen": brutto, "szja": szja, "tb_jarulek": tb, "netto_ber": netto
        }

        # --- BIZTONSÁGOS MENTÉS ---
        conn = sqlite3.connect(db_path, timeout=60)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # 1. Oszlopok ellenőrzése és kényszerített frissítése
        cursor.execute("PRAGMA table_info(berszamitas)")
        existing_cols = [i['name'] for i in cursor.fetchall()]
        
        new_cols = {
            "munkabajaras_osszeg": "REAL DEFAULT 0",
            "tulora50_ora": "REAL DEFAULT 0",
            "tulora50_osszeg": "REAL DEFAULT 0",
            "tulora100_ora": "REAL DEFAULT 0",
            "tulora100_osszeg": "REAL DEFAULT 0",
            "keszenlet_ora": "REAL DEFAULT 0",
            "keszenlet_osszeg": "REAL DEFAULT 0",
            "extra_plusz_adokoteles": "REAL DEFAULT 0",
            "extra_plusz_adomentes": "REAL DEFAULT 0",
            "extra_minusz_adokoteles": "REAL DEFAULT 0",
            "extra_minusz_adomentes": "REAL DEFAULT 0",
            "extra_tetelek_reszletezve": "TEXT"
        }
        
        for col_name, col_def in new_cols.items():
            if col_name not in existing_cols:
                print(f"[DB] Oszlop hozzáadása: {col_name}")
                cursor.execute(f"ALTER TABLE berszamitas ADD COLUMN {col_name} {col_def}")

        # 2. Meglévő rekord keresése
        cursor.execute("""
            SELECT id FROM berszamitas 
            WHERE dolgozo_id=? AND ev=? AND honap=? AND torles_ideje IS NULL
        """, (dolgozo_id, ev, honap))
        letezo = cursor.fetchone()
        
        most = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        # 3. Mentés végrehajtása
        if letezo:
            # UPDATE logika
            update_fields = [f"{k}=:{k}" for k in final_data.keys()]
            sql = f"UPDATE berszamitas SET {', '.join(update_fields)}, utolso_modositas=:most WHERE id=:id"
            params = {**final_data, "most": most, "id": letezo["id"]}
            cursor.execute(sql, params)
            print(f"[SQL] Rekord frissítve (ID: {letezo['id']})")
        else:
            # INSERT logika
            final_data["letrehozas_datuma"] = most
            cols_str = ", ".join(final_data.keys())
            places = ", ".join([f":{k}" for k in final_data.keys()])
            sql = f"INSERT INTO berszamitas ({cols_str}) VALUES ({places})"
            cursor.execute(sql, final_data)
            print("[SQL] Új rekord beszúrva")

        conn.commit()
        conn.close()
        esemeny_naplozas(db_path, f"Bérszámítás kész: Netto {netto:,.0f} Ft", str(dolgozo_id))
        
        return final_data
        
    except Exception as e:
        hiba_naplozas(db_path, "szamitas_vegrehajtasa", e)
        return None