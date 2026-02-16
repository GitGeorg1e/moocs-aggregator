# MOOCs Aggregator

Οριζόντιο Repository / Aggregator Ανοικτών Μαθημάτων με **React** front-end, **FastAPI** back-end και **Apache Spark** για large-scale ML.

Το σύστημα συγκεντρώνει δεδομένα μαθημάτων από πολλαπλές πλατφόρμες MOOCs (Coursera, MIT OpenCourseWare), τα αποθηκεύει σε ενιαίο σχήμα σε MySQL βάση δεδομένων και παρέχει ενιαίο web UI για αναζήτηση, φιλτράρισμα, εξερεύνηση μαθημάτων και ML-based recommendations.

---

## Πίνακας Περιεχομένων

- [Αρχιτεκτονική](#αρχιτεκτονική)
- [Τεχνολογίες](#τεχνολογίες)
- [Προαπαιτούμενα](#προαπαιτούμενα)
- [Εγκατάσταση](#εγκατάσταση)
- [Εκτέλεση](#εκτέλεση)
- [API Endpoints](#api-endpoints)
- [Spark Jobs](#spark-jobs)
- [Testing](#testing)
- [Δομή Φακέλων](#δομή-φακέλων)

---

## Αρχιτεκτονική

Το σύστημα αποτελείται από τρία βασικά layers:

```
┌─────────────────────────────────────────────────────────┐
│                   React Front-end                       │
│  (Vite + React Router + Axios)                          │
│  Σελίδες: Αναζήτηση/Λίστα, Λεπτομέρειες, Analytics     │
└──────────────────────┬──────────────────────────────────┘
                       │  REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│                 FastAPI Back-end                         │
│  Endpoints: /courses, /courses/{id}, /courses/{id}/     │
│  similar, /sync/{source}, /analytics, /spark/*          │
│                                                         │
│  Connectors: CourseraConnector, MitOcwConnector          │
│  Services: CourseService, SyncService                   │
└──────────┬───────────────────────────────┬──────────────┘
           │                               │
     ┌─────▼─────┐               ┌─────────▼──────────┐
     │   MySQL    │◄──────────── │  Apache Spark       │
     │   (DB)     │  results     │  (PySpark)          │
     │            │              │                     │
     │ - courses  │              │ Jobs:               │
     │ - sources  │              │ - TF-IDF Similarity │
     │ - similar_ │              │ - K-Means Clustering│
     │   courses  │              │ - Analytics         │
     │ - course_  │              │                     │
     │   clusters │              │ Reads courses,      │
     │ - analytics│              │ writes results back │
     └────────────┘              └─────────────────────┘
```

### Ροή Δεδομένων

1. **Harvesting**: Οι Connectors (Coursera, MIT OCW) κάνουν scrape μέσω sitemaps, εξάγουν μεταδεδομένα μαθημάτων (JSON-LD, HTML parsing) και τα αποθηκεύουν στη βάση με ενιαίο σχήμα.
2. **API Layer**: Το FastAPI back-end σερβίρει τα δεδομένα με αναζήτηση, φίλτρα και pagination.
3. **Spark Processing**: Τα Spark jobs διαβάζουν τα μαθήματα από τη βάση, εφαρμόζουν ML pipelines (TF-IDF, K-Means) και γράφουν τα αποτελέσματα πίσω (similar_courses, course_clusters, analytics tables).
4. **Front-end**: Το React UI καταναλώνει τα API endpoints και εμφανίζει μαθήματα, recommendations και analytics.

---

## Τεχνολογίες

| Layer | Τεχνολογία | Έκδοση |
|-------|-----------|--------|
| Front-end | React + Vite | React 19, Vite 7 |
| Routing | React Router | 7.x |
| HTTP Client | Axios | 1.x |
| Back-end | FastAPI (Python) | 0.124+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | MySQL (PyMySQL) | 8.x |
| Big Data / ML | Apache Spark (PySpark) | 4.0+ |
| ML Algorithms | Spark MLlib (TF-IDF, K-Means, Cosine Similarity) | — |
| Web Scraping | BeautifulSoup4, lxml, requests | — |
| Config | Pydantic Settings, python-dotenv | — |
| Testing | pytest, FastAPI TestClient | — |
| Package Manager | uv (Python), npm (JS) | — |

---

## Προαπαιτούμενα

- **Python** 3.11.x (απαίτηση: `>=3.11.14, <3.12`)
- **Node.js** 18+ και npm
- **Java** 11+ (απαραίτητο για το Apache Spark)
- **MySQL** 8.x server
- **Apache Spark** (μέσω PySpark — εγκαθίσταται αυτόματα ως Python dependency)

---

## Εγκατάσταση

### 1. Clone του repository

```bash
git clone <repository-url>
cd moocs-aggregator
```

### 2. Δημιουργία MySQL βάσης

```sql
CREATE DATABASE moocs_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'moocs_user'@'localhost' IDENTIFIED BY '123456789';
GRANT ALL PRIVILEGES ON moocs_db.* TO 'moocs_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Ρύθμιση environment variables

Δημιουργήστε αρχείο `.env` στο root directory:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=moocs_user
DB_PASSWORD=123456789
DB_NAME=moocs_db

# Coursera connector
COURSERA_MAX_URLS=100

# MIT OCW connector
MIT_OCW_MAX_URLS=100

# Spark
SPARK_MASTER=local[*]
SPARK_OUTPUT_DIR=./src/spark_output
```

### 4. Εγκατάσταση Python dependencies

```bash
# Με uv (προτεινόμενο)
uv sync

# Ή με pip
pip install -e .
pip install -e ".[test]"
```

### 5. Εγκατάσταση Front-end dependencies

```bash
cd frontend
npm install
cd ..
```

### 6. Δημιουργία πινάκων βάσης

Οι πίνακες `courses`, `sources`, `similar_courses` δημιουργούνται αυτόματα κατά την εκκίνηση του FastAPI server (SQLAlchemy `create_all`). Για τους πίνακες αποτελεσμάτων Spark:

```bash
cd src
python -m sparkjobs.db_schema
```

---

## Εκτέλεση

### Back-end API Server

```bash
# Από το root directory
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Ή μέσα από src/
cd src
uvicorn backend.app.main:app --reload --port 8000
```

Το API είναι διαθέσιμο στο `http://localhost:8000`. Η τεκμηρίωση (Swagger UI) στο `http://localhost:8000/docs`.

### Front-end Dev Server

```bash
cd frontend
npm run dev
```

Το React app ξεκινά στο `http://localhost:5173`.

### Harvesting / Sync μαθημάτων

Μέσω API (ενώ τρέχει ο backend server):

```bash
# Sync Coursera
curl -X POST http://localhost:8000/api/v1/sync/coursera

# Sync MIT OpenCourseWare
curl -X POST http://localhost:8000/api/v1/sync/mit_ocw
```

Ή απευθείας μέσω scripts:

```bash
cd src
python -m backend.app.scripts.sync_coursera
python -m backend.app.scripts.sync_mit_ocw
python -m backend.app.scripts.sync_all
```

### Spark Jobs

```bash
cd src

# Εκτέλεση μεμονωμένων jobs
python -m sparkjobs similarity     # TF-IDF similarity
python -m sparkjobs clustering     # K-Means clustering
python -m sparkjobs analytics      # Aggregated analytics

# Εκτέλεση όλων σε σειρά
python -m sparkjobs all
```

Ή μέσω API endpoints (ενώ τρέχει ο server):

```bash
curl -X POST http://localhost:8000/api/v1/spark/run-similarity-job
curl -X POST http://localhost:8000/api/v1/spark/run-clustering-job
curl -X POST http://localhost:8000/api/v1/spark/run-analytics-job
```

---

## API Endpoints

### Courses

| Method | Endpoint | Περιγραφή |
|--------|----------|-----------|
| `GET` | `/api/v1/courses` | Λίστα μαθημάτων (search, filters, pagination) |
| `GET` | `/api/v1/courses/filters` | Διαθέσιμες τιμές φίλτρων |
| `GET` | `/api/v1/courses/{id}` | Λεπτομέρειες μαθήματος |
| `GET` | `/api/v1/courses/{id}/similar` | Παρόμοια μαθήματα (Spark TF-IDF) |

**Query parameters για `/courses`:**
- `q` / `search` — Αναζήτηση κειμένου (ILIKE σε title, description)
- `language` — Φίλτρο γλώσσας (π.χ. `en`, `es`)
- `level` — Φίλτρο επιπέδου (`Beginner`, `Intermediate`, `Advanced`)
- `source` — Φίλτρο πηγής (`coursera`, `mit_ocw`)
- `topic` — Φίλτρο θεματικής
- `page`, `per_page` — Pagination

### Sync

| Method | Endpoint | Περιγραφή |
|--------|----------|-----------|
| `POST` | `/api/v1/sync/coursera` | Εκκίνηση Coursera harvesting |
| `POST` | `/api/v1/sync/mit_ocw` | Εκκίνηση MIT OCW harvesting |
| `GET` | `/api/v1/sync/status/{task_id}` | Status sync task |

### Analytics

| Method | Endpoint | Περιγραφή |
|--------|----------|-----------|
| `GET` | `/api/v1/analytics` | Συγκεντρωτικά analytics |

### Spark ML

| Method | Endpoint | Περιγραφή |
|--------|----------|-----------|
| `POST` | `/api/v1/spark/run-similarity-job` | Εκτέλεση TF-IDF similarity job |
| `POST` | `/api/v1/spark/run-clustering-job` | Εκτέλεση K-Means clustering job |
| `POST` | `/api/v1/spark/run-analytics-job` | Εκτέλεση analytics job |
| `GET` | `/api/v1/spark/clusters/{id}/courses` | Μαθήματα ανά cluster |
| `GET` | `/api/v1/spark/clusters/stats` | Στατιστικά clusters |
| `GET` | `/api/v1/spark/analytics/overview` | Συνολική επισκόπηση analytics |
| `GET` | `/api/v1/spark/analytics/by-source` | Analytics ανά πηγή |
| `GET` | `/api/v1/spark/analytics/by-language` | Analytics ανά γλώσσα |
| `GET` | `/api/v1/spark/analytics/by-topic` | Analytics ανά θεματική |

---

## Spark Jobs

### 1. Course Similarity (TF-IDF + Cosine Similarity)

- **Αλγόριθμος**: Tokenizer → HashingTF → IDF (Pipeline)
- **Features**: Συνδυασμός title, short_description, keywords, topic
- **Similarity**: Cosine similarity μέσω self-join και vector operations
- **Threshold**: Αποθηκεύονται μόνο ζεύγη με similarity ≥ 0.3
- **Top-N**: Κάθε μάθημα αποκτά τα 5 πιο παρόμοια
- **Output**: Πίνακας `similar_courses` + CSV στο `spark_output/similarity_results/`

### 2. Course Clustering (K-Means)

- **Αλγόριθμος**: TF-IDF features → StandardScaler → K-Means
- **k**: 10 clusters (configurable)
- **Evaluation**: Silhouette score
- **Output**: Πίνακας `course_clusters` (course_id, cluster_id, cluster_center_distance) + CSV στο `spark_output/clustering_results/`

### 3. Analytics Aggregation

- **Υπολογισμοί**: Στατιστικά ανά source, language, level, topic
- **Output**: Πίνακες `analytics_by_source`, `analytics_by_language`, `analytics_by_level`, `analytics_by_topic` + CSV στο `spark_output/analytics_results/`

---

## Testing

```bash
# Εκτέλεση όλων των tests
cd src
pytest

# Ή από root
pytest tests/

# Μεμονωμένα test modules
pytest tests/test_api.py          # Integration tests (API endpoints)
pytest tests/test_connectors.py   # Unit tests (connector parsing/normalization)
pytest tests/test_services.py     # Unit tests (service layer)
pytest tests/test_spark.py        # Spark job tests (requires Java)

# Με verbose output
pytest -v
```

Τα API tests χρησιμοποιούν in-memory SQLite (δεν χρειάζεται MySQL server). Τα Spark tests χρησιμοποιούν local SparkSession (χρειάζεται Java).

---

## Δομή Φακέλων

```
moocs-aggregator/
├── frontend/                      # React front-end (Vite)
│   ├── src/
│   │   ├── api/
│   │   │   └── courses.js         # API client (axios)
│   │   ├── components/
│   │   │   ├── Analytics.jsx      # Analytics charts
│   │   │   ├── CourseCard.jsx     # Course card component
│   │   │   ├── CourseFilters.jsx  # Sidebar filters
│   │   │   ├── CourseList.jsx     # Course grid/list
│   │   │   ├── Navbar.jsx         # Navigation bar
│   │   │   ├── SearchBar.jsx      # Search input
│   │   │   └── SimilarCourses.jsx # ML recommendations
│   │   ├── pages/
│   │   │   ├── HomePage.jsx       # Search + list page
│   │   │   ├── CourseDetailPage.jsx # Course details + similar
│   │   │   └── AnalyticsPage.jsx  # Platform analytics
│   │   ├── App.jsx                # Router setup
│   │   └── main.jsx               # Entry point
│   └── package.json
│
├── src/
│   ├── backend/                   # FastAPI back-end
│   │   └── app/
│   │       ├── api/v1/
│   │       │   ├── endpoints/
│   │       │   │   ├── courses.py # /courses endpoints
│   │       │   │   ├── sync.py    # /sync endpoints
│   │       │   │   ├── analytics.py # /analytics endpoint
│   │       │   │   └── spark.py   # /spark ML endpoints
│   │       │   └── router.py
│   │       ├── connectors/
│   │       │   ├── base.py        # BaseConnector (ABC)
│   │       │   ├── coursera.py    # Coursera scraper
│   │       │   └── mit_ocw.py     # MIT OCW scraper
│   │       ├── core/
│   │       │   ├── config.py      # App settings (pydantic)
│   │       │   └── db.py          # SQLAlchemy engine
│   │       ├── models/
│   │       │   ├── course.py      # Course model
│   │       │   ├── source.py      # Source model
│   │       │   └── similar_course.py # SimilarCourse model
│   │       ├── schemas/
│   │       │   ├── course.py      # Pydantic schemas
│   │       │   ├── analytics.py   # Analytics schema
│   │       │   └── sync.py        # Sync request/response
│   │       ├── services/
│   │       │   ├── course_service.py
│   │       │   ├── sync_service.py
│   │       │   └── ...
│   │       ├── scripts/
│   │       │   ├── sync_coursera.py
│   │       │   ├── sync_mit_ocw.py
│   │       │   └── sync_all.py
│   │       └── main.py            # FastAPI app entry
│   │
│   ├── sparkjobs/                 # PySpark ML jobs
│   │   ├── __init__.py            # Job runners
│   │   ├── __main__.py            # CLI entry point
│   │   ├── config.py              # Spark configuration
│   │   ├── course_similarity_job.py  # TF-IDF + cosine similarity
│   │   ├── clustering_job.py      # K-Means clustering
│   │   ├── analytics_job.py       # Aggregated statistics
│   │   ├── spark_utils.py         # Session, loaders, preprocessors
│   │   ├── db_schema.py           # DB table definitions
│   │   └── job_scheduler.py       # Periodic job scheduler
│   │
│   └── spark_output/              # Spark job output files
│       ├── similarity_results/
│       ├── clustering_results/
│       ├── analytics_results/
│       └── tfidf_model/
│
├── tests/
│   ├── conftest.py                # Shared fixtures (in-memory SQLite)
│   ├── test_api.py                # API integration tests
│   ├── test_connectors.py         # Connector unit tests
│   ├── test_services.py           # Service layer tests
│   └── test_spark.py              # Spark job tests
│
├── docs/
│   └── Project2-Spark-2025(Gr)[100%] (3).pdf
│
├── pyproject.toml                 # Python project config & deps
└── .env                           # Environment variables (not in git)
```

---

## Database Schema (ER)

```
┌──────────────┐       ┌───────────────────────────────────────┐
│   sources    │       │              courses                  │
├──────────────┤       ├───────────────────────────────────────┤
│ id (PK)      │──┐    │ id (PK)                               │
│ name         │  │    │ source_id (FK → sources.id)           │
│ base_url     │  └───>│ source_course_id                      │
└──────────────┘       │ title                                 │
                       │ short_description                     │
                       │ full_description                      │
                       │ keywords                              │
                       │ topic                                 │
                       │ language                              │
                       │ level                                 │
                       │ course_url                            │
                       │ enrollment_url                        │
                       │ image_url                             │
                       │ last_updated_at_source                │
                       │ created_at, updated_at                │
                       └────┬─────────────────┬────────────────┘
                            │                 │
              ┌─────────────▼──┐    ┌─────────▼────────────┐
              │ similar_courses│    │   course_clusters     │
              ├────────────────┤    ├──────────────────────┤
              │ id (PK)        │    │ id (PK)              │
              │ course_id (FK) │    │ course_id (FK)       │
              │ similar_course_│    │ title                │
              │   id (FK)      │    │ topic                │
              │ similarity     │    │ level                │
              └────────────────┘    │ cluster_id           │
                                    │ cluster_center_dist. │
                                    └──────────────────────┘

  ┌─────────────────────┐  ┌──────────────────────┐
  │ analytics_by_source │  │ analytics_by_language │
  ├─────────────────────┤  ├──────────────────────┤
  │ source_name         │  │ language             │
  │ num_courses         │  │ num_courses          │
  │ num_languages       │  │ num_sources          │
  │ num_topics          │  │ num_topics           │
  │ num_levels          │  └──────────────────────┘
  └─────────────────────┘
  ┌─────────────────────┐  ┌──────────────────────┐
  │ analytics_by_level  │  │ analytics_by_topic   │
  ├─────────────────────┤  ├──────────────────────┤
  │ level               │  │ topic                │
  │ num_courses         │  │ num_courses          │
  │ num_sources         │  │ num_sources          │
  │ num_languages       │  │ num_languages        │
  │ num_topics          │  │ num_levels           │
  └─────────────────────┘  └──────────────────────┘
```
