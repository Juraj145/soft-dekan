"""Dialóg na pridanie / úpravu člena volebného zhromaždenia."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .models import Clen, Kandidat, Skupina, Stav


class ClenDialog(tk.Toplevel):
    """Modálny dialóg na zadanie údajov o členovi."""

    def __init__(self, parent: tk.Misc, clen: Clen | None = None):
        super().__init__(parent)
        self.title("Úprava člena" if clen else "Nový člen")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.vysledok: Clen | None = None
        self._povodny = clen

        self.var_titul_pred = tk.StringVar(value=clen.titul_pred if clen else "")
        self.var_meno = tk.StringVar(value=clen.meno if clen else "")
        self.var_priezvisko = tk.StringVar(value=clen.priezvisko if clen else "")
        self.var_titul_za = tk.StringVar(value=clen.titul_za if clen else "")
        self.var_skupina = tk.StringVar(
            value=(clen.skupina if clen else Skupina.SENAT).value
        )
        self.var_stav = tk.StringVar(
            value=(clen.stav if clen else Stav.PRITOMNY).value
        )

        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Titul pred menom:").grid(row=0, column=0, sticky="w", pady=4)
        ent_titul_pred = ttk.Entry(frm, textvariable=self.var_titul_pred, width=32)
        ent_titul_pred.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Meno:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_meno, width=32).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Priezvisko:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_priezvisko, width=32).grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Titul za menom:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_titul_za, width=32).grid(
            row=3, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Skupina:").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frm,
            textvariable=self.var_skupina,
            values=[s.value for s in Skupina],
            state="readonly",
            width=30,
        ).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Stav:").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frm,
            textvariable=self.var_stav,
            values=[s.value for s in Stav],
            state="readonly",
            width=30,
        ).grid(row=5, column=1, sticky="ew", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(btns, text="Zrušiť", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Uložiť", command=self._uloz).grid(row=0, column=1, padx=4)

        ent_titul_pred.focus_set()
        self.bind("<Return>", lambda _e: self._uloz())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _uloz(self) -> None:
        meno = self.var_meno.get().strip()
        priezvisko = self.var_priezvisko.get().strip()
        if not meno or not priezvisko:
            messagebox.showwarning(
                "Chýbajúce údaje",
                "Vyplňte meno aj priezvisko člena.",
                parent=self,
            )
            return
        cid = self._povodny.id if self._povodny else None
        self.vysledok = Clen(
            meno=meno,
            priezvisko=priezvisko,
            titul_pred=self.var_titul_pred.get().strip(),
            titul_za=self.var_titul_za.get().strip(),
            skupina=Skupina(self.var_skupina.get()),
            stav=Stav(self.var_stav.get()),
            **({"id": cid} if cid else {}),
        )
        self.destroy()


class KandidatDialog(tk.Toplevel):
    """Modálny dialóg na zadanie údajov o kandidátovi na dekana."""

    def __init__(self, parent: tk.Misc, kandidat: Kandidat | None = None):
        super().__init__(parent)
        self.title("Úprava kandidáta" if kandidat else "Nový kandidát")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.vysledok: Kandidat | None = None
        self._povodny = kandidat

        self.var_titul_pred = tk.StringVar(
            value=kandidat.titul_pred if kandidat else ""
        )
        self.var_meno = tk.StringVar(value=kandidat.meno if kandidat else "")
        self.var_priezvisko = tk.StringVar(
            value=kandidat.priezvisko if kandidat else ""
        )
        self.var_titul_za = tk.StringVar(
            value=kandidat.titul_za if kandidat else ""
        )
        self.var_navrhy = tk.StringVar(
            value=str(kandidat.pocet_navrhov) if kandidat else "0"
        )

        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Titul pred menom:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        ent_titul_pred = ttk.Entry(frm, textvariable=self.var_titul_pred, width=32)
        ent_titul_pred.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Meno:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_meno, width=32).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Priezvisko:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_priezvisko, width=32).grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Titul za menom:").grid(
            row=3, column=0, sticky="w", pady=4
        )
        ttk.Entry(frm, textvariable=self.var_titul_za, width=32).grid(
            row=3, column=1, sticky="ew", pady=4
        )

        ttk.Label(frm, text="Počet návrhov z akad. obce:").grid(
            row=4, column=0, sticky="w", pady=4
        )
        ttk.Spinbox(
            frm, from_=0, to=100000, textvariable=self.var_navrhy, width=10
        ).grid(row=4, column=1, sticky="w", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(btns, text="Zrušiť", command=self.destroy).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(btns, text="Uložiť", command=self._uloz).grid(
            row=0, column=1, padx=4
        )

        ent_titul_pred.focus_set()
        self.bind("<Return>", lambda _e: self._uloz())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _uloz(self) -> None:
        meno = self.var_meno.get().strip()
        priezvisko = self.var_priezvisko.get().strip()
        if not meno or not priezvisko:
            messagebox.showwarning(
                "Chýbajúce údaje",
                "Vyplňte meno aj priezvisko kandidáta.",
                parent=self,
            )
            return
        try:
            navrhy = max(0, int(self.var_navrhy.get().strip() or "0"))
        except ValueError:
            messagebox.showwarning(
                "Neplatný údaj",
                "Počet návrhov musí byť celé číslo.",
                parent=self,
            )
            return
        povodny = self._povodny
        self.vysledok = Kandidat(
            meno=meno,
            priezvisko=priezvisko,
            titul_pred=self.var_titul_pred.get().strip(),
            titul_za=self.var_titul_za.get().strip(),
            pocet_navrhov=navrhy,
            dokumenty=dict(povodny.dokumenty) if povodny else {},
            **({"id": povodny.id} if povodny else {}),
        )
        self.destroy()
