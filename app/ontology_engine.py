"""
Ontoloji Motoru
---------------
Türk üniversiteleri ontolojisini (Turtle/RDF) yükler, SPARQL ile sorgular
ve doğal dilden tespit edilen üniversite isimlerine ait olguları döner.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

UNI = Namespace("http://example.org/tr-uni#")

ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "ontology" / "universities.ttl"


def _normalize(text: str) -> str:
    """Türkçe karakterleri ve büyük/küçük harf farkını kaldırır."""
    text = text.lower()
    text = (
        text.replace("ç", "c").replace("ğ", "g").replace("ı", "i")
        .replace("ö", "o").replace("ş", "s").replace("ü", "u")
        .replace("â", "a").replace("î", "i").replace("û", "u")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class UniversityFacts:
    uri: str
    label: str
    official_name: str | None = None
    founded_year: int | None = None
    city: str | None = None
    type_label: str | None = None
    faculties: list[str] = field(default_factory=list)
    website: str | None = None

    def as_natural_text(self) -> str:
        parts = [f"- **{self.label}**"]
        if self.official_name and self.official_name != self.label:
            parts.append(f"  • Resmi ad: {self.official_name}")
        if self.founded_year:
            parts.append(f"  • Kuruluş yılı: {self.founded_year}")
        if self.city:
            parts.append(f"  • Şehir: {self.city}")
        if self.type_label:
            parts.append(f"  • Tür: {self.type_label}")
        if self.faculties:
            parts.append(f"  • Fakülteler: {', '.join(self.faculties)}")
        if self.website:
            parts.append(f"  • Web sitesi: {self.website}")
        return "\n".join(parts)


class OntologyEngine:
    def __init__(self, ttl_path: Path = ONTOLOGY_PATH) -> None:
        self.graph = Graph()
        self.graph.parse(ttl_path, format="turtle")
        self.graph.bind("uni", UNI)
        self._aliases = self._build_alias_index()

    # ---------------- alias index ----------------
    def _build_alias_index(self) -> dict[str, URIRef]:
        """Üniversiteler için arama dostu takma ad indeksi (kısaltmalar dahil)."""
        manual: dict[str, str] = {
            "bogazici": "Bogazici", "boun": "Bogazici",
            "itu": "ITU", "istanbul teknik": "ITU",
            "odtu": "ODTU", "metu": "ODTU", "orta dogu teknik": "ODTU",
            "ankara universitesi": "Ankara",
            "istanbul universitesi": "IstanbulU",
            "bilkent": "Bilkent",
            "hacettepe": "Hacettepe",
            "koc": "Koc", "koc universitesi": "Koc",
            "sabanci": "Sabanci",
            "yildiz teknik": "Yildiz", "ytu": "Yildiz", "yildiz": "Yildiz",
            "gazi": "Gazi",
            "ege": "Ege",
            "dokuz eylul": "DEU", "deu": "DEU",
            "marmara": "Marmara",
            "galatasaray": "Galatasaray", "gsu": "Galatasaray",
            "tobb": "TOBB", "tobb etu": "TOBB",
            "ozyegin": "Ozyegin",
            "bahcesehir": "Bahcesehir", "bau": "Bahcesehir",
            "ataturk": "Ataturk", "ataturk universitesi": "Ataturk",
            "ktu": "KTU", "karadeniz teknik": "KTU",
            "esogu": "ESOGU", "osmangazi": "ESOGU",
            "eskisehir osmangazi": "ESOGU",
        }
        index: dict[str, URIRef] = {}
        for alias, local in manual.items():
            index[_normalize(alias)] = UNI[local]

        # Ayrıca rdfs:label'lardan otomatik alias oluştur
        for s, _, o in self.graph.triples((None, RDFS.label, None)):
            if isinstance(s, URIRef) and str(s).startswith(str(UNI)):
                if (s, RDF.type, UNI.University) in self.graph or any(
                    (s, RDF.type, t) in self.graph
                    for t in (UNI.PublicUniversity, UNI.FoundationUniversity)
                ):
                    label = str(o)
                    norm = _normalize(label)
                    index[norm] = s
                    # "X Üniversitesi" → "X" da eklensin
                    short = norm.replace(" universitesi", "").strip()
                    if short and short not in index:
                        index[short] = s
        return index

    # ---------------- entity tespiti ----------------
    def detect_universities(self, text: str) -> list[URIRef]:
        norm = _normalize(text)
        hits: dict[str, URIRef] = {}
        # En uzun alias önce eşleşsin diye azalan sırada bak
        for alias in sorted(self._aliases.keys(), key=len, reverse=True):
            if len(alias) < 3:
                continue
            # tam kelime sınırı kontrolü
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", norm):
                uri = self._aliases[alias]
                hits.setdefault(str(uri), uri)
        return list(hits.values())

    # ---------------- olgu çekimi ----------------
    def get_facts(self, uri: URIRef) -> UniversityFacts | None:
        if (uri, None, None) not in self.graph:
            return None

        label = self.graph.value(uri, RDFS.label)
        official = self.graph.value(uri, UNI.officialName)
        year = self.graph.value(uri, UNI.foundedYear)
        city_uri = self.graph.value(uri, UNI.locatedIn)
        city = self.graph.value(city_uri, RDFS.label) if city_uri else None
        website = self.graph.value(uri, UNI.website)

        # tür
        type_label = None
        if (uri, RDF.type, UNI.PublicUniversity) in self.graph:
            type_label = "Devlet Üniversitesi"
        elif (uri, RDF.type, UNI.FoundationUniversity) in self.graph:
            type_label = "Vakıf Üniversitesi"

        faculties = []
        for fac_uri in self.graph.objects(uri, UNI.hasFaculty):
            fac_label = self.graph.value(fac_uri, RDFS.label)
            if fac_label:
                faculties.append(str(fac_label))

        return UniversityFacts(
            uri=str(uri),
            label=str(label) if label else str(uri),
            official_name=str(official) if official else None,
            founded_year=int(year) if year is not None else None,
            city=str(city) if city else None,
            type_label=type_label,
            faculties=sorted(faculties),
            website=str(website) if website else None,
        )

    def facts_for_text(self, text: str) -> list[UniversityFacts]:
        return [
            f for uri in self.detect_universities(text)
            if (f := self.get_facts(uri)) is not None
        ]

    # ---------------- doğrulama ----------------
    def verify_claim(self, university_uri: str, prop: str, value) -> tuple[bool, str | None]:
        """Bir iddiayı (üniversite, özellik, değer) ontolojiye karşı kontrol eder.
        Döner: (eşleşiyor_mu, gerçek_değer)."""
        uri = URIRef(university_uri)
        facts = self.get_facts(uri)
        if facts is None:
            return False, None

        prop = prop.lower()
        if prop in ("foundedyear", "founded_year", "kurulus", "kurulusyili", "year"):
            return facts.founded_year == int(value) if facts.founded_year else False, \
                   str(facts.founded_year) if facts.founded_year else None
        if prop in ("city", "sehir", "located", "locatedin", "il"):
            return _normalize(str(value)) == _normalize(facts.city or ""), facts.city
        if prop in ("type", "tur", "kategori"):
            return _normalize(str(value)).startswith(_normalize((facts.type_label or "").split()[0])), facts.type_label
        return False, None

    def all_universities(self) -> list[UniversityFacts]:
        out = []
        for s in set(self.graph.subjects(RDF.type, UNI.PublicUniversity)) | \
                 set(self.graph.subjects(RDF.type, UNI.FoundationUniversity)):
            f = self.get_facts(s)
            if f:
                out.append(f)
        return sorted(out, key=lambda x: x.founded_year or 9999)
