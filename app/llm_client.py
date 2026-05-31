"""
LLM İstemcisi
-------------
İki çağrı modu sağlar:
  1) ask_raw            — saf GPT (bağlamsız, halüsinasyon riskli)
  2) ask_with_ontology  — ontoloji destekli (RAG benzeri, sadece doğrulanmış olgular)

Ek olarak yapısal iddia çıkarımı (extract_claims_json) yapar.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@dataclass
class LLMResponse:
    text: str
    model: str
    used_ontology: bool


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY ortam değişkeni bulunamadı. "
                ".env dosyasına ekleyin veya arayüzden girin."
            )
        self.client = OpenAI(api_key=key)
        self.model = model or DEFAULT_MODEL

    # --------------- 1) Saf GPT ---------------
    def ask_raw(self, question: str) -> LLMResponse:
        system = (
            "Sen Türkiye'deki üniversiteler hakkında soruları yanıtlayan bir asistansın. "
            "Cevapların kısa ve doğrudan olsun. Türkçe yanıtla."
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        )
        return LLMResponse(
            text=resp.choices[0].message.content.strip(),
            model=self.model,
            used_ontology=False,
        )

    # --------------- 2) Ontoloji destekli GPT ---------------
    def ask_with_ontology(self, question: str, ontology_context: str) -> LLMResponse:
        system = (
            "Sen Türkiye üniversiteleri hakkında soruları SADECE ve SADECE "
            "aşağıdaki 'DOĞRULANMIŞ ONTOLOJİ OLGULARI' bölümünde verilen bilgilere "
            "dayanarak cevaplayan bir asistansın.\n\n"
            "KESİN KURALLAR:\n"
            "1. Ontolojide olmayan bilgi için 'Ontolojide bu bilgi bulunmuyor' de.\n"
            "2. ASLA varsayım yapma, tahmin etme, genel bilgi kullanma.\n"
            "3. Ontolojideki sayı/şehir/yıl/isim bilgilerini değiştirmeden kullan.\n"
            "4. Cevabını kaynak gösterecek şekilde yaz: '(Ontoloji: …)' formatında.\n"
            "5. Türkçe yanıtla, kısa ve net ol.\n\n"
            "DOĞRULANMIŞ ONTOLOJİ OLGULARI:\n"
            f"{ontology_context if ontology_context.strip() else '(Bu soruyla ilgili eşleşen olgu yok.)'}"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        )
        return LLMResponse(
            text=resp.choices[0].message.content.strip(),
            model=self.model,
            used_ontology=True,
        )

    # --------------- 3) Yapısal iddia çıkarımı ---------------
    def extract_claims_json(self, answer_text: str) -> list[dict]:
        """
        Verilen cevap metninden olgu iddialarını JSON olarak çıkarır.
        Çıktı: [{"university": "...", "property": "foundedYear|city|type", "value": "..."}]
        """
        system = (
            "Sen bir bilgi çıkarım modülüsün. Verilen Türkçe metinden, "
            "Türk üniversiteleri ile ilgili olgu iddialarını çıkar. "
            "Sadece geçerli JSON dizisi döndür, başka hiçbir metin yazma.\n"
            "Format: [{\"university\": \"<üniversite adı>\", "
            "\"property\": \"foundedYear|city|type\", "
            "\"value\": \"<değer>\"}]\n"
            "  - foundedYear için değer 4 haneli yıl (örn 1956).\n"
            "  - city için değer şehir adı (örn İstanbul).\n"
            "  - type için değer 'Devlet' veya 'Vakıf'.\n"
            "Hiçbir iddia yoksa boş dizi [] döndür."
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system + "\nÖnemli: JSON nesnesi döndür, "
                                                       "anahtarı 'claims' olsun, değeri dizi."},
                {"role": "user", "content": answer_text},
            ],
        )
        try:
            payload = json.loads(resp.choices[0].message.content)
            claims = payload.get("claims", [])
            if isinstance(claims, list):
                return claims
        except (json.JSONDecodeError, AttributeError):
            pass
        return []
