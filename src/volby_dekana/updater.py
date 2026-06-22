"""Stiahnutie a spustenie najnovšieho inštalátora z GitHubu.

Program si vie sám skontrolovať a stiahnuť aktualizáciu, takže používateľ
nemusí používať Git ani príkazový riadok.
"""
from __future__ import annotations

import os
import tempfile
import urllib.request

from . import __version__

# Vetva v repozitári, z ktorej sa berú vydania.
GITHUB_VETVA = "devin/1782113058-volby-dekana"
_ZAKLAD = (
    "https://raw.githubusercontent.com/Juraj145/soft-dekan/"
    f"{GITHUB_VETVA}/Program"
)
URL_VERZIA = f"{_ZAKLAD}/version.txt"
URL_INSTALATOR = f"{_ZAKLAD}/VolbyDekana-Setup.exe"

AKTUALNA_VERZIA = __version__


def _otvor(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": "VolbyDekana-Updater"})
    return urllib.request.urlopen(req, timeout=timeout)


def zisti_najnovsiu_verziu(timeout: int = 15) -> str:
    """Načíta číslo najnovšej verzie z repozitára."""
    with _otvor(URL_VERZIA, timeout) as r:
        return r.read().decode("utf-8").strip()


def _verzia_tuple(verzia: str) -> tuple[int, ...]:
    casti: list[int] = []
    for c in verzia.split("."):
        try:
            casti.append(int(c))
        except ValueError:
            casti.append(0)
    return tuple(casti)


def je_novsia(verzia: str) -> bool:
    """Vráti True, ak je zadaná verzia novšia ako aktuálne spustená."""
    return _verzia_tuple(verzia) > _verzia_tuple(AKTUALNA_VERZIA)


def stiahni_instalator(timeout: int = 180) -> str:
    """Stiahne inštalátor do dočasného priečinka a vráti cestu k nemu."""
    cielovy = os.path.join(tempfile.gettempdir(), "VolbyDekana-Setup.exe")
    with _otvor(URL_INSTALATOR, timeout) as r, open(cielovy, "wb") as f:
        f.write(r.read())
    return cielovy
