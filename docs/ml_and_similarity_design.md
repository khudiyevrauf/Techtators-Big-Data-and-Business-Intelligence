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
| `pagerank` | PageRank | Global structural importance of the movie node in the collaboration network |
| `community` | Louvain | Creative-cluster assignment (franchise group, genre cluster, studio ecosystem) |

**Predicted lift direction:** **+3% to +8% macro-F1**

**Reasoning:** The business question is explicitly about *collaboration networks* — global structural position carries signal that local degree counts cannot capture. Degree features already rank competitively in S5; PageRank and community membership should extend this signal meaningfully.

**Trigger interpretations:**
- Lift below +1% → target is more local than expected (budget dominates)
- Lift above +10% → graph features dominate, narrative shifts to "collaboration network drives commercial success"

---

## 5. Knowledge Graph Schema (Final)

### Node Types

| Node | Count | Key Properties | Merge Key |
|---|---|---|---|
| `Movie` | 3,114 | `title`, `revenue`, `budget`, `imdb_rating`, `roi`, `overview`, `tagline`, `original_language`, `release_year`, `runtime` | `title` |
| `Director` | 1,400 | `name` | `name` |
| `Actor` | 1,243 | `name` | `name` |
| `Genre` | 991 | `name` | `name` |

### Relationship Types

| Relationship | Count | Direction | Properties |
|---|---|---|---|
| `DIRECTED` | 3,146 | Director → Movie | — |
| `ACTED_IN` | 3,137 | Actor → Movie | — |
| `BELONGS_TO` | 3,144 | Movie → Genre | — |
| `COLLABORATED_WITH` | 3,059 | Director → Actor | `movies` (count), `total_revenue` |

### Uniqueness Constraints

```cypher
CREATE CONSTRAINT movie_title    IF NOT EXISTS FOR (m:Movie)    REQUIRE m.title IS UNIQUE;
CREATE CONSTRAINT director_name  IF NOT EXISTS FOR (d:Director) REQUIRE d.name  IS UNIQUE;
CREATE CONSTRAINT actor_name     IF NOT EXISTS FOR (a:Actor)    REQUIRE a.name  IS UNIQUE;
CREATE CONSTRAINT genre_name     IF NOT EXISTS FOR (g:Genre)    REQUIRE g.name  IS UNIQUE;
```

### Derived Properties (added by S6 — `03_graph_analytics.ipynb`)

| Property | Written To | Algorithm | GDS Call |
|---|---|---|---|
| `pagerank` | All node types | PageRank | `gds.pageRank.write(writeProperty: 'pagerank', maxIterations: 20, dampingFactor: 0.85)` |
| `community` | All node types | Louvain | `gds.louvain.write(writeProperty: 'community', maxLevels: 10, tolerance: 0.0001)` |

### Changes from S2/S3 Schema
- No structural changes to nodes or relationships
- Two new derived properties added to all nodes: `pagerank` (float) and `community` (integer)
- GDS projection uses `UNDIRECTED` orientation for all relationship types to support both PageRank and Louvain on the same projection

---

## 6. Streamlit Data Flow

The Streamlit dashboard (S7) connects to two data sources: **Neo4j** for graph queries and **Qdrant** for vector similarity search.

### Load-Time Queries (run once when dashboard starts)

1. Connect to Neo4j at `neo4j://127.0.0.1:7687`
2. Load top-10 Directors by PageRank → displayed on the home tab as "Most Influential Directors"
3. Load community size distribution → used to populate the community filter dropdown
4. Load all movie titles → used to populate the movie-to-movie similarity picker dropdown
5. Connect to Qdrant at `localhost:6333` and verify the `movies_overview` collection exists

### User-Input Queries (run on each user interaction)

| User Action | Query Type | Tool |
|---|---|---|
| Types a free-text search query | `model.encode(query)` → `client.query_points(limit=5)` | Qdrant |
| Selects a movie from the picker | Retrieve seed embedding → `client.query_points(limit=6, exclude seed)` | Qdrant |
| Applies IMDb rating filter | `client.query_points(query_filter=FieldCondition(imdb_rating >= X))` | Qdrant |
| Applies release-year filter | `client.query_points(query_filter=FieldCondition(release_year in range))` | Qdrant |
| Clicks on a movie card | `MATCH (m:Movie {title: $title}) RETURN m, director, actor, genres` | Neo4j |
| Views collaboration network | `MATCH (d:Director)-[:COLLABORATED_WITH]->(a:Actor) WHERE d.community = $cid RETURN d, a` | Neo4j |

### Background / Cached Queries

- PageRank scores and community labels are pre-computed in `03_graph_analytics.ipynb` and stored as node properties — no re-computation at dashboard runtime
- Qdrant embeddings are pre-indexed in `05_embeddings.ipynb` — no re-encoding at dashboard runtime
- All Neo4j graph queries use indexed properties (`title`, `name`) so no full scans occur

### Data Flow Diagram

```
User Input
    │
    ├── Text query / movie picker
    │       │
    │       └── model.encode() → Qdrant query_points() → Top-5 similar movies
    │
    ├── Movie card click
    │       │
    │       └── Neo4j MATCH → movie details + collaboration network
    │
    └── Community / PageRank view
            │
            └── Neo4j MATCH → top nodes by pagerank / community filter
```

---

## Hand-off Summary

| Stage | Deliverable | Status |
|---|---|---|
| S5 | `notebooks/04_ml.ipynb` | ✅ |
| S5 | `notebooks/05_embeddings.ipynb` | ✅ |
| S5 | `docs/ml_and_similarity_design.md` | ✅ |
| S6 | `notebooks/03_graph_analytics.ipynb` | ✅ |
| S6 | `notebooks/04_ml.ipynb` (enriched + before-after metric) | ✅ |
| S6 | `docs/ml_and_similarity_design.md` (sections 5 + 6 added) | ✅ |
| S7 | Streamlit dashboard with similarity widget | ⏳ |
| S8 | Final Presentation (baseline vs enriched F1) | ⏳ |
