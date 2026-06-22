from volby_dekana.models import Clen, Skupina, Stav, Zhromazdenie
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
