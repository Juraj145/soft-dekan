# Voľby dekana TF SPU v Nitre

Desktopová aplikácia (Windows) na evidenciu volebného zhromaždenia pre voľbu
kandidáta na dekana Technickej fakulty SPU v Nitre, výpočet uznášaniaschopnosti
a generovanie prezenčnej listiny vo formáte `.docx`.

## Funkcie

- **Vstupné údaje:** celkový počet členov volebného zhromaždenia, miesto a dátum
  konania, funkčné obdobie dekana (od – do).
- **Prezenčná listina** s členmi v dvoch skupinách:
  - členovia akademického senátu,
  - členovia menovaní rektorom / rektorkou.
  Pri každom členovi sa eviduje titul pred menom, meno, priezvisko, titul za
  menom, stav **Prítomný / Ospravedlnený** a možnosť určiť **predsedu volebnej
  komisie**.
- **Abecedné zoradenie** všetkých členov podľa priezviska (slovenská abeceda).
- **Výpočet kvóra:** zhromaždenie je uznášaniaschopné, ak je prítomných aspoň
  **3/5 z celkového počtu** členov (napr. 12 z 20).
- **Export do `.docx`** podľa referenčnej predlohy prezenčnej listiny vrátane
  listiny hostí a zhrnutia uznášaniaschopnosti.
- Uloženie a načítanie rozpracovaných údajov do/zo súboru `.json`.

## Spustenie zo zdrojového kódu

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=src python -m volby_dekana
```

## Testy

```bash
pip install pytest
PYTHONPATH=src python -m pytest
```

## Zostavenie inštalačného `.exe`

`.exe` aj inštalátor sa automaticky zostavujú na Windows runneri cez GitHub
Actions (`.github/workflows/build-windows.yml`) – výsledky nájdeš v artefaktoch
behu. Lokálne na Windowse:

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller build\volby_dekana.spec --noconfirm
# voliteľne inštalátor (vyžaduje Inno Setup 6):
& "$Env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe" build\installer.iss
```

Výsledok: `dist\VolbyDekana.exe` (samostatná aplikácia) a
`dist\VolbyDekana-Setup-<verzia>.exe` (inštalátor).
