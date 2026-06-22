"""Generovanie prezenčnej listiny do formátu .docx.

Listina sa vytvára vyplnením referenčnej predlohy 'Prezenčná listina.docx'
(zabalenej v assets), takže výsledok zodpovedá predlohe 1:1 – vrátane loga
v hlavičke, písiem, nadpisov a rozloženia. Doplnia sa len údaje:
miesto konania (po riadkoch), dátum a tabuľka členov.
"""
from __future__ import annotations

import copy

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table, _Row
from docx.text.paragraph import Paragraph

from .models import Kandidat, Skupina, Stav, Zhromazdenie
from .resources import cesta_k_asetu
from .volba import VysledokKola, vyhodnot_kolo

# Indexy tabuliek v predlohe.
_TAB_CLENOVIA = 1
_TAB_HOSTIA = 3


def _nastav_za_tabulatorom(p: Paragraph, hodnota: str) -> None:
    """Nahradí text za prvým tabulátorom v odseku (zachová popis pred ním)."""
    for idx, run in enumerate(p.runs):
        if "\t" in run.text:
            pred = run.text.split("\t")[0]
            run.text = f"{pred}\t{hodnota}"
            for zvysny in p.runs[idx + 1:]:
                zvysny.text = ""
            return
    if p.runs:
        p.runs[-1].text += hodnota


def _klon_odseku_za(p: Paragraph) -> Paragraph:
    novy = copy.deepcopy(p._p)
    p._p.addnext(novy)
    return Paragraph(novy, p._parent)


def _odstran_odsek(p: Paragraph) -> None:
    p._p.getparent().remove(p._p)


def _nastav_text_bunky(cell, text: str) -> None:
    """Nastaví text bunky do prvého behu (zachová formátovanie predlohy)."""
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def _klon_riadku(table: Table, vzor: _Row) -> None:
    novy = copy.deepcopy(vzor._tr)
    table._tbl.append(novy)


def _odstran_riadok(row: _Row) -> None:
    row._tr.getparent().remove(row._tr)


def _vypln_miesto_a_datum(doc: Document, z: Zhromazdenie) -> None:
    odseky = doc.paragraphs
    i_miesto = next(
        (i for i, p in enumerate(odseky) if p.text.strip().startswith("Miesto konania")),
        None,
    )
    i_datum = next(
        (i for i, p in enumerate(odseky) if p.text.strip().startswith("Dátum")),
        None,
    )
    if i_miesto is None or i_datum is None:
        return

    _nastav_za_tabulatorom(odseky[i_datum], z.datum)

    hodnoty = [r.strip() for r in z.miesto_riadky if r.strip()]
    pokracovacie = odseky[i_miesto + 1: i_datum]

    # Prvý riadok adresy patrí k odseku „Miesto konania:".
    _nastav_za_tabulatorom(odseky[i_miesto], hodnoty[0] if hodnoty else "")

    zvysok = hodnoty[1:]
    posledny = odseky[i_miesto]
    for k, hodnota in enumerate(zvysok):
        if k < len(pokracovacie):
            cielovy = pokracovacie[k]
        else:
            cielovy = _klon_odseku_za(posledny)
        _nastav_za_tabulatorom(cielovy, hodnota)
        posledny = cielovy

    # Nepoužité pokračovacie riadky predlohy odstránime.
    for p in pokracovacie[len(zvysok):]:
        _odstran_odsek(p)


def _vypln_clenov(doc: Document, z: Zhromazdenie) -> None:
    table = doc.tables[_TAB_CLENOVIA]
    mena = [c.cele_meno for c in z.clenovia_zoradeni()]
    pocet = max(z.celkovy_pocet, len(mena))

    while len(table.rows) - 1 < pocet:
        _klon_riadku(table, table.rows[-1])
    while len(table.rows) - 1 > pocet:
        _odstran_riadok(table.rows[-1])

    for i in range(pocet):
        bunky = table.rows[i + 1].cells
        _nastav_text_bunky(bunky[0], f"{i + 1}.")
        _nastav_text_bunky(bunky[1], mena[i] if i < len(mena) else "")
        _nastav_text_bunky(bunky[2], "")


