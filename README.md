# Security Bérkalkulátor 2026 – Univerzális Bérügyi Keretrendszer

A **Security Bérkalkulátor 2026** egy moduláris felépítésű, professzionális bérszámfejtő és munkaidő-nyilvántartó szoftver[cite: 15]. Bár a projekt neve a biztonsági szektor igényeire utal, a rendszer valójában egy **univerzális motor**, amely bármely iparágban (kereskedelem, gyártás, szolgáltatás) alkalmazható a munkavállalók bérének és jelenlétének precíz kezelésére[cite: 15].

## 🌟 Főbb Jellemzők

*   **Többcéges architektúra**: A rendszer képes több különböző munkáltató (cég) párhuzamos kezelésére, külön székhely- és adószám-nyilvántartással[cite: 12, 15].
*   **Univerzális bérkezelés**: Automatikusan megkülönbözteti és kezeli az óradíjas és a havibéres dolgozókat[cite: 12].
*   **Intelligens távolléti díj**: Havibéres dolgozók esetén is képes kiszámítani az egy órára jutó távolléti díjat az adott hónap munkanapjainak száma alapján[cite: 12].
*   **Automatizált pótlékolás**: A beépített Gauss-algoritmus segítségével a rendszer felismeri a mozgóünnepeket (Húsvét, Pünkösd) és az éjszakai műszakokat, majd automatikusan kalkulálja a pótlékokat[cite: 12].
*   **Dinamikus módosító tételek**: Kezeli a jutalmakat, bérelőlegeket és levonásokat, akár több hónapon átívelő, ciklikus futamidővel is[cite: 14].

## 🛠️ Funkcionális Felépítés

### 1. Jelenléti és Munkaidő-nyilvántartás
A rendszer naptár alapú rögzítést használ, ahol a kezdési idő és az óraszám megadása után a szoftver automatikusan kiszámítja a műszak végét és a napszak szerinti bontást[cite: 12]. Megkülönbözteti a ledolgozott órákat, a szabadságot, a betegszabadságot és az ünnepi munkavégzést[cite: 12].

### 2. Pénzügyi Modul és Hátralékkezelés
A szoftver követi a kifizetett extrákat és a végrehajtott levonásokat[cite: 11, 14]. A ciklikus tételek rögzítésekor megadható egy záró dátum, ameddig a rendszer minden hónapban automatikusan érvényesíti az adott tételt[cite: 14].

### 3. Transzparens Dokumentáció (Bérlap Függelék)
Minden számfejtés végén egy részletes **PDF dokumentum** generálható, amely tartalmazza a havi mozgásokat és a munkavállaló aktuális tartozásait vagy hátralékait[cite: 11].

## 🛡️ Biztonság és Jogosultság

*   **Többszintű beléptetés**: Külön jogosultsági körök a Superuser (su), Keyuser (ku) és általános User felhasználók számára[cite: 15].
*   **Adatvédelem**: A jelszavak SHA-256 titkosítással tárolódnak[cite: 15].
*   **Eseménynapló**: Minden kritikus művelet (mentés, törlés, véglegesítés) visszakövethetően rögzítésre kerül a rendszerlogban[cite: 12].

## 💻 Technikai Adatok

*   **Adattárolás**: Helyi SQLite adatbázis (`berszamitas.db`)[cite: 12, 15].
*   **Interfész**: Python/Tkinter alapú grafikus felület, intelligens vizuális visszajelzésekkel (pl. lüktető értesítő gomb)[cite: 15].
*   **Azonosítás**: A beviteli fejlécben a biztonság érdekében mindig szerepel a kiválasztott dolgozó neve és születési dátuma[cite: 16].

---
*© 2026 Security Bérkalkulátor Projekt – Precizitás minden szektorban.*[cite: 15]
