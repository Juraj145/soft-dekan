"""Vyhodnotenie kola voľby kandidáta na dekana TF SPU v Nitre.

Podľa zásad voľby je kandidát zvolený, ak získa nadpolovičnú väčšinu hlasov
všetkých členov volebného zhromaždenia (t. j. viac ako polovicu z celkového
počtu členov). Ak v 1. kole nikto túto väčšinu nezíska, do 2. kola postupujú
dvaja kandidáti s najvyšším počtom hlasov (pri zhode na druhom mieste postupujú
všetci kandidáti s rovnakým počtom hlasov).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Kandidat


def potrebna_vacsina(celkovy_pocet: int) -> int:
    """Minimálny počet hlasov na zvolenie (nadpolovičná väčšina všetkých členov)."""
    if celkovy_pocet <= 0:
        return 0
    return celkovy_pocet // 2 + 1


@dataclass
class VysledokKola:
    kolo: int
    potrebna_vacsina: int
    poradie: list[tuple[Kandidat, int]] = field(default_factory=list)
    zvoleny: Kandidat | None = None
    postupujuci: list[Kandidat] = field(default_factory=list)


def _hlasy(kandidat: Kandidat, kolo: int) -> int:
    return kandidat.hlasy_k1 if kolo == 1 else kandidat.hlasy_k2


def vyhodnot_kolo(
    kandidati: list[Kandidat], kolo: int, celkovy_pocet: int
) -> VysledokKola:
    """Vyhodnotí kolo voľby z počtov hlasov priradených kandidátom."""
    vacsina = potrebna_vacsina(celkovy_pocet)
    poradie = sorted(
        ((k, _hlasy(k, kolo)) for k in kandidati),
        key=lambda kh: kh[1],
        reverse=True,
    )
    zvoleny = None
    for k, h in poradie:
        if h >= vacsina and vacsina > 0:
            zvoleny = k
            break

    postupujuci: list[Kandidat] = []
    if zvoleny is None and len(poradie) > 2:
        # Dvaja s najvyšším počtom hlasov; pri zhode na 2. mieste všetci zhodní.
        druhy_najvyssi = poradie[1][1]
        postupujuci = [k for k, h in poradie if h >= druhy_najvyssi]
    elif zvoleny is None:
        postupujuci = [k for k, _ in poradie]

    return VysledokKola(
        kolo=kolo,
        potrebna_vacsina=vacsina,
        poradie=poradie,
        zvoleny=zvoleny,
        postupujuci=postupujuci,
    )
