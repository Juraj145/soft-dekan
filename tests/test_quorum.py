from volby_dekana.docx_export import vytvor_prezencnu_listinu
from volby_dekana.models import (
    Clen,
    Kandidat,
    Material,
    Skupina,
    Stav,
    Zhromazdenie,
)
from volby_dekana.quorum import potrebne_kvorum, vyhodnot_kvorum


def _clen(priezvisko: str, stav: Stav = Stav.PRITOMNY, skupina=Skupina.SENAT) -> Clen:
    return Clen(meno="Test", priezvisko=priezvisko, skupina=skupina, stav=stav)


def test_potrebne_kvorum_3_5():
    assert potrebne_kvorum(20) == 12
    assert potrebne_kvorum(10) == 6
    assert potrebne_kvorum(11) == 7  # ceil(6.6) -> 7
    assert potrebne_kvorum(0) == 0


def test_uznasaniaschopne_pri_12_pritomnych_z_20():
    z = Zhromazdenie(celkovy_pocet=20)
    z.clenovia = [_clen(f"P{i:02d}") for i in range(12)]
    z.clenovia += [_clen(f"O{i:02d}", Stav.OSPRAVEDLNENY) for i in range(8)]
    vk = vyhodnot_kvorum(z)
    assert vk.pocet_pritomnych == 12
    assert vk.pocet_ospravedlnenych == 8
    assert vk.potrebne_kvorum == 12
    assert vk.uznasaniaschopne is True
    assert vk.chyba_do_kvora == 0


def test_neuznasaniaschopne_pri_11_pritomnych():
    z = Zhromazdenie(celkovy_pocet=20)
    z.clenovia = [_clen(f"P{i:02d}") for i in range(11)]
    vk = vyhodnot_kvorum(z)
    assert vk.uznasaniaschopne is False
    assert vk.chyba_do_kvora == 1


def test_abecedne_zoradenie_podla_priezviska():
    z = Zhromazdenie()
    z.clenovia = [_clen("Žiak"), _clen("Adam"), _clen("Čech"), _clen("Cibula")]
    poradie = [c.priezvisko for c in z.clenovia_zoradeni()]
    # V slovenskej abecede platí c < č, preto Cibula predchádza Čech.
    assert poradie == ["Adam", "Cibula", "Čech", "Žiak"]


def test_cele_meno_format():
    c = Clen(meno="Ján", priezvisko="Novák", titul_pred="Ing.", titul_za="PhD.")
    assert c.cele_meno == "Ing. Ján Novák, PhD."
    c2 = Clen(meno="Eva", priezvisko="Malá")
    assert c2.cele_meno == "Eva Malá"


def test_miesto_riadky_serializacia_a_property():
    z = Zhromazdenie(celkovy_pocet=20)
    z.miesto_riadky = ["Technická fakulta SPU", "Tr. A. Hlinku 2", "949 76 Nitra", "", ""]
    d = z.to_dict()
    assert d["miesto_riadky"] == z.miesto_riadky
    z2 = Zhromazdenie.from_dict(d)
    assert z2.miesto_riadky == z.miesto_riadky
    # property 'miesto' spojí len neprázdne riadky novými riadkami.
    assert z2.miesto == "Technická fakulta SPU\nTr. A. Hlinku 2\n949 76 Nitra"


def test_miesto_spatna_kompatibilita_stary_format():
    # Starý JSON mal jediný reťazec 'miesto'; musí sa rozdeliť na 5 riadkov.
    z = Zhromazdenie.from_dict({"celkovy_pocet": 20, "miesto": "Aula\nNitra"})
    assert len(z.miesto_riadky) == 5
    assert z.miesto_riadky[0] == "Aula"
    assert z.miesto_riadky[1] == "Nitra"


def test_prezencna_listina_z_predlohy():
    z = Zhromazdenie(celkovy_pocet=20, datum="15. 09. 2024")
    z.miesto_riadky = ["Aula SPU", "Tr. A. Hlinku 2", "949 76 Nitra", "", ""]
    z.clenovia = [_clen("Žiak"), _clen("Adam"), _clen("Čech")]
    doc = vytvor_prezencnu_listinu(z)
    # Miesto a dátum sú vyplnené.
    texty = [p.text for p in doc.paragraphs]
    assert any("Miesto konania:" in t and "Aula SPU" in t for t in texty)
    assert any(t.strip().startswith("Dátum:") and "15. 09. 2024" in t for t in texty)
    # Tabuľka členov: hlavička + 20 riadkov; mená zoradené podľa priezviska.
    tab = doc.tables[1]
    assert len(tab.rows) == 21
    assert tab.rows[1].cells[1].text == "Test Adam"
    assert tab.rows[2].cells[1].text == "Test Čech"
    assert tab.rows[3].cells[1].text == "Test Žiak"
    assert tab.rows[4].cells[1].text == ""
    # Hostia: poradové čísla sú súvislé (oprava preskočeného 21).
    hostia = doc.tables[3]
    cisla = [hostia.rows[i].cells[0].text for i in range(1, len(hostia.rows))]
    assert cisla == [f"{i}." for i in range(1, len(hostia.rows))]


