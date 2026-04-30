# Security Bérkalkulátor 2026 – Technikai Architektúra és Rendszerleírás

A **Security Bérkalkulátor 2026** egy univerzális bérszámfejtő motor, amely a modularitást és a precíziós adatfeldolgozást helyezi előtérbe. A rendszer alkalmas korlátlan számú munkáltató (cég) és a hozzájuk tartozó munkavállalói állomány egyidejű, elkülönített kezelésére.

## 🛠️ Technikai Stack és Modulok

A szoftver Python alapú, az alábbi kulcsfontosságú könyvtárak felhasználásával:
*   `sqlite3`: A teljes adatkezelés, tárolás és belső eseménynaplózás színhelye.
*   `tkinter` & `ttk`: A dinamikus, skálázható felhasználói felületért felelős modulok.
*   `fpdf`: A számfejtési adatokból generált, hiteles PDF dokumentumok motorja.
*   `hashlib`: Az SHA-256 alapú biztonsági réteg a felhasználói hitelesítéshez.
*   `datetime`, `calendar`, `math`: Az időalapú algoritmusok és a bértranszformációk matematikai háttere.

---

## 🧮 Számítási Algoritmusok: A Rendszer Logikája

A motor három fő területen végez komplex műveleteket:

### 1. Bértranszformációs Motor (Óradíj/Havibér)
A rendszer képessége az **automatikus távolléti díj kalkuláció**, amely havibéres dolgozóknál is tűpontos elszámolást tesz lehetővé.
*   **Logika**: A szoftver az adott naptári hónap munkanapjainak száma alapján meghatározza az egy órára eső alapbért.
*   **Alkalmazás**: Szabadság, betegszabadság vagy igazolt távollét esetén a rendszer ezzel a dinamikus értékkel korrigálja a havi fix összeget, biztosítva a jogszabályi megfelelést.

### 2. Műszak-analitika és Pótlékolás
A jelenléti ívek feldolgozása során a rendszer percalapú bontást végez:
*   **Éjszakai analízis**: Automatikusan elkülöníti a 22:00 és 06:00 közötti idősávot, és erre számolja fel az éjszakai pótlékot.
*   **Ünnepnap-algoritmus**: A beépített Gauss-húsvétalgoritmus segítségével a szoftver önműködően azonosítja a mozgóünnepeket (Húsvét, Pünkösd), így ezeken a napokon a megfelelő extra szorzókkal kalkulál.

### 3. Pénzügyi Hátralék-kezelő (Ciklikus Modul)
A levonások és extrák (pl. bérelőleg, jutalom) nem statikus tételek:
*   A rendszer támogatja a **ciklikus futamidőt**, ahol egy tétel egy meghatározott záró dátumig minden hónapban automatikusan beemelésre kerül a bérbe.
*   A hátralékok követése folyamatos, így a kifizetések és levonások egyenlege minden pillanatban naprakész.

---

## 🗄️ Adatbázis és Belső Logolás

A szoftver minden adatot és eseményt a központi SQLite adatbázisban tárol. 

### Adatbázis-séma jellemzői:
*   **Munkáltatói izoláció**: A dolgozók és a számfejtési adatok cégazonosítóhoz kötöttek, így biztosított a multi-company működés.
*   **Belső Eseménynapló**: A rendszer nem külső fájlba, hanem az adatbázis dedikált táblájába rögzít minden módosítást, mentést és véglegesítést, biztosítva az adatok integritását és visszakövethetőségét.
*   **Azonosítási protokoll**: A beviteli felületeken a tévesztések elkerülése érdekében a rendszer a név mellett a születési dátumot használja elsődleges vizuális azonosítóként.

---

## 📄 Kimeneti Dokumentáció (Bérlap Függelék)

A számítások végeredménye egy professzionális PDF dokumentum, amely túlmutat az egyszerű bérpapíron:
*   Tételes kimutatást ad a havi mozgásokról (pótlékok, módosító tételek).
*   Megjeleníti a ciklikus levonások aktuális státuszát és a még fennmaradó összegeket.
*   Átlátható szerkezetet biztosít a munkavállaló és a könyvelés számára egyaránt.

---
*© 2026 Security Bérkalkulátor Projekt – Precizitás, Modularitás, Biztonság.*
