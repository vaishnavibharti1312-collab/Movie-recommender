# AI OTT Content Intelligence Platform 🎬✨

A complete AI-driven SaaS intelligence platform for OTT users and business analytics, powered by a FastAPI backend, SQLite database, and machine learning models for recommendations, subscriber churn forecasting, and trend forecasting.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/vaishnavibharti1312-collab/Movie-recommender)

---

## 🚀 One-Click Cloud Deployment
Simply click the **Deploy to Render** button above! It will automatically read our `render.yaml` configuration, set up the Python web service, and deploy the entire full-stack app online.

---

## 🛠️ Features
- **Viewer Portal**:
  - **Discover Content**: Filter, search, and browse the TMDB database of 4,800+ movies (with cast and directors).
  - **Personalized Matching**: TF-IDF cosine-similarity content engine combined with user watch preferences.
  - **Conversational Movie Assistant**: Chat about reviews, plot details, and streaming links.
- **Business BI Suite**:
  - **KPI Dashboard**: View aggregate catalog size, active users, average ratings, and positive review sentiments.
  - **Subscriber Churn Hub**: Random Forest model flagging high-risk subscribers based on logins, complaints, and billing history.
  - **Market Trends**: Google Trends data linear regression modeling to forecast next-quarter genre popularity.
  - **Ad Placement Simulator**: Evaluates movie suitability scores for targeted demographic ad campaigns.

---

## 💻 Local Setup & Installation

### Prerequisities
- Python 3.8 or newer
- Git

### Steps
1. **Clone the repo**:
   ```bash
   git clone https://github.com/vaishnavibharti1312-collab/Movie-recommender.git
   cd Movie-recommender
   ```
2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   # Activate on Windows
   .\venv\Scripts\activate
   # Activate on macOS/Linux
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Run the application**:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
5. **Access in browser**:
   Go to `http://127.0.0.1:8000/app/index.html`
