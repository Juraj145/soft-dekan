"""Generovanie prezenčnej listiny do formátu .docx.

Listina sa vytvára vyplnením referenčnej predlohy 'Prezenčná listina.docx'
(zabalenej v assets), takže výsledok zodpovedá predlohe 1:1 – vrátane loga
v hlavičke, písiem, nadpisov a rozloženia. Doplnia sa len údaje:
miesto konania (po riadkoch), dátum a tabuľka členov.
"""
from __future__ import annotations

import copy

from docx import Document
from docx.table import Table, _Row
from docx.text.paragraph import Paragraph

from .models import Zhromazdenie
from .resources import cesta_k_asetu

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
