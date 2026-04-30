## 🧠 1. A Rendszer Logikai Magja: Az Univerzális Bérszámítás

A szoftver legnagyobb innovációja a **bérforma-agnosztikus megközelítés**. Ez azt jelenti, hogy a számítási motor képes bármilyen bérszerződést értelmezni és abból precíz adatokat kinyerni.

### Óradíj vs. Havibér Kezelése
*   **Dinamikus átváltás:** Havibéres dolgozó esetén a rendszer a háttérben kiszámolja az adott hónapra eső elméleti óradíjat (Havi bér / adott havi munkanapok óraszáma). Ez elengedhetetlen a pótlékok és a távolléti díj pontos meghatározásához.
*   **Távolléti díj (Absence Fee) automatizmus:**
    *   A rendszer figyeli a kieső napokat (szabadság, betegszabadság).
    *   **Havibéreseknél:** Ha a dolgozó szabadságra megy, a fix bérét a rendszer arányosítja, és a távolléti díjat az egy órára jutó alapbér alapján számolja ki, biztosítva a jogszabályi megfelelést.
    *   **Óradíjasoknál:** A rögzített alap-óradíj szolgál a számítás alapjául, de a rendszer képes figyelembe venni az előző időszaki átlagkereseteket is.

---

## 📅 2. Intelligens Naptárkezelés és Vezénylés

A naptármodul a rendszer "szeme", amely látja a munkarendet és automatikusan alkalmazza a szabályokat.

*   **Ünnepnap-algoritmus:** A szoftverbe beépített **Gauss-algoritmus** segítségével a rendszer 2026-ban (és bármely évben) automatikusan tudja, mikorra esik Húsvét, Pünkösd és a többi mozgó ünnep. Nem kell kézzel állítani a piros betűs napokat.
*   **Műszak-analízis:**
    *   A kezdési idő és az időtartam megadása után a szoftver szétválogatja az órákat.
    *   Kiszámolja a **nappali** és az **éjszakai** (22:00 – 06:00 közötti) órák számát.
    *   Azonosítja, ha a műszak **vasárnapra** vagy **munkaszüneti napra** esik, és ezekre automatikusan felszorozza a releváns pótlékokat.

---

## 💰 3. Pénzügyi Modul: "Módosító Tételek"

Ez a rész felelős a bruttó-nettó mozgások finomhangolásáért. Itt kezelhetők azok a tételek, amik nem a közvetlen munkaidőből fakadnak.

*   **Bérelőleg és Törlesztés:** A rendszer képes kezelni a többhavi futamidejű levonásokat. Megadható a tőkeösszeg és a havi törlesztő; a szoftver addig vonja a béregyenlegből, amíg a hátralék el nem fogy.
*   **Ciklikus Extrák:** Jutalmak vagy cafeteria elemek, amik akár fixen minden hónapban, vagy egy meghatározott záró dátumig járnak a dolgozónak.
*   **Adózási jelzők:** Minden egyes tételnél külön beállítható, hogy az adóköteles-e vagy sem, így a rendszer a nettó kifizetést ezek alapján kalkulálja.

---

## 📄 4. A "Bérlap Függelék" – A Transzparencia Eszköze

A hagyományos bérpapírok gyakran érthetetlenek. A Security Bérkalkulátor egy egyedi **PDF generátorral** válaszol erre.

*   **Részletes elszámolás:** A függelék tételesen felsorolja, miért annyi a vége, amennyi.
*   **Egyenleg-történet:** Megmutatja a munkavállalónak a korábbi tartozásait, a már levont összegeket és a még fennmaradó hátralékot. Ez drasztikusan csökkenti a bérszámfejtők felé irányuló reklamációk és kérdések számát.

---

## 🛡️ 5. Technikai Biztonság és Adminisztráció

A rendszer a "Security" nevet nem csak a célpiac, hanem a biztonsági megoldások miatt is viseli.

*   **Jogosultsági szintek:**
    *   **User:** Csak a hozzárendelt adatok rögzítésére képes.
    *   **Keyuser:** Ellenőrizhet és véglegesíthet.
    *   **Superuser (su):** Teljes hozzáférés a törzsadatokhoz és a rendszerbeállításokhoz.
*   **Naplózási rendszer (Logging):** Minden eseményt (bejelentkezés, adatmentés, törlés) egy titkosított naplófájl rögzít, így pontosan tudható, ki és mikor módosította a számokat.
*   **Adatvédelem:** A jelszavak SHA-256 hasheléssel tárolódnak, a kommunikáció pedig zárt adatbázis-kapcsolaton (SQLite) keresztül zajlik.

---

## 🎨 6. Felhasználói Élmény (UI/UX)

A felületet úgy tervezték, hogy nagy adatmennyiség mellett is átlátható maradjon:
*   **Intelligens Fejléc:** A kiválasztott dolgozó neve és születési dátuma mindig látható a beviteli mezők felett, így elkerülhető a téves adatrögzítés.
*   **Vizuális Feedback:** Például az üzenetkezelő gomb lüktetve jelzi, ha új rendszerüzenet vagy fejlesztői értesítés érkezett.
*   **Stabilitás:** A Python/Tkinter alapú fejlesztés biztosítja a villámgyors működést még régebbi irodai gépeken is.

Ez a rendszer tehát nem csak számol, hanem **menedzsel**: összeköti a munkaidő-nyilvántartást, a pénzügyi tervezést és a dolgozói tájékoztatást egyetlen, automatizált keretbe.
