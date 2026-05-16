# Movie Collaboration Network Analysis
## Techtators — BD & BI Capstone Project | SRH University

---

## Business Question
**"Which collaboration networks between actors and directors have the greatest
impact on the commercial success of films?"**

---

## Dataset
**IMDB + TMDb Movie Metadata Dataset (1M rows)**
- Source: Kaggle — IMDB TMDB Movie Metadata Big Dataset
- 🔗 https://www.kaggle.com/datasets/shubhamchandra235/imdb-and-tmdb-movie-metadata-big-dataset-1m
- Final cleaned dataset: 3,114 movies (1990–2024)
- Format: CSV + Parquet

> The raw dataset is too large for GitHub (~500MB).
> Download from Kaggle and place in `data/` folder.

### Columns Used
| Column | Type | Description |
|---|---|---|
| title | VARCHAR | Movie title |
| release_year | INTEGER | Year of release |
| runtime | DOUBLE | Movie duration in minutes |
| budget | DOUBLE | Production budget in USD |
| revenue | DOUBLE | Box office revenue in USD |
| imdb_rating | DOUBLE | IMDB user rating |
| roi | DOUBLE | Return on investment (%) |
| overview | VARCHAR ✦ | Full plot summary — unstructured text |
| tagline | VARCHAR ✦ | Marketing tagline — unstructured text |
| director | VARCHAR | Director name |
| actor | VARCHAR | Lead actor name |
| writer | VARCHAR | Writer name |
| genres_list | VARCHAR | Movie genre combination |
| production_companies | VARCHAR | Production company |
| production_countries | VARCHAR | Country of production |

✦ Free text columns embedded using sentence-transformers for Qdrant search

---

## Project Stages

### Stage 1 — Dataset Discovery + Business Question 
- Selected and explored the IMDB + TMDb dataset
- Defined business question and decision maker
- Built entity/relationship sketch
- Identified free text columns for embeddings

### Stage 2 — Data Modeling + First Load 
- Cleaned dataset using DuckDB (3,114 movies, 0 nulls)
- Defined Neo4j schema — 4 node types, 4 relationship types
- Loaded full graph using LOAD CSV queries
- Built collaboration network with COLLABORATED_WITH relationships

### Stage 3 — ETL Pipeline + Scale-Up Draft 
- Built complete ETL pipeline (Extract → Transform → Load)
- Exported cleaned data as CSV and Parquet
- Ran 5 analytical queries answering the business question
- Wrote scale-up reasoning document

### Stage 4 — Mid-term Presentation 
- 10-minute presentation with live Neo4j demo
- 3 Cypher queries demonstrated live
- Product Vision for Streamlit similarity widget
- Gap analysis and next steps

### Stage 5 — ML + Embeddings 
- Built baseline Random Forest classifier (81% accuracy)
- Predicts whether a collaboration will achieve high ROI (>200%)
- Embedded 3,146 movie overviews using sentence-transformers
- Loaded vectors into Qdrant with payload filters
- 3 similarity queries + R+A augmentation

### Stage 6 — Graph Analytics + Interpretation 
- Built GDS notebook for PageRank + Louvain community detection
- Merged GDS features onto ML feature matrix
- Before vs After comparison — baseline vs enriched model
- Written business interpretation of graph analytics results

### Stage 7 — Integration Workshop 
- Built Streamlit dashboard with 5 pages
- Containerised with Docker Compose (Qdrant + Streamlit)
- Dashboard connects to Neo4j, Qdrant and CSV data

### Stage 8 — Final Presentation 

---

## Entity / Relationship Schema

### Nodes
| Node | Count | Key Properties |
|---|---|---|
| Movie | 3,114 | title, revenue, budget, roi, imdb_rating, overview ✦, tagline ✦ |
| Director | 1,400 | name, pagerank, community |
| Actor | 1,243 | name |
| Genre | 991 | name |

