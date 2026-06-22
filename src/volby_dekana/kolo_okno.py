"""Panel kroku 4 – 1. a 2. kolo voľby dekana TF.

Umožňuje vygenerovať hlasovacie lístky pre dané kolo, zadať počty hlasov
jednotlivým kandidátom, vyhodnotiť kolo (zvolený / postup do 2. kola) a
vygenerovať zápisnicu z volebného zhromaždenia.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from .docx_export import (
    uloz_hlasovaci_listok,
    uloz_zapisnicu,
)
from .models import Kandidat, Zhromazdenie
from .resources import priecinok_udajov
from .volba import VysledokKola, vyhodnot_kolo


class KoloPanel(ttk.Frame):
    """1. a 2. kolo voľby kandidáta na dekana."""

    def __init__(self, parent: tk.Misc, z: Zhromazdenie) -> None:
        super().__init__(parent)
        self.z = z
        self._var_hlasy_k1: dict[str, tk.StringVar] = {}
        self._var_hlasy_k2: dict[str, tk.StringVar] = {}
        self._var_neplatne_k1 = tk.StringVar()
        self._var_neplatne_k2 = tk.StringVar()
        self._v1: VysledokKola | None = None
        self._v2: VysledokKola | None = None
        self._vytvor_widgety()
        self.obnov()

    # ------------------------------------------------------------------ build
    def _vytvor_widgety(self) -> None:
        # --- 1. kolo ---
        self.ramec_k1 = ttk.LabelFrame(self, text="1. kolo voľby", padding=10)
        self.ramec_k1.pack(fill="x", pady=(0, 6))
        ttk.Button(
            self.ramec_k1,
            text="Generovať hlasovacie lístky (1. kolo)…",
            command=self._generuj_listky_k1,
        ).pack(anchor="w", pady=(0, 6))
        self.box_hlasy_k1 = ttk.Frame(self.ramec_k1)
        self.box_hlasy_k1.pack(fill="x")
        spod_k1 = ttk.Frame(self.ramec_k1)
        spod_k1.pack(fill="x", pady=(6, 0))
        ttk.Label(spod_k1, text="Počet neplatných hlasov:").pack(side="left")
        ttk.Entry(spod_k1, textvariable=self._var_neplatne_k1, width=6).pack(
            side="left", padx=(4, 16)
        )
        ttk.Button(
            spod_k1, text="Vyhodnotiť 1. kolo", command=self._vyhodnot_k1
        ).pack(side="left")
        self.lbl_vysledok_k1 = tk.Label(
            self.ramec_k1, text="", justify="left", anchor="w", wraplength=860
        )
        self.lbl_vysledok_k1.pack(fill="x", pady=(6, 0))

        # --- 2. kolo ---
        self.ramec_k2 = ttk.LabelFrame(self, text="2. kolo voľby", padding=10)
        self.ramec_k2.pack(fill="x", pady=(6, 6))
        self.btn_listky_k2 = ttk.Button(
            self.ramec_k2,
            text="Generovať hlasovacie lístky (2. kolo)…",
            command=self._generuj_listky_k2,
        )
        self.btn_listky_k2.pack(anchor="w", pady=(0, 6))
        self.box_hlasy_k2 = ttk.Frame(self.ramec_k2)
        self.box_hlasy_k2.pack(fill="x")
        spod_k2 = ttk.Frame(self.ramec_k2)
        spod_k2.pack(fill="x", pady=(6, 0))
        ttk.Label(spod_k2, text="Počet neplatných hlasov:").pack(side="left")
        ttk.Entry(spod_k2, textvariable=self._var_neplatne_k2, width=6).pack(
            side="left", padx=(4, 16)
        )
        self.btn_vyhodnot_k2 = ttk.Button(
            spod_k2, text="Vyhodnotiť 2. kolo", command=self._vyhodnot_k2
        )
        self.btn_vyhodnot_k2.pack(side="left")
        self.lbl_vysledok_k2 = tk.Label(
            self.ramec_k2, text="", justify="left", anchor="w", wraplength=860
        )
        self.lbl_vysledok_k2.pack(fill="x", pady=(6, 0))

        # --- Zápisnica ---
        ramec_z = ttk.Frame(self)
        ramec_z.pack(fill="x", pady=(6, 0))
        ttk.Button(
            ramec_z,
            text="Generovať zápisnicu z volebného zhromaždenia…",
            command=self._generuj_zapisnicu,
        ).pack(anchor="w")

    # ------------------------------------------------------------- napĺňanie
    def _riadky_hlasov(
        self, box: tk.Misc, kandidati: list[Kandidat],
        vars_map: dict[str, tk.StringVar], atribut: str,
    ) -> None:
        for w in box.winfo_children():
            w.destroy()
        vars_map.clear()
        if not kandidati:
            ttk.Label(box, text="(žiadni kandidáti)").grid(row=0, column=0, sticky="w")
            return
        for i, k in enumerate(kandidati):
            ttk.Label(box, text=k.cele_meno).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2
            )
            var = tk.StringVar(value=str(getattr(k, atribut)))
            vars_map[k.id] = var
            ttk.Entry(box, textvariable=var, width=6).grid(
                row=i, column=1, sticky="w", pady=2
            )
            ttk.Label(box, text="hlasov").grid(row=i, column=2, sticky="w")

    def obnov(self) -> None:
        kandidati = self.z.kandidati_zoradeni()
        self._riadky_hlasov(self.box_hlasy_k1, kandidati, self._var_hlasy_k1, "hlasy_k1")
        self._var_neplatne_k1.set(str(self.z.neplatne_k1))
        self._var_neplatne_k2.set(str(self.z.neplatne_k2))
        # 2. kolo sa sprístupní až po vyhodnotení 1. kola bez zvoleného kandidáta.
        postupujuci = self._postupujuci()
        self._riadky_hlasov(
            self.box_hlasy_k2, postupujuci, self._var_hlasy_k2, "hlasy_k2"
        )
        self._nastav_stav_k2(bool(postupujuci))

    def _postupujuci(self) -> list[Kandidat]:
        if self._v1 is None or self._v1.zvoleny is not None:
            return []
        return sorted(
            self._v1.postupujuci,
            key=lambda k: (k.priezvisko.lower(), k.meno.lower()),
        )

    def _nastav_stav_k2(self, aktivne: bool) -> None:
        stav = "normal" if aktivne else "disabled"
        self.btn_listky_k2.config(state=stav)
        self.btn_vyhodnot_k2.config(state=stav)

    # ----------------------------------------------------------- zber hlasov
    @staticmethod
    def _cislo(var: tk.StringVar) -> int:
        try:
            return max(0, int(var.get().strip() or "0"))
        except ValueError:
            return 0

    def _zber_k1(self) -> None:
        for k in self.z.kandidati:
            if k.id in self._var_hlasy_k1:
                k.hlasy_k1 = self._cislo(self._var_hlasy_k1[k.id])
        self.z.neplatne_k1 = self._cislo(self._var_neplatne_k1)

    def _zber_k2(self) -> None:
        for k in self.z.kandidati:
            if k.id in self._var_hlasy_k2:
                k.hlasy_k2 = self._cislo(self._var_hlasy_k2[k.id])
        self.z.neplatne_k2 = self._cislo(self._var_neplatne_k2)

    # --------------------------------------------------------------- akcie
    def _generuj_listky_k1(self) -> None:
        self._generuj_listky(1, self.z.kandidati_zoradeni())

    def _generuj_listky_k2(self) -> None:
        self._generuj_listky(2, self._postupujuci())

    def _generuj_listky(self, kolo: int, kandidati: list[Kandidat]) -> None:
        if not kandidati:
            messagebox.showinfo(
                "Hlasovacie lístky",
                "Najprv pridajte kandidátov (krok 3).",
                parent=self,
            )
            return
        cesta = os.path.join(
            priecinok_udajov(), f"Hlasovací lístok - {kolo}. kolo.docx"
        )
        try:
            uloz_hlasovaci_listok(self.z, kolo, kandidati, cesta)
        except OSError as e:
            messagebox.showerror(
                "Hlasovacie lístky", f"Uloženie zlyhalo:\n{e}", parent=self
            )
            return
        self._otvor_subor(cesta, "Hlasovacie lístky")

    def _vyhodnot_k1(self) -> None:
        if not self.z.kandidati:
            messagebox.showinfo(
                "1. kolo", "Najprv pridajte kandidátov (krok 3).", parent=self
            )
            return
        self._zber_k1()
        self._v1 = vyhodnot_kolo(self.z.kandidati_zoradeni(), 1, self.z.celkovy_pocet)
        self._v2 = None
        self.lbl_vysledok_k1.config(
            text=self._text_vysledku(self._v1, 1), fg=self._farba(self._v1)
        )
        self.obnov()

    def _vyhodnot_k2(self) -> None:
        postupujuci = self._postupujuci()
        if not postupujuci:
            return
        self._zber_k2()
        self._v2 = vyhodnot_kolo(postupujuci, 2, self.z.celkovy_pocet)
        self.lbl_vysledok_k2.config(
            text=self._text_vysledku(self._v2, 2), fg=self._farba(self._v2)
        )

    def _generuj_zapisnicu(self) -> None:
        if not self.z.kandidati:
            messagebox.showinfo(
                "Zápisnica", "Najprv pridajte kandidátov (krok 3).", parent=self
            )
            return
        self._zber_k1()
        self._zber_k2()
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
