# GPT Ontoloji Demo - PowerShell başlatıcı
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    Write-Host "Sanal ortam oluşturuluyor..." -ForegroundColor Cyan
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host "Bagimliliklar kuruluyor..." -ForegroundColor Cyan
pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "`n⚠️  .env dosyası yok. .env.example dosyasını .env olarak kopyalayıp" -ForegroundColor Yellow
    Write-Host "    OPENAI_API_KEY satırına anahtarınızı yazın, sonra tekrar çalıştırın." -ForegroundColor Yellow
    Write-Host "    (Anahtarı arayüzden de girebilirsiniz; o durumda devam edin.)`n" -ForegroundColor Yellow
}

Write-Host "Streamlit başlatiliyor..." -ForegroundColor Green
streamlit run app/main.py