def _precisluj_hosti(doc: Document) -> None:
    """Opraví poradové čísla v tabuľke hostí (predloha mala preskočené č. 21)."""
    table = doc.tables[_TAB_HOSTIA]
    for i, row in enumerate(table.rows[1:], start=1):
        _nastav_text_bunky(row.cells[0], f"{i}.")


def vytvor_prezencnu_listinu(z: Zhromazdenie) -> Document:
    """Vytvorí dokument prezenčnej listiny vyplnením referenčnej predlohy."""
    doc = Document(cesta_k_asetu("prezencna_template.docx"))
    _vypln_miesto_a_datum(doc, z)
    _vypln_clenov(doc, z)
    _precisluj_hosti(doc)
    return doc


def uloz_prezencnu_listinu(z: Zhromazdenie, cesta: str) -> None:
    vytvor_prezencnu_listinu(z).save(cesta)


def uloz_pokyny_hlasovanie(cesta: str) -> None:
    """Uloží pokyny k vyplňovaniu hlasovacieho lístka z referenčnej predlohy."""
    doc = Document(cesta_k_asetu("pokyny_template.docx"))
    doc.save(cesta)


# --------------------------------------------------------------- hlasovací lístok
def _nastav_odsek_text(p: Paragraph, text: str) -> None:
    """Nahradí celý text odseku do prvého behu (zachová štýl predlohy)."""
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def _vypln_tabulku(table: Table, riadky: list[list[str]]) -> None:
    """Naplní dátové riadky tabuľky (riadok 0 je hlavička) podľa zoznamu hodnôt."""
    pocet = max(1, len(riadky))
    while len(table.rows) - 1 < pocet:
        _klon_riadku(table, table.rows[-1])
    while len(table.rows) - 1 > pocet:
        _odstran_riadok(table.rows[-1])
    for i in range(pocet):
        bunky = table.rows[i + 1].cells
        hodnoty = riadky[i] if i < len(riadky) else [""] * len(bunky)
        for ci, bunka in enumerate(bunky):
            _nastav_text_bunky(bunka, hodnoty[ci] if ci < len(hodnoty) else "")


def vytvor_hlasovaci_listok(
    z: Zhromazdenie, kolo: int, kandidati: list[Kandidat]
) -> Document:
    """Vytvorí hlasovací lístok pre dané kolo vyplnením referenčnej predlohy."""
    doc = Document(cesta_k_asetu("hlasovaci_listok_template.docx"))
    for p in doc.paragraphs:
        if p.text.strip().startswith("Termín konania volieb"):
            _nastav_za_tabulatorom(p, z.datum)
        elif p.text.strip().endswith("kolo volieb"):
            for r in p.runs:
                if "kolo volieb" in r.text:
                    r.text = r.text.replace("kolo volieb", f"{kolo}. kolo volieb")
                    break
    tabulka = doc.tables[1]
    riadky = [[f"{i + 1}.", k.cele_meno] for i, k in enumerate(kandidati)]
    _vypln_tabulku(tabulka, riadky)
    return doc


def uloz_hlasovaci_listok(
    z: Zhromazdenie, kolo: int, kandidati: list[Kandidat], cesta: str
) -> None:
    vytvor_hlasovaci_listok(z, kolo, kandidati).save(cesta)


# ----------------------------------------------------- zápisnica z volieb (krok 4)
# Indexy tabuliek v predlohe zápisnice.
_ZAP_TAB_KOMISIA = 1
_ZAP_TAB_SENAT = 2
_ZAP_TAB_REKTOR = 3
_ZAP_TAB_OSPRAVEDLNENI = 4
_ZAP_TAB_KANDIDATI = 5
_ZAP_TAB_SCHVALENI = 6
_ZAP_TAB_VYSLEDOK_K1 = 8
_ZAP_TAB_VYSLEDOK_K2 = 9
_ZAP_TAB_PODPISY = 10


