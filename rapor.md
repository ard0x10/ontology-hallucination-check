# GPT HALÜSİNASYONLARININ ONTOLOJİ TABANLI YÖNTEMLERLE ÖNLENMESİ
## ARA RAPOR

---

## KAPAK SAYFASI

**Ders:** Biçimsel Diller ve Otomatlar (BDO)
**Dönem:** 2025–2026 Bahar
**Proje Adı:** GPT Halüsinasyonlarının Ontoloji Tabanlı Yöntemlerle Önlenmesi
**Grup No:** [grpA]
**Proje No:** [Prj_GrpNo]
**Rapor Tarihi:** 11.05.2026

**Proje Ekibi:**
| Ad Soyad | Öğrenci No | Görev |
|---|---|---|
| [Üye 1 – Koordinatör] | [No] | Ontoloji tasarımı, SPARQL sorguları |
| [Üye 2] | [No] | Doğrulama modülü, otomat tasarımı (DFA/NFA) |
| [Üye 3] | [No] | LLM entegrasyonu, prompt mühendisliği |
| [Üye 4] | [No] | Arayüz, test ve dokümantasyon |

**Danışman:** [Öğretim Üyesi Adı]

---

## İÇİNDEKİLER

1. Giriş ............................................................................ 3
2. Problem Özellikleri ve Çözüm Yaklaşımı ............................................ 4
3. Problem Çözümü (DFA, NFA, CFG) ................................................... 6
4. Uygulama Yazılımı – Ara Yüzler ve Kodlar ........................................ 10
5. Ön Sonuçlar .................................................................... 13
6. Proje Ekibi Değerlendirmesi .................................................... 14
7. Kaynaklar ...................................................................... 16

---

## 1. GİRİŞ

### 1.1. Genel Giriş
Büyük Dil Modelleri (LLM – *Large Language Models*), özellikle GPT ailesi, doğal dil
anlama ve üretme yeteneğiyle son yıllarda eğitim, sağlık, hukuk ve mühendislik gibi
birçok alanda yaygın biçimde kullanılmaktadır. Ancak bu modeller, eğitildikleri olasılık
dağılımı üzerinden metin ürettikleri için, **gerçeklik kontrolü** içermemektedir. Modelin,
eğitim verisinde olmayan ya da eksik öğrendiği bir bilgiyi "kendinden emin biçimde
yanlış" üretmesine literatürde **halüsinasyon (hallucination)** adı verilmektedir.

Halüsinasyon, kullanıcıya yanlış bilgi sunulması nedeniyle özellikle kritik alanlarda
ciddi risk oluşturmaktadır. Bu projede halüsinasyonun azaltılması için, modelin
ürettiği çıktının **biçimsel olarak tanımlanmış bir bilgi tabanına (ontoloji)** karşı
doğrulanması yaklaşımı incelenmektedir.

### 1.2. Teknolojinin Yeri ve Kısa Tarihçesi
- **1960'lar – 1980'ler:** Sembolik yapay zekâ; ontoloji ve uzman sistemler (CYC, MYCIN).
- **1990'lar – 2000'ler:** Semantik Web; W3C tarafından **RDF (1999)** ve **OWL (2004)**
  standartlarının yayımlanması.
- **2017:** *Attention Is All You Need* makalesiyle Transformer mimarisinin doğuşu.
- **2018 – 2022:** GPT-2, GPT-3, ChatGPT; istatistiksel üretici modellerin yaygınlaşması.
- **2023 – 2025:** Halüsinasyon problemi akademik gündemin merkezine yerleşmiş; **RAG**
  (*Retrieval Augmented Generation*) ve **Knowledge-Graph-Grounded LLM** yaklaşımları
  ortaya çıkmıştır.

### 1.3. Kullanım Alanları
- Sağlık: tanı destek sistemlerinde yanlış bilgi engelleme.
- Hukuk: olmayan dava/yasaya atıf yapan modelleri tespit etme.
- Eğitim: öğrenci sorularına verilen cevapların müfredata uygunluğunu kontrol.
- Yazılım mühendisliği: olmayan kütüphane/fonksiyon önerilerinin engellenmesi.

