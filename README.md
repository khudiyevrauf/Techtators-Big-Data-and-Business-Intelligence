# Movie Collaboration Network Analysis
## Techtators-Big-Dat-and-Bussiness-Intellligence Capstone Project

---

## Business Question
**"Which collaboration networks between actors and directors have the greatest 
impact on the commercial success of films?"**

---

## Raw Dataset
The raw dataset is too large for GitHub (1M rows, ~500MB).

Download it from Kaggle:
🔗 https://www.kaggle.com/datasets/shubhamchandra235/imdb-and-tmdb-movie-metadata-big-dataset-1m

After downloading:
1. Place the file in the `data/` folder
2. Rename it to `IMDB TMDB Movie Metadata Big Dataset (1M).csv`
3. Run `notebooks/Code_clean_duckdb.ipynb` to reproduce the cleaned dataset
   
-Source: Kaggle — IMDB TMDB Movie Metadata Big Dataset
- Final cleaned dataset: 3,146 movies (1990–2024)
- Format: CSV
  
---
## Project Stages
### Stage 1 — Team Formation + Dataset Discovery
### Stage 2 — Data Modeling + First Load 
### Stage 3 — ETL Pipeline + Scale-Up Draft
### Stage 4 — Mid-term Presentation
### Stage 5 — ML + Embeddings
### Stage 6 — Graph Analytics + Interpretation
### Stage 7 - Integration Workshop
### Stage 8 - Final Presentation

---

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

✦ Free text / unstructured columns used for semantic embeddings
  
---

## Project Stages

### Stage 1 — Team Formation + Dataset Discovery
- Selected and explored the IMDB + TMDb dataset
- Defined business question
- Built entity/relationship sketch
- Cleaned dataset using DuckDB:
  - Removed unwanted columns
  - Filtered nulls and empty strings
  - Removed unrealistic values (budget/revenue < $1000, runtime = 0)
  - Filtered movies from 1990 onwards
  - Final dataset: 3,146 movies, 18 columns, 0 nulls

### Stage 2 — Data Modeling + First Load 
- Defined Neo4j schema with 4 node types and 4 relationship types
- Loaded data using LOAD CSV queries
- Built collaboration network graph

---


## Entity / Relationship Schema

### Nodes
| Node | Count | Key Properties |
|---|---|---|
| Movie | 3,114 | title, revenue, budget, imdb_rating, overview, tagline |
| Director | 1,400 | name |
| Actor | 1,243 | name |
| Genre | 991 | name |

### Relationships
| Relationship | Count | Description |
|---|---|---|
| DIRECTED | 3,146 | Director → Movie |
| ACTED_IN | 3,137 | Actor → Movie |
| BELONGS_TO | 3,144 | Movie → Genre |
| COLLABORATED_WITH | 3,059 | Director → Actor (weighted by revenue) |

---

## Key Findings (DuckDB Analysis)

### Top Collaboration Networks by Revenue
| Director | Actor | Movies Together | Total Revenue |
|---|---|---|---|
| Russo Brothers | Joe Russo | 3 | $5.57B |
| Christopher Nolan | Christian Bale | 4 | $3.67B |
| David Yates | Daniel Radcliffe | 3 | $3.22B |
| Peter Jackson | Elijah Wood | 3 | $2.91B |

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

---

**What We Did in Neo4j?**
1. Setup
Connected to the locally running Neo4j Desktop instance bdbi via the Query Browser at neo4j://127.0.0.1:7687.
2. Found Import Folder
Ran a config query to find the exact path where Neo4j reads CSV files from, then copied movies_cleaned.csv into that folder via Mac Terminal.
3. Created Constraints (Schema)
Defined uniqueness constraints for all 4 node types — Movie, Director, Actor and Genre — to ensure no duplicate nodes and to speed up lookups.
4. Loaded Nodes + Relationships
Used LOAD CSV to build the full graph in 5 steps:

   Movie nodes — 3,114 nodes with all properties including free text overview and tagline
   Director nodes + DIRECTED — 1,400 directors linked to their movies
   Actor nodes + ACTED_IN — 1,243 actors linked to their movies
   Genre nodes + BELONGS_TO — 991 genres linked to movies
   COLLABORATED_WITH — 3,059 relationships between directors and actors, weighted by number of movies and total revenue

5. Verified & Visualized
Confirmed all nodes and relationships loaded correctly, then ran a visual query showing the blockbuster collaboration
 network (revenue > $500M) — 10 Directors, 11 Actors, 15 Movies.

---

## Tech Stack
| Tool | Purpose |
|---|---|
| Python / Pandas | Initial data exploration |
| DuckDB | Data cleaning and analytical queries |
| Neo4j | Graph database and collaboration network |
| Jupyter Notebook | Development environment |
| GitHub | Version control |

---

## Repository Structure

Techtators-Big-Data-and-Bussiness-Intelligence/
├── data/
│   └── movies_cleaned.csv
├── neo4j/
│   └── load_csv_queries.cypher
├── notebooks/
│   └── Code_clean_duckdb.ipynb
└── README.md