def test_komisia_a_materialy_serializacia():
    z = Zhromazdenie(celkovy_pocet=20)
    z.clenovia = [_clen("Adam"), _clen("Cibula"), _clen("Žiak")]
    z.komisia_ids = [z.clenovia[0].id, z.clenovia[2].id]
    z.predseda_komisie_id = z.clenovia[2].id
    z.materialy_komisie = [Material(nazov="zapisnica.pdf", cesta="/x/zapisnica.pdf")]
    # Predseda je v komisii a je vrátený ako prvý.
    komisia = z.komisia()
    assert komisia[0].id == z.predseda_komisie_id
    assert {c.id for c in komisia} == set(z.komisia_ids)
    # Round-trip serializácia.
    z2 = Zhromazdenie.from_dict(z.to_dict())
    assert z2.komisia_ids == z.komisia_ids
    assert z2.predseda_komisie_id == z.predseda_komisie_id
    assert z2.materialy_komisie[0].nazov == "zapisnica.pdf"
    assert z2.materialy_komisie[0].cesta == "/x/zapisnica.pdf"


def test_kandidati_zoradenie_a_serializacia():
    z = Zhromazdenie(celkovy_pocet=20)
    z.kandidati = [
        Kandidat(meno="Eva", priezvisko="Žiaková", titul_pred="Ing.", titul_za="PhD."),
        Kandidat(meno="Marek", priezvisko="Adam", pocet_navrhov=7),
    ]
    z.kandidati[0].dokumenty["Životopis"] = Material(
        nazov="cv.pdf", cesta="/x/cv.pdf"
    )
    # Zoradenie podľa priezviska.
    poradie = [k.priezvisko for k in z.kandidati_zoradeni()]
    assert poradie == ["Adam", "Žiaková"]
    # Round-trip serializácia vrátane návrhov a dokumentov.
    z2 = Zhromazdenie.from_dict(z.to_dict())
    adam = next(k for k in z2.kandidati if k.priezvisko == "Adam")
    ziak = next(k for k in z2.kandidati if k.priezvisko == "Žiaková")
    assert adam.pocet_navrhov == 7
    assert ziak.cele_meno == "Ing. Eva Žiaková, PhD."
    assert ziak.dokument("Životopis").nazov == "cv.pdf"


def test_potrebna_vacsina_nadpolovicna():
    from volby_dekana.volba import potrebna_vacsina
    assert potrebna_vacsina(20) == 11
    assert potrebna_vacsina(21) == 11
    assert potrebna_vacsina(19) == 10
    assert potrebna_vacsina(0) == 0


def test_vyhodnot_kolo_zvoleny_v_prvom_kole():
    from volby_dekana.volba import vyhodnot_kolo
    kandidati = [
        Kandidat(meno="A", priezvisko="Adam", hlasy_k1=11),
        Kandidat(meno="B", priezvisko="Boris", hlasy_k1=5),
        Kandidat(meno="C", priezvisko="Cyril", hlasy_k1=2),
    ]
    v = vyhodnot_kolo(kandidati, 1, 20)
    assert v.zvoleny is not None
    assert v.zvoleny.priezvisko == "Adam"
    assert v.postupujuci == []


def test_vyhodnot_kolo_postup_dvoch_pri_zhode():
    from volby_dekana.volba import vyhodnot_kolo
    kandidati = [
        Kandidat(meno="A", priezvisko="Gálik", hlasy_k1=8),
        Kandidat(meno="B", priezvisko="Tkáč", hlasy_k1=8),
        Kandidat(meno="C", priezvisko="Novák", hlasy_k1=2),
    ]
    v = vyhodnot_kolo(kandidati, 1, 20)
    assert v.zvoleny is None
    assert {k.priezvisko for k in v.postupujuci} == {"Gálik", "Tkáč"}
    # Poradie je zostupne podľa hlasov.
    assert v.poradie[0][1] >= v.poradie[-1][1]


def test_vyhodnot_kolo2_zvoleny():
    from volby_dekana.volba import vyhodnot_kolo
    kandidati = [
        Kandidat(meno="A", priezvisko="Gálik", hlasy_k2=5),
        Kandidat(meno="B", priezvisko="Tkáč", hlasy_k2=13),
    ]
    v = vyhodnot_kolo(kandidati, 2, 20)
    assert v.zvoleny is not None
    assert v.zvoleny.priezvisko == "Tkáč"


def test_hlasy_serializacia():
    z = Zhromazdenie(celkovy_pocet=20, neplatne_k1=2, neplatne_k2=1)
    z.kandidati = [Kandidat(meno="A", priezvisko="Adam", hlasy_k1=8, hlasy_k2=13)]
    z2 = Zhromazdenie.from_dict(z.to_dict())
    assert z2.neplatne_k1 == 2
    assert z2.neplatne_k2 == 1
    assert z2.kandidati[0].hlasy_k1 == 8
    assert z2.kandidati[0].hlasy_k2 == 13