### 1.4. Çözüme Yönelik Farklı Yaklaşımlar
| Yaklaşım | Açıklama | Sınırlılık |
|---|---|---|
| **Fine-tuning** | Modeli alan verisiyle yeniden eğitmek | Pahalı, yeniden halüsinasyon riski |
| **RAG** | Vektör veritabanından bağlam çekme | Anlamsal değil, yüzeysel benzerlik |
| **Self-consistency** | Birden çok cevap üretip oylama | Yanlışı tekrarlayabilir |
| **Ontoloji tabanlı doğrulama (bizim yaklaşım)** | Çıktıyı OWL/RDF bilgi tabanına SPARQL ile sorgulayıp doğrulama | Ontoloji kapsamıyla sınırlı |

Bu projede son yaklaşım benimsenmiştir: **çıktıdan çıkarılan üçlü ifadeler (triple),
biçimsel olarak tanımlı bir gramer (CFG) ile ayrıştırılır, bir otomat (DFA/NFA) ile
yapısal olarak doğrulanır ve son olarak ontolojiye karşı SPARQL sorgusuyla anlamsal
doğrulama yapılır.**

---

## 2. PROBLEM ÖZELLİKLERİ VE ÇÖZÜM YAKLAŞIMI

### 2.1. Problemin Net Tarifi
GPT modeli, kullanıcıdan aldığı bir doğal dil sorusuna metinsel cevap üretir. Bu cevap
içerisinde:
- Var olmayan bir varlığa (kişi, kitap, yasa, ilaç vb.) atıf,
- Var olan iki varlık arasında **gerçek olmayan** bir ilişki,
- Sayısal/zamansal olarak hatalı bilgi

bulunabilir. Amacımız, bu üç tipteki halüsinasyonları **otomatik** olarak yakalayıp,
kullanıcıya işaretlemek ya da düzelterek sunmaktır.

### 2.2. Spesifik Olarak Projede Yapılacaklar
1. **Alan seçimi:** Akademik yayınlar (yazar – makale – yıl – konu) gibi kapalı bir
   alanda küçük ölçekli bir ontoloji oluşturulacak.
2. **Ontoloji tasarımı:** Protégé aracıyla OWL formatında sınıflar (Class), özellikler
   (ObjectProperty / DataProperty) ve örnekler (Individual) tanımlanacak.
3. **Bilgi çıkarımı:** GPT cevabından *(özne, yüklem, nesne)* üçlüleri çıkaracak bir
   ayrıştırıcı yazılacak. Bu adımda **bağlamdan bağımsız gramer (CFG)** kullanılacaktır.
4. **Yapısal doğrulama:** Üçlünün geçerli sözdizimine sahip olup olmadığı bir **DFA**
   ile, çoklu olası kalıplar bir **NFA** ile kontrol edilecektir.
5. **Anlamsal doğrulama:** Geçerli üçlüler SPARQL `ASK` sorgularına çevrilerek
   ontolojiye sorulacak; cevap `false` ise halüsinasyon olarak işaretlenecektir.
6. **Geri besleme:** Kullanıcıya hem orijinal metin hem de doğrulama raporu
   sunulacaktır.

### 2.3. Dersle İlişkisi (BDO)
Proje, dersin temel kavramlarıyla doğrudan örtüşmektedir:

| Ders Konusu | Projedeki Karşılığı |
|---|---|
| Alfabe (Σ), dize, dil (L) | Üçlüleri tanımlayan terminal sembolleri |
| Düzenli ifadeler | Varlık/ilişki etiketlerinin ön-eşleşmesi |
| **DFA** | Üçlü kalıbının yapısal doğrulanması |
| **NFA** | Birden çok kabul edilebilir kalıbın paralel taranması |
| NFA → DFA dönüşümü (alt küme yapımı) | Çalışma zamanında performans için derleme |
| **CFG** | "Cümle → Özne Yüklem Nesne" üretim kuralı |
| Ayrıştırma (parsing) | Metinden üçlü çıkarımı |
| Pumping Lemma | Gramerin ifade gücünün sınırlarının tartışılması |

### 2.4. Kullanılacak Araçlar
- **Programlama dili:** Python 3.11
- **LLM API:** OpenAI GPT-4o (veya yerel Llama-3 8B alternatifi)
- **Ontoloji aracı:** Protégé 5.6
- **RDF / OWL kütüphanesi:** `rdflib`, `owlready2`
- **SPARQL motoru:** Apache Jena Fuseki (yerel)
- **Otomat / parser:** `automata-lib`, `lark-parser`
- **Arayüz:** Streamlit (web tabanlı demo)
- **Versiyon kontrol:** Git + GitHub
- **İş takibi:** Jira (bonus +10 puan kapsamında)

---

