# GPT Ontoloji Test

> ⚠️ **ÖNEMLİ:** Bu depoya `.env` dosyası **yüklenmemiştir**. API anahtarınız gizli kalır.
> Projeyi klonladıktan sonra kendi `.env` dosyanızı oluşturup `OPENAI_API_KEY` değerini kendiniz girmelisiniz.
> `.env` dosyası `.gitignore` içinde tanımlıdır ve asla commit edilmez.

GPT halüsinasyonlarının ontoloji tabanlı yöntemlerle önlenmesi üzerine bir Streamlit demosu. Türkiye üniversiteleri hakkındaki LLM yanıtlarını RDF/OWL ontolojisiyle karşılaştırarak doğrular.

## Kurulum

1. Depoyu klonlayın:
   ```bash
   git clone <repo-url>
   cd gpt_ontoloji_test
   ```

2. Proje kökünde bir `.env` dosyası oluşturun:
   ```
   OPENAI_API_KEY=sk-...
   ```

3. Uygulamayı başlatın (Windows / PowerShell):
   ```powershell
   .\run.ps1
   ```

   Bu komut sanal ortamı kurar, bağımlılıkları yükler ve Streamlit'i başlatır.

## Manuel Çalıştırma

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
streamlit run app/main.py
```

> API anahtarınızı `.env` dosyasına yazmak yerine doğrudan Streamlit arayüzünden de girebilirsiniz.

## Proje Yapısı

```
app/
  main.py                  # Streamlit arayüzü
  llm_client.py            # OpenAI istemcisi
  ontology_engine.py       # RDF/OWL ontoloji motoru
  hallucination_detector.py# Halüsinasyon tespiti
ontology/
  universities.ttl         # Üniversite ontolojisi (Turtle)
tests/
  smoke_test.py
requirements.txt
run.ps1
```

## Gereksinimler

- Python 3.10+
- OpenAI API anahtarı
- `requirements.txt` içindeki paketler: streamlit, rdflib, openai, python-dotenv, pyvis, networkx
