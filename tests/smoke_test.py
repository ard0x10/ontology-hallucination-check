"""
Smoke test — API anahtarı GEREKMEZ.
Sadece ontoloji motorunun ve dedektörün doğru çalıştığını kontrol eder.

Çalıştırma:
    python -m tests.smoke_test
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ontology_engine import OntologyEngine
from app.hallucination_detector import HallucinationDetector, ClaimStatus


def test_ontology_load():
    onto = OntologyEngine()
    unis = onto.all_universities()
    assert len(unis) >= 20, f"En az 20 üniversite bekleniyordu, {len(unis)} bulundu"
    print(f"  ✅ {len(unis)} üniversite yüklendi")


def test_entity_detection():
    onto = OntologyEngine()
    cases = [
        ("Boğaziçi Üniversitesi hangi yıl kuruldu?", "Bogazici"),
        ("ODTÜ hakkında bilgi ver", "ODTU"),
        ("Bilkent ne zaman açıldı?", "Bilkent"),
        ("Sabancı Üniversitesi nerede?", "Sabanci"),
    ]
    for question, expected in cases:
        uris = onto.detect_universities(question)
        local_names = [str(u).split("#")[-1] for u in uris]
        assert expected in local_names, f"'{question}' -> {local_names}, beklenen {expected}"
        print(f"  ✅ '{question}' -> {expected}")


def test_facts():
    onto = OntologyEngine()
    facts = onto.facts_for_text("Boğaziçi Üniversitesi")
    assert len(facts) == 1
    bogazici = facts[0]
    assert bogazici.founded_year == 1863
    assert bogazici.city == "İstanbul"
    assert bogazici.type_label == "Devlet Üniversitesi"
    print(f"  ✅ Boğaziçi olguları doğru: {bogazici.founded_year}, {bogazici.city}")


def test_hallucination_detector():
    onto = OntologyEngine()
    detector = HallucinationDetector(onto)

    fake_claims = [
        {"university": "Sabancı Üniversitesi", "property": "foundedYear", "value": "1999"},
        {"university": "Sabancı Üniversitesi", "property": "city", "value": "Ankara"},
        {"university": "Boğaziçi Üniversitesi", "property": "foundedYear", "value": "1863"},
        {"university": "Atlantis Üniversitesi", "property": "foundedYear", "value": "2020"},
    ]
    verified = detector.verify_claims(fake_claims)
    statuses = [v.status for v in verified]

    assert statuses[0] == ClaimStatus.CONTRADICTED, "Sabancı 1999 -> çelişmeli"
    assert statuses[1] == ClaimStatus.CONTRADICTED, "Sabancı Ankara -> çelişmeli"
    assert statuses[2] == ClaimStatus.SUPPORTED,    "Boğaziçi 1863 -> doğru"
    assert statuses[3] == ClaimStatus.UNKNOWN,      "Atlantis -> bilinmeyen"

    for v in verified:
        print(f"  {v.emoji} {v.university} / {v.humanize_property()} = {v.claimed_value} (gerçek: {v.actual_value})")


def main():
    print("\n[1/4] Ontoloji yükleme")
    test_ontology_load()
    print("\n[2/4] Varlık tespiti")
    test_entity_detection()
    print("\n[3/4] Olgu çekimi")
    test_facts()
    print("\n[4/4] Halüsinasyon dedektörü")
    test_hallucination_detector()
    print("\n🎉 Tüm testler başarılı.")


if __name__ == "__main__":
    main()