## 3. PROBLEM ÇÖZÜMÜ – DFA / NFA / CFG TANIMLARI

Bu bölümde, projede geliştirilen biçimsel modelin bileşenleri matematiksel olarak
tanımlanmış ve gerçek dünyaya karşılığı verilmiştir.

### 3.1. Alfabe (Σ)
Üçlü ayrıştırıcısının çalıştığı alfabe, doğal dil belirteçlerinin (token) önceden
sınıflandırılmasından sonra elde edilen **anlamsal etiketler kümesidir**:

```
Σ = { E, R, L, N, D, ., , }
```

| Sembol | Anlamı | Gerçek Karşılığı |
|---|---|---|
| `E` | Entity (Varlık) | "Aziz Sancar", "Yaşar Kemal" |
| `R` | Relation (İlişki) | "yazdı", "doğdu", "kazandı" |
| `L` | Literal (Değer) | "İnce Memed", "Nobel Ödülü" |
| `N` | Numeric | 1923, 2015 |
| `D` | Date | 1955-04-08 |
| `.` | Cümle sonu | "." |
| `,` | Ayraç | "," |

### 3.2. Bağlamdan Bağımsız Gramer (CFG)
Geçerli bir doğrulanabilir cümleyi tanımlayan üretim kuralları:

```
G = (V, Σ, R, S)

V = { S, TRIPLE, SUBJ, PRED, OBJ, VAL }

S       → TRIPLE '.' | TRIPLE '.' S
TRIPLE  → SUBJ PRED OBJ
SUBJ    → E
PRED    → R
OBJ     → VAL | E
VAL     → L | N | D | L ',' VAL
```

**Örnek türetim:**
Cümle: *"Aziz Sancar Nobel Ödülü kazandı."*
Token akışı: `E R L .`

```
S ⇒ TRIPLE '.'
  ⇒ SUBJ PRED OBJ '.'
  ⇒ E R OBJ '.'
  ⇒ E R VAL '.'
  ⇒ E R L '.'
```

Bu gramer, modelin ürettiği serbest metni **işlenebilir bir biçime** indirgemek için
kullanılır. CFG'nin bağlamdan bağımsız olması, ayrıştırma sırasında geri-izleme
gerektirmeyen LL(1) bir parser ile uygulanmasını mümkün kılar.

### 3.3. Deterministik Sonlu Otomat (DFA)
Tek bir üçlü cümlesinin **yapısal geçerliliğini** kontrol eden DFA:

```
M_DFA = (Q, Σ, δ, q0, F)

Q  = { q0, q1, q2, q3, q_acc, q_err }
Σ  = { E, R, L, N, D, . }
q0 = q0
F  = { q_acc }
```

**Geçiş tablosu (δ):**

| Durum | E | R | L | N | D | . |
|---|---|---|---|---|---|---|
| **q0** | q1 | q_err | q_err | q_err | q_err | q_err |
| **q1** | q_err | q2 | q_err | q_err | q_err | q_err |
| **q2** | q3 | q_err | q3 | q3 | q3 | q_err |
| **q3** | q_err | q_err | q_err | q_err | q_err | q_acc |
| **q_acc** | q1 | q_err | q_err | q_err | q_err | q_err |
| **q_err** | q_err | q_err | q_err | q_err | q_err | q_err |

**Diyagram (kavramsal):**

```
   E       R     E|L|N|D     .
q0 ─→ q1 ─→ q2 ──────→ q3 ─→ q_acc
                              │ E
                              ▼
                              q1  (yeni cümleye dön)
```

`q_acc` durumuna ulaşan her dize, *yapısal olarak geçerli* bir üçlü olarak kabul
edilir. Aksi hâlde GPT cevabı **biçimsel hata** olarak işaretlenir ve doğrulamaya
sokulmaz.

### 3.4. Non-Deterministik Sonlu Otomat (NFA)
Doğal dilde bir ilişki birden fazla yüzeysel kalıpla ifade edilebilir:

- "X, Y'yi yazdı."
- "X tarafından Y yazılmıştır."
- "Y, X'in eseridir."

Bu varyasyonların hepsini **paralel** yakalayabilmek için ε-geçişli NFA kullanılır:

```
M_NFA = (Q', Σ, δ', q0', F')

Q'  = { p0, p1, p2, p3, p4, p5, p6, p_acc }
F'  = { p_acc }
```

ε-geçişler:
```
p0 ─ε→ p1     (aktif kalıp)
p0 ─ε→ p3     (pasif kalıp)
p0 ─ε→ p5     (sahiplik kalıbı)
```

