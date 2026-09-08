# Ontoloji Tabanlı Halüsinasyon Denetimi

LLM'in üniversiteler hakkında söylediklerini, elle kurulmuş bir RDF/OWL ontolojisine
karşı doğrulayan Streamlit demosu. Model bir şey iddia eder, ontoloji onaylar ya da yalanlar.

> ⚠️ **API anahtarı:** Bu depoda `.env` dosyası yok, olması da gerekmiyor.
> Kendi anahtarınızı kendiniz girersiniz. `.env`, `.gitignore` içinde tanımlı,
> hiçbir zaman commit edilmedi.

## Ne yapıyor

Aynı soru iki kez cevaplanır ve yan yana konur:

1. **Saf GPT** — modele hiçbir bağlam verilmez, hafızasından cevaplar.
2. **Ontoloji destekli GPT** — soruda geçen üniversite tespit edilir, ontolojiden
   o üniversitenin olguları çekilir, modele bağlam olarak verilir.

Ardından **halüsinasyon dedektörü** çalışır: modelin cevabından yapısal iddialar
(`üniversite`, `özellik`, `değer`) çıkarılır ve her biri ontolojiye sorulur.

## Neyi doğruluyor

Üç özellik doğrulanabilir:

| Özellik | Ontolojideki karşılığı |
|---|---|
| `foundedYear` | kuruluş yılı (tam sayı eşleşmesi) |
| `city` | bulunduğu şehir (Türkçe karakter normalize edilerek) |
| `type` | devlet / vakıf üniversitesi |

Her iddia üç durumdan birini alır:

| Durum | Anlamı |
|---|---|
| ✅ destekleniyor | ontoloji ile birebir uyumlu |
| ❌ çelişiyor | ontoloji başka bir değer söylüyor |
| ❔ doğrulanamadı | varlık ontolojide yok, hüküm verilemiyor |

Üçüncü durum bilerek ayrı tutuluyor: **ontolojide olmaması, iddianın yanlış olduğu
anlamına gelmez.** Bilinmeyeni yanlışla karıştırmamak, doğrulama tarafının asıl işi.

Üniversite adı eşleştirmesi Türkçeye göre normalize edilir; "Boğaziçi", "bogazici"
ve "BOĞAZİÇİ" aynı varlığa düşer.

## Ontolojinin kapsamı

`ontology/universities.ttl` elle yazılmış, 234 satırlık bir Turtle dosyası:

- **21 üniversite** (15 devlet, 6 vakıf)
- 8 şehir, 8 fakülte
- Namespace: `http://example.org/tr-uni#`

T-BOX (sınıflar, özellikler) ve A-BOX (örnekler) aynı dosyada ayrılmış durumda.
Kapsam kasıtlı olarak dar: amaç Türkiye'nin tüm üniversitelerini listelemek değil,
doğrulama mekanizmasının çalıştığını gösterebilecek kadar zemin kurmak.

## Kurulum

```bash
git clone https://github.com/ard0x10/ontology-hallucination-check.git
cd ontology-hallucination-check
```

Windows / PowerShell:

```powershell
.\run.ps1
```

Sanal ortamı kurar, bağımlılıkları yükler, Streamlit'i başlatır.

Elle çalıştırmak isterseniz:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
streamlit run app/main.py
```

### API anahtarı

Proje kökünde `.env` oluşturun:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_MODEL` isteğe bağlı, verilmezse `gpt-4o-mini` kullanılır.
Anahtarı dosyaya hiç yazmadan, doğrudan Streamlit arayüzünden de girebilirsiniz.

## Test

```bash
python -m tests.smoke_test
```

Bu test **API anahtarı istemez.** Ontoloji motorunu ve dedektörü ağa çıkmadan
denetler: ontoloji yükleniyor mu, üniversite adları doğru varlığa düşüyor mu,
doğru/yanlış iddialar doğru durumu alıyor mu.

## Proje yapısı

```
app/
  main.py                    # Streamlit arayüzü (Demo + Nasıl Çalışıyor sekmeleri)
  llm_client.py              # OpenAI istemcisi, bağlamlı/bağlamsız çağrılar
  ontology_engine.py         # Turtle yükleme, SPARQL sorguları, varlık tespiti
  hallucination_detector.py  # İddiaları ontolojiye karşı doğrulama
ontology/
  universities.ttl           # Ontoloji (T-BOX + A-BOX)
tests/
  smoke_test.py              # Anahtar gerektirmeyen duman testi
rapor.md                     # Ders projesi raporu
run.ps1                      # PowerShell başlatıcı
requirements.txt
```

## Gereksinimler

Python 3.10+ ve bir OpenAI API anahtarı.
Paketler: `streamlit`, `rdflib`, `openai`, `python-dotenv`, `pyvis`, `networkx`.

## Sınırlar

- Ontoloji 21 üniversite ile sınırlı; dışında kalan her şey "doğrulanamadı" döner.
- Yalnızca üç özellik denetleniyor. Fakülte listesi ve resmi ad ontolojide var,
  ama dedektör bunları henüz karşılaştırmıyor.
- İddia çıkarımı modelin yapılandırılmış çıktısına dayanıyor; model beklenen
  biçimde cevap vermezse o iddia hiç denetlenmez.

## Kaynak

Biçimsel Diller ve Otomatlar dersi grup projesi, 2025–2026 Bahar.
Ayrıntılı anlatım için `rapor.md`.
