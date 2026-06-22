"""Panely krokov 4 a 5 – 1. a 2. kolo voľby dekana TF.

Každé kolo je samostatný krok (okno) sprievodcu. V rámci kola sa najprv
vygenerujú hlasovacie lístky; až potom je možné zadávať počty hlasov a kolo
vyhodnotiť. Po vyhodnotení sa dá vygenerovať zápisnica z volebného
zhromaždenia.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import messagebox, ttk

from .docx_export import (
    uloz_hlasovaci_listok,
    uloz_prebratie_listka,
    uloz_protokol_listka,
    uloz_zapisnicu,
)
from .models import Kandidat, Stav, Zhromazdenie
from .resources import priecinok_udajov
from .volba import VysledokKola, vyhodnot_kolo


@dataclass
class VolbaStav:
    """Zdieľaný stav medzi oknami 1. a 2. kola voľby."""

    v1: VysledokKola | None = None
    v2: VysledokKola | None = None
    listky_k1: bool = False
    listky_k2: bool = False
    prebratie_k1: bool = False
    prebratie_k2: bool = False
    protokol_k1: bool = False
    protokol_k2: bool = False


class KoloPanel(ttk.Frame):
    """Jedno kolo voľby kandidáta na dekana (1. alebo 2.)."""

    def __init__(
        self, parent: tk.Misc, z: Zhromazdenie, kolo: int, stav: VolbaStav
    ) -> None:
        super().__init__(parent)
        self.z = z
        self.kolo = kolo
        self.stav = stav
        self._var_hlasy: dict[str, tk.StringVar] = {}
        self._var_neplatne = tk.StringVar()
        self._var_platne = tk.StringVar(value="0")
        self.on_zmena: Callable[[], None] | None = None
        self._entry_hlasy: dict[str, ttk.Entry] = {}
        self._vytvor_widgety()
        self.obnov()

    @property
    def _atribut(self) -> str:
        return "hlasy_k1" if self.kolo == 1 else "hlasy_k2"

    def _set_listky(self, hodnota: bool) -> None:
        if self.kolo == 1:
            self.stav.listky_k1 = hodnota
        else:
            self.stav.listky_k2 = hodnota

    def _listky_hotove(self) -> bool:
        return self.stav.listky_k1 if self.kolo == 1 else self.stav.listky_k2

    def _prebratie_hotove(self) -> bool:
        return (
            self.stav.prebratie_k1 if self.kolo == 1 else self.stav.prebratie_k2
        )

    def _protokol_hotove(self) -> bool:
        return (
            self.stav.protokol_k1 if self.kolo == 1 else self.stav.protokol_k2
        )

    def _preddoklady_hotove(self) -> bool:
        return self._prebratie_hotove() and self._protokol_hotove()

    # ------------------------------------------------------------------ build
    def _vytvor_widgety(self) -> None:
        ramec = ttk.LabelFrame(
            self, text=f"{self.kolo}. kolo voľby", padding=10
        )
        ramec.pack(fill="x")

        ttk.Label(
            ramec,
            text="1) Pred hlasovaním vygenerujte oba doklady:",
        ).pack(anchor="w")
        self.btn_prebratie = ttk.Button(
            ramec,
            text="Generovať prebratie hlasovacieho lístka…",
            command=self._generuj_prebratie,
        )
        self.btn_prebratie.pack(anchor="w", pady=(2, 2))
        self.btn_protokol = ttk.Button(
            ramec,
            text="Generovať protokol o prebratí nového hlasovacieho lístka…",
            command=self._generuj_protokol,
        )
        self.btn_protokol.pack(anchor="w", pady=(2, 6))

        ttk.Label(
            ramec, text="2) Potom vygenerujte hlasovacie lístky:"
        ).pack(anchor="w")
        self.btn_listky = ttk.Button(
            ramec,
            text=f"Generovať hlasovacie lístky ({self.kolo}. kolo)…",
            command=self._generuj_listky,
        )
        self.btn_listky.pack(anchor="w", pady=(2, 6))

        self.lbl_pokyn = tk.Label(
            ramec,
            text="",
            justify="left",
            anchor="w",
            fg="#b00020",
            wraplength=860,
        )
        self.lbl_pokyn.pack(fill="x", pady=(0, 6))

        self.box_hlasy = ttk.Frame(ramec)
        self.box_hlasy.pack(fill="x")

        spod = ttk.Frame(ramec)
        spod.pack(fill="x", pady=(6, 0))
        ttk.Label(spod, text="Počet platných hlasov:").pack(side="left")
        ttk.Label(
            spod, textvariable=self._var_platne, width=6,
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side="left", padx=(4, 16))
        ttk.Label(spod, text="Počet neplatných hlasov:").pack(side="left")
        self.ent_neplatne = ttk.Entry(spod, textvariable=self._var_neplatne, width=6)
        self.ent_neplatne.pack(side="left", padx=(4, 16))
        self.btn_vyhodnot = ttk.Button(
            spod, text=f"Vyhodnotiť {self.kolo}. kolo", command=self._vyhodnot
        )
        self.btn_vyhodnot.pack(side="left")

        self.lbl_vysledok = tk.Label(
            ramec, text="", justify="left", anchor="w", wraplength=860
        )
        self.lbl_vysledok.pack(fill="x", pady=(6, 0))

        ramec_z = ttk.Frame(self)
        ramec_z.pack(fill="x", pady=(10, 0))
        self.btn_zapisnica = ttk.Button(
            ramec_z,
            text="Generovať zápisnicu z volebného zhromaždenia…",
            command=self._generuj_zapisnicu,
        )
        self.btn_zapisnica.pack(anchor="w")
        self.lbl_zapisnica = tk.Label(
            ramec_z, text="", justify="left", anchor="w", fg="#666666",
            wraplength=860,
        )
        self.lbl_zapisnica.pack(fill="x")

    # ------------------------------------------------------------- napĺňanie
    def _kandidati(self) -> list[Kandidat]:
        if self.kolo == 1:
            return self.z.kandidati_zoradeni()
        return self._postupujuci()

    def _postupujuci(self) -> list[Kandidat]:
        v1 = self.stav.v1
        if v1 is None or v1.zvoleny is not None:
            return []
        return sorted(
            v1.postupujuci,
            key=lambda k: (k.priezvisko.lower(), k.meno.lower()),
        )

    def _riadky_hlasov(self, kandidati: list[Kandidat]) -> None:
        for w in self.box_hlasy.winfo_children():
            w.destroy()
        self._var_hlasy.clear()
        self._entry_hlasy.clear()
        if not kandidati:
            ttk.Label(self.box_hlasy, text="(žiadni kandidáti)").grid(
                row=0, column=0, sticky="w"
            )
            return
        for i, k in enumerate(kandidati):
            ttk.Label(self.box_hlasy, text=k.cele_meno).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2
            )
            var = tk.StringVar(value=str(getattr(k, self._atribut)))
            var.trace_add("write", lambda *_a: self._prepocitaj_platne())
            self._var_hlasy[k.id] = var
            ent = ttk.Entry(self.box_hlasy, textvariable=var, width=6)
            ent.grid(row=i, column=1, sticky="w", pady=2)
            self._entry_hlasy[k.id] = ent
            ttk.Label(self.box_hlasy, text="hlasov").grid(
                row=i, column=2, sticky="w"
            )

    def _prepocitaj_platne(self) -> None:
        """Aktualizuje zobrazený počet platných hlasov (súčet hlasov kandidátov)."""
        spolu = sum(self._cislo(v) for v in self._var_hlasy.values())
        self._var_platne.set(str(spolu))

    def obnov(self) -> None:
        kandidati = self._kandidati()
        self._riadky_hlasov(kandidati)
        self._prepocitaj_platne()
        self._var_neplatne.set(
            str(self.z.neplatne_k1 if self.kolo == 1 else self.z.neplatne_k2)
        )
        v = self.stav.v1 if self.kolo == 1 else self.stav.v2
        if v is not None:
            self.lbl_vysledok.config(
                text=self._text_vysledku(v, self.kolo), fg=self._farba(v)
            )
        else:
            self.lbl_vysledok.config(text="")
        self._aktualizuj_stav()

    def _aktualizuj_stav(self) -> None:
        """Sprístupní/zablokuje generovanie dokladov, lístkov a zadávanie hlasov."""
        kandidati = self._kandidati()
        # 2. kolo je dostupné až po vyhodnotení 1. kola bez zvoleného kandidáta.
        if self.kolo == 2 and not kandidati:
            for w in (self.btn_prebratie, self.btn_protokol, self.btn_listky):
                w.config(state="disabled")
            self._nastav_zadavanie(False)
            self.lbl_pokyn.config(
                text="2. kolo sa sprístupní po vyhodnotení 1. kola, "
                "ak nikto nezíska potrebnú väčšinu."
            )
            return

        self.btn_prebratie.config(state="normal")
        self.btn_protokol.config(state="normal")
        # Hlasovacie lístky – až po vygenerovaní prebratia aj protokolu.
        self.btn_listky.config(
            state="normal" if self._preddoklady_hotove() else "disabled"
        )

        # Zadávanie hlasov – až po vygenerovaní hlasovacích lístkov.
        self._nastav_zadavanie(self._listky_hotove() and bool(kandidati))

        if not kandidati:
            self.lbl_pokyn.config(text="")
        elif not self._preddoklady_hotove():
            self.lbl_pokyn.config(
                text="Najprv vygenerujte prebratie hlasovacieho lístka aj "
                "protokol o prebratí nového lístka, potom hlasovacie lístky."
            )
        elif not self._listky_hotove():
            self.lbl_pokyn.config(
                text="Vygenerujte hlasovacie lístky – až potom je možné "
                "zadávať výsledky volieb."
            )
        else:
            self.lbl_pokyn.config(text="")

    def _nastav_zadavanie(self, aktivne: bool) -> None:
        stav = "normal" if aktivne else "disabled"
        for ent in self._entry_hlasy.values():
            ent.config(state=stav)
        self.ent_neplatne.config(state=stav)
        self.btn_vyhodnot.config(state=stav)
        self._aktualizuj_zapisnicu()

    def _aktualizuj_zapisnicu(self) -> None:
        """Zápisnicu možno generovať až po vyhodnotení kola.

        V 1. kole len ak bol kandidát zvolený (neúspešné kolo → pokračuje 2. kolom),
        v 2. kole po jeho vyhodnotení.
        """
        if self.kolo == 1:
            v1 = self.stav.v1
            mozne = v1 is not None and v1.zvoleny is not None
            if v1 is not None and v1.zvoleny is None:
                pokyn = ("1. kolo bolo neúspešné – zápisnica sa vygeneruje až "
                         "po vyhodnotení 2. kola.")
            else:
                pokyn = ""
        else:
            mozne = self.stav.v2 is not None
            pokyn = "" if mozne else "Zápisnicu možno generovať až po vyhodnotení 2. kola."
        self.btn_zapisnica.config(state="normal" if mozne else "disabled")
        self.lbl_zapisnica.config(text=pokyn)

    # ----------------------------------------------------------- zber hlasov
    @staticmethod
    def _cislo(var: tk.StringVar) -> int:
        try:
            return max(0, int(var.get().strip() or "0"))
        except ValueError:
            return 0

    def _pocet_hlasujucich(self) -> int:
        """Počet hlasujúcich (prítomných) členov volebného zhromaždenia."""
        return sum(1 for c in self.z.clenovia if c.stav == Stav.PRITOMNY)

    def _kontrola_poctu(self, odovzdane: int) -> bool:
        """Overí, že počet odovzdaných hlasov neprekročí počet hlasujúcich."""
        hlasujuci = self._pocet_hlasujucich()
        if odovzdane > hlasujuci:
            messagebox.showerror(
                "Príliš veľa hlasov",
                "Počet odovzdaných hlasov "
                f"({odovzdane}) nemôže byť vyšší ako počet hlasujúcich "
                f"(prítomných) členov volebného zhromaždenia ({hlasujuci}).",
                parent=self,
            )
            return False
        return True

    def _zber(self, kandidati: list[Kandidat]) -> None:
        for k in kandidati:
            if k.id in self._var_hlasy:
                setattr(k, self._atribut, self._cislo(self._var_hlasy[k.id]))
        if self.kolo == 1:
            self.z.neplatne_k1 = self._cislo(self._var_neplatne)
        else:
            self.z.neplatne_k2 = self._cislo(self._var_neplatne)

    # --------------------------------------------------------------- akcie
    def _generuj_prebratie(self) -> None:
        cesta = os.path.join(
            priecinok_udajov(),
            f"Prebratie hlasovacieho lístka - {self.kolo}. kolo.docx",
        )
        try:
            uloz_prebratie_listka(self.z, self.kolo, cesta)
        except OSError as e:
            messagebox.showerror(
                "Prebratie hlasovacieho lístka",
                f"Uloženie zlyhalo:\n{e}",
                parent=self,
            )
            return
        if self.kolo == 1:
            self.stav.prebratie_k1 = True
        else:
            self.stav.prebratie_k2 = True
        self._aktualizuj_stav()
        self._otvor_subor(cesta, "Prebratie hlasovacieho lístka")

    def _generuj_protokol(self) -> None:
        cesta = os.path.join(
            priecinok_udajov(),
            f"Protokol o prebratí nového hlasovacieho lístka - {self.kolo}. kolo.docx",
        )
        try:
            uloz_protokol_listka(self.z, self.kolo, cesta)
        except OSError as e:
            messagebox.showerror(
                "Protokol o prebratí nového hlasovacieho lístka",
                f"Uloženie zlyhalo:\n{e}",
                parent=self,
            )
            return
        if self.kolo == 1:
            self.stav.protokol_k1 = True
        else:
            self.stav.protokol_k2 = True
        self._aktualizuj_stav()
        self._otvor_subor(cesta, "Protokol o prebratí nového hlasovacieho lístka")

    def _generuj_listky(self) -> None:
        kandidati = self._kandidati()
        if not kandidati:
            messagebox.showinfo(
                "Hlasovacie lístky",
                "Najprv pridajte kandidátov (krok 3)."
                if self.kolo == 1
                else "2. kolo je dostupné až po vyhodnotení 1. kola "
                "bez zvoleného kandidáta.",
                parent=self,
            )
            return
        cesta = os.path.join(
            priecinok_udajov(), f"Hlasovací lístok - {self.kolo}. kolo.docx"
        )
        try:
            uloz_hlasovaci_listok(self.z, self.kolo, kandidati, cesta)
        except OSError as e:
            messagebox.showerror(
                "Hlasovacie lístky", f"Uloženie zlyhalo:\n{e}", parent=self
            )
            return
        self._set_listky(True)
        self._aktualizuj_stav()
        self._otvor_subor(cesta, "Hlasovacie lístky")

    def _vyhodnot(self) -> None:
        kandidati = self._kandidati()
        if not kandidati:
            return
        if not self._listky_hotove():
            messagebox.showinfo(
                f"{self.kolo}. kolo",
                "Najprv vygenerujte hlasovacie lístky.",
                parent=self,
            )
            return
        self._zber(kandidati)
        odovzdane = sum(getattr(k, self._atribut) for k in kandidati) + (
            self.z.neplatne_k1 if self.kolo == 1 else self.z.neplatne_k2
        )
        if not self._kontrola_poctu(odovzdane):
            return
        v = vyhodnot_kolo(kandidati, self.kolo, self.z.celkovy_pocet)
        if self.kolo == 1:
            self.stav.v1 = v
            self.stav.v2 = None
            self.stav.listky_k2 = False
            self.stav.prebratie_k2 = False
            self.stav.protokol_k2 = False
        else:
            self.stav.v2 = v
        self.lbl_vysledok.config(
            text=self._text_vysledku(v, self.kolo), fg=self._farba(v)
        )
        self._aktualizuj_stav()
        if self.on_zmena is not None:
            self.on_zmena()

    def _generuj_zapisnicu(self) -> None:
        if not self.z.kandidati:
            messagebox.showinfo(
                "Zápisnica", "Najprv pridajte kandidátov (krok 3).", parent=self
            )
            return
        cesta = os.path.join(
            priecinok_udajov(), "Zápisnica z volebného zhromaždenia.docx"
        )
        try:
            uloz_zapisnicu(self.z, cesta)
        except OSError as e:
            messagebox.showerror(
                "Zápisnica", f"Uloženie zlyhalo:\n{e}", parent=self
            )
            return
        self._otvor_subor(cesta, "Zápisnica")

    # --------------------------------------------------------------- pomocné
    @staticmethod
    def _farba(v: VysledokKola) -> str:
        return "#1b7f1b" if v.zvoleny is not None else "#b00020"

    @staticmethod
    def _text_vysledku(v: VysledokKola, kolo: int) -> str:
        poradie = "\n".join(
            f"   {i + 1}. {k.cele_meno}: {h} hlasov"
            for i, (k, h) in enumerate(v.poradie)
        )
        if v.zvoleny is not None:
            hlavicka = (
                f"ZVOLENÝ: {v.zvoleny.cele_meno} "
                f"(potrebná väčšina min. {v.potrebna_vacsina} hlasov)."
            )
        else:
            mena = ", ".join(k.cele_meno for k in v.postupujuci)
            hlavicka = (
                f"V {kolo}. kole nebol nikto zvolený (potrebných min. "
                f"{v.potrebna_vacsina} hlasov). Do ďalšieho kola postupujú: {mena}."
            )
        return hlavicka + "\n" + poradie

    def _otvor_subor(self, cesta: str, titulok: str) -> None:
        if sys.platform == "win32":
            try:
                os.startfile(cesta)
                return
            except OSError:
                pass
        messagebox.showinfo(
            titulok, f"Dokument bol uložený a otvorený:\n{cesta}", parent=self
        )
