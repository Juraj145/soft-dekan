"""Pomocné funkcie pre prístup k zabaleným súborom a priečinku s údajmi."""
from __future__ import annotations

import os
import sys

NAZOV_PRIECINKA_UDAJE = "Vstupné údaje"
NAZOV_PRIECINKA_ZAPISNICE = "Zápisnice komisie"
NAZOV_PRIECINKA_KANDIDATI = "Kandidáti na dekana a dokumenty"


def cesta_k_asetu(nazov: str) -> str:
    """Vráti absolútnu cestu k súboru v priečinku assets (aj v .exe balíku)."""
    if getattr(sys, "frozen", False):
        zaklad = os.path.join(sys._MEIPASS, "volby_dekana", "assets")  # type: ignore[attr-defined]
    else:
        zaklad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return os.path.join(zaklad, nazov)


def _kandidati_zakladu() -> list[str]:
    """Možné základné priečinky pre 'Vstupné údaje' v poradí preferencie."""
    domov = os.path.expanduser("~")
    kandidati = [
        os.path.join(domov, "OneDrive", "Počítač", "SOFT_DEKAN", "Install"),
        os.path.join(domov, "OneDrive", "SOFT_DEKAN", "Install"),
        os.path.join(domov, "SOFT_DEKAN", "Install"),
    ]
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        kandidati.append(exe_dir)
        kandidati.append(os.path.dirname(exe_dir))
    kandidati.append(os.path.join(domov, "Documents", "SOFT_DEKAN"))
    return kandidati


def priecinok_udajov() -> str:
    """Vráti (a vytvorí) priečinok pre ukladanie vstupných údajov.

    Uprednostní existujúci priečinok '...\\SOFT_DEKAN\\Install'; ak neexistuje,
    použije prvú zmysluplnú alternatívu. Priečinok 'Vstupné údaje' vytvorí.
    """
    for zaklad in _kandidati_zakladu():
        if os.path.isdir(zaklad):
            cesta = os.path.join(zaklad, NAZOV_PRIECINKA_UDAJE)
            try:
                os.makedirs(cesta, exist_ok=True)
                return cesta
            except OSError:
                continue
    nahradny = os.path.join(
        os.path.expanduser("~"), "SOFT_DEKAN", "Install", NAZOV_PRIECINKA_UDAJE
    )
    try:
        os.makedirs(nahradny, exist_ok=True)
    except OSError:
        return os.path.expanduser("~")
    return nahradny


def priecinok_zapisnic() -> str:
    """Vráti (a vytvorí) priečinok pre uložené dokumenty volebnej komisie."""
    return _podpriecinok_udajov(NAZOV_PRIECINKA_ZAPISNICE)


def priecinok_kandidatov() -> str:
    """Vráti (a vytvorí) priečinok pre uložené dokumenty kandidátov."""
    return _podpriecinok_udajov(NAZOV_PRIECINKA_KANDIDATI)


def _podpriecinok_udajov(nazov: str) -> str:
    cesta = os.path.join(priecinok_udajov(), nazov)
    try:
        os.makedirs(cesta, exist_ok=True)
    except OSError:
        return priecinok_udajov()
    return cesta
