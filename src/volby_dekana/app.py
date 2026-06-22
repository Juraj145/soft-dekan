"""Hlavné okno aplikácie Voľby dekana TF SPU v Nitre."""
from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .dialogs import ClenDialog
from .docx_export import uloz_prezencnu_listinu
from .kandidati_okno import KandidatiPanel
from .komisia_okno import KomisiaPanel
from .models import POCET_KOMISIA, POCET_RIADKOV_MIESTA, Zhromazdenie
from .quorum import vyhodnot_kvorum
from .resources import cesta_k_asetu, priecinok_udajov
from . import updater

APP_TITLE = "Voľby dekana TF SPU v Nitre"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("960x720")
        self.minsize(820, 640)

        self.z = Zhromazdenie()
        self._aktualna_cesta: str | None = None
        self._index = 0

        self._nastav_ikonu()
        self._vytvor_menu()
        self._vytvor_widgety()
        self._obnov_zoznam()
        self._prepocitaj()
        self._vytvor_uvod()

    # ---------------------------------------------------------------- UI build
    def _nastav_ikonu(self) -> None:
        """Nastaví ikonu okna na logo fakulty (ak je dostupné)."""
        try:
            self.iconbitmap(cesta_k_asetu("logo.ico"))
        except Exception:
            pass

    def _vytvor_menu(self) -> None:
        menubar = tk.Menu(self)
        m_subor = tk.Menu(menubar, tearoff=0)
        m_subor.add_command(label="Nové zhromaždenie", command=self._novy)
        m_subor.add_command(label="Otvoriť…", command=self._otvor)
        m_subor.add_command(label="Uložiť…", command=self._uloz)
        m_subor.add_separator()
        m_subor.add_command(
            label="Generovať prezenčnú listinu (.docx)…",
            command=self._generuj_listinu,
        )
        m_subor.add_separator()
        m_subor.add_command(label="Koniec", command=self.destroy)
        menubar.add_cascade(label="Súbor", menu=m_subor)

        m_pomoc = tk.Menu(menubar, tearoff=0)
        m_pomoc.add_command(
            label="Aktualizovať program…", command=self._aktualizuj_program
        )
        m_pomoc.add_command(label="O programe…", command=self._o_programe)
        menubar.add_cascade(label="Pomoc", menu=m_pomoc)
        self.config(menu=menubar)

    def _vytvor_widgety(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # --- Hlavička s logom fakulty ---
        hlavicka = ttk.Frame(root)
        hlavicka.pack(fill="x", pady=(0, 8))
        self._logo_img = None
        try:
            self._logo_img = tk.PhotoImage(file=cesta_k_asetu("logo.png"))
            ttk.Label(hlavicka, image=self._logo_img).pack(side="left")
        except Exception:
            pass
        ttk.Label(
            hlavicka, text=APP_TITLE, font=("TkDefaultFont", 13, "bold")
        ).pack(side="left", padx=12)
        ttk.Button(
            hlavicka, text="Aktualizovať program", command=self._aktualizuj_program
        ).pack(side="right")

        # --- Názov aktuálneho kroku ---
        self.lbl_krok = ttk.Label(root, text="", font=("TkDefaultFont", 12, "bold"))
        self.lbl_krok.pack(fill="x", pady=(0, 6))

        # --- Navigačné tlačidlá (Späť / Ďalej) ---
        navlista = ttk.Frame(root)
        navlista.pack(side="bottom", fill="x", pady=(8, 0))
        self.btn_spat = ttk.Button(navlista, text="◀ Späť", command=self._spat)
        self.btn_spat.pack(side="left")
        self.btn_dalej = ttk.Button(navlista, text="Ďalej ▶", command=self._dalej)
        self.btn_dalej.pack(side="right")
        self.lbl_nav_info = tk.Label(
            root, text="", fg="#b00020", justify="left", anchor="w", wraplength=900
        )
        self.lbl_nav_info.pack(side="bottom", fill="x", pady=(6, 0))

        # --- Kontajner stránok sprievodcu ---
        self.kontajner = ttk.Frame(root)
        self.kontajner.pack(fill="both", expand=True)

        self.stranka_listina = self._vytvor_stranku_listina(self.kontajner)
        self.panel_komisia = KomisiaPanel(self.kontajner, self.z)
        self.panel_kandidati = KandidatiPanel(self.kontajner, self.z)
        self._stranky = [
            ("Krok 1 z 3 – Prezenčná listina", self.stranka_listina),
            ("Krok 2 z 3 – Volebná komisia", self.panel_komisia),
            ("Krok 3 z 3 – Kandidáti na dekana TF", self.panel_kandidati),
        ]
        self._zobraz_stranku()

    def _vytvor_uvod(self) -> None:
        """Úvodná titulná obrazovka zobrazená pred sprievodcom."""
        self.uvod = tk.Frame(self, bg="white")
        self.uvod.place(relx=0, rely=0, relwidth=1, relheight=1)
        stred = tk.Frame(self.uvod, bg="white")
        stred.place(relx=0.5, rely=0.5, anchor="center")
        self._uvod_img = None
        try:
            self._uvod_img = tk.PhotoImage(file=cesta_k_asetu("uvod.png"))
            tk.Label(
                stred, image=self._uvod_img, bg="white", bd=1, relief="solid"
            ).pack()
        except Exception:
            tk.Label(
                stred,
                text="Voľba dekana Technickej fakulty\nSPU v Nitre 2026 – 2030",
                font=("TkDefaultFont", 18, "bold"),
                bg="white",
                justify="center",
            ).pack(pady=60)
        ttk.Button(
            stred, text="Pokračovať ▶", command=self._zavri_uvod
        ).pack(pady=16)

    def _zavri_uvod(self) -> None:
        if hasattr(self, "uvod") and self.uvod.winfo_exists():
            self.uvod.destroy()

    def _vytvor_stranku_listina(self, kontajner: tk.Misc) -> ttk.Frame:
        root = ttk.Frame(kontajner)

        # --- Vstupné údaje ---
        ramec_vstup = ttk.LabelFrame(root, text="Vstupné údaje", padding=10)
        ramec_vstup.pack(fill="x")

        self.var_celkovy = tk.StringVar(value=str(self.z.celkovy_pocet))
        self.var_miesto_riadky = [tk.StringVar() for _ in range(POCET_RIADKOV_MIESTA)]
        self.var_datum = tk.StringVar()
        self.var_od = tk.StringVar()
        self.var_do = tk.StringVar()

        def _riadok(r: int, popis: str, var: tk.StringVar, col: int = 0, **kw):
            ttk.Label(ramec_vstup, text=popis).grid(
                row=r, column=col, sticky="w", padx=4, pady=4
            )
            ent = ttk.Entry(ramec_vstup, textvariable=var, **kw)
            ent.grid(row=r, column=col + 1, sticky="ew", padx=4, pady=4)
            return ent

        ramec_vstup.columnconfigure(1, weight=1)
        ramec_vstup.columnconfigure(3, weight=1)

        ent_celk = _riadok(0, "Celkový počet členov:", self.var_celkovy, width=10)
        ent_celk.bind("<KeyRelease>", lambda _e: self._prepocitaj())
        _riadok(1, "Dátum konania:", self.var_datum)
        _riadok(2, "Funkčné obdobie dekana od:", self.var_od)
        _riadok(3, "do:", self.var_do)

        # Miesto konania ako 5 riadkov adresy pod sebou (vpravo).
        ttk.Label(ramec_vstup, text="Miesto konania:").grid(
            row=0, column=2, sticky="nw", padx=4, pady=4
        )
        for i, var in enumerate(self.var_miesto_riadky):
            ttk.Entry(ramec_vstup, textvariable=var).grid(
                row=i, column=3, sticky="ew", padx=4, pady=2
            )

        # --- Prezenčná listina ---
        ramec_zoznam = ttk.LabelFrame(root, text="Prezenčná listina", padding=10)
        ramec_zoznam.pack(fill="both", expand=True, pady=(10, 0))

        panel_tlac = ttk.Frame(ramec_zoznam)
        panel_tlac.pack(fill="x", pady=(0, 6))
        ttk.Button(panel_tlac, text="Pridať člena", command=self._pridaj).pack(
            side="left", padx=2
        )
        ttk.Button(panel_tlac, text="Upraviť", command=self._uprav).pack(
            side="left", padx=2
        )
        ttk.Button(panel_tlac, text="Odstrániť", command=self._odstran).pack(
            side="left", padx=2
        )
        ttk.Button(
            panel_tlac, text="Pridať/odobrať z komisie", command=self._prepni_komisiu
        ).pack(side="left", padx=2)
        ttk.Button(
            panel_tlac, text="Nastaviť ako predsedu komisie", command=self._nastav_predsedu
        ).pack(side="left", padx=2)

        stlpce = ("priezvisko", "meno", "titul", "skupina", "stav", "komisia", "predseda")
        self.tree = ttk.Treeview(
            ramec_zoznam, columns=stlpce, show="headings", selectmode="browse"
        )
        nadpisy = {
            "priezvisko": "Priezvisko",
            "meno": "Meno",
            "titul": "Titul(y)",
            "skupina": "Skupina",
            "stav": "Stav",
            "komisia": "Komisia",
            "predseda": "Predseda komisie",
        }
        sirky = {
            "priezvisko": 140,
            "meno": 120,
            "titul": 110,
            "skupina": 210,
            "stav": 100,
            "komisia": 80,
            "predseda": 120,
        }
        for s in stlpce:
            self.tree.heading(s, text=nadpisy[s])
            self.tree.column(s, width=sirky[s], anchor="w")
        self.tree.column("komisia", anchor="center")
        self.tree.column("predseda", anchor="center")

        scroll = ttk.Scrollbar(ramec_zoznam, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _e: self._uprav())

        # --- Kvórum ---
        ramec_kvorum = ttk.LabelFrame(root, text="Uznášaniaschopnosť", padding=10)
        ramec_kvorum.pack(fill="x", pady=(10, 0))

        self.lbl_kvorum = ttk.Label(ramec_kvorum, text="", justify="left")
        self.lbl_kvorum.pack(side="left")
        self.lbl_stav = tk.Label(
            ramec_kvorum, text="", font=("TkDefaultFont", 12, "bold")
        )
        self.lbl_stav.pack(side="right")

        return root

    # ---------------------------------------------------------------- sprievodca
    def _zobraz_stranku(self) -> None:
        for _, panel in self._stranky:
            panel.pack_forget()
        nazov, panel = self._stranky[self._index]
        panel.pack(fill="both", expand=True)
        self.lbl_krok.config(text=nazov)
        if panel is self.panel_komisia:
            self.panel_komisia.z = self.z
            self.panel_komisia.obnov()
        elif panel is self.panel_kandidati:
            self.panel_kandidati.z = self.z
            self.panel_kandidati.obnov()
        self._aktualizuj_nav()

    def _chybajuce_udaje(self, index: int) -> list[str]:
        """Zoznam povinných údajov, ktoré na danom kroku ešte chýbajú."""
        if index != 0:
            return []
        self._zber_vstupy()
        chyby: list[str] = []
        if self.z.celkovy_pocet <= 0:
            chyby.append("celkový počet členov")
        if not self.z.miesto.strip():
            chyby.append("miesto konania")
        if not self.z.datum:
            chyby.append("dátum konania")
        if not self.z.obdobie_od:
            chyby.append("funkčné obdobie od")
        if not self.z.obdobie_do:
            chyby.append("funkčné obdobie do")
        if not self.z.clenovia:
            chyby.append("členov prezenčnej listiny")
        if len(self.z.komisia_ids) != POCET_KOMISIA:
            chyby.append(
                f"volebnú komisiu ({len(self.z.komisia_ids)}/{POCET_KOMISIA} členov)"
            )
        elif self.z.predseda_komisie_id is None:
            chyby.append("predsedu komisie")
        return chyby

    def _aktualizuj_nav(self) -> None:
        self.btn_spat.config(state="normal" if self._index > 0 else "disabled")
        posledny = self._index >= len(self._stranky) - 1
        chyby = self._chybajuce_udaje(self._index)
        if posledny:
            self.btn_dalej.config(state="disabled")
            self.lbl_nav_info.config(text="")
        elif chyby:
            self.btn_dalej.config(state="disabled")
            self.lbl_nav_info.config(
                text="Pre pokračovanie doplňte: " + ", ".join(chyby) + "."
            )
        else:
            self.btn_dalej.config(state="normal")
            self.lbl_nav_info.config(text="")

    def _dalej(self) -> None:
        self._zber_vstupy()
        if self._chybajuce_udaje(self._index):
            return
        if self._index < len(self._stranky) - 1:
            self._index += 1
            self._zobraz_stranku()

    def _spat(self) -> None:
        self._zber_vstupy()
        if self._index > 0:
            self._index -= 1
            self._zobraz_stranku()

    # ---------------------------------------------------------------- helpers
    def _zber_vstupy(self) -> None:
        self.z.miesto_riadky = [v.get().strip() for v in self.var_miesto_riadky]
        self.z.datum = self.var_datum.get().strip()
        self.z.obdobie_od = self.var_od.get().strip()
        self.z.obdobie_do = self.var_do.get().strip()
        try:
            self.z.celkovy_pocet = int(self.var_celkovy.get().strip() or "0")
        except ValueError:
            self.z.celkovy_pocet = 0

    def _vybrany_id(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _obnov_zoznam(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for c in self.z.clenovia_zoradeni():
            je_predseda = "✓" if c.id == self.z.predseda_komisie_id else ""
            je_komisia = "✓" if c.id in self.z.komisia_ids else ""
            self.tree.insert(
                "",
                "end",
                iid=c.id,
                values=(
                    c.priezvisko,
                    c.meno,
                    c.tituly,
                    c.skupina.value,
                    c.stav.value,
                    je_komisia,
                    je_predseda,
                ),
            )
        if hasattr(self, "panel_komisia"):
            self.panel_komisia.z = self.z
            self.panel_komisia.obnov()
        if hasattr(self, "panel_kandidati"):
            self.panel_kandidati.z = self.z
            self.panel_kandidati.obnov()
        if hasattr(self, "btn_dalej"):
            self._aktualizuj_nav()

    def _prepocitaj(self) -> None:
        self._zber_vstupy()
        vk = vyhodnot_kvorum(self.z)
        self.lbl_kvorum.config(
            text=(
                f"Celkový počet členov: {vk.celkovy_pocet}\n"
                f"Potrebné kvórum (3/5): {vk.potrebne_kvorum}\n"
                f"Počet prítomných: {vk.pocet_pritomnych}    "
                f"Ospravedlnení: {vk.pocet_ospravedlnenych}"
            )
        )
        if vk.uznasaniaschopne:
            self.lbl_stav.config(text="UZNÁŠANIASCHOPNÉ", fg="#1b7f1b")
        else:
            chyba = vk.chyba_do_kvora
            self.lbl_stav.config(
                text=f"NEUZNÁŠANIASCHOPNÉ\n(chýba {chyba})", fg="#b00020"
            )
        if hasattr(self, "btn_dalej"):
            self._aktualizuj_nav()

    # ---------------------------------------------------------------- akcie
    def _pridaj(self) -> None:
        dlg = ClenDialog(self)
        self.wait_window(dlg)
        if dlg.vysledok:
            self.z.clenovia.append(dlg.vysledok)
            self._obnov_zoznam()
            self._prepocitaj()

    def _uprav(self) -> None:
        cid = self._vybrany_id()
        if not cid:
            return
        clen = next((c for c in self.z.clenovia if c.id == cid), None)
        if clen is None:
            return
        dlg = ClenDialog(self, clen)
        self.wait_window(dlg)
        if dlg.vysledok:
            idx = self.z.clenovia.index(clen)
            self.z.clenovia[idx] = dlg.vysledok
            self._obnov_zoznam()
            self._prepocitaj()

    def _odstran(self) -> None:
        cid = self._vybrany_id()
        if not cid:
            return
        self.z.clenovia = [c for c in self.z.clenovia if c.id != cid]
        if self.z.predseda_komisie_id == cid:
            self.z.predseda_komisie_id = None
        if cid in self.z.komisia_ids:
            self.z.komisia_ids.remove(cid)
        self._obnov_zoznam()
        self._prepocitaj()

    def _prepni_komisiu(self) -> None:
        cid = self._vybrany_id()
        if not cid:
            messagebox.showinfo(
                "Volebná komisia", "Najprv vyberte člena v zozname.", parent=self
            )
            return
        if cid in self.z.komisia_ids:
            self.z.komisia_ids.remove(cid)
            if self.z.predseda_komisie_id == cid:
                self.z.predseda_komisie_id = None
        else:
            if len(self.z.komisia_ids) >= POCET_KOMISIA:
                messagebox.showinfo(
                    "Volebná komisia",
                    f"Volebná komisia má {POCET_KOMISIA} členov. "
                    "Najprv niekoho odoberte.",
                    parent=self,
                )
                return
            self.z.komisia_ids.append(cid)
        self._obnov_zoznam()

    def _nastav_predsedu(self) -> None:
        cid = self._vybrany_id()
        if not cid:
            messagebox.showinfo(
                "Predseda komisie", "Najprv vyberte člena v zozname.", parent=self
            )
            return
        if cid not in self.z.komisia_ids:
            if len(self.z.komisia_ids) >= POCET_KOMISIA:
                messagebox.showinfo(
                    "Volebná komisia",
                    f"Volebná komisia má {POCET_KOMISIA} členov. "
                    "Najprv niekoho odoberte.",
                    parent=self,
                )
                return
            self.z.komisia_ids.append(cid)
        self.z.predseda_komisie_id = cid
        self._obnov_zoznam()

    def _novy(self) -> None:
        if not messagebox.askyesno(
            "Nové zhromaždenie", "Vymazať všetky údaje a začať odznova?", parent=self
        ):
            return
        self.z = Zhromazdenie()
        self._aktualna_cesta = None
        self.var_celkovy.set(str(self.z.celkovy_pocet))
        for v in (self.var_datum, self.var_od, self.var_do):
            v.set("")
        for v in self.var_miesto_riadky:
            v.set("")
        self._obnov_zoznam()
        self._prepocitaj()

    def _uloz(self) -> None:
        self._zber_vstupy()
        cesta = filedialog.asksaveasfilename(
            title="Uložiť vstupné údaje",
            defaultextension=".json",
            initialdir=priecinok_udajov(),
            initialfile="vstupne_udaje.json",
            filetypes=[("Súbor zhromaždenia", "*.json")],
        )
        if not cesta:
            return
        with open(cesta, "w", encoding="utf-8") as f:
            json.dump(self.z.to_dict(), f, ensure_ascii=False, indent=2)
        self._aktualna_cesta = cesta
        messagebox.showinfo("Uložené", "Údaje boli uložené.", parent=self)

    def _otvor(self) -> None:
        cesta = filedialog.askopenfilename(
            title="Načítať vstupné údaje",
            initialdir=priecinok_udajov(),
            filetypes=[("Súbor zhromaždenia", "*.json")],
        )
        if not cesta:
            return
        with open(cesta, encoding="utf-8") as f:
            data = json.load(f)
        self.z = Zhromazdenie.from_dict(data)
        self._aktualna_cesta = cesta
        self.var_celkovy.set(str(self.z.celkovy_pocet))
        for v, hodnota in zip(self.var_miesto_riadky, self.z.miesto_riadky):
            v.set(hodnota)
        self.var_datum.set(self.z.datum)
        self.var_od.set(self.z.obdobie_od)
        self.var_do.set(self.z.obdobie_do)
        self._obnov_zoznam()
        self._prepocitaj()

    def _generuj_listinu(self) -> None:
        self._zber_vstupy()
        cesta = filedialog.asksaveasfilename(
            title="Generovať prezenčnú listinu",
            defaultextension=".docx",
            initialdir=priecinok_udajov(),
            initialfile="Prezenčná listina.docx",
            filetypes=[("Dokument Word", "*.docx")],
        )
        if not cesta:
            return
        uloz_prezencnu_listinu(self.z, cesta)
        messagebox.showinfo(
            "Hotovo", f"Prezenčná listina bola uložená:\n{cesta}", parent=self
        )

    # ---------------------------------------------------------------- aktualizácia
    def _o_programe(self) -> None:
        messagebox.showinfo(
            "O programe",
            f"{APP_TITLE}\nVerzia {__version__}",
            parent=self,
        )

    def _aktualizuj_program(self) -> None:
        """Skontroluje GitHub a ponúkne stiahnutie a spustenie inštalátora."""
        def uloha() -> None:
            try:
                najnovsia = updater.zisti_najnovsiu_verziu()
            except Exception as e:
                self.after(
                    0,
                    lambda e=e: messagebox.showerror(
                        "Aktualizácia",
                        "Nepodarilo sa zistiť najnovšiu verziu.\n"
                        f"Skontrolujte pripojenie na internet.\n\n{e}",
                        parent=self,
                    ),
                )
                return
            self.after(0, lambda: self._po_zisteni_verzie(najnovsia))

        threading.Thread(target=uloha, daemon=True).start()

    def _po_zisteni_verzie(self, najnovsia: str) -> None:
        if not updater.je_novsia(najnovsia):
            messagebox.showinfo(
                "Aktualizácia",
                f"Máte najnovšiu verziu ({__version__}).",
                parent=self,
            )
            return
        if not messagebox.askyesno(
            "Aktualizácia",
            f"Je dostupná novšia verzia {najnovsia} (máte {__version__}).\n"
            "Stiahnuť a nainštalovať teraz?",
            parent=self,
        ):
            return

        def stiahnut() -> None:
            try:
                cesta = updater.stiahni_instalator()
            except Exception as e:
                self.after(
                    0,
                    lambda e=e: messagebox.showerror(
                        "Aktualizácia", f"Sťahovanie zlyhalo:\n{e}", parent=self
                    ),
                )
                return
            self.after(0, lambda: self._spusti_instalator(cesta))

        threading.Thread(target=stiahnut, daemon=True).start()

    def _spusti_instalator(self, cesta: str) -> None:
        if sys.platform != "win32":
            messagebox.showinfo(
                "Aktualizácia",
                f"Inštalátor je stiahnutý tu:\n{cesta}\nSpustite ho ručne.",
                parent=self,
            )
            return
        messagebox.showinfo(
            "Aktualizácia",
            "Spustí sa inštalátor novej verzie. Program sa teraz zatvorí, "
            "po inštalácii ho spustite znova.",
            parent=self,
        )
        os.startfile(cesta)
        self.destroy()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