def test_hlasovaci_listok_z_predlohy():
    from volby_dekana.docx_export import vytvor_hlasovaci_listok
    z = Zhromazdenie(celkovy_pocet=20, datum="22.06.2026")
    z.kandidati = [
        Kandidat(meno="Roman", priezvisko="Gálik", titul_pred="prof. Ing.", titul_za="PhD."),
        Kandidat(meno="Zdenko", priezvisko="Tkáč", titul_pred="prof. Ing.", titul_za="PhD."),
    ]
    doc = vytvor_hlasovaci_listok(z, 1, z.kandidati_zoradeni())
    texty = [p.text for p in doc.paragraphs]
    assert any("1. kolo volieb" in t for t in texty)
    assert any("22.06.2026" in t for t in texty)
    tab = doc.tables[1]
    assert len(tab.rows) == 3  # hlavička + 2 kandidáti
    assert "Gálik" in tab.rows[1].cells[1].text


def test_zapisnica_z_predlohy_postup_do_2_kola():
    from volby_dekana.docx_export import vytvor_zapisnicu
    z = Zhromazdenie(celkovy_pocet=20, datum="22.06.2026", neplatne_k1=2)
    z.clenovia = [_clen(f"P{i:02d}") for i in range(18)]
    z.clenovia += [_clen(f"O{i:02d}", Stav.OSPRAVEDLNENY) for i in range(2)]
    z.kandidati = [
        Kandidat(meno="Roman", priezvisko="Gálik", hlasy_k1=8, hlasy_k2=5),
        Kandidat(meno="Zdenko", priezvisko="Tkáč", hlasy_k1=8, hlasy_k2=13),
        Kandidat(meno="Jan", priezvisko="Novák", hlasy_k1=2),
    ]
    doc = vytvor_zapisnicu(z)
    texty = "\n".join(p.text for p in doc.paragraphs)
    assert "1. kolo bolo neúspešné" in texty
    assert "Do 2. kola postupujú" in texty
    assert "ZVOLENÝ" in texty
    assert "Tkáč" in texty


def test_obdobie_property():
    z = Zhromazdenie(obdobie_od="2026", obdobie_do="2030")
    assert z.obdobie == "2026 \u2013 2030"
    assert Zhromazdenie(obdobie_od="2026").obdobie == "2026"
    assert Zhromazdenie().obdobie == ""


def test_otvaranie_overenie_serializacia():
    z = Zhromazdenie(
        otvaranie_obalok="11.06.2026 o 13:00 h",
        overenie_navrhov="15.06.2026 o 13:00 h",
    )
    z2 = Zhromazdenie.from_dict(z.to_dict())
    assert z2.otvaranie_obalok == "11.06.2026 o 13:00 h"
    assert z2.overenie_navrhov == "15.06.2026 o 13:00 h"


def test_zapisnica_doplni_obdobie_datumy_a_podpisy_bez_predsedu():
    from volby_dekana.docx_export import vytvor_zapisnicu
    z = Zhromazdenie(
        celkovy_pocet=20,
        datum="22.06.2026",
        obdobie_od="2026",
        obdobie_do="2030",
        otvaranie_obalok="11.06.2026 o 13:00 h",
        overenie_navrhov="15.06.2026 o 13:00 h",
    )
    z.clenovia = [_clen(f"P{i:02d}") for i in range(7)]
    z.komisia_ids = [c.id for c in z.clenovia[:5]]
    z.predseda_komisie_id = z.clenovia[0].id
    z.kandidati = [
        Kandidat(meno="Roman", priezvisko="Gálik", hlasy_k1=12),
        Kandidat(meno="Zdenko", priezvisko="Tkáč", hlasy_k1=6),
    ]
    doc = vytvor_zapisnicu(z)
    texty = "\n".join(p.text.replace("\xa0", " ") for p in doc.paragraphs)
    # Roky funkčného obdobia doplnené za „na funkčné obdobie".
    assert "na funkčné obdobie 2026 \u2013 2030" in texty
    # Dátum a čas otvárania obálok a overenia návrhov.
    assert "Otváranie obálok" in texty
    assert "sa uskutočnilo dňa 11.06.2026 o 13:00 h." in texty
    assert "sa uskutočnilo dňa 15.06.2026 o 13:00 h." in texty
    # Zvýraznený placeholder času vyhlásenia voľby.
    for p in doc.paragraphs:
        if "vyhlásil voľbu" in p.text:
            hl = [r for r in p.runs if r.font.highlight_color]
            assert len(hl) == 1
            assert "DOPLNIŤ RUČNE" in hl[0].text
    # Podpisy členov komisie bez predsedu (komisia má 5, podpisuje 4).
    podpisy = doc.tables[10]
    predseda = z.predseda_komisie().cele_meno
    mena = [podpisy.rows[i].cells[1].text for i in range(1, len(podpisy.rows))]
    assert len(mena) == 4
    assert predseda not in mena
