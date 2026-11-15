# FFBeast – wsuwany Quick Release (klin V + jaskółczy ogon)

Stan: **model CAD gotowy i sprawdzony geometrycznie w Fusion 360. Nic nie zostało wydrukowane ani przetestowane fizycznie.**
Wszystkie liczby wytrzymałościowe poniżej to szacunki ręczne, nie wyniki testów ani MES.

## Pliki

| Plik | Co to jest |
|---|---|
| `cad/FFBeast_QR.f3d` | projekt Fusion 360 (3 komponenty, 74 operacje na osi czasu, parametry użytkownika `qr_*`) |
| `cad/FFBeast_QR.step` | to samo jako STEP |
| `cad/build_qr.py` | skrypt-generator: zmieniasz wartości w słowniku `P` i uruchamiasz w Fusion – buduje cały zespół od nowa |
| `cad/verify_qr.py` | skrypt kontroli kolizji i dopasowania (tylko odczyt) |
| `stl/A_baza_QR.stl` | część A, już w orientacji do druku |
| `stl/B_adapter_kierownicy.stl` | część B, już w orientacji do druku (odwrócona, strona kierownicy na stole) |
| `stl/C_sruba_blokujaca.stl` | śruba blokująca, już w orientacji do druku (na leżąco) |
| `img/*.png` | widoki z Fusion |

Uwaga do parametrów: parametry `qr_*` w Fusion są listą wartości, a szkice są liczone przez skrypt.
Żeby zmienić wymiar, edytuj `P` w `build_qr.py` i uruchom skrypt ponownie (ok. 20 s) – to jest właściwe źródło parametryczne.

## 1. Analiza dostarczonych STL

W folderze były trzy pliki. Wszystkie mają ten sam interfejs: **6 otworów na okręgu Ø70,00 mm co 60°**.

| Plik | Gabaryt | Otwory na Ø70 | Reszta |
|---|---|---|---|
| `flansza (3).stl` | Ø85 (kołnierz Ø88) × 30,4 mm | 12 × Ø6,27 co 30° (dwa zestawy po 6) | szczeliny na nakrętki 8,3 × 4,3 mm (pasują do M5), 4,5 mm pod czołem; otwór środkowy Ø35 / Ø50; 4 × Ø3 na Ø42 |
| `flansza2 (1).stl` | Ø83 × 76 mm | podstawa 15 mm: 12 × Ø7; górny kołnierz 6 mm: 6 × Ø5 | tuleja Ø60 / Ø50 |
| `Wzor do wiercenia otworow.stl` | Ø80 × 11 mm | 6 × Ø5 + Ø5 w środku | szablon |

Czego STL **nie** mówi i co trzeba potwierdzić – patrz „Do potwierdzenia” na końcu.

## 2. Wybrana konstrukcja

![zespół](img/zespol.png)

- **Część A (baza)** – dysk Ø86 × 16 mm przykręcony 6 śrubami do flanszy. Ma kanał w kształcie litery V z podciętymi ścianami oraz wieżyczkę ze śrubą blokującą.
- **Część B (adapter kierownicy)** – dysk Ø86 × 10 mm z piórem w kształcie V pasującym do kanału; przykręcony do kierownicy jej obecnymi śrubami.
- **Część C (śruba blokująca)** – drukowana, gwint trapezowy, skok 3 mm. Wciąga pióro w klin i trzyma je tam.

Kierownica odsuwa się od flanszy o **26 mm**.

Jak to działa:
1. Kanał zwęża się w planie (półkąt 14°). Pióro wsuwa się w niego aż oprze się **obiema** ścianami naraz – luz boczny i obrotowy znika niezależnie od dokładności druku.
2. Ściany są podcięte o 35° (jaskółczy ogon), więc dociśnięcie klina jednocześnie ściąga płytę B do powierzchni A – znika luz osiowy.
3. Śruba ciągnie pióro w głąb klina i jest jedynym elementem, który nie pozwala mu się cofnąć. Klin 14° **nie jest samohamowny** – celowo: mały kąt dawałby samohamowność, ale każda 0,1 mm błędu druku przesuwałaby kierownicę z osi o ok. 2 mm.

### Porównanie rozważanych geometrii

| Geometria | Luz | Ocena |
|---|---|---|
| Równoległy jaskółczy ogon | zawsze zostaje luz druku (0,1–0,2 mm) | odrzucony |
| Jaskółczy ogon z listwą dociskową | zero, ale kilka śrub do regulacji | odrzucony – za dużo części |
| Płaski klin bez podcięcia | zero w planie, ale nic nie trzyma osiowo | odrzucony |
| Klin o małym kącie (3–5°) | zero, samohamowny | odrzucony – położenie osi zbyt czułe na tolerancję druku |
| **Klin V 14° + podcięcie 35°** | zero w trzech kierunkach, pozycja powtarzalna (0,1 mm błędu → 0,4 mm w osi Y) | **wybrany** |

### Blokada – dlaczego śruba i dlaczego z boku