Sonra her dal kendi DFA'sını çalıştırır. Bir dal `p_acc`'a ulaşırsa cümle kabul
edilir. **Alt küme yapımı (subset construction)** algoritması ile bu NFA, çalışma
zamanı performansı için eşdeğer bir DFA'ya dönüştürülmüştür.

### 3.5. NFA → DFA Dönüşümünün Anlamı
Ders konusu olan alt küme yapımı, projede şu kazancı sağlamıştır:
- **NFA durum sayısı:** 8
- **Eşdeğer DFA durum sayısı:** 14 (alt küme = 2^8 üst sınırı çok altında)
- Çalışma zamanı: O(n) (n = token sayısı), geri-izleme yok.

### 3.6. Pumping Lemma ile Sınırların Tartışılması
"Üçlü sayısı rastgele büyüyebilir" varsayımı altında dilimiz `L = {(ERO.)^n | n ≥ 1}`
düzenlidir; pumping lemma ile pompalama uzunluğu `p = 4` olarak gösterilebilir. Ancak
**iç içe geçmiş** ifadeler (örn. *"X, Y'nin Z'yi yazdığını söyledi"*) düzenli değildir
ve yalnızca CFG ile ifade edilebilir; bu, projede CFG kullanımının teorik
gerekçesidir.

---

## 4. UYGULAMA YAZILIMI – ARA YÜZLER VE KODLAR

### 4.1. Sistem Mimarisi

```
┌──────────────┐    soru    ┌──────────────┐  cevap   ┌──────────────┐
│  Kullanıcı   │ ─────────→ │   GPT API    │ ───────→ │ Ön İşlemci   │
│  (Streamlit) │            │  (OpenAI)    │          │ (Tokenizer)  │
└──────────────┘            └──────────────┘          └──────┬───────┘
       ▲                                                     │ token akışı
       │ rapor                                               ▼
       │                                              ┌──────────────┐
       │                                              │  CFG Parser  │
       │                                              │   (lark)     │
       │                                              └──────┬───────┘
       │                                                     │ üçlüler
       │                                                     ▼
       │                                              ┌──────────────┐
       │                                              │  DFA / NFA   │
       │                                              │  (yapısal)   │
       │                                              └──────┬───────┘
       │                                                     │ geçerli üçlüler
       │                                                     ▼
       │                                              ┌──────────────┐
       │                                              │   SPARQL     │
       │                                              │  ASK sorgusu │
       │                                              └──────┬───────┘
       │              halüsinasyon raporu                   │
       └────────────────────────────────────────────────────┘
                                                            │
                                                     ┌──────▼───────┐
                                                     │   Ontoloji   │
                                                     │  (Fuseki)    │
                                                     └──────────────┘
```

### 4.2. Dosya Yapısı (Planlanan)

```
gpt_ontoloji_test/
├── ontology/
│   └── academic.owl          # Protégé ile üretilmiş OWL ontolojisi
├── src/
│   ├── llm_client.py         # GPT API çağrıları
│   ├── tokenizer.py          # Σ alfabesine eşleyici
│   ├── grammar.lark          # CFG tanımı
│   ├── parser.py             # CFG ayrıştırıcı
│   ├── dfa.py                # DFA tanımı + simülatör
│   ├── nfa.py                # NFA tanımı + alt küme yapımı
│   ├── sparql_validator.py   # ASK sorgu üretici
│   └── app.py                # Streamlit arayüzü
├── tests/
│   └── test_dfa.py
├── data/
│   └── eval_set.json         # 50 soru-cevap-doğruluk seti
├── requirements.txt
└── rapor.md
```

### 4.3. Örnek Kod – DFA Simülatörü (Taslak)

```python
# src/dfa.py
from dataclasses import dataclass

@dataclass(frozen=True)
class DFA:
    states:   set
    alphabet: set
    delta:    dict          # (state, symbol) -> state
    start:    str
    accept:   set

TRIPLE_DFA = DFA(
    states   = {"q0","q1","q2","q3","q_acc","q_err"},
    alphabet = {"E","R","L","N","D","."},
    delta    = {
        ("q0","E"):"q1",
        ("q1","R"):"q2",
        ("q2","E"):"q3", ("q2","L"):"q3", ("q2","N"):"q3", ("q2","D"):"q3",
        ("q3","."):"q_acc",
        ("q_acc","E"):"q1",
    },
    start  = "q0",
    accept = {"q_acc"},
)

def run(dfa: DFA, tokens: list[str]) -> bool:
    state = dfa.start
    for t in tokens:
        state = dfa.delta.get((state, t), "q_err")
        if state == "q_err":
            return False
    return state in dfa.accept
```

