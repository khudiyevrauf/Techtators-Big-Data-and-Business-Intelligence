# Final Presentation Outline
## BD & BI Capstone — Movie Collaboration Network Analysis
## Techtators Team

---

## Presentation Structure (20 minutes + 5 min Q&A)

| Section | Title | Slides | Who |
|---|---|---|---|
| 1 | Problem Statement & Business Question | 2 | Manohar |
| 2 | Data Pipeline & ETL | 3 | Manohar |
| 3 | Graph Database & Schema | 3 | Maziyar |
| 4 | ML Pipeline & Baseline Results | 3 | Maziyar |
| 5 | Graph Analytics & Model Enrichment | 3 | Manohar |
| 6 | Live Demo & Conclusion | 3 | Maziyar |

**Total: 17 slides + title slide + Q&A**

---

## Section 1 — Problem Statement & Business Question (2 slides)

### Slide 1 — The Problem
**Who says it:** Manohar

**Key points:**
- Production companies make casting decisions worth billions with limited data
- Intuition-driven casting vs data-driven collaboration intelligence
- Business question: *"Which collaboration networks between actors and directors have the greatest impact on the commercial success of films?"*

**Who benefits:**
- Film studios evaluating greenlight decisions
- Talent agencies assessing partnership value
- Investors measuring project risk

### Slide 2 — Our Solution
**Who says it:** Manohar

**Key points:**
- End-to-end data pipeline: raw CSV → Neo4j graph → ML model → Streamlit dashboard
- Dataset: 3,146 movies (1990–2024), cleaned from 1M raw rows
- Tech stack: DuckDB, Neo4j, scikit-learn, Qdrant, Streamlit

---

## Section 2 — Data Pipeline & ETL (3 slides)

### Slide 3 — Raw Dataset
**Who says it:** Manohar

**Key points:**
- Source: Kaggle — IMDB + TMDB Movie Metadata (1M rows, ~500MB)
- Final cleaned dataset: 3,146 movies, 18 columns, 0 nulls
- Key columns: revenue, budget, roi, imdb_rating, director, actor, genres_list, overview

### Slide 4 — ETL Pipeline
**Who says it:** Manohar

**Key points:**
- Tool: DuckDB in-memory SQL engine
- 4 steps: Extract → Transform → Validate → Export
- Filters applied: revenue > $1K, budget > $1K, runtime > 0, release_year >= 1990
- Output: movies_cleaned.csv + movies_cleaned.parquet

### Slide 5 — Scale-Up Reasoning
**Who says it:** Manohar

**Key points:**
- Current: DuckDB (local, 3K rows) — works perfectly at this scale
- 10x scale: DuckDB + S3 Parquet + Apache Airflow
- 100x scale: Apache Spark + Neo4j Enterprise + Kafka streaming
- Threshold: ~100GB is the DuckDB → Spark crossover point

---

## Section 3 — Graph Database & Schema (3 slides)

### Slide 6 — Why Neo4j?
**Who says it:** Maziyar

**Key points:**
- Collaboration networks are graph problems — SQL requires expensive multi-table JOINs
- Neo4j traverses relationships natively in constant time per hop
- Variable-length Cypher patterns vs linear SQL JOIN chains

### Slide 7 — Graph Schema
**Who says it:** Maziyar

**Key points:**
- 4 node types: Movie (3,114), Director (1,400), Actor (1,243), Genre (991)
- 4 relationship types: DIRECTED, ACTED_IN, BELONGS_TO, COLLABORATED_WITH
- Total: 5,748 nodes, 12,486 relationships
- COLLABORATED_WITH weighted by movies_together and total_revenue

### Slide 8 — Key Graph Findings
**Who says it:** Maziyar

**Key points:**
- Top collaboration by revenue: show top 3 director-actor pairs
- ROI with vs without collaboration: Michel Hazanavicius + Jean Dujardin (22,325% vs 382%)
- Most valuable genre combination: Adventure + Action + Sci-Fi ($836M avg revenue, 423% ROI)

---

## Section 4 — ML Pipeline & Baseline Results (3 slides)

### Slide 9 — Feature Engineering
**Who says it:** Maziyar

**Key points:**
- 4 feature families: tabular numeric, tabular categorical, graph-derived (degree), text
- Degree features from Neo4j via Cypher: movie_degree, actor_degree, genre_degree, director_total_movies, actor_total_movies, director_collab_count
- Excluded (leakage): revenue, roi, imdb_rating, vote_count
- Target: is_blockbuster (revenue > $100M)

