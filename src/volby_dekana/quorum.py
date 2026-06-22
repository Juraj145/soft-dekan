"""Výpočet uznášaniaschopnosti (kvóra) volebného zhromaždenia.

Podľa zásad voľby kandidáta na dekana TF SPU v Nitre musí byť prítomných
aspoň 3/5 z celkového počtu členov volebného zhromaždenia.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from .models import Stav, Zhromazdenie

# Požadovaný podiel prítomných z celkového počtu členov.
POTREBNY_PODIEL = Fraction(3, 5)


@dataclass
class VysledokKvora:
    celkovy_pocet: int
    potrebne_kvorum: int
    pocet_pritomnych: int
    pocet_ospravedlnenych: int
    uznasaniaschopne: bool

    @property
    def chyba_do_kvora(self) -> int:
        """Koľko prítomných ešte chýba do dosiahnutia kvóra (0 ak je splnené)."""
        return max(0, self.potrebne_kvorum - self.pocet_pritomnych)


def potrebne_kvorum(celkovy_pocet: int) -> int:
    """Minimálny počet prítomných (zaokrúhlené nahor z 3/5 celkového počtu)."""
    if celkovy_pocet <= 0:
        return 0
    return math.ceil(POTREBNY_PODIEL * celkovy_pocet)


def vyhodnot_kvorum(z: Zhromazdenie) -> VysledokKvora:
    pritomni = sum(1 for c in z.clenovia if c.stav == Stav.PRITOMNY)
    ospravedlneni = sum(1 for c in z.clenovia if c.stav == Stav.OSPRAVEDLNENY)
    kvorum = potrebne_kvorum(z.celkovy_pocet)
    return VysledokKvora(
        celkovy_pocet=z.celkovy_pocet,
        potrebne_kvorum=kvorum,
        pocet_pritomnych=pritomni,
        pocet_ospravedlnenych=ospravedlneni,
        uznasaniaschopne=pritomni >= kvorum and kvorum > 0,
    )
