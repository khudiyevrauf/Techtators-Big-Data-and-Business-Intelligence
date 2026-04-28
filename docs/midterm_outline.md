# Mid-Term Presentation Outline
## BD & BI Capstone — Movie Collaboration Network Analysis

---

## Presentation Structure (10 minutes)

---

### Part 1 — Problem Statement & Product Vision (2 minutes)

**What problem are we solving?**
Production companies spend millions of dollars on casting decisions with limited
data-driven insights. The question of which director-actor collaborations 
generate the highest return on investment is currently answered by intuition 
and experience rather than data.

**Product Vision**
A data-driven collaboration intelligence tool that helps production companies 
identify the most commercially successful director-actor networks before 
greenlighting a film. By analyzing historical collaboration patterns, ROI, and 
revenue data, studios can make evidence-based casting decisions that maximize 
commercial success.

**Business Question**
> "Which collaboration networks between actors and directors have the greatest 
> impact on the commercial success of films?"

**Who benefits?**
- Production companies making casting decisions
- Studios evaluating greenlight decisions
- Investors assessing film project risk

---

### Part 2 — Dataset & Data Preparation (2 minutes)

**Dataset**
- Source: IMDB + TMDb Movie Metadata (1M rows, ~500MB)
- Final cleaned dataset: 3,146 movies (1990–2024)
- Link: https://www.kaggle.com/datasets/shubhamchandra235/imdb-and-tmdb-movie-metadata-big-dataset-1m

**Key Columns**
- Structured: revenue, budget, roi, imdb_rating, release_year, genres
- Unstructured ✦: overview (plot summaries), tagline (marketing text)

**Cleaning Steps**
- Removed irrelevant columns (image URLs, duplicates)
- Filtered revenue > $1,000 and budget > $1,000
- Removed runtime = 0 and release_year < 1990
- Dropped all null and empty string values
- Added ROI column: ((revenue - budget) / budget) × 100
- Final result: 3,146 movies, 18 columns, 0 nulls

**Tools Used**
- DuckDB for SQL-based cleaning and transformation
- Exported as CSV (for Neo4j) and Parquet (for downstream ML)

---

### Part 3 — Data Modeling & Graph Database (2 minutes)

**Why Neo4j?**
Collaboration networks are naturally a graph problem. Traditional SQL databases 
require complex multi-table JOINs to find connections between directors and 
actors. Neo4j traverses these relationships natively and efficiently.

**Graph Schema**

Nodes:
- Movie (3,114) — title, revenue, budget, roi, overview, tagline
- Director (1,400) — name
- Actor (1,243) — name
- Genre (991) — name

Relationships:
- DIRECTED (3,146) — Director → Movie
- ACTED_IN (3,137) — Actor → Movie
- BELONGS_TO (3,144) — Movie → Genre
- COLLABORATED_WITH (3,059) — Director → Actor
  - Properties: movies (count), total_revenue

**Key Insight**
The COLLABORATED_WITH relationship is the core of our analysis. It captures 
not just who worked together, but how many times and how much revenue their 
combined work generated.

---

### Part 4 — Key Findings (2 minutes)

**Finding 1 — Top Collaboration Networks by Revenue**
| Director | Actor | Films | Total Revenue |
|---|---|---|---|
| Russo Brothers | Joe Russo | 3 | $5.57B |
| Christopher Nolan | Christian Bale | 4 | $3.67B |
| David Yates | Daniel Radcliffe | 3 | $3.22B |
| Peter Jackson | Elijah Wood | 3 | $2.91B |

**Finding 2 — ROI: With vs Without Collaboration**
Repeated director-actor collaborations consistently achieve higher ROI than 
the same director working with other actors. Peter Jackson achieves 999% ROI 
with Elijah Wood but significantly less with other actors.

**Finding 3 — Genre Impact**
Adventure + Action + Sci-Fi is the most commercially powerful genre 
combination with $836M average revenue and 423% average ROI. Every top 
collaboration network operates within this genre space.

**Finding 4 — Quality vs Volume**
Christopher Nolan generates $8.14B total revenue across 15 films with an 
average rating of 8.02 — proving that quality and consistency of collaboration 
beats volume every time.

---

### Part 5 — Gap Analysis & Next Steps (2 minutes)

**What we have done**
-  Dataset selected, cleaned and validated
-  ETL pipeline built (DuckDB → CSV + Parquet)
-  Neo4j graph loaded with 5,748 nodes and 12,486 relationships
-  Analytical queries answering the business question
-  Scale-up reasoning documented

**Current Gaps**
| Gap | Description | Plan |
|---|---|---|
| Machine Learning | No predictive model yet | scikit-learn in S5 |
| Semantic Search | overview + tagline not embedded yet | Qdrant in S5 |
| Graph Analytics | No community detection yet | GDS in S6 |
| Dashboard | No visualization layer yet | Streamlit in S7 |
| Automation | Pipeline not fully automated | Docker Compose in S7 |

**Next Steps**
- S4: Build scikit-learn model to predict collaboration success
- S5: Embed movie overviews using Qdrant for semantic search
- S6: Run GDS community detection to find collaboration clusters
- S7: Build Streamlit dashboard + Docker Compose

**Final Vision**
A fully automated, containerized pipeline that ingests movie data, builds a 
collaboration network graph, predicts ROI for new director-actor pairs, and 
presents findings through an interactive dashboard — all reproducible with a 
single `docker compose up` command.