# ML + Similarity Design Document
## Techtators — BD & BI Capstone

---

## 1. Prediction Task

**Target:** Binary classification — whether a director-actor collaboration
will achieve high ROI (above 200% threshold) or low ROI.

**Who consumes the prediction:** A production company executive uses the
predicted ROI category to decide whether to greenlight a new film project
with a specific director-actor pairing.

**One sentence:**
> "A production company executive uses the predicted ROI category to decide
> whether to invest in a specific director-actor collaboration before
> greenlighting a new film."

**Model:** Random Forest Classifier with class_weight='balanced'

**Baseline Results:**
- Overall Accuracy: 81%
- High ROI Precision: 1.00 (every predicted high ROI was correct)
- High ROI Recall: 0.50 (catches 50% of actual high ROI cases)
- Macro F1: 0.77

**Known Limitation:** Test set contains only 16 samples due to the small
number of director-actor pairs with 2+ collaborations. S6 graph features
are expected to improve recall significantly.

---

## 2. Text Field for Embedding

**Field chosen:** Movie.overview

**Why this field over alternatives:**

| Field | Decision | Reason |
|---|---|---|
| overview | Selected | Full plot summary, avg 272 chars, rich semantic content |
| tagline |  Not used | Too short, adds noise rather than value |
| genres_list |  Not used | Structured categorical data, not free text |
| keywords |  Not used | Too short, keyword lists lack semantic depth |

**Average text length:** ~272 characters per overview — well within
the all-MiniLM-L6-v2 512-token limit. No chunking required.

**Model used:** sentence-transformers/all-MiniLM-L6-v2
**Vector size:** 384 dimensions
**Distance metric:** Cosine similarity
**Total vectors:** 3,146 movie embeddings

---

## 3. Similarity Widget in Streamlit

**User Journey:**

A film curator or production company analyst opens the Streamlit dashboard
and navigates to the "Find Similar Films" tab. They paste a free-text
concept description into a text input box — for example: "two strangers
stranded in space must trust each other to survive". The system embeds
this query using the same all-MiniLM-L6-v2 model and queries the Qdrant
collection for the 5 most similar movies ranked by cosine similarity score.

The dashboard displays each result as a card showing the movie title,
director, actor, genre, IMDB rating, ROI percentage, and similarity score.
The user can apply payload-based filters on the right side panel to narrow
results — available filters include minimum ROI threshold (e.g. ROI >= 200%),
minimum IMDB rating (e.g. >= 7.0), genre filter (e.g. Action only), and
release year range (e.g. 2000–2024). This allows the curator to find not
just semantically similar films but commercially validated comparable titles
for pricing and positioning decisions.

**Ranking:** Results are ranked by cosine similarity score (0 to 1).
Higher score = more semantically similar plot and theme.

**Filters available (Qdrant payload-based):**
- roi — minimum ROI threshold
- imdb_rating — minimum rating
- genres_list — genre match
- release_year — year range
- director — specific director search

---

## 4. Graph-Analytics Columns S6 Will Add

S6 will compute the following columns via Neo4j GDS and join them onto
the baseline feature matrix using node_id (director name) as the merge key.

| Column | Source | Description | Expected Lift |
|---|---|---|---|
| pagerank_score | GDS PageRank | Importance of director in collaboration network | Higher PageRank directors likely produce higher ROI |
| betweenness_centrality | GDS Betweenness | How often director acts as bridge between communities | Bridge directors connect diverse talent = higher ROI |
| community_id | GDS Louvain | Which collaboration cluster the director belongs to | Adds categorical signal for community-based patterns |
| degree_centrality | GDS Degree | Normalized degree in collaboration network | More connected directors = more proven networks |

**Merge key:** node_id (director name — consistent with 04_ml.ipynb)

**Expected lift:** Adding PageRank and community ID is expected to improve
High ROI recall from 0.50 to approximately 0.65-0.75, as directors who are
central in the collaboration network historically produce more commercially
successful films. The baseline model already achieves 1.00 precision on
High ROI — S6 features should improve recall without sacrificing precision.

**S6 notebook:** notebooks/03_graph_analytics.ipynb

**S6 merge operation:**
df_s6 = baseline_df.merge(gds_features_df, how='left', on='node_id')