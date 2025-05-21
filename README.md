# CSE - Insights and Query App

This project ingests company PDFs (annual & quarterly reports), converts them to clean text, builds a Chroma vector index with OpenAI embeddings, and exposes a FastAPI chat endpoint powered by LangChain.
A React dashboard (Vite + Tailwind) lets analysts query the knowledge-base and visualise cited passages. All services can run locally with Python or fully containerised with Docker Compose.

## 1. Repository Layout

```plaintext
FINANCIAL_QUERY_APP/
├── .env
├── .gitignore
├── docker-compose.yml
├── README.md
│
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── index/
│
├── logs/
│
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   │── prompts/
│   │    ├── system_prompt.j2
│   ├── scripts/
│   │   ├── build_index.py
│   │   ├── merge_jsons.py
│   │   └── scrape_reports.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── utils.py
│   │   ├── extract_interim_financials.py
│   │   └── prompts/
│   │       └── financial_extraction.j2
│   └── tests/
│       ├── __init__.py
│       ├── test_postvalidate.py
│       └── test_snippet.py
│
├── frontend/
│   └── financial-dashboard/
│       ├── Dockerfile
│       ├── nginx/
│       │   └── default.conf
│       ├── public/
│       │   ├── favicon.ico
│       │   ├── index.html
│       │   ├── manifest.json
│       │   └── data/
│       ├── src/
│       │   ├── components/
│       │   │   ├── ChartCard.jsx
│       │   │   ├── ChartCard.css
│       │   │   ├── ChatModal.jsx
│       │   │   ├── ChatModal.css
│       │   │   ├── ChatPage.jsx
│       │   │   ├── ChatPage.css
│       │   │   ├── CompanySelector.jsx
│       │   │   ├── CompanySelector.css
│       │   │   ├── ComparisonChart.jsx
│       │   │   ├── Dashboard.jsx
│       │   │   ├── Dashboard.css
│       │   │   ├── DateRangePicker.jsx
│       │   │   ├── DateRangePicker.css
│       │   │   ├── EntitySelector.jsx
│       │   │   ├── EntitySelector.css
│       │   │   ├── ExpenseBarChart.jsx
│       │   │   ├── GrossMarginChart.jsx
│       │   │   ├── InfoCard.jsx
│       │   │   ├── InfoCard.css
│       │   │   ├── MarginHeatmap.jsx
│       │   │   ├── MarginHeatmap.css
│       │   │   ├── MarginTrendChart.jsx
│       │   │   ├── MetricCard.jsx
│       │   │   ├── MetricCard.css
│       │   │   ├── NavBar.jsx
│       │   │   ├── NavBar.css
│       │   │   ├── NetMarginChart.jsx
│       │   │   ├── PnLChart.jsx
│       │   │   ├── PnLChart.css
│       │   │   ├── QoQGrowthChart.jsx
│       │   │   ├── RevenuePieChart.jsx
│       │   │   ├── SharePieChart.jsx
│       │   │   ├── TimeSeriesChart.jsx
│       │   │   └── TTMNetIncomeChart.jsx
│       │   ├── services/
│       │   │   ├── chatApi.js
│       │   │   └── financialApi.js
│       │   ├── App.jsx
│       │   ├── App.css
│       │   ├── index.js
│       │   ├── index.css
│       │   ├── logo.svg
│       │   ├── setupProxy.js
├       ├   ├── setupTests.js
│       │   ├── reportWebVitals.js
│       │   └── theme.css
│       ├── package.json
│       ├── package-lock.json
│       
│ 
├── logs/

```


## 2. Local Setup

### 2.1 Clone & create venv

git clone https://github.com/Thivakaran12/Financial_Query_App
cd financial_query_app
python -m venv venv             # built-in venv module :contentReference[oaicite:1]{index=1}
source venv/bin/activate        # PowerShell: .\venv\Scripts\Activate.ps1

### 2.2 Install backend dependencies

pip install -r backend/requirements.txt

### 2.3 Environment variables
OPENAI_EMBEDDING_KEY = 
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_VERSION=2024-02-15-preview
INDEX_DIR=backend/index
GENERATE_SOURCEMAP=false
REACT_APP_API_URL=http://localhost:8000


### 2.4 Build / refresh the vector index

python backend/scripts/build_index.py


### 2.5 Start the server
uvicorn backend.app:app --reload --port 8000    # Uvicorn 0.29 :contentReference[oaicite:5]{index=5}

### 2.6 Run the React dashboard
cd frontend/financial-dashboard
npm install
npm start       # serves on http://localhost:3000 (CRA default) :contentReference[oaicite:6]{index=6}



## 3. Running Everything with Docker Compose
docker compose up --build -d            

## 4. Configuration Reference (.env)
| Variable                   | Purpose                        |
| -------------------------- | ------------------------------ |
| **OPENAI_API_KEY**       | chat completions               |
| **OPENAI_EMBEDDING_KEY** | text-embedding-ada-002         |
| **INDEX_DIR**             | override `data/index` location |
| **REACT_APP_API_URL**   | frontend → backend URL         |


## 5. Notebooks & Experiments
Exploratory notebooks live under notebooks/; they demonstrate how to query the Chroma store directly and benchmark retrieval + LLM answer quality.


## 6. Tech Stack Versions
FastAPI 0.111 (2024-04) introduces dependency override helpers 
LangChain-OpenAI integrates native OpenAI client 
tiktoken 0.9 for accurate token counting 
Docker Compose V2 handles multi-service orchestration; version: field deprecated


## 7. Common Commands

#### rebuild index after adding new PDFs
python backend/scripts/build_index.py

####  health-check OpenAI creds
python backend/scripts/test.py

####  live backend reload during dev
uvicorn backend.app:app --reload

#### clear & vacuum Chroma
docker exec -it chroma chroma utils vacuum