def _zaver_kolo1(v1: VysledokKola) -> str:
    if v1.zvoleny is not None:
        h = v1.zvoleny.hlasy_k1
        return (
            f"Kandidát {v1.zvoleny.cele_meno} získal nadpolovičnú väčšinu všetkých "
            f"členov volebného zhromaždenia ({h} hlasov, min. {v1.potrebna_vacsina}) "
            "a bol ZVOLENÝ za dekana Technickej fakulty na funkčné obdobie."
        )
    riadky = "\n".join(
        f" - {k.cele_meno} ({k.hlasy_k1} hlasov)" for k in v1.postupujuci
    )
    return (
        "1. kolo bolo neúspešné. Žiadny z kandidátov na dekana Technickej fakulty "
        "nezískal nadpolovičnú väčšinu všetkých členov volebného zhromaždenia "
        f"(min. {v1.potrebna_vacsina} hlasov).\n\nDo 2. kola postupujú:\n{riadky}"
    )


def _zaver_kolo2(v1: VysledokKola, v2: VysledokKola | None) -> str:
    if v2 is None:
        return "2. kolo sa neuskutočnilo – kandidát bol zvolený v 1. kole."
    if v2.zvoleny is not None:
        h = v2.zvoleny.hlasy_k2
        return (
            f"Kandidát {v2.zvoleny.cele_meno} získal nadpolovičnú väčšinu všetkých "
            f"členov volebného zhromaždenia ({h} hlasov, min. {v2.potrebna_vacsina}) "
            "a bol ZVOLENÝ za dekana Technickej fakulty na funkčné obdobie."
        )
    return (
        "2. kolo bolo neúspešné. Žiadny z kandidátov nezískal nadpolovičnú väčšinu "
        f"všetkých členov volebného zhromaždenia (min. {v2.potrebna_vacsina} hlasov)."
    )


def _vypln_pocty(doc: Document, z: Zhromazdenie, v1: VysledokKola,
                 v2: VysledokKola | None) -> None:
    pritomni = sum(1 for c in z.clenovia if c.stav == Stav.PRITOMNY)
    ospravedlneni = sum(1 for c in z.clenovia if c.stav == Stav.OSPRAVEDLNENY)
    platne1 = sum(k.hlasy_k1 for k in z.kandidati)
    platne2 = sum(k.hlasy_k2 for k in v1.postupujuci) if v2 else 0
    kolo = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        if t == "1. kolo voľby":
            kolo = 1
        elif t == "2. kolo voľby":
            kolo = 2
        elif t.startswith("Celkový počet členov"):
            _nastav_za_tabulatorom(p, str(z.celkovy_pocet))
        elif t.startswith("Počet prítomných členov"):
            _nastav_za_tabulatorom(p, str(pritomni))
        elif t.startswith("Počet ospravedlnených členov"):
            _nastav_za_tabulatorom(p, str(ospravedlneni))
        elif t.startswith("Termín vyhotovenia zápisnice"):
            _nastav_za_tabulatorom(p, z.datum)
        elif t.startswith("Počet platných hlasov"):
            _nastav_za_tabulatorom(p, str(platne1 if kolo == 1 else platne2))
        elif t.startswith("Počet neplatných hlasov"):
            _nastav_za_tabulatorom(
                p, str(z.neplatne_k1 if kolo == 1 else z.neplatne_k2))
        elif t.startswith("Počet odovzdaných hlasovacích lístkov"):
            spolu = (platne1 + z.neplatne_k1) if kolo == 1 else (
                platne2 + z.neplatne_k2)
            _nastav_za_tabulatorom(p, str(spolu))


