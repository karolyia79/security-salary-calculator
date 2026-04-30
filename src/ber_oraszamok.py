import sqlite3
from datetime import datetime, timedelta

def muszakpotlek_szamitas(kezd_str, veg_str):
    """Műszakpótlék óráinak kiszámítása (18:00 - 06:00)."""
    if not kezd_str or not veg_str or str(kezd_str).strip() in ["", "None", "00:00"]:
        return 0
    fmt = "%H:%M"
    try:
        k = datetime.strptime(str(kezd_str).strip(), fmt)
        v = datetime.strptime(str(veg_str).strip(), fmt)
        if v <= k: v += timedelta(days=1)
        
        potlek_ora = 0
        aktualis = k
        lepes = timedelta(minutes=15)
        while aktualis < v:
            if aktualis.hour >= 18 or aktualis.hour < 6:
                potlek_ora += 0.25
            aktualis += lepes
        return potlek_ora
    except:
        return 0

def oraszamok_osszesitese(db_path, dolgozo_id, ev, honap, get_szabi_callback):
    print(f"\n{'='*80}")
    print(f" DEBUG: ÖSSZESÍTÉS INDÍTÁSA - ID: {dolgozo_id} | Időszak: {ev}.{honap:02d}")
    print(f"{'='*80}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- OSZLOPOK LÉTREHOZÁSA (DINAMIKUSAN MINDEN VÁLTOZÓHOZ) ---
    szukseges_oszlopok = [
        "osszes_ledolgozott_ora", "unnep_ledolgozott_ora", "fizetett_unnep_ora", 
        "szabadsag_ora", "beteg_70_ora", "beteg_60_ora", "utibaleset_90_ora", 
        "mhbaleset_100_ora", "potlekos_ora", "tulora50_ora", "tulora100_ora", 
        "alap_ora_korrigalt", "keszenlet_ora"
    ]
    
    for oszlop in szukseges_oszlopok:
        try:
            cursor.execute(f"ALTER TABLE berszamitas ADD COLUMN {oszlop} REAL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    
    # --- 1. BETEGSZABADSÁG KERET ELLENŐRZÉSE ---
    cursor.execute("""SELECT COUNT(DISTINCT datum) as korabbi FROM jelenleti_adatok 
                      WHERE dolgozo_id = ? AND datum LIKE ? AND datum < ? AND tipus = 'Beteg'""", 
                   (dolgozo_id, f"{ev}.%", f"{ev}.{honap:02d}.01"))
    hasznalt_napok = cursor.fetchone()['korabbi'] or 0
    szabad_keret_nap = max(0, 15 - hasznalt_napok)
    
    print(f"[FORRÁS: DB query] Előző betegnapok száma: {hasznalt_napok}")
    print(f"[SZÁMÍTÁS] Szabad keret: 15 - {hasznalt_napok} = {szabad_keret_nap} nap\n")

    # --- 2. ADATOK LEKÉRDEZÉSE (k_ora-val kiegészítve) ---
    cursor.execute("""SELECT datum, m_ora, t_ora, k_ora, tipus, m_kez, m_veg, t_kez, t_veg, unnep 
                      FROM jelenleti_adatok WHERE dolgozo_id=? AND datum LIKE ? ORDER BY datum ASC""", 
                   (dolgozo_id, f"{ev}.{honap:02d}.%"))
    rows = cursor.fetchall()
    
    res = {
        "osszes_ledolgozott_ora": 0,
        "unnep_ledolgozott_ora": 0,
        "fizetett_unnep_ora": 0,
        "szabi_ora": 0,
        "beteg_70_ora": 0,
        "beteg_60_ora": 0,
        "utibaleset_90_ora": 0,
        "mhbaleset_100_ora": 0,
        "potlekos_ora": 0,
        "tulora50_ora": 0,
        "tulora100_ora": 0,
        "keszenlet_ora": 0
    }
    
    akt_havi_beteg_napok = 0
    
    print(f"{'Dátum':<11} | {'Típus':<12} | {'Óra (m_ora)':<10} | {'K_ora':<8} | {'Pótlék':<8} | {'Esemény/Képlet'}")
    print("-" * 110)

    for row in rows:
        ora = float(row['m_ora'] or 0)
        t_ora_ertek = float(row['t_ora'] or 0)
        k_ora_ertek = float(row['k_ora'] or 0)
        t = str(row['tipus'] or "").strip()
        is_unnep = int(row['unnep'] or 0)
        datum_str = row['datum']
        
        datum_obj = datetime.strptime(datum_str, "%Y.%m.%d")
        is_hetkoznap = datum_obj.weekday() < 5

        # --- KÉSZENLÉT GYŰJTÉSE ---
        res["keszenlet_ora"] += k_ora_ertek

        # --- PÓTLÉK SZÁMÍTÁSA ---
        p1 = muszakpotlek_szamitas(row['m_kez'], row['m_veg'])
        p2 = muszakpotlek_szamitas(row['t_kez'], row['t_veg'])
        napi_potlek = p1 + p2
        res["potlekos_ora"] += napi_potlek

        log_note = ""

        # --- TÚLÓRA ÓRASZÁMOK SZÁMÍTÁSA ---
        if t_ora_ertek > 0:
            if t == "Ledolgozott":
                if is_unnep == 1:
                    res["tulora100_ora"] += t_ora_ertek
                else:
                    res["tulora50_ora"] += t_ora_ertek
            else:
                res["tulora100_ora"] += t_ora_ertek

        # --- ÜNNEPNAPI LOGIKA ---
        if is_unnep == 1:
            if t == "Ledolgozott":
                res["osszes_ledolgozott_ora"] += ora
                res["unnep_ledolgozott_ora"] += ora
                res["fizetett_unnep_ora"] += 8
                log_note = "Ünnep + Munka: +8 fiz. ünnep, m_ora bekerül az ünnepi ledolgozottba"
            elif is_hetkoznap:
                res["fizetett_unnep_ora"] += 8
                log_note = "Hétköznapi ünnep: +8 fiz. ünnep"
        
        # --- EGYÉB KATEGÓRIÁK ---
        elif t == "Ledolgozott":
            res["osszes_ledolgozott_ora"] += ora
            log_note = "Normál munkanap"

        elif t == "Szabadság": 
            res["szabi_ora"] += ora
            log_note = "Szabadság rögzítve"

        elif t == "Beteg":
            if is_hetkoznap and akt_havi_beteg_napok < szabad_keret_nap:
                res["beteg_70_ora"] += ora
                akt_havi_beteg_napok += 1
                log_note = f"Betegszabi (70%): {akt_havi_beteg_napok}. nap a keretből"
            else:
                res["beteg_60_ora"] += ora
                log_note = "Táppénz (60%): Kereten felül vagy hétvége"

        elif t == "Uti Baleset": 
            res["utibaleset_90_ora"] += ora
            log_note = "Úti baleset (90%)"

        elif t == "MHBaleset": 
            res["mhbaleset_100_ora"] += ora
            log_note = "Munkabaleset (100%)"

        print(f"{datum_str:<11} | {t:<12} | {ora:<10.1f} | {k_ora_ertek:<8.1f} | {napi_potlek:<8.1f} | {log_note}")

    # --- 3. SZABADSÁG SZINKRONIZÁCIÓ ---
    t_szabi_ora, _ = get_szabi_callback(db_path, dolgozo_id, ev, honap)
    if res["szabi_ora"] == 0 and t_szabi_ora > 0:
        print(f"\n[SZINKRON] Szabadság órák átvéve a callback-ből: {t_szabi_ora}")
        res["szabi_ora"] = t_szabi_ora

    # --- 4. VÉGSŐ ÖSSZESÍTÉS ---
    res["alap_ora_korrigalt"] = res["osszes_ledolgozott_ora"] - res["unnep_ledolgozott_ora"]
    res["info_hasznalt_beteg_nap"] = hasznalt_napok
    res["info_maradt_beteg_nap"] = szabad_keret_nap
    szabadsag_ora = res["szabi_ora"]

    # --- 5. ADATBÁZIS MENTÉS (Bővítve a keszenlet_ora-val) ---
    cursor.execute("""UPDATE berszamitas SET 
                      osszes_ledolgozott_ora = ?,
                      unnep_ledolgozott_ora = ?,
                      fizetett_unnep_ora = ?,
                      szabadsag_ora = ?,
                      beteg_70_ora = ?,
                      beteg_60_ora = ?,
                      utibaleset_90_ora = ?,
                      mhbaleset_100_ora = ?,
                      potlekos_ora = ?,
                      tulora50_ora = ?, 
                      tulora100_ora = ?,
                      alap_ora_korrigalt = ?,
                      keszenlet_ora = ?
                      WHERE dolgozo_id = ? AND ev = ? AND honap = ? AND torles_ideje IS NULL""",
                   (res["osszes_ledolgozott_ora"], res["unnep_ledolgozott_ora"], 
                    res["fizetett_unnep_ora"], szabadsag_ora, res["beteg_70_ora"], 
                    res["beteg_60_ora"], res["utibaleset_90_ora"], res["mhbaleset_100_ora"], 
                    res["potlekos_ora"], res["tulora50_ora"], res["tulora100_ora"], 
                    res["alap_ora_korrigalt"], res["keszenlet_ora"], dolgozo_id, ev, honap))
    conn.commit()

    print(f"\n{'='*80}")
    print(" VÉGSŐ ÖSSZESÍTETT ÉRTÉKEK ÉS KÉPLETEK")
    print(f"{'='*80}")
    print(f"KÉPLET: alap_ora_korrigalt = {res['osszes_ledolgozott_ora']} (Összes ledolgozott) - {res['unnep_ledolgozott_ora']} (Ünnepi ledolgozott) = {res['alap_ora_korrigalt']}")
    print(f"KÉSZENLÉT ÖSSZESEN: {res['keszenlet_ora']} óra")
    print("-" * 80)
    
    print("FŐPROGRAMNAK ÁTADOTT SZÓTÁR (res):")
    for key, value in res.items():
        print(f"  - {key:<25}: {value}")
    print(f"{'='*80}\n")

    conn.close()
    return res