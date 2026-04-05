<div align="center">

<img src="./assets/logo.svg" alt="TestGen AI Logo" width="400" />

**NLP Destekli, Hybrid Eşleştirme Mimarisine Sahip Akıllı Test Üretim Platformu**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![NLP](https://img.shields.io/badge/NLP-BERT%20%7C%20MiniLM-FF9900?style=flat&logo=huggingface&logoColor=white)](https://huggingface.co/)

*CSV tabanlı iş kurallarından test senaryosu üreten, JSON şablonları ve environment profillerini semantik olarak eşleştiren, senaryo zekası (Scenario Intelligence) platformu.*

[Canlı Demo](https://atakan-emre.github.io/TestGen-AI/) • [GitHub Reposu](https://github.com/Atakan-Emre/TestGen-AI) • [Lokal Kurulum](#-lokal-kurulum)

</div>

---

## 📌 İçindekiler

<details>
<summary>Menüyü Genişletmek İçin Tıklayın</summary>

1. [Ürün Özeti ve Çözülen Problemler](#-ürün-özeti-ve-ne-çözer)
2. [Mimari Genel Bakış](#-mimari-genel-bakış)
3. [Uçtan Uca Çalışma Akışı](#-uçtan-uca-çalışma-akışı)
4. [Temel Yetenekler](#-temel-yetenekler)
5. [NLP ve Hybrid Matching Katmanı](#-nlp-ve-hybrid-matching-katmanı)
6. [Lokal Kurulum ve Docker](#-lokal-kurulum)
7. [API Referansları ve Yapı](#-api-grupları-ve-klasör-yapısı)
8. [GitHub Pages Yayın Akışı](#-github-pages-demo-ve-yayın-akışı)
</details>

---

## 🎯 Ürün Özeti ve Ne Çözer?

Kurumsal ekiplerde iş kuralları (CSV/Excel), API payload şablonları (JSON) ve environment değerleri (Variables) genellikle kopuk yaşar. Test mühendisleri aynı doğrulamaları manuel kurmak zorunda kalır.

**TestGen AI**, bir "test case generator" olmanın ötesindedir. Sistem şu sorunları çözer:

*   **Senaryo Zekası:** CSV alan bilgisini otomatik senaryo ve constraint setine çevirir.
*   **Semantik Eşleştirme:** JSON alanlarını semantik, *type-aware* ve *domain-aware* mantıkla analiz eder. Benzer ama farklı isimli alanları bağlar.
*   **Kontrollü Üretim:** Negatif testleri alan tipine göre tutarlı üretir (`BSC`, `NGI`, `NGV`, `OPT`).
*   **İnsan Onayı (Human-in-the-loop):** Gözden geçirme gerektiren alanları `confidence` (güven) skoru ile işaretler ve **Binding Studio** üzerinden yönetir.

---

## 🏗️ Mimari Genel Bakış

Sistem, React tabanlı bir önyüz ve veri işleme/NLP süreçlerini yöneten FastAPI tabanlı bir arka yüzden oluşur.

```mermaid
flowchart LR
    U["👤 Kullanıcı"] --> FE["⚛️ React + Vite"]
    FE --> API["⚡ FastAPI Backend"]

    subgraph Inputs["📥 Girdi Katmanı"]
      CSV["CSV Dosyaları"]
      JSON["JSON Şablonları"]
      VAR["Variables"]
      BIND["Bindings"]
    end

    subgraph Intelligence["🧠 Intelligence Katmanı"]
      SCN["Scenario Intelligence"]
      NLP["Embedding + BERT NER"]
      DT["Domain Tuning"]
      BM["Binding Matcher"]
    end

    subgraph Generators["⚙️ Test Generator"]
      BSC["BSC (Pozitif)"]
      NGI["NGI (Tip/Semantik İhlali)"]
      NGV["NGV (Sınır/Geçersiz Değer)"]
      OPT["OPT (Opsiyonel Komb.)"]
    end

    Inputs --> API
    API <--> Intelligence
    Intelligence --> Generators
    Generators --> TOUT["📄 Test Case JSON Çıktıları"]
````

-----

## 🔄 Uçtan Uca Çalışma Akışı

```mermaid
sequenceDiagram
    participant User as Kullanıcı
    participant FE as Frontend
    participant API as FastAPI
    participant NLP as Scenario Intelligence
    participant GEN as Test Generator

    User->>FE: CSV, JSON, variables seçer
    FE->>API: Job başlatır (/scenarios/generate)
    API->>NLP: CSV'den field profile çıkar
    NLP->>NLP: Embedding + Domain Tuning + NER
    NLP-->>API: Scenario bundle + .meta.json döner
    
    FE->>API: Auto-resolve talep eder
    API-->>FE: Confidence skorlu eşleşmeleri önerir

    alt Auto Mode
        FE->>API: Inline binding payload gönder
    else Review Mode
        User->>FE: Binding Studio'da onayla/düzelt
        FE->>API: Kayıtlı binding ile ilerle
    end

    API->>GEN: Seçili tiplerde (BSC, NGI vb.) test üret
    GEN-->>API: Test case ciktilari
    API-->>FE: Test listesi ve özetleri sun
```

-----

## 🧠 NLP ve Hybrid Matching Katmanı

Sistem deterministik sonuçlar için kural tabanlı yapıyı, esneklik için LLM/NLP modellerini harmanlayan **Hybrid** bir yaklaşıma sahiptir.

| Bileşen | Teknoloji | Kullanım Amacı |
| :--- | :--- | :--- |
| **Embedding Modeli** | `paraphrase-multilingual-MiniLM` | Alan adı, açıklama ve tip prototipleri arası anlamsal yakınlık |
| **NER Pipeline** | `bert-large-cased-finetuned` | Kaynak metinlerden ve alan adlarından entity zenginleştirme |
| **Domain Tuning** | Custom Rules | Finans/evrak alan adlarında hızlı id/date/enum kararları |
| **Binding Scoring** | Algorithm | Token örtüşmesi, tip uyumluluğu ve bağlam skoru hesaplama |

> **💡 Neden Hybrid?** Yalnızca kural tabanlı sistemler esnek değildir, yalnızca LLM tabanlı sistemler ise halüsinasyon görebilir. TestGen AI; semantik NLP modelleriyle esneklik sağlarken, kural tabanlı motorla deterministik test cıktılarını garanti eder.

-----

## 🐳 Lokal Kurulum

Geliştirme ortamını ayağa kaldırmak için **Docker Desktop** (veya Docker Engine + Compose) gereklidir.

```bash
# Repoyu klonlayın
git clone [https://github.com/Atakan-Emre/TestGen-AI.git](https://github.com/Atakan-Emre/TestGen-AI.git)
cd TestGen-AI

# Ortam değişkenlerini ayarlayın
cp .env.example .env

# Container'ları başlatın
docker compose up -d --build
```

**🌐 Erişim Adresleri:**

  * Frontend: `http://localhost:5173`
  * Backend: `http://localhost:8000`
  * Sağlık Kontrolü: `http://localhost:8000/health`

*(Servisleri durdurmak için: `docker compose down`)*

-----

## 📂 API Grupları ve Klasör Yapısı

<details>
<summary><b>Ana API Uç Noktalarını Göster</b></summary>

| Endpoint Grubu | Açıklama |
| :--- | :--- |
| `/api/csv` & `/api/json` | Girdi dosyalarının yüklenmesi ve yönetimi |
| `/api/scenarios` | Senaryo üretimi ve job takibi |
| `/api/bindings` | Otomatik eşleştirme, güven skorları, aksiyonlar (`bind`, `ignore` vb.) |
| `/api/tests/*` | `bsc`, `ngi`, `ngv`, `opt` üretim uç noktaları |
| `/api/variables` | Ortam profillerinin (txt, json, yaml) CRUD işlemleri |

</details>

<details>
<summary><b>Klasör Yapısını Göster</b></summary>

```text
.
├── backend
│   ├── app (routes, services, models)
│   ├── src (generators, analysis/NLP)
│   ├── tests
│   └── Dockerfile
├── frontend
│   ├── src (components, hooks, pages)
│   └── Dockerfile / Dockerfile.prod
├── data
│   ├── input (Csv, Json, Variables)
│   └── output (Test Scenarios, Test Cases)
├── .github/workflows (CI/CD)
├── docker-compose.yml
└── docker-compose.prod.yml
````


-----

## 🚀 GitHub Pages Demo ve Yayın Akışı

Frontend demosu GitHub Actions üzerinden otomatik olarak GitHub Pages'e deploy edilmektedir. [frontend-pages.yml](/Users/atakanemre/Downloads/test_project-main/.github/workflows/frontend-pages.yml) dosyası `main` veya `master` branch'ine yapılan push sonrası tetiklenir. İstenirse Actions ekranından manuel olarak da çalıştırılabilir.

GitHub Pages yalnızca statik frontend sunar; FastAPI backend'i barındırmaz. Bu nedenle Pages üzerinde iki çalışma modu vardır:

  * `VITE_API_URL` tanımlıysa frontend gerçek backend'e bağlanır.
  * `VITE_API_URL` tanımlı değilse uygulama otomatik olarak **demo moduna** geçer ve repo içindeki örnek CSV, JSON, variables, senaryo ve test çıktıları ile çalışır.

**Gereksinimler:**

  * GitHub repo ayarlarından Pages kaynağının **GitHub Actions** seçilmesi.
  * Canlı API akışı isteniyorsa `VITE_API_URL` variable'ının eklenmiş olması.
  * Repo daha önce Pages için hiç açılmadıysa ya bir kez `Settings > Pages > Source: GitHub Actions` seçilmesi ya da `PAGES_ADMIN_TOKEN` secret'ının eklenmiş olması.

-----


*Bu proje, senaryo zekası ve şema bağlama işlemlerini tek platformda toplayan, denetlenebilir bir mühendislik altyapısıdır.*


---
**Keywords / Anahtar Kelimeler:** `Test Automation`, `Test Case Generator`, `NLP`, `Natural Language Processing`, `Software Testing`, `QA Automation`, `FastAPI`, `React`, `JSON Schema Matching`, `Hybrid NLP`, `Yapay Zeka Destekli Test`, `Otomatik Test Senaryosu Üretimi`, `API Testing`.
