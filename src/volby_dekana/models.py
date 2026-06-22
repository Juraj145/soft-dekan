"""Dátové modely pre voľby dekana TF SPU v Nitre."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum


class Skupina(str, Enum):
    """Skupina, do ktorej člen volebného zhromaždenia patrí."""

    SENAT = "Člen akademického senátu"
    REKTOR = "Menovaný rektorom / rektorkou"


class Stav(str, Enum):
    """Stav účasti člena na volebnom zhromaždení."""

    PRITOMNY = "Prítomný"
    OSPRAVEDLNENY = "Ospravedlnený"


@dataclass
class Clen:
    """Člen volebného zhromaždenia."""

    meno: str
    priezvisko: str
    titul_pred: str = ""
    titul_za: str = ""
    skupina: Skupina = Skupina.SENAT
    stav: Stav = Stav.PRITOMNY
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def tituly(self) -> str:
        """Tituly v skrátenom zobrazení, napr. 'Ing. / PhD.'."""
        casti = [self.titul_pred.strip(), self.titul_za.strip()]
        return " / ".join(c for c in casti if c)

    @property
    def cele_meno(self) -> str:
        """Meno v tvare 'Ing. Meno Priezvisko, PhD.' (tituly voliteľné)."""
        zaklad = " ".join(
            c
            for c in (self.titul_pred.strip(), self.meno.strip(), self.priezvisko.strip())
            if c
        )
        za = self.titul_za.strip()
        return f"{zaklad}, {za}" if za else zaklad

    def to_dict(self) -> dict:
        d = asdict(self)
        d["skupina"] = self.skupina.value
        d["stav"] = self.stav.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Clen":
        return cls(
            meno=d.get("meno", ""),
            priezvisko=d.get("priezvisko", ""),
            titul_pred=d.get("titul_pred", d.get("titul", "")),
            titul_za=d.get("titul_za", ""),
            skupina=Skupina(d.get("skupina", Skupina.SENAT.value)),
            stav=Stav(d.get("stav", Stav.PRITOMNY.value)),
            id=d.get("id", uuid.uuid4().hex),
        )


# Počet riadkov adresy miesta konania.
POCET_RIADKOV_MIESTA = 5

# Počet členov volebnej komisie.
POCET_KOMISIA = 5


@dataclass
class Material:
    """Pripojený dokument (zápisnica zo zasadnutia volebnej komisie)."""

    nazov: str
    cesta: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Material":
        return cls(
            nazov=d.get("nazov", ""),
            cesta=d.get("cesta", ""),
            id=d.get("id", uuid.uuid4().hex),
        )


@dataclass
class Zhromazdenie:
    """Údaje o volebnom zhromaždení a jeho členoch."""

    celkovy_pocet: int = 20
    miesto_riadky: list[str] = field(
        default_factory=lambda: [""] * POCET_RIADKOV_MIESTA
    )
    datum: str = ""
    obdobie_od: str = ""
    obdobie_do: str = ""
    predseda_komisie_id: str | None = None
    komisia_ids: list[str] = field(default_factory=list)
    materialy_komisie: list[Material] = field(default_factory=list)
    clenovia: list[Clen] = field(default_factory=list)

    @property
    def miesto(self) -> str:
        """Adresa miesta konania ako viacriadkový text (neprázdne riadky)."""
        return "\n".join(r.strip() for r in self.miesto_riadky if r.strip())

    def clenovia_zoradeni(self) -> list[Clen]:
        """Všetci členovia zoradení abecedne podľa priezviska (potom mena)."""
        return sorted(
            self.clenovia,
            key=lambda c: (
                _key_sk(c.priezvisko),
                _key_sk(c.meno),
            ),
        )

    def predseda_komisie(self) -> Clen | None:
        if self.predseda_komisie_id is None:
            return None
        for c in self.clenovia:
            if c.id == self.predseda_komisie_id:
                return c
        return None

    def komisia(self) -> list[Clen]:
        """Členovia volebnej komisie (predseda ako prvý, potom podľa priezviska)."""
        vybrani = [c for c in self.clenovia if c.id in self.komisia_ids]
        return sorted(
            vybrani,
            key=lambda c: (
                c.id != self.predseda_komisie_id,
                _key_sk(c.priezvisko),
                _key_sk(c.meno),
            ),
        )

    def to_dict(self) -> dict:
        return {
            "celkovy_pocet": self.celkovy_pocet,
            "miesto_riadky": list(self.miesto_riadky),
            "datum": self.datum,
            "obdobie_od": self.obdobie_od,
            "obdobie_do": self.obdobie_do,
            "predseda_komisie_id": self.predseda_komisie_id,
            "komisia_ids": list(self.komisia_ids),
            "materialy_komisie": [m.to_dict() for m in self.materialy_komisie],
            "clenovia": [c.to_dict() for c in self.clenovia],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Zhromazdenie":
        return cls(
            celkovy_pocet=int(d.get("celkovy_pocet", 20)),
            miesto_riadky=_nacitaj_miesto_riadky(d),
            datum=d.get("datum", ""),
            obdobie_od=d.get("obdobie_od", ""),
            obdobie_do=d.get("obdobie_do", ""),
            predseda_komisie_id=d.get("predseda_komisie_id"),
            komisia_ids=[str(i) for i in d.get("komisia_ids", [])],
            materialy_komisie=[
                Material.from_dict(m) for m in d.get("materialy_komisie", [])
            ],
            clenovia=[Clen.from_dict(c) for c in d.get("clenovia", [])],
        )


def _nacitaj_miesto_riadky(d: dict) -> list[str]:
    """Načíta riadky adresy s podporou starého formátu (jeden reťazec)."""
    if isinstance(d.get("miesto_riadky"), list):
        riadky = [str(r) for r in d["miesto_riadky"]]
    else:
        stary = str(d.get("miesto", ""))
        riadky = stary.split("\n") if stary else []
    riadky = riadky[:POCET_RIADKOV_MIESTA]
    riadky += [""] * (POCET_RIADKOV_MIESTA - len(riadky))
    return riadky


# Slovenská abeceda pre korektné abecedné zoradenie (č nasleduje za c atď.).
_SK_ABECEDA = "aáäbcčdďeéfghiíjklĺľmnňoóôpqrŕsštťuúvwxyýzž"
_SK_RANK = {ch: i for i, ch in enumerate(_SK_ABECEDA)}


def _key_sk(text: str) -> tuple[int, ...]:
    """Triediaci kľúč rešpektujúci poradie slovenskej abecedy."""
    return tuple(_SK_RANK.get(ch, len(_SK_ABECEDA) + ord(ch)) for ch in text.strip().lower())
