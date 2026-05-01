import sqlite3
import json
from datetime import datetime
import calendar

def get_hatalyos_elem(ber_lista, tipus_nev, vizsgalt_datum_str):
    """
    Kikeresi a JSON listából a legfrissebb hatályos elemet és naplózza a terminálba.
    """
    dt = datetime.strptime(vizsgalt_datum_str, '%Y-%m-%d')
    v_ev = str(dt.year)
    v_ho = str(dt.month).zfill(2)

    talalatok = []
    for elem in ber_lista:
        if elem.get('t') == tipus_nev:
            e_ev = str(elem.get('ev', '0'))
            e_ho = str(elem.get('ho', '0')).zfill(2)
            
            if e_ev < v_ev or (e_ev == v_ev and e_ho <= v_ho):
                talalatok.append(elem)

    if not talalatok:
        print(f"  [!] Nincs hatályos bejegyzés ehhez a típushoz: {tipus_nev}")
        return None

    talalatok.sort(key=lambda x: (str(x['ev']), str(x['ho']).zfill(2)), reverse=True)
    valasztott = talalatok[0]
    
    print(f"  [OK] {tipus_nev} kiválasztva: {valasztott['ev']}.{valasztott['ho']} hatályú, érték: {valasztott['o']}")
    return valasztott

def get_havi_munkaorak(ev, ho):
    """Egyszerűsített számítás: munkanapok száma (H-P) * 8 óra"""
    munkanapok = 0
    honap_napjai = calendar.monthrange(ev, ho)[1]
    for nap in range(1, honap_napjai + 1):
        if calendar.weekday(ev, ho, nap) < 5: 
            munkanapok += 1
    return munkanapok * 8

