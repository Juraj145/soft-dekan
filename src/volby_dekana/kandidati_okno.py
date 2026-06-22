"""Okno kandidátov na dekana TF s návrhmi a dokumentmi."""
from __future__ import annotations

import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .dialogs import KandidatDialog
from .models import (
    TYPY_DOKUMENTOV_KANDIDATA,
    Kandidat,
    Material,
    Zhromazdenie,
)
from .resources import priecinok_kandidatov


class KandidatiOkno(tk.Toplevel):
    """Pridávanie kandidátov na dekana a ich dokumentov."""

    def __init__(self, parent: tk.Misc, z: Zhromazdenie) -> None:
        super().__init__(parent)
        self.z = z
        self.title("Kandidáti na dekana TF")
        self.geometry("760x600")
        self.minsize(640, 520)
        self.transient(parent)
        self._vytvor_widgety()
        self.obnov()

    # ------------------------------------------------------------------ build
    def _vytvor_widgety(self) -> None:
        ramec_k = ttk.LabelFrame(
            self, text="Kandidáti na dekana (abecedne podľa priezviska)", padding=10
        )
        ramec_k.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        panel = ttk.Frame(ramec_k)
        panel.pack(fill="x", pady=(0, 6))
        ttk.Button(panel, text="Pridať kandidáta", command=self._pridaj).pack(
            side="left", padx=2
        )
        ttk.Button(panel, text="Upraviť", command=self._uprav).pack(
            side="left", padx=2
        )
        ttk.Button(panel, text="Odstrániť", command=self._odstran).pack(
            side="left", padx=2
        )

        stlpce = ("priezvisko", "meno", "titul", "navrhy", "dokumenty")
        self.tree_k = ttk.Treeview(
            ramec_k, columns=stlpce, show="headings", selectmode="browse", height=8
        )
        nadpisy = {
            "priezvisko": "Priezvisko",
            "meno": "Meno",
            "titul": "Titul(y)",
            "navrhy": "Počet návrhov",
            "dokumenty": "Dokumenty",
        }
        sirky = {
            "priezvisko": 150,
            "meno": 130,
            "titul": 130,
            "navrhy": 110,
            "dokumenty": 110,
        }
        for s in stlpce:
            self.tree_k.heading(s, text=nadpisy[s])
            self.tree_k.column(s, width=sirky[s], anchor="w")
        self.tree_k.column("navrhy", anchor="center")
        self.tree_k.column("dokumenty", anchor="center")
        self.tree_k.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(ramec_k, orient="vertical", command=self.tree_k.yview)
        self.tree_k.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree_k.bind("<<TreeviewSelect>>", lambda _e: self._obnov_dokumenty())
        self.tree_k.bind("<Double-1>", lambda _e: self._uprav())

        ramec_d = ttk.LabelFrame(
            self, text="Dokumenty vybraného kandidáta", padding=10
        )
        ramec_d.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        panel_d = ttk.Frame(ramec_d)
        panel_d.pack(fill="x", pady=(0, 6))
        ttk.Button(
            panel_d, text="Pridať / nahradiť dokument…", command=self._pridaj_dokument
        ).pack(side="left", padx=2)
        ttk.Button(panel_d, text="Otvoriť", command=self._otvor_dokument).pack(
            side="left", padx=2
        )
        ttk.Button(panel_d, text="Odstrániť", command=self._odstran_dokument).pack(
            side="left", padx=2
        )

        self.tree_d = ttk.Treeview(
            ramec_d, columns=("typ", "subor"), show="headings", selectmode="browse"
        )
        self.tree_d.heading("typ", text="Typ dokumentu")
        self.tree_d.heading("subor", text="Súbor")
        self.tree_d.column("typ", width=320, anchor="w")
        self.tree_d.column("subor", width=380, anchor="w")
        self.tree_d.pack(fill="both", expand=True)
        self.tree_d.bind("<Double-1>", lambda _e: self._otvor_dokument())

    # ----------------------------------------------------------------- refresh
    def obnov(self) -> None:
        self._obnov_kandidatov()
        self._obnov_dokumenty()

    def _obnov_kandidatov(self) -> None:
        vyber = self.tree_k.selection()
        self.tree_k.delete(*self.tree_k.get_children())
        for k in self.z.kandidati_zoradeni():
            self.tree_k.insert(
                "",
                "end",
                iid=k.id,
                values=(
                    k.priezvisko,
                    k.meno,
                    k.tituly,
                    k.pocet_navrhov,
                    f"{len(k.dokumenty)}/{len(TYPY_DOKUMENTOV_KANDIDATA)}",
                ),
            )
        if vyber and self.tree_k.exists(vyber[0]):
            self.tree_k.selection_set(vyber[0])

    def _vybrany_kandidat(self) -> Kandidat | None:
        sel = self.tree_k.selection()
        if not sel:
            return None
        return next((k for k in self.z.kandidati if k.id == sel[0]), None)

    def _obnov_dokumenty(self) -> None:
        self.tree_d.delete(*self.tree_d.get_children())
        k = self._vybrany_kandidat()
        if k is None:
            return
        for typ in TYPY_DOKUMENTOV_KANDIDATA:
            mat = k.dokument(typ)
            self.tree_d.insert(
                "", "end", iid=typ, values=(typ, mat.nazov if mat else "—")
            )

    # ------------------------------------------------------------ kandidáti
    def _pridaj(self) -> None:
        dlg = KandidatDialog(self)
        self.wait_window(dlg)
        if dlg.vysledok:
            self.z.kandidati.append(dlg.vysledok)
            self._obnov_kandidatov()
            self.tree_k.selection_set(dlg.vysledok.id)
            self._obnov_dokumenty()

    def _uprav(self) -> None:
        k = self._vybrany_kandidat()
        if k is None:
            return
        dlg = KandidatDialog(self, k)
        self.wait_window(dlg)
        if dlg.vysledok:
            idx = self.z.kandidati.index(k)
            self.z.kandidati[idx] = dlg.vysledok
            self._obnov_kandidatov()
            self.tree_k.selection_set(dlg.vysledok.id)
            self._obnov_dokumenty()

    def _odstran(self) -> None:
        k = self._vybrany_kandidat()
        if k is None:
            return
        if not messagebox.askyesno(
            "Kandidát", f"Odstrániť kandidáta {k.cele_meno}?", parent=self
        ):
            return
        self.z.kandidati = [x for x in self.z.kandidati if x.id != k.id]
        self._obnov_kandidatov()
        self._obnov_dokumenty()

    # ------------------------------------------------------------ dokumenty
    def _vybrany_typ(self) -> str | None:
        sel = self.tree_d.selection()
        return sel[0] if sel else None

    def _pridaj_dokument(self) -> None:
        k = self._vybrany_kandidat()
        if k is None:
            messagebox.showinfo(
                "Dokumenty", "Najprv vyberte kandidáta.", parent=self
            )
            return
        typ = self._vybrany_typ()
        if typ is None:
            messagebox.showinfo(
                "Dokumenty",
                "Vyberte typ dokumentu (riadok dole), ktorý chcete pridať.",
                parent=self,
            )
            return
        zdroj = filedialog.askopenfilename(
            parent=self,
            title=f"Vybrať súbor – {typ}",
            filetypes=[
                ("Dokumenty PDF/Word", "*.pdf *.doc *.docx"),
                ("PDF", "*.pdf"),
                ("Word", "*.doc *.docx"),
                ("Všetky súbory", "*.*"),
            ],
        )
        if not zdroj:
            return
        nazov = os.path.basename(zdroj)
        koren, pripona = os.path.splitext(nazov)
        mat = Material(nazov=nazov, cesta="")
        cielovy = os.path.join(
            priecinok_kandidatov(), f"{koren}_{mat.id[:8]}{pripona}"
        )
        try:
            shutil.copy2(zdroj, cielovy)
        except OSError as e:
            messagebox.showerror(
                "Dokumenty", f"Súbor sa nepodarilo skopírovať:\n{e}", parent=self
            )
            return
        mat.cesta = cielovy
        k.dokumenty[typ] = mat
        self._obnov_kandidatov()
        self._obnov_dokumenty()

    def _otvor_dokument(self) -> None:
        k = self._vybrany_kandidat()
        typ = self._vybrany_typ()
        if k is None or typ is None:
            return
        mat = k.dokument(typ)
        if mat is None:
            return
        if not os.path.exists(mat.cesta):
            messagebox.showwarning(
                "Dokumenty",
                "Súbor sa nenašiel (mohol byť presunutý alebo zmazaný).",
                parent=self,
            )
            return
        if sys.platform != "win32":
            messagebox.showinfo("Dokumenty", f"Súbor:\n{mat.cesta}", parent=self)
            return
        os.startfile(mat.cesta)

    def _odstran_dokument(self) -> None:
        k = self._vybrany_kandidat()
        typ = self._vybrany_typ()
        if k is None or typ is None or typ not in k.dokumenty:
            return
        if not messagebox.askyesno(
            "Dokumenty", f'Odstrániť dokument „{typ}"?', parent=self
        ):
            return
        del k.dokumenty[typ]
        self._obnov_kandidatov()
        self._obnov_dokumenty()
