
# 📘 Felhasználói Kézikönyv: Security Bérkalkulátor 2026

## 1. Belépés és Jogosultságok
A rendszer indítása után egy biztonságos beléptetőfelület fogadja.
1.  **Azonosítás:** Adja meg felhasználónevét és jelszavát. A rendszer SHA-256 titkosítást használ a jelszavak védelmére.
2.  **Jogosultsági szintek:**
    *   **User:** Adatrögzítésre és saját üzenetek kezelésére jogosult.
    *   **Keyuser (ku):** Ellenőrizheti az adatokat és jóváhagyási jogkörrel rendelkezik.
    *   **Superuser (su):** Teljes hozzáférés a törzsadatokhoz, a naplózáshoz és a felhasználók kezeléséhez.

---

## 2. Alapadatok és Törzsadat-kezelés
Mielőtt elkezdené a munkát, rögzítenie kell a keretadatokat.

### Munkáltatók és Dolgozók felvétele
1.  Navigáljon a **Törzsadatok** menüpontra.
2.  **Munkáltató rögzítése:** Adja meg a cég nevét, székhelyét és adószámát.
3.  **Munkavállaló rögzítése:**
    *   Adja meg a dolgozó nevét és **születési dátumát**.
    *   Rögzítse az adóazonosító jelet és a szerződés szerinti bérformát (óradíj vagy havi bér).
    *   **Fontos:** A beviteli felület fejlécében ettől a ponttól kezdve mindig látható lesz a név és a születési dátum az azonosításhoz.

---

## 3. Jelenléti adatok rögzítése (Naptár modul)
Ez a modul szolgál a napi munkavégzés dokumentálására.

1.  **Hónap kiválasztása:** A rendszer automatikusan generálja az adott havi naptárat, megjelölve a hétvégéket és az ünnepnapokat.
2.  **Műszak rögzítése:**
    *   Kattintson az adott napra.
    *   Adja meg a **kezdési időpontot** (óra:perc).
    *   Adja meg a **ledolgozott órák számát**.
    *   A rendszer automatikusan kiszámítja a műszak végének idejét.
3.  **Távollétek jelölése:** Ha a dolgozó nem dolgozott, válassza ki a távollét típusát (szabadság, betegszabadság, igazolt/igazolatlan távollét).
4.  **Automatikus pótlékolás:** A rendszer a háttérben elemzi a műszakot, és ha az éjszakába (22:00 – 06:00) vagy vasárnapra/ünnepnapra nyúlik, automatikusan felszámolja a pótlékokat.

---

## 4. Módosító tételek (Extrák és Levonások) kezelése
Itt rögzítheti a bérkiegészítéseket és a levonásokat.

1.  **Új tétel hozzáadása:** Válassza ki a kategóriát (pl. Jutalom, Bérelőleg, Eszközhasználat).
2.  **Paraméterek beállítása:**
    *   **Összeg:** A tétel értéke.
    *   **Adózás:** Jelölje be, ha a tétel adóköteles.
    *   **Ciklikusság:** Ha a tétel több hónapon át ismétlődik (pl. törlesztőrészlet), adja meg a záró dátumot.
3.  **Bérelőleg:** Külön opció a tőke és a havi törlesztőrészlet rögzítésére. A rendszer automatikusan számolja a hátralékot.

---

## 5. Számfejtés és Dokumentumgenerálás
A hónap végén az összesített adatokból dokumentumokat hozhat létre.

1.  **Ellenőrzés:** A "Számítás" gombra kattintva a rendszer összesíti a ledolgozott órákat, a pótlékokat, a távolléti díjakat és a módosító tételeket.
2.  **Bérlap Függelék generálása:**
    *   Kattintson a PDF generálás gombra.
    *   A szoftver elkészíti a részletes kimutatást, amely tartalmazza a havi mozgásokat és a hosszú távú egyenlegeket (pl. mennyi van még hátra egy levonásból).
3.  **Véglegesítés:** A Keyuser jóváhagyása után az adatok lezárásra kerülnek, és bekerülnek a történeti naplóba.

---

## 6. Kiegészítő funkciók

### Belső üzenetküldés
*   Használja az üzenetpanelt a munkatársak értesítésére.
*   Ha új üzenete érkezik, az értesítő gomb lüktetni kezd a felületen.

### Naplózás (Log)
*   Bármilyen hiba vagy vitás kérdés esetén a Superuser megtekintheti az **Eseménynaplót**, ahol minden mentés, módosítás és törlés időbélyeggel és felhasználói névvel szerepel.

---

## 💡 Hasznos tippek a használathoz
*   **Havi bérnél:** Ha havi bért adott meg a dolgozónak, a rendszer akkor is kiszámolja az egy órára jutó díjat a távolléti díj és a pótlékok miatt – ne lepődjön meg a tizedesjegyeken!
*   **Mozgó ünnepek:** Nem kell kézzel beállítania a Húsvétot vagy Pünkösdöt, a rendszer Gauss-algoritmusa minden évre pontosan kalkulálja ezeket.
*   **Adatmentés:** A rendszer minden sikeres rögzítés után automatikusan frissíti a `berszamitas.db` adatbázist.
