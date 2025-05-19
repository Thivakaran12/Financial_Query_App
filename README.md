# Financial Query App

This project scrapes, extracts, indexes and visualizes quarterly P&L statements
for **Dipped Products PLC** and **Richard Pieris Exports PLC** (CSE symbols
`DIPD.N0000` & `REXP.N0000`).

---

## ⏩ Quickstart

1. **Clone & deps**  
   ```bash
   git clone <repo>
   cd Financial_Query_App
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd backend
   pip install requests beautifulsoup4

Scrape PDFs
Downloads the last 3 years of interim reports into backend/Data/Raw/....

bash
Copy
Edit
