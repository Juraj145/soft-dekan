"""Krok – generátor náhodného poradia prezentácií kandidátov.

Každý kandidát príde k PC, stlačí Enter (čísla sa rolujú) a opätovným Enter
rolovanie zastaví – tým si vyžrebuje poradie, v ktorom prezentoval stratégiu
rozvoja fakulty. Čísla sú jedinečné (1 … počet kandidátov) a poradie sa
zapisuje do zápisnice.
"""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from .models import Kandidat, Zhromazdenie


class PoradiePanel(ttk.Frame):
    """Žrebovanie poradia verejných prezentácií kandidátov na dekana."""

    def __init__(self, parent: tk.Misc, z: Zhromazdenie) -> None:
        super().__init__(parent)
        self.z = z
        self._poradie_drawn: list[Kandidat] = []
        self._volne: list[int] = []
        self._rolling = False
        self._after_id: str | None = None
        self._vytvor_widgety()

    # ------------------------------------------------------------------ build
    def _vytvor_widgety(self) -> None:
        ramec = ttk.LabelFrame(
            self, text="Poradie verejných prezentácií kandidátov", padding=10
        )
        ramec.pack(fill="both", expand=True)

        ttk.Label(
            ramec,
            text=(
                "Generátor náhodného poradia, v ktorom kandidáti na dekana "
                "prezentovali stratégie rozvoja Technickej fakulty SPU v Nitre.\n"
                "Kandidát príde k PC, stlačí Enter pre začiatok žrebovania a "
                "opätovným Enter žrebovanie ukončí. Počet vyžrebovaných čísel "
                "zodpovedá počtu kandidátov."
            ),
            justify="left",
            wraplength=860,
        ).pack(anchor="w", pady=(0, 8))

        self.lbl_kandidat = tk.Label(
            ramec, text="", font=("TkDefaultFont", 13, "bold"),
            justify="center", anchor="center",
        )
        self.lbl_kandidat.pack(fill="x")

        self.lbl_cislo = tk.Label(
            ramec, text="–", font=("TkDefaultFont", 72, "bold"),
            fg="#1a6e1a", justify="center", anchor="center",
        )
        self.lbl_cislo.pack(fill="x", pady=(4, 8))

        riadok = ttk.Frame(ramec)
        riadok.pack()
        self.btn_krok = ttk.Button(
            riadok, text="Začať žrebovanie (Enter)", command=self._krok
        )
        self.btn_krok.pack(side="left", padx=4)
        self.btn_krok.bind("<Return>", lambda _e: self._krok())
        self.btn_reset = ttk.Button(
            riadok, text="Vymazať a žrebovať odznova", command=self._reset
        )
        self.btn_reset.pack(side="left", padx=4)

        stlpce = ("poradie", "kandidat")
        self.tree = ttk.Treeview(
            ramec, columns=stlpce, show="headings", height=8
        )
        self.tree.heading("poradie", text="Poradie prezentácie")
        self.tree.heading("kandidat", text="Meno, priezvisko, tituly kandidáta")
        self.tree.column("poradie", width=140, anchor="center")
        self.tree.column("kandidat", width=520, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(10, 0))

    # ------------------------------------------------------------- napĺňanie
    def _kandidati(self) -> list[Kandidat]:
        return self.z.kandidati_zoradeni()

    def _hotovo(self) -> bool:
        kand = self._kandidati()
        if not kand:
            return False
        cisla = sorted(k.poradie_prezentacie for k in kand)
        return cisla == list(range(1, len(kand) + 1))

    def _aktualny(self) -> Kandidat | None:
        """Kandidát, ktorý je práve na rade (ešte nemá pridelené poradie)."""
        for k in self._poradie_drawn:
            return k
        return None

    def obnov(self) -> None:
        self._zrus_rolovanie()
        if self._hotovo():
            self._poradie_drawn = []
            self._volne = []
        else:
            self._zacni_odznova()
        self._vykresli()

    def _zacni_odznova(self) -> None:
        kand = self._kandidati()
        for k in kand:
            k.poradie_prezentacie = 0
        self._poradie_drawn = list(kand)
        self._volne = list(range(1, len(kand) + 1))

    def _reset(self) -> None:
        self._zrus_rolovanie()
        self._zacni_odznova()
        self.lbl_cislo.config(text="–")
        self._vykresli()
        self.btn_krok.focus_set()

    # ---------------------------------------------------------- žrebovanie
    def _krok(self) -> None:
        if not self._poradie_drawn:
            return
        if not self._rolling:
            self._rolling = True
            self.btn_krok.config(text="Zastaviť žrebovanie (Enter)")
            self.btn_reset.config(state="disabled")
            self._roluj()
        else:
            self._zastav()

    def _roluj(self) -> None:
        if not self._volne:
            return
        self.lbl_cislo.config(text=str(random.choice(self._volne)))
        self._after_id = self.after(60, self._roluj)

    def _zastav(self) -> None:
        self._zrus_rolovanie()
        cislo = random.choice(self._volne)
        self._volne.remove(cislo)
        self.lbl_cislo.config(text=str(cislo))
        kand = self._poradie_drawn.pop(0)
        kand.poradie_prezentacie = cislo
        self.btn_krok.config(text="Začať žrebovanie (Enter)")
        self.btn_reset.config(state="normal")
        self._vykresli()
        if self._poradie_drawn:
            self.btn_krok.focus_set()

    def _zrus_rolovanie(self) -> None:
        self._rolling = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    # ----------------------------------------------------------- vykreslenie
    def _vykresli(self) -> None:
        akt = self._aktualny()
        if akt is not None:
            self.lbl_kandidat.config(
                text=f"Na rade: {akt.cele_meno}", fg="#000000"
            )
            self.btn_krok.config(state="normal")
        else:
            self.lbl_kandidat.config(
                text="Žrebovanie ukončené – poradie je určené.", fg="#1a6e1a"
            )
            self.btn_krok.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        for k in sorted(
            self._kandidati(),
            key=lambda c: (c.poradie_prezentacie or 999, c.priezvisko.lower()),
        ):
            poradie = str(k.poradie_prezentacie) if k.poradie_prezentacie else "–"
            self.tree.insert("", "end", values=(poradie, k.cele_meno))
