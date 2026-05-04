# ML and Similarity — Design Document

## Capstone: Movie Collaboration Network Analysis

**Business question:** Which collaboration networks between actors and directors have the greatest impact on the commercial success of films?

---

## 1. Prediction Task

**Target:** `is_blockbuster` — binary classification (revenue > $100M).

**Consumer:** A film production company executive uses the predicted blockbuster probability to decide which director–actor collaboration projects to greenlight before committing budget.

**Features:**
- Tabular: `budget`, `runtime`, `release_year`, `original_language`
- Graph-derived (degree only): `movie_degree`, `actor_degree`, `genre_degree`, `director_total_movies`, `actor_total_movies`, `director_collab_count`

**Excluded (leakage):** `revenue`, `roi`, `imdb_rating`, `vote_count`

**Pipeline:** `train_test_split(stratify=y)` → `Pipeline([ColumnTransformer(StandardScaler + OneHotEncoder), RandomForestClassifier])`

**Baseline metric:** macro-F1 + 5-fold CV, persisted to `data/baseline_metrics.txt`

---

## 2. Text Field for Embedding

**Field:** `overview` (plot summary)

**Why this field:**
- Longest free-text field (mean ≈ 300 chars, ≈ 60 tokens)
- Captures plot semantics, not marketing voice
- `tagline` rejected — too short and stylized
- `overview + tagline` rejected — tagline adds little semantic content

**Chunking:** None — whole-field embedding fits inside the 256-token context

**Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, cosine similarity)

---

## 3. Streamlit Similarity Widget (S7)

**Two input modes:**
- Free-text search (e.g., "a heartwarming family story")
- Movie-to-movie picker (dropdown of all titles)

**Sidebar filters (Qdrant payload-based):**
- IMDb rating slider (0–10)
- Release-year range slider
- Genre multi-select

**Flow:** User input → `model.encode()` → `client.query_points(query_filter=...)` → render top-5 cards

**Card content:** cosine score, title + year, director, lead actor, IMDb rating, first 200 chars of overview

**Ranking:** Descending cosine similarity. In movie-to-movie mode, the seed is filtered out.

---

## 4. Graph-Analytics Columns S6 Will Add

**Merge key:** `node_id` (= movie title)

| Column | Algorithm | Captures |
|---|---|---|
| `director_pagerank` | PageRank | Global influence of the director |
| `actor_pagerank` | PageRank | Global influence of the lead actor |
| `director_betweenness` | Betweenness centrality | Bridge role across actor clusters |
| `collab_community_id` | Louvain | Creative-camp cluster assignment |
| `community_size` | Louvain | Hub vs niche signal |

**Predicted lift direction:** **+3% to +8% macro-F1**

**Reasoning:** The business question is explicitly about *collaboration networks* — global structural position carries signal that local degree counts cannot capture. Degree features already rank competitively in S5; PageRank and community membership should extend this signal meaningfully.

**Trigger interpretations:**
- Lift below +1% → target is more local than expected (budget dominates)
- Lift above +10% → graph features dominate, narrative shifts to "collaboration network drives commercial success"

---

## Hand-off Summary

| Stage | Deliverable | Status |
|---|---|---|
| S5 | `notebooks/04_ml.ipynb` | ✅ |
| S5 | `notebooks/05_embeddings.ipynb` | ✅ |
| S5 | `docs/ml_and_similarity_design.md` | ✅ |
| S6 | `notebooks/03_graph_analytics.ipynb` (compute + join + lift) | ⏳ |
| S7 | Streamlit dashboard with similarity widget | ⏳ |
| S8 | Final Presentation (baseline vs enriched F1) | ⏳ |