def ber_valtozok_kiszamitasa(db_path, dolgozo_id, datum_str):
    print(f"\n--- SZÁMÍTÁS INDÍTÁSA | ID: {dolgozo_id} | Dátum: {datum_str} ---")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # --- OSZLOPOK LÉTREHOZÁSA (HA MÉG NINCSENEK) ---
        uj_oszlopok = [
            "unnepnapi_potlek_oradij REAL",
            "tulora50 REAL",
            "tulora100 REAL",
            "keszenlet_oradij REAL"
        ]
        for oszlop in uj_oszlopok:
            try:
                cursor.execute(f"ALTER TABLE berszamitas ADD COLUMN {oszlop}")
                conn.commit()
            except sqlite3.OperationalError:
                pass 

        # 1. ADATBÁZIS LEKÉRDEZÉS
        cursor.execute("SELECT beosztas, ber_adatok FROM munkavallalok WHERE id = ?", (dolgozo_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"  [HIBA] Dolgozó (ID: {dolgozo_id}) nem található az adatbázisban.")
            return None

        beosztas = row[0]
        ber_adatok_lista = json.loads(row[1])
        print(f"  [INFO] Beosztás: {beosztas}")

        # --- ALAPBÉR ÓRADÍJ ---
        print("\n  >> Alapbér számítása:")
        alap_adat = get_hatalyos_elem(ber_adatok_lista, "Alapbér", datum_str)
        if alap_adat:
            o = float(alap_adat.get('o', 0))
            h = alap_adat.get('h', False)
            if h:
                alapber_oradij = round(o, 2)
                print(f"     Logika: Órabéres (h=True) -> {alapber_oradij} Ft")
            else:
                alapber_oradij = round(o / 174, 2)
                print(f"     Logika: Havi béres (h=False) -> {o} / 174 = {alapber_oradij} Ft")
        else:
            alapber_oradij = 0

        # --- ADHATÓ ÓRADÍJ ---
        print("\n  >> Adható kiegészítés számítása:")
        adhato_adat = get_hatalyos_elem(ber_adatok_lista, "Adható/FIX bérkiegészítés", datum_str)
        if adhato_adat:
            o = float(adhato_adat.get('o', 0))
            h = adhato_adat.get('h', False)
            if h:
                adhato_oradij = round(o, 2)
                print(f"     Logika: Órabéres (h=True) -> {adhato_oradij} Ft")
            else:
                adhato_oradij = round(o / 174, 2)
                print(f"     Logika: Havi béres (h=False) -> {o} / 174 = {adhato_oradij} Ft")
        else:
            adhato_oradij = 0

        # --- ALAP ÓRADÍJ (ÚTELLENŐR + SZEZON LOGIKA) ---
        print("\n  >> Alap óradíj (pótlékalap) összeállítása:")
        dt = datetime.strptime(datum_str, '%Y-%m-%d')
        honap = dt.month
        is_teli_szezon = (honap >= 11 or honap <= 3)
        teli_plusz = 0
        
        if beosztas == "Útellenőr téli" and is_teli_szezon:
            ut_adat = get_hatalyos_elem(ber_adatok_lista, "Útellenőri pótlék", datum_str)
            if ut_adat:
                utellenor_potlek_ertek = float(ut_adat.get('o', 0))
                teli_plusz = utellenor_potlek_ertek
                print(f"     [!] Szezonális pótlék aktív: +{teli_plusz} Ft")
            else:
                print(f"     [!] Nincs rögzített pótlék adat, érték: 0 Ft")
        
        alap_oradij = round(alapber_oradij + teli_plusz, 2)
        print(f"     VÉGEREDMÉNY (alap_oradij): {alap_oradij} Ft")
                
        # --- TÚLÓRA ÉS KÉSZENLÉT SZÁMÍTÁSA ---
        print("\n  >> Túlóra és Készenléti óradíjak számítása:")
        tulora50 = round((alap_oradij + adhato_oradij) * 1.5, 2)
        tulora100 = round((alap_oradij + adhato_oradij) * 2, 2)
        keszenlet_oradij = round((alap_oradij + adhato_oradij) * 0.2, 2)
        print(f"     VÉGEREDMÉNY (tulora50): {tulora50} Ft")
        print(f"     VÉGEREDMÉNY (tulora100): {tulora100} Ft")
        print(f"     VÉGEREDMÉNY (keszenlet_oradij): {keszenlet_oradij} Ft")

        # --- MŰSZAKPÓTLÉK SZÁMÍTÁSA ---
        cursor.execute("SELECT muszak_potlek FROM global_beallitasok LIMIT 1")
        global_row = cursor.fetchone()
        muszak_potlek_szazalek = float(global_row[0]) / 100 if global_row else 0.3
        
        potlek_bazis = alap_oradij + adhato_oradij
        muszakpotlek_oradij = round(potlek_bazis * muszak_potlek_szazalek, 2)
        
        # --- EGYÉB PÓTLÉKOK ---
        munkaszuneti_munkavegzes_oradij = round(alap_oradij + adhato_oradij, 2)
        unnepnap_munkaber_oradij = round(alap_oradij, 2)
        
        # --- TÁVOLLÉTI DÍJ ÉS ÁTLAGSZÁMÍTÁS ---
        sum_potlek_osszeg, sum_ledolgozott_ora, potlek_atlag_oradij = 0, 0, 0
        cursor.execute("""
            SELECT SUM(muszakpotlek_osszeg), SUM(alapber_osszeg / NULLIF(alap_oradij, 0)) 
            FROM berszamitas 
            WHERE dolgozo_id = ? AND (ev * 12 + honap) < (? * 12 + ?)
              AND (ev * 12 + honap) >= ((? * 12 + ?) - 6) AND torles_ideje IS NULL
        """, (dolgozo_id, dt.year, dt.month, dt.year, dt.month))
        
        row_atlag = cursor.fetchone()
        if row_atlag and row_atlag[1] and row_atlag[1] > 0:
            sum_potlek_osszeg = float(row_atlag[0] or 0)
            sum_ledolgozott_ora = float(row_atlag[1])
            potlek_atlag_oradij = round(sum_potlek_osszeg / sum_ledolgozott_ora, 2)

        alap_adat_tav = get_hatalyos_elem(ber_adatok_lista, "Alapbér", datum_str)
        is_oraberes = alap_adat_tav.get('h', False) if alap_adat_tav else False

        if is_oraberes:
            tavolleti_oradij = round(alap_oradij + adhato_oradij + potlek_atlag_oradij, 2)
            tavolleti_havi_oradij = 0
        else:
            tavolleti_oradij = round((alap_oradij / 174) + potlek_atlag_oradij, 2)
            tavolleti_havi_oradij = alap_oradij

        # --- TÁVOLLÉTI TÍPUSOK ---
        szabadsag_oradij = tavolleti_oradij
        fizetett_unnep_oradij = tavolleti_oradij
        unnepnapi_potlek_oradij = tavolleti_oradij if tavolleti_oradij > 0 else tavolleti_havi_oradij
        
        tav_bazis = tavolleti_oradij if is_oraberes else tavolleti_havi_oradij
        beteg_70_oradij = round(tav_bazis * 0.7, 2)
        beteg_60_oradij = round(tav_bazis * 0.6, 2)
        utibaleset_90_oradij = round(tav_bazis * 0.9, 2)
        mhbaleset_100_oradij = round(tav_bazis, 2)

        # --- ADATBÁZIS FRISSÍTÉSE ---
        cursor.execute("""
            UPDATE berszamitas 
            SET tulora50 = ?, tulora100 = ?, unnepnapi_potlek_oradij = ?, keszenlet_oradij = ?
            WHERE dolgozo_id = ? AND ev = ? AND honap = ? AND torles_ideje IS NULL
        """, (tulora50, tulora100, unnepnapi_potlek_oradij, keszenlet_oradij, dolgozo_id, dt.year, dt.month))
        conn.commit()
        print(f"  [OK] Adatbázis frissítve (túlórák, ünnepi, készenlét)")

        return {
            "alapber_oradij": alapber_oradij,
            "adhato_oradij": adhato_oradij,
            "alap_oradij": alap_oradij,
            "tulora50": tulora50,
            "tulora100": tulora100,
            "keszenlet_oradij": keszenlet_oradij,
            "muszakpotlek_oradij": muszakpotlek_oradij,
            "munkaszuneti_munkavegzes_oradij": munkaszuneti_munkavegzes_oradij,
            "unnepnap_munkaber_oradij": unnepnap_munkaber_oradij,
            "unnepnapi_potlek_oradij": unnepnapi_potlek_oradij,
            "tavolleti_oradij": tavolleti_oradij,
            "tavolleti_havi_oradij": tavolleti_havi_oradij,
            "fizetett_unnep_oradij": fizetett_unnep_oradij,
            "szabadsag_oradij": szabadsag_oradij, 
            "beteg_70_oradij": beteg_70_oradij,
            "beteg_60_oradij": beteg_60_oradij,
            "utibaleset_90_oradij" : utibaleset_90_oradij,
            "mhbaleset_100_oradij": mhbaleset_100_oradij,
            "beosztas": beosztas
        }
                     
    except Exception as e:
        print(f"  [HIBA] Váratlan hiba a számítás során: {e}")
        return None
    finally:
        conn.close()