- Śruba przez sam środek w osi kierownicy nie da się obsłużyć: od przodu zasłania ją kierownica, od tyłu silnik.
- Zatrzask i dźwignię wykluczyłeś; blokada bez regulacji nie kasuje zużycia.
- Śruba biegnie więc **w kierunku wsuwania**, przez środek mechanizmu, a pokrętło wystaje promieniowo z bazy.
- Jest w całości drukowana. Ma szyjkę i krótki gwint w wieżyczce, dzięki czemu po odkręceniu **nie wypada** z bazy.
- Metalowej śruby do blokady nie trzeba kupować. Jest to jednak najsłabszy element zespołu (patrz pkt 6).

## 3. Co trzeba dokupić

Nie da się tego uniknąć przy dwóch częściach: obecne 6 śrub trzyma kierownicę, a baza też musi być czymś przykręcona.

| Ilość | Element | Do czego |
|---|---|---|
| 6 | śruba **M5 × 16, łeb kulisty ISO 7380** | część A → flansza (wchodzą w obecne nakrętki flanszy) |
| 6 | nakrętka M5 (DIN 934) | gniazda w części B |

Łeb kulisty jest konieczny w dwóch otworach leżących w dnie kanału (pod łbem zostaje 4,8 mm materiału). Zwykły łeb walcowy M5 tam się nie zmieści.

## 4. Montaż

**Część A**
1. Odkręć kierownicę. Nakrętki we flanszy zostają.
2. Przyłóż A płaską stroną do flanszy, wieżyczką **w dół**.
3. Wkręć 6 śrub M5 × 16 na krzyż, lekko. Wyrównaj A z obrzeżem flanszy na całym obwodzie, potem dokręć. Nie dociągaj na siłę – to PETG.
4. Wkręć śrubę C w wieżyczkę, aż gwint przejdzie przez krótki gwint wejściowy i śruba zacznie się swobodnie przesuwać.

**Część B**
1. Włóż 6 nakrętek M5 w gniazda (strona z piórem).
2. Przyłóż B gładką stroną do tyłu kierownicy.
3. Przykręć obecnymi śrubami kierownicy. **Końce śrub nie mogą wystawać ponad powierzchnię z gniazdami** – inaczej B nie wsunie się na A. Dopuszczalne wystawanie śruby za tył kierownicy: 8–10 mm. Jeśli jest większe, daj podkładki pod łby albo krótsze śruby.

**Zakładanie kierownicy**
1. Odkręć śrubę C do oporu (ok. 3,5 obrotu).
2. Przyłóż kierownicę ok. 15 mm powyżej pozycji końcowej – pióro wpada w szeroką część kanału.
3. Zsuń w dół do oporu.
4. Dokręć śrubę C palcami, do wyraźnego oporu.

**Zdejmowanie:** odkręć C aż przestanie trzymać, przesuń kierownicę ok. 15 mm w górę, zdejmij do siebie.

## 5. Parametry druku (Ender 3 V3, dysza 0,4)

| | A – baza | B – adapter | C – śruba |
|---|---|---|---|
| Materiał | PETG | PETG | PETG |
| Orientacja | jak w STL: płaska strona na stole | jak w STL: strona kierownicy na stole, pióro do góry | jak w STL: na leżąco, na ściętej płaszczyźnie |
| Warstwa | 0,20 mm | 0,20 mm | 0,12–0,16 mm |
| Ścianki | 6 | 6 | 6 |
| Góra / dół | 6 / 6 | 6 / 6 | – |
| Wypełnienie | 60 % gyroid | 60 % gyroid | 100 % |
| Podpory | brak | brak | brak; brim 5 mm |
| Filament (szac.) | ok. 75–80 g | ok. 68–72 g | ok. 5 g |
| Czas (szac.) | ok. 3–3,5 h | ok. 3 h | ok. 25 min |

- Temperatura 240–250 °C, stół 80 °C, chłodzenie 30–50 % – ważniejsze jest zespolenie warstw niż wygląd.
- Czas i masa to szacunek z objętości (A 69,1 cm³, B 61,6 cm³, C 3,6 cm³); dokładne wartości poda slicer.
- PLA nie używaj: pełza pod stałym naciskiem klina i mięknie przy ok. 55 °C. TPU nie jest tu potrzebne.
- Śruba C musi być drukowana na leżąco. Na stojąco warstwy byłyby w poprzek rozciągania i szyjka by pękła.

Kierunek warstw: w A i B warstwy są prostopadłe do osi kierownicy. Moment obrotowy idzie wzdłuż warstw (mocny kierunek). Odrywanie kierownicy od bazy rozciąga warstwy pióra w poprzek (słaby kierunek) – dlatego szyjka pióra ma ok. 1300 mm² przekroju.

## 6. Szacunek obciążeń i punkty awarii

Założenia: moment 15 N·m, siła na obręczy 150 N na promieniu 150 mm (22,5 N·m zginania).