### Slide 10 — Data Leakage & Pipeline
**Who says it:** Maziyar

**Key points:**
- Split FIRST, then build the Pipeline — prevents leakage
- StandardScaler and OneHotEncoder live inside the Pipeline
- RandomForestClassifier(n_estimators=200, class_weight='balanced')
- 5-fold cross-validation for robust metric estimation

### Slide 11 — Baseline Results
**Who says it:** Maziyar

**Key points:**
- Report macro-F1 from baseline_metrics.txt
- Report 5-fold CV mean and std
- Feature importance: which family (graph vs tabular) ranks highest?
- This is the before number — S4 will show the after

---

## Section 5 — Graph Analytics & Model Enrichment (3 slides)

### Slide 12 — PageRank Results
**Who says it:** Manohar

**Key points:**
- GDS workflow: Project → Run → Write back → Drop
- PageRank: damping factor 0.85, 20 iterations, UNDIRECTED projection
- Top 5 directors by PageRank — name them in domain vocabulary
- Business interpretation: high-PageRank director = safest greenlight signal

### Slide 13 — Community Detection Results
**Who says it:** Manohar

**Key points:**
- Louvain algorithm: optimises modularity
- Report modularity score and number of communities found
- Top 3 communities: describe each in business terms (franchise cluster, drama cluster, etc.)
- Business interpretation: community label = creative ecosystem signal

### Slide 14 — Before vs After Metric
**Who says it:** Manohar

**Key points:**
- Show the before-after table from 04_ml.ipynb enrichment section
- Report delta in macro-F1
- Interpret the lift: did graph analytics earn its place?
- If lift is positive: "PageRank and community carry structural signal beyond degree"
- If lift is small: "Degree already captures most local-structure signal; baseline is competitive"

---

## Section 6 — Live Demo & Conclusion (3 slides)

### Slide 15 — Live Demo
**Who says it:** Maziyar

**Demo path (walk this end-to-end before presentation):**
1. Open Streamlit dashboard at `localhost:8501`
2. Tab 1 — Top Collaborations: show top directors by PageRank + top revenue pairs
3. Tab 2 — ROI Analysis: select a director and show their movies
4. Tab 3 — Similarity Search: type "space adventure with alien battles" → show top-5 results

**Pre-warm:** open the dashboard before going on stage. Do not cold-start on stage.

### Slide 16 — Scale-Up Summary
**Who says it:** Maziyar

**Key points:**

| Component | PoC Tool | Production Alternative | Threshold |
|---|---|---|---|
| ETL | DuckDB | Apache Spark | ~100 GB |
| Graph DB | Neo4j Desktop | Neo4j AuraDB / Enterprise | ~500K nodes |
| ML | scikit-learn | Spark MLlib | ~100 GB |
| Vector Search | Qdrant local | Qdrant Cloud | ~few million vectors |
| Orchestration | Manual Jupyter | Apache Airflow | Any production deployment |

### Slide 17 — Conclusion & Next Steps
**Who says it:** Maziyar

**Key points:**
- Answer the business question directly: which collaboration patterns drive commercial success?
- Graph analytics earned its place: PageRank and community add structural signal
- Semantic similarity search finds thematically related films without keyword overlap
- Next steps: real-time box office API integration, LLM-augmented generation (full RAG)

---

## Demo Checklist (run before presentation day)

- [ ] Neo4j instance `bdbi` is running at `neo4j://127.0.0.1:7687`
- [ ] `movies_cleaned.csv` is in the `data/` folder
- [ ] `03_graph_analytics.ipynb` has been run (pagerank + community written to graph)
- [ ] `05_embeddings.ipynb` has been run (Qdrant collection indexed)
- [ ] Qdrant is running at `localhost:6333`
- [ ] `streamlit run dashboard/app.py` opens without errors
- [ ] All 3 tabs render correctly
- [ ] One team member has walked the full demo path end-to-end

---

## Common Pitfalls to Avoid

- Do NOT cold-start the demo on stage — pre-warm the dashboard before you talk
- Do NOT say "87% accuracy" without citing the baseline — always show the before number
- Do NOT present Scale-Up as a wishlist — anchor every tool choice in the S3/S5 threshold bands
- Run `docker compose down -v && up -d` the day before S8 to verify a clean checkout