def vytvor_zapisnicu(z: Zhromazdenie) -> Document:
    """Vytvorí zápisnicu z volebného zhromaždenia vyplnením referenčnej predlohy."""
    v1 = vyhodnot_kolo(z.kandidati_zoradeni(), 1, z.celkovy_pocet)
    postupujuci = sorted(
        v1.postupujuci, key=lambda k: (k.priezvisko.lower(), k.meno.lower())
    )
    v2 = vyhodnot_kolo(postupujuci, 2, z.celkovy_pocet) if (
        v1.zvoleny is None and postupujuci
    ) else None

    doc = Document(cesta_k_asetu("zapisnica_template.docx"))

    komisia = z.komisia()
    _vypln_tabulku(doc.tables[_ZAP_TAB_KOMISIA],
                   [[f"{i + 1}.", c.cele_meno] for i, c in enumerate(komisia)])
    # Zoznamy členov volebného zhromaždenia podľa skupiny (z kroku 1).
    senat = [c for c in z.clenovia_zoradeni() if c.skupina == Skupina.SENAT]
    rektor = [c for c in z.clenovia_zoradeni() if c.skupina == Skupina.REKTOR]
    _vypln_tabulku(doc.tables[_ZAP_TAB_SENAT],
                   [[f"{i + 1}.", c.cele_meno] for i, c in enumerate(senat)])
    _vypln_tabulku(doc.tables[_ZAP_TAB_REKTOR],
                   [[f"{i + 1}.", c.cele_meno] for i, c in enumerate(rektor)])

    ospravedlneni = [
        c for c in z.clenovia_zoradeni() if c.stav == Stav.OSPRAVEDLNENY
    ]
    _vypln_tabulku(doc.tables[_ZAP_TAB_OSPRAVEDLNENI],
                   [[f"{i + 1}.", c.cele_meno] for i, c in enumerate(ospravedlneni)])

    kandidati = z.kandidati_zoradeni()
    _vypln_tabulku(doc.tables[_ZAP_TAB_KANDIDATI],
                   [[f"{i + 1}.", k.cele_meno, str(k.pocet_navrhov)]
                    for i, k in enumerate(kandidati)])
    _vypln_tabulku(doc.tables[_ZAP_TAB_SCHVALENI],
                   [[f"{i + 1}.", k.cele_meno] for i, k in enumerate(kandidati)])

    _vypln_tabulku(
        doc.tables[_ZAP_TAB_VYSLEDOK_K1],
        [[f"{i + 1}.", k.cele_meno, str(h)]
         for i, (k, h) in enumerate(v1.poradie)],
    )
    if v2 is not None:
        _vypln_tabulku(
            doc.tables[_ZAP_TAB_VYSLEDOK_K2],
            [[f"{i + 1}.", k.cele_meno, str(h)]
             for i, (k, h) in enumerate(v2.poradie)],
        )
    else:
        _vypln_tabulku(doc.tables[_ZAP_TAB_VYSLEDOK_K2], [["", "", ""]])

    _vypln_tabulku(doc.tables[_ZAP_TAB_PODPISY],
                   [[f"{i + 1}.", c.cele_meno, ""] for i, c in enumerate(komisia)])

    _vypln_pocty(doc, z, v1, v2)
    _vypln_miesto_zapisnica(doc, z)
    _vypln_zavery(doc, v1, v2)
    return doc


def _vypln_miesto_zapisnica(doc: Document, z: Zhromazdenie) -> None:
    """Adresu miesta konania vypíše po riadkoch zarovnanú k pravému okraju."""
    odseky = doc.paragraphs
    i = next(
        (i for i, p in enumerate(odseky)
         if p.text.strip().startswith("Miesto konania")),
        None,
    )
    if i is None:
        return
    riadky = [r.strip() for r in z.miesto_riadky if r.strip()]
    posledny = odseky[i]
    for hodnota in riadky:
        novy = _klon_odseku_za(posledny)
        _nastav_odsek_text(novy, hodnota)
        novy.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        posledny = novy


def _vypln_zavery(doc: Document, v1: VysledokKola, v2: VysledokKola | None) -> None:
    """Doplní záverové odseky 1. a 2. kola (text podľa výsledku)."""
    odseky = doc.paragraphs
    # Záver 1. kola: odsek pred nadpisom „2. kolo voľby".
    idx_k2 = next(
        (i for i, p in enumerate(odseky) if p.text.strip() == "2. kolo voľby"),
        None,
    )
    if idx_k2 is not None:
        for i in range(idx_k2 - 1, -1, -1):
            t = odseky[i].text.strip()
            if t.startswith("1. kolo bolo") or (
                t.startswith("Kandidát ") and "ZVOLENÝ" in t
            ):
                _nastav_odsek_text(odseky[i], _zaver_kolo1(v1))
                break
    # Záver 2. kola: posledný odsek so „získal/ZVOLENÝ/neúspešné" za nadpisom.
    for i in range(len(odseky) - 1, (idx_k2 or 0), -1):
        t = odseky[i].text.strip()
        if t.startswith("Kandidát ") and "ZVOLENÝ" in t:
            _nastav_odsek_text(odseky[i], _zaver_kolo2(v1, v2))
            break


def uloz_zapisnicu(z: Zhromazdenie, cesta: str) -> None:
    vytvor_zapisnicu(z).save(cesta)