| Miejsce | Szacunek | Uwagi |
|---|---|---|
| Ściany klina – moment obrotowy | ok. 1,5–2 MPa nacisku | duży zapas |
| Szyjka pióra – odrywanie (w poprzek warstw) | ok. 1,5–2 MPa | PETG między warstwami wytrzymuje statycznie 15–25 MPa; zależy od jakości druku |
| Ściany klina – odrywanie | ok. 3–4 MPa nacisku | podcięcie 35° zwielokrotnia siłę ok. 1,7× |
| **Śruba C – rdzeń Ø7,5 (44 mm²)** | przy 500 N ok. 11 MPa | **najsłabszy element**; zapas statyczny ok. 3–4×, na zmęczenie i pełzanie mniejszy |
| Gwint śruby (3 zwoje w zazębieniu) | ok. 4–5 MPa | – |
| Pod łbami śrub A w dnie kanału (4,8 mm) | – | nie dociągać na siłę |

Co się stanie, gdy coś zawiedzie:
- **Pęknie lub odkręci się śruba C** → kierownica może wysunąć się w górę o 15 mm i wtedy zejść z bazy. Nic poza śrubą jej wtedy nie trzyma.
- **Rozwarstwi się pióro B** → kierownica odpada razem z płytą.
- **Pełzanie PETG** → po kilku dniach śruba będzie luźniejsza; trzeba ją dociągać.
- **Zużycie ścian klina** → pióro siada głębiej; zapas wynosi 3 mm, potem pióro oprze się o ścianę końcową i pojawi się luz.

Jeżeli śruba C okaże się za słaba, sensowną poprawką jest metalowa śruba M5/M6 z nakrętką w piórze – wymaga zmiany modelu.

## 7. Co zostało sprawdzone w CAD

Sprawdzone skryptem `verify_qr.py` na gotowym modelu:
- każda część to jedna zamknięta bryła, oś czasu bez błędów, STL-e szczelne;
- kolizja A–B, A–C, B–C w pozycji nominalnej: **0 mm³**;
- pióro siada w klinie 0,4 mm za pozycją nominalną (zgodnie z założonym luzem 0,10 mm na stronę);
- w pozycji zamkniętej obrót o 0,5° i przesunięcie boczne o 0,3 mm dają kolizję – połączenie jest kształtowe;
- podniesienie B w osi przy wysunięciu 0–12 mm daje kolizję, od 14 mm jest wolne;
- śruba Tr11×3 w gwincie Tr12×3 obraca się bez kolizji w oknie ±20° (luz osiowy ok. 0,3 mm – celowy, pod druk).

Nie sprawdzone: wytrzymałość, sztywność, rzeczywiste pasowanie po wydruku, zachowanie pod FFB.

## 8. Plan testów prototypu

1. **Pasowanie na sucho, bez silnika.** Wsuń B w A ręką. Zmierz szczelinę między czołem pióra a ścianą wieżyczki: powinna wynosić 2–3 mm. Poniżej 1 mm → zwiększ `fit_clr` o 0,05–0,10 i wydrukuj B ponownie. Powyżej 4 mm → zmniejsz.
2. **Śruba.** Musi wkręcać się palcami na całej długości. Jeśli się zacina, przeskaluj C w slicerze do 97–98 % w osiach X i Z.
3. **Luz ręką, silnik wyłączony.** Dokręć C i spróbuj poruszyć kierownicą obrotowo, na boki i do siebie. Nie powinno być wyczuwalnego ruchu ani stuku.
4. **Próba statyczna, silnik wyłączony.** Obciąż obręcz ok. 5 kg w kilku kierunkach; obejrzyj nasadę pióra i wieżyczkę pod kątem białych rys.
5. **FFB 10–20 %**, 10 minut, spokojne ruchy. Potem zdejmij kierownicę i obejrzyj ściany klina, śrubę i szczelinę z pkt 1.
6. **Zwiększaj siłę stopniowo** (30 → 50 → 70 %), po każdym kroku oględziny i sprawdzenie, czy śruba nie poluzowała się.
7. **Pełna siła dopiero po kilku godzinach bez zmian.** Przez pierwsze tygodnie dociągaj śrubę przed każdą sesją.

Podczas prób pod napięciem nie trzymaj palców przy mechanizmie i pokrętle. Przerwij test, jeśli pojawi się stuk, luz, biała rysa albo śruba daje się dokręcić wyraźnie dalej niż poprzednio.

## Do potwierdzenia

1. **Która flansza jest zamontowana** – `flansza (3)` czy `flansza2`? Projekt pasuje do obu (ten sam rozstaw), ale warto to wiedzieć.
2. **Czy śruby kierownicy to M5.** Wynika to tylko ze szczelin na nakrętki w STL. Jeśli to M6, trzeba zmienić `a_hole_d`, `a_cbore_d`, `b_hole_d`, `b_nut_af`.
3. **Ile śruby wystają za tył kierownicy** (potrzebne 8–10 mm).
4. **Czy tył kierownicy jest płaski na średnicy 86 mm** i czy nic nie wystaje ze środka.
5. **Maksymalny moment ustawiony w FFBeast.**