### Relationships
| Relationship | Count | Description |
|---|---|---|
| DIRECTED | 3,114 | Director → Movie |
| ACTED_IN | 3,137 | Actor → Movie |
| BELONGS_TO | 3,144 | Movie → Genre |
| COLLABORATED_WITH | 3,059 | Director → Actor (movies count + total revenue) |

---

## Key Findings

### Top Collaboration Networks by Revenue
| Director | Actor | Films | Total Revenue | Avg ROI |
|---|---|---|---|---|
| Russo Brothers | Joe Russo | 3 | $5.57B | 530% |
| Christopher Nolan | Christian Bale | 4 | $3.67B | 358% |
| David Yates | Daniel Radcliffe | 3 | $3.22B | 509% |
| Peter Jackson | Elijah Wood | 3 | $2.91B | 999% |

### Top Collaborations by ROI
| Director | Actor | Avg ROI | Avg Revenue |
|---|---|---|---|
| Michel Hazanavicius | Jean Dujardin | 22,325% | $81M |
| Steven Soderbergh | Julia Roberts | 6,365% | $75M |
| Peter Jackson | Elijah Wood | 999% | $972M |
| Robert Zemeckis | Tom Hanks | 906% | $827M |

### Most Successful Directors
| Director | Total Movies | Total Revenue | Avg Rating |
|---|---|---|---|
| Christopher Nolan | 15 | $8.14B | 8.02 |
| Steven Spielberg | 27 | $7.34B | 7.37 |
| James Cameron | 7 | $6.44B | 7.74 |

### Most Successful Genre Combinations
| Genre | Avg Revenue | Avg ROI |
|---|---|---|
| Adventure + Action + Sci-Fi | $836M | 423% |
| Adventure + Fantasy | $739M | 393% |
| Adventure + Fantasy + Action | $621M | 379% |

### ML Model Results
| Metric | Baseline S5 | Enriched S6 (+GDS) |
|---|---|---|
| Accuracy | 81% | 75% |
| F1 Macro | 0.77 | 0.67 |
| High ROI Precision | 1.00 | 1.00 |
| High ROI Recall | 0.50 | 0.33 |

> Degree features (collaboration history) are more predictive than
> global graph centrality for ROI classification.

---

## Tech Stack
| Tool | Purpose |
|---|---|
| DuckDB | Data cleaning + analytical SQL queries |
| Neo4j | Graph database + collaboration network |
| scikit-learn | Random Forest ROI classifier |
| sentence-transformers | Movie overview embeddings |
| Qdrant | Vector database + semantic search |
| Streamlit | Interactive dashboard |
| Docker Compose | Container orchestration |
| Python / Pandas | Data processing |
| Jupyter Notebook | Development environment |
| GitHub | Version control |

---

## How to Run

### Prerequisites
- Neo4j Desktop (running locally)
- Docker Desktop
- Python 3.11+
- Anaconda / Jupyter

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Techtators-Big-Data-and-Business-Intelligence.git
cd Techtators-Big-Data-and-Business-Intelligence
```

### 2. Download the raw dataset
Download from Kaggle and place in `data/` folder:
🔗 https://www.kaggle.com/datasets/shubhamchandra235/imdb-and-tmdb-movie-metadata-big-dataset-1m

### 3. Run the ETL pipeline
```bash
jupyter notebook notebooks/01_etl.ipynb
```

### 4. Load Neo4j graph
1. Start Neo4j Desktop and create a database
2. Copy `data/movies_cleaned.csv` to Neo4j import folder
3. Run queries from `neo4j/load_csv_queries.cypher`

### 5. Generate embeddings
```bash
jupyter notebook notebooks/05_embeddings.ipynb
```

### 6. Start the dashboard with Docker
```bash
docker compose up --build
```

Open: http://localhost:8501

---

## Dashboard Pages
| Page | Description |
|---|---|
| Overview | Dataset stats, graph counts, top genres |
| Collaboration Network | Interactive Neo4j network explorer |
| ROI Analysis | With vs without collaboration comparison |
| Similarity Search | Qdrant semantic film search |
| ROI Predictor | Director-actor ROI prediction |

---

## Team
**Techtators**
BD & BI Capstone — SRH University


