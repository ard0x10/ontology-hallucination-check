"""
Halüsinasyon Dedektörü
----------------------
LLM çıktısındaki yapısal iddiaları (üniversite, özellik, değer) ontolojiye
karşı doğrular. Her iddia için durum etiketi ve gerçek değer döner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ontology_engine import OntologyEngine, _normalize


class ClaimStatus(str, Enum):
    SUPPORTED   = "destekleniyor"      # ontoloji ile birebir uyumlu
    CONTRADICTED = "çelişiyor"          # ontoloji farklı bir değer söylüyor
    UNKNOWN      = "doğrulanamadı"      # ontolojide bu varlık yok


@dataclass
class VerifiedClaim:
    university: str
    property: str
    claimed_value: str
    status: ClaimStatus
    actual_value: str | None = None

    @property
    def emoji(self) -> str:
        return {
            ClaimStatus.SUPPORTED: "✅",
            ClaimStatus.CONTRADICTED: "❌",
            ClaimStatus.UNKNOWN: "❔",
        }[self.status]

    def humanize_property(self) -> str:
        return {
            "foundedYear": "kuruluş yılı",
            "city": "şehir",
            "type": "tür",
        }.get(self.property, self.property)


class HallucinationDetector:
    def __init__(self, ontology: OntologyEngine) -> None:
        self.onto = ontology

    def verify_claims(self, claims: list[dict]) -> list[VerifiedClaim]:
        results: list[VerifiedClaim] = []
        for c in claims:
            uni_name = (c.get("university") or "").strip()
            prop = (c.get("property") or "").strip()
            value = c.get("value")
            if not uni_name or not prop or value is None:
                continue

            uri_list = self.onto.detect_universities(uni_name)
            if not uri_list:
                results.append(VerifiedClaim(
                    university=uni_name, property=prop,
                    claimed_value=str(value),
                    status=ClaimStatus.UNKNOWN,
                ))
                continue

            uri = uri_list[0]
            facts = self.onto.get_facts(uri)
            if facts is None:
                results.append(VerifiedClaim(
                    university=uni_name, property=prop,
                    claimed_value=str(value),
                    status=ClaimStatus.UNKNOWN,
                ))
                continue

            actual: str | None = None
            ok = False
            try:
                if prop == "foundedYear":
                    claimed = int(str(value).strip())
                    actual = str(facts.founded_year) if facts.founded_year else None
                    ok = facts.founded_year == claimed
                elif prop == "city":
                    actual = facts.city
                    ok = _normalize(str(value)) == _normalize(facts.city or "")
                elif prop == "type":
                    actual = facts.type_label
                    needle = _normalize(str(value))
                    haystack = _normalize(facts.type_label or "")
                    ok = needle and (needle in haystack or haystack.startswith(needle))
                else:
                    actual = None
                    ok = False
            except (ValueError, TypeError):
                ok = False

            status = ClaimStatus.SUPPORTED if ok else ClaimStatus.CONTRADICTED
            if actual is None:
                status = ClaimStatus.UNKNOWN

            results.append(VerifiedClaim(
                university=facts.label,
                property=prop,
                claimed_value=str(value),
                status=status,
                actual_value=actual,
            ))
        return results

    @staticmethod
    def summary(verified: list[VerifiedClaim]) -> dict:
        counts = {s.value: 0 for s in ClaimStatus}
        for v in verified:
            counts[v.status.value] += 1
        return counts