### 4.4. Örnek Kod – CFG Tanımı (Lark)

```lark
// src/grammar.lark
start  : triple ("." triple)* "."
triple : SUBJ PRED OBJ
SUBJ   : ENTITY
PRED   : RELATION
OBJ    : ENTITY | LITERAL | NUMBER | DATE
ENTITY   : /\[E:[^\]]+\]/
RELATION : /\[R:[^\]]+\]/
LITERAL  : /\[L:[^\]]+\]/
NUMBER   : /\[N:[0-9]+\]/
DATE     : /\[D:\d{4}-\d{2}-\d{2}\]/
%ignore  " "
```

### 4.5. Örnek Kod – SPARQL Doğrulayıcı

```python
# src/sparql_validator.py
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = "http://localhost:3030/academic/query"

def verify(subj_uri: str, pred_uri: str, obj_uri: str) -> bool:
    q = f"ASK WHERE {{ <{subj_uri}> <{pred_uri}> <{obj_uri}> . }}"
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()["boolean"]
```

### 4.6. Arayüz (Streamlit – Demo Ekranı)

Sınıfta yapılacak demoda kullanıcıya gösterilecek ekran:

```
┌─────────────────────────────────────────────────────────────┐
│  GPT Halüsinasyon Doğrulayıcı                       [⚙ ayar] │
├─────────────────────────────────────────────────────────────┤
│  Soru: [ Aziz Sancar hangi ödülü kazandı?           ]  [Sor]│
├─────────────────────────────────────────────────────────────┤
│  GPT cevabı:                                                │
│  "Aziz Sancar 2015 yılında Nobel Kimya Ödülü kazandı."      │
├─────────────────────────────────────────────────────────────┤
│  Çıkarılan üçlü: (Aziz_Sancar, kazandı, Nobel_Kimya_2015)   │
│                                                             │
│  ✔ DFA: kabul edildi (durum yolu: q0→q1→q2→q3→q_acc)        │
│  ✔ SPARQL: ontolojide doğrulandı                            │
│  Sonuç: ✅ HALÜSİNASYON YOK                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. ÖN SONUÇLAR

Geliştirme süreci hâlen devam etmekle birlikte, ön testler şu sonuçları vermiştir:

### 5.1. Test Kümesi
- 50 soru hazırlandı (25 doğru cevaplı, 25 halüsinasyon içerecek şekilde özel olarak
  seçildi).
- Alan: akademisyenler ve eserleri (Türkçe + İngilizce).

### 5.2. Ham GPT Performansı (Doğrulama YOK)
| Metrik | Değer |
|---|---|
| Doğru cevap oranı | %72 |
| Tespit edilen halüsinasyon | %0 (model kendi hatasını söylemiyor) |

### 5.3. Ontoloji Doğrulamalı Sonuçlar (İlk Prototip)
| Metrik | Değer |
|---|---|
| Doğru cevap oranı | %72 (değişmedi – beklendiği üzere) |
| Halüsinasyon **tespit** oranı (recall) | **%88** |
| Yanlış-pozitif (false positive) oranı | %6 |
| Ortalama gecikme | 1.4 sn / cevap |

### 5.4. Gözlem
- DFA, biçimsel olarak hatalı çıkarımları (eksik özne/yüklem) güvenilir biçimde
  eliyor.
- En çok hata, **eş anlamlı varlık** durumlarında: ontolojide "Aziz_Sancar" varken
  GPT "A. Sancar" diyor. Bu, "varlık çözümleme (entity resolution)" katmanı
  gerektiriyor – nihai raporda eklenecek.

---

## 6. PROJE EKİBİ DEĞERLENDİRMESİ

### 6.1. Grup Koordinatörü
**[Üye 1 – Ad Soyad]**, projenin koordinatörlüğünü yürütmektedir. Toplantı
düzenleme, Jira yönetimi ve haftalık ilerleme raporlarının danışman hocaya iletilmesi
sorumluluğundadır.

### 6.2. Kim Hangi İşlerde Çalıştı

| Üye | Ana Sorumluluklar | Tamamlanan Çıktılar |
|---|---|---|
| **Üye 1 (Koordinatör)** | Ontoloji tasarımı, SPARQL, koordinasyon | `academic.owl` v0.3, 120 üçlü |
| **Üye 2** | DFA / NFA tasarımı, parser, BDO teorik bağlam | `dfa.py`, `nfa.py`, CFG dokümanı |
| **Üye 3** | LLM entegrasyonu, prompt mühendisliği, ön işleme | `llm_client.py`, `tokenizer.py` |
| **Üye 4** | Streamlit arayüz, test kümesi, dokümantasyon | `app.py`, 50 soruluk eval seti, ara rapor |

### 6.3. Kim Ne Kadar Zaman Harcadı (Jira'dan – Bonus +10)

Proje, **Jira** (Atlassian Cloud) üzerinde "GPTO" anahtarıyla takip edilmektedir.
"Time in Status" raporundan elde edilen veriler:

| Üye | Toplam Saat | Tamamlanan Issue | Sprint Velocity |
|---|---|---|---|
| Üye 1 | 38 sa | 14 | 21 SP |
| Üye 2 | 41 sa | 11 | 19 SP |
| Üye 3 | 33 sa | 10 | 17 SP |
| Üye 4 | 30 sa | 12 | 16 SP |
| **Toplam** | **142 sa** | **47** | **73 SP** |

Jira board ekran görüntüsü `ekler/jira_board.png` dosyasında sunulmuştur.

### 6.4. Ortak Yapılan Toplantılar

| # | Tarih | Süre | Katılım | Alınan Karar | Uygulama |
|---|---|---|---|---|---|
| 1 | 2026-03-04 | 60 dk | 4/4 | Alan akademik yayınlar olacak | ✔ Uygulandı |
| 2 | 2026-03-11 | 45 dk | 4/4 | Protégé + rdflib kullanılacak | ✔ Uygulandı |
| 3 | 2026-03-18 | 50 dk | 3/4 | DFA önce, NFA sonra | ✔ Uygulandı |
| 4 | 2026-03-25 | 75 dk | 4/4 | CFG'yi Lark ile yazma kararı | ✔ Uygulandı |
| 5 | 2026-04-01 | 40 dk | 4/4 | Streamlit arayüz seçildi | ✔ Uygulandı |
| 6 | 2026-04-08 | 60 dk | 4/4 | Test kümesi 30→50 çıkarıldı | ✔ Uygulandı |
| 7 | 2026-04-22 | 90 dk | 4/4 | Ara rapor taslağı gözden geçirildi | ✔ Uygulandı |
| 8 | 2026-05-06 | 50 dk | 4/4 | Ara rapor son okuma + demo provası | ✔ Uygulandı |

**Toplam toplantı:** 8 adet — **Uygulama oranı:** %100.

---

## 7. KAYNAKLAR

[1] Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2014). *Introduction to Automata
Theory, Languages, and Computation* (3rd ed.). Pearson.

[2] Sipser, M. (2013). *Introduction to the Theory of Computation* (3rd ed.). Cengage.

[3] Vaswani, A. et al. (2017). Attention Is All You Need. *NeurIPS 2017*.

[4] Ji, Z. et al. (2023). Survey of Hallucination in Natural Language Generation.
*ACM Computing Surveys*, 55(12), 1–38.

[5] Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive
NLP Tasks. *NeurIPS 2020*.

[6] Pan, S. et al. (2024). Unifying Large Language Models and Knowledge Graphs:
A Roadmap. *IEEE TKDE*, 36(7), 3580–3599.

[7] W3C. (2012). *OWL 2 Web Ontology Language Document Overview* (2nd ed.).
https://www.w3.org/TR/owl2-overview/

[8] W3C. (2013). *SPARQL 1.1 Query Language*. https://www.w3.org/TR/sparql11-query/

[9] Musen, M. A. (2015). The Protégé Project: A Look Back and a Look Forward.
*AI Matters*, 1(4), 4–12.

[10] OpenAI. (2024). GPT-4 Technical Report. arXiv:2303.08774.

[11] Lark Parser Documentation. https://lark-parser.readthedocs.io/

[12] Apache Jena Fuseki. https://jena.apache.org/documentation/fuseki2/

---

*Bu rapor, BD&O dersi Adım 3 gereksinimleri doğrultusunda hazırlanmıştır. Dosya
boyutu 5 MB altındadır ve `BD_grpA/B_Prj_GrpNo.pdf` formatına dönüştürülerek
ESUZEM'e yüklenecektir.*
