"""Panel volebnej komisie a jej zápisníc (pripojené PDF/Word dokumenty)."""
from __future__ import annotations

import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .models import Material, Zhromazdenie
from .resources import priecinok_zapisnic


class KomisiaPanel(ttk.Frame):
    """Zobrazí členov volebnej komisie a umožní vkladať zápisnice."""

    def __init__(self, parent: tk.Misc, z: Zhromazdenie) -> None:
        super().__init__(parent)
        self.z = z
        self._vytvor_widgety()
        self.obnov()

    # ------------------------------------------------------------------ build
    def _vytvor_widgety(self) -> None:
        ramec_term = ttk.LabelFrame(
            self, text="Termíny zo zasadnutí volebnej komisie", padding=10
        )
        ramec_term.pack(fill="x", pady=(0, 6))
        self.var_otvaranie = tk.StringVar()
        self.var_overenie = tk.StringVar()
        self.var_otvaranie.trace_add("write", self._uloz_terminy)
        self.var_overenie.trace_add("write", self._uloz_terminy)
        ttk.Label(
            ramec_term, text="Otváranie obálok – dátum a čas:"
        ).grid(row=0, column=0, sticky="w", padx=2, pady=2)
        ttk.Entry(ramec_term, textvariable=self.var_otvaranie, width=40).grid(
            row=0, column=1, sticky="w", padx=2, pady=2
        )
        ttk.Label(
            ramec_term, text="(napr. 11.06.2026 o 13:00 h)"
        ).grid(row=0, column=2, sticky="w", padx=6, pady=2)
        ttk.Label(
            ramec_term, text="Overenie platnosti návrhov – dátum a čas:"
        ).grid(row=1, column=0, sticky="w", padx=2, pady=2)
        ttk.Entry(ramec_term, textvariable=self.var_overenie, width=40).grid(
            row=1, column=1, sticky="w", padx=2, pady=2
        )
        ttk.Label(
            ramec_term, text="(napr. 15.06.2026 o 13:00 h)"
        ).grid(row=1, column=2, sticky="w", padx=6, pady=2)

        ramec_cl = ttk.LabelFrame(
            self, text="Členovia volebnej komisie", padding=10
        )
        ramec_cl.pack(fill="x", pady=(0, 6))
        self.tree_cl = ttk.Treeview(
            ramec_cl,
            columns=("clen", "funkcia"),
            show="headings",
            height=6,
            selectmode="none",
        )
        self.tree_cl.heading("clen", text="Meno, priezvisko, titul(y)")
        self.tree_cl.heading("funkcia", text="Funkcia")
        self.tree_cl.column("clen", width=470, anchor="w")
        self.tree_cl.column("funkcia", width=150, anchor="w")
        self.tree_cl.pack(fill="x")

        ramec_z = ttk.LabelFrame(
            self, text="Zápisnice zo zasadnutia volebnej komisie", padding=10
        )
        ramec_z.pack(fill="both", expand=True, pady=(6, 0))

        panel = ttk.Frame(ramec_z)
        panel.pack(fill="x", pady=(0, 6))
        ttk.Button(panel, text="Pridať dokument…", command=self._pridaj).pack(
            side="left", padx=2
        )
        ttk.Button(panel, text="Otvoriť", command=self._otvor).pack(
            side="left", padx=2
        )
        ttk.Button(panel, text="Odstrániť", command=self._odstran).pack(
            side="left", padx=2
        )

        self.tree_z = ttk.Treeview(
            ramec_z, columns=("nazov",), show="headings", selectmode="browse"
        )
        self.tree_z.heading("nazov", text="Dokument (PDF / Word)")
        self.tree_z.column("nazov", width=620, anchor="w")
        scroll = ttk.Scrollbar(ramec_z, orient="vertical", command=self.tree_z.yview)
        self.tree_z.configure(yscrollcommand=scroll.set)
        self.tree_z.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree_z.bind("<Double-1>", lambda _e: self._otvor())

    def _uloz_terminy(self, *_args: object) -> None:
        self.z.otvaranie_obalok = self.var_otvaranie.get().strip()
        self.z.overenie_navrhov = self.var_overenie.get().strip()

    # ----------------------------------------------------------------- refresh
    def obnov(self) -> None:
        if self.var_otvaranie.get() != self.z.otvaranie_obalok:
            self.var_otvaranie.set(self.z.otvaranie_obalok)
        if self.var_overenie.get() != self.z.overenie_navrhov:
            self.var_overenie.set(self.z.overenie_navrhov)
        self._obnov_clenov()
        self._obnov_materialy()

    def _obnov_clenov(self) -> None:
        self.tree_cl.delete(*self.tree_cl.get_children())
        komisia = self.z.komisia()
        if not komisia:
            self.tree_cl.insert(
                "",
                "end",
                values=(
                    "(žiadni členovia – označte ich v okne Prezenčná listina)",
                    "",
                ),
            )
            return
        for c in komisia:
            funkcia = (
                "Predseda komisie"
                if c.id == self.z.predseda_komisie_id
                else "Člen"
            )
            self.tree_cl.insert("", "end", values=(c.cele_meno, funkcia))

    def _obnov_materialy(self) -> None:
        self.tree_z.delete(*self.tree_z.get_children())
        for m in self.z.materialy_komisie:
            self.tree_z.insert("", "end", iid=m.id, values=(m.nazov,))

    # ------------------------------------------------------------------ akcie
    def _pridaj(self) -> None:
        cesty = filedialog.askopenfilenames(
            parent=self,
            title="Vybrať dokument(y) zápisnice",
            filetypes=[
                ("Dokumenty PDF/Word", "*.pdf *.doc *.docx"),
                ("PDF", "*.pdf"),
                ("Word", "*.doc *.docx"),
                ("Všetky súbory", "*.*"),
            ],
        )
        if not cesty:
            return
        ciel = priecinok_zapisnic()
        for zdroj in cesty:
            nazov = os.path.basename(zdroj)
            koren, pripona = os.path.splitext(nazov)
            mat = Material(nazov=nazov, cesta="")
            cielovy = os.path.join(ciel, f"{koren}_{mat.id[:8]}{pripona}")
            try:
                shutil.copy2(zdroj, cielovy)
            except OSError as e:
                messagebox.showerror(
                    "Zápisnica",
                    f"Súbor sa nepodarilo skopírovať:\n{e}",
                    parent=self,
                )
                continue
            mat.cesta = cielovy
            self.z.materialy_komisie.append(mat)
        self._obnov_materialy()

    def _vybrany(self) -> Material | None:
        sel = self.tree_z.selection()
        if not sel:
            return None
        return next(
            (m for m in self.z.materialy_komisie if m.id == sel[0]), None
        )

    def _otvor(self) -> None:
        m = self._vybrany()
        if m is None:
            return
        if not os.path.exists(m.cesta):
            messagebox.showwarning(
                "Zápisnica",
                "Súbor sa nenašiel (mohol byť presunutý alebo zmazaný).",
                parent=self,
            )
            return
        if sys.platform != "win32":
            messagebox.showinfo("Zápisnica", f"Súbor:\n{m.cesta}", parent=self)
            return
        os.startfile(m.cesta)

    def _odstran(self) -> None:
        m = self._vybrany()
        if m is None:
            return
        if not messagebox.askyesno(
            "Zápisnica",
            f"Odstrániť dokument zo zoznamu?\n{m.nazov}",
            parent=self,
        ):
            return
        self.z.materialy_komisie = [
            x for x in self.z.materialy_komisie if x.id != m.id
        ]
        self._obnov_materialy()
