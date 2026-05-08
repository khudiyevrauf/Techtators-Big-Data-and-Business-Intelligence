"""
dashboard/app.py
Movie Collaboration Network Analysis — Streamlit Dashboard
BD & BI Capstone — Techtators
"""

import streamlit as st
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import warnings
warnings.filterwarnings('ignore')

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Movie Collaboration Network",
    page_icon="🎬",
    layout="wide",
)

# ── Constants ──────────────────────────────────────────────────
NEO4J_URI   = "neo4j://127.0.0.1:7687"
NEO4J_USER  = "neo4j"
NEO4J_PASS  = "Manuvamshi@12"
CLEAN_CSV   = "../data/movies_cleaned.csv"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION  = "movies_overview"
MODEL_NAME  = "all-MiniLM-L6-v2"

# ── Helpers ────────────────────────────────────────────────────

@st.cache_resource
def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        driver.verify_connectivity()
        return driver, True
    except Exception as e:
        return None, False

@st.cache_data
def load_movies_csv():
    try:
        df = pd.read_csv(CLEAN_CSV)
        return df, True
    except Exception:
        try:
            df = pd.read_csv("data/movies_cleaned.csv")
            return df, True
        except Exception:
            return pd.DataFrame(), False

@st.cache_resource
def get_qdrant_client():
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=3)
        client.get_collections()
        return client, True
    except Exception:
        return None, False

@st.cache_resource
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
        return model, True
    except Exception:
        return None, False

def run_neo4j_query(driver, query, params=None):
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return pd.DataFrame([dict(r) for r in result]), True
    except Exception as e:
        return pd.DataFrame(), False

# ── Load resources ─────────────────────────────────────────────
driver, neo4j_ok  = get_neo4j_driver()
movies_df, csv_ok = load_movies_csv()
qdrant, qdrant_ok = get_qdrant_client()
emb_model, emb_ok = get_embedding_model()

# ── Header ─────────────────────────────────────────────────────
st.title("🎬 Movie Collaboration Network Analysis")
st.markdown("**BD & BI Capstone — Techtators**  |  Which director-actor collaborations drive commercial success?")

# Status bar
col1, col2, col3 = st.columns(3)
col1.metric("Neo4j", "🟢 Connected" if neo4j_ok else "🔴 Offline")
col2.metric("Data", f"🟢 {len(movies_df):,} movies" if csv_ok else "🔴 No CSV")
col3.metric("Qdrant", "🟢 Connected" if qdrant_ok else "🟡 Offline (similarity disabled)")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🏆 Top Collaborations",
    "📈 ROI Analysis",
    "🔍 Similarity Search",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — Top Collaborations
# ══════════════════════════════════════════════════════════════
with tab1:
    st.header("Top Collaboration Networks")
    st.markdown("Directors and actors ranked by total revenue and structural importance (PageRank).")

    col_a, col_b = st.columns(2)

    # ── Top Directors by PageRank ──────────────────────────────
    with col_a:
        st.subheader("Most Influential Directors (PageRank)")

        if neo4j_ok:
            df_pr, ok = run_neo4j_query(driver, """
                MATCH (d:Director)
                WHERE d.pagerank IS NOT NULL
                RETURN d.name              AS Director,
                       ROUND(d.pagerank, 4) AS PageRank
                ORDER BY PageRank DESC
                LIMIT 10
            """)
            if ok and not df_pr.empty:
                st.dataframe(df_pr, use_container_width=True, hide_index=True)
            else:
                st.info("PageRank not computed yet. Run 03_graph_analytics.ipynb first.")
        else:
            st.warning("Neo4j offline. Showing top directors by revenue from CSV.")
            if csv_ok:
                top_dirs = (
                    movies_df.groupby("director")["revenue"]
                    .sum()
                    .reset_index()
                    .rename(columns={"director": "Director", "revenue": "Total Revenue"})
                    .sort_values("Total Revenue", ascending=False)
                    .head(10)
                )
                top_dirs["Total Revenue"] = top_dirs["Total Revenue"].apply(lambda x: f"${x/1e6:.0f}M")
                st.dataframe(top_dirs, use_container_width=True, hide_index=True)

    # ── Top Collaborations by Revenue ─────────────────────────
    with col_b:
        st.subheader("Top Director-Actor Pairs by Revenue")

        if neo4j_ok:
            df_collab, ok = run_neo4j_query(driver, """
                MATCH (d:Director)-[c:COLLABORATED_WITH]->(a:Actor)
                RETURN d.name                          AS Director,
                       a.name                          AS Actor,
                       c.movies                        AS Films,
                       ROUND(c.total_revenue/1e6, 1)   AS Revenue_M
                ORDER BY Revenue_M DESC
                LIMIT 10
            """)
            if ok and not df_collab.empty:
                st.dataframe(df_collab, use_container_width=True, hide_index=True)
            else:
                st.info("COLLABORATED_WITH relationships not found. Run 02_graph_load.ipynb first.")
        else:
            if csv_ok:
                top_pairs = (
                    movies_df.groupby(["director", "actor"])
                    .agg(films=("title", "count"), revenue=("revenue", "sum"))
                    .reset_index()
                    .rename(columns={"director": "Director", "actor": "Actor",
                                     "films": "Films", "revenue": "Revenue_M"})
                    .sort_values("Revenue_M", ascending=False)
                    .head(10)
                )
                top_pairs["Revenue_M"] = top_pairs["Revenue_M"].apply(lambda x: f"${x/1e6:.0f}M")
                st.dataframe(top_pairs, use_container_width=True, hide_index=True)

    st.divider()

    # ── Community Clusters ─────────────────────────────────────
    st.subheader("Collaboration Communities (Louvain)")

    if neo4j_ok:
        df_comm, ok = run_neo4j_query(driver, """
            MATCH (n)
            WHERE n.community IS NOT NULL
            RETURN n.community AS Community,
                   COUNT(n)    AS Members
            ORDER BY Members DESC
            LIMIT 10
        """)
        if ok and not df_comm.empty:
            col_x, col_y = st.columns([1, 2])
            with col_x:
                st.dataframe(df_comm, use_container_width=True, hide_index=True)
            with col_y:
                st.bar_chart(df_comm.set_index("Community")["Members"])
        else:
            st.info("Community detection not run yet. Run 03_graph_analytics.ipynb first.")
    else:
        st.warning("Neo4j offline. Community data requires a live Neo4j connection.")


# ══════════════════════════════════════════════════════════════
# TAB 2 — ROI Analysis
# ══════════════════════════════════════════════════════════════
with tab2:
    st.header("ROI Analysis")
    st.markdown("How does repeated director-actor collaboration affect return on investment?")

    if not csv_ok:
        st.error("movies_cleaned.csv not found. Please check the data path.")
    else:
        # ── Key stats ──────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Movies",   f"{len(movies_df):,}")
        m2.metric("Avg Revenue",    f"${movies_df['revenue'].mean()/1e6:.0f}M")
        m3.metric("Avg ROI",        f"{movies_df['roi'].median():.0f}%")
        m4.metric("Blockbusters",   f"{(movies_df['revenue'] > 1e8).sum():,}")

        st.divider()

        col_left, col_right = st.columns(2)

        # ── ROI with vs without collaboration ─────────────────
        with col_left:
            st.subheader("ROI: With vs Without Collaboration")

            collab_counts = movies_df.groupby("director")["actor"].nunique()
            multi_collab  = collab_counts[collab_counts > 1].index

            movies_df["collab_type"] = movies_df["director"].apply(
                lambda d: "Repeated Collaboration" if d in multi_collab else "One-off Pairing"
            )

            roi_comparison = (
                movies_df.groupby("collab_type")["roi"]
                .median()
                .reset_index()
                .rename(columns={"collab_type": "Type", "roi": "Median ROI (%)"})
            )
            st.dataframe(roi_comparison, use_container_width=True, hide_index=True)
            st.bar_chart(roi_comparison.set_index("Type")["Median ROI (%)"])

        # ── Top ROI collaborations ─────────────────────────────
        with col_right:
            st.subheader("Top Collaborations by ROI")

            top_roi = (
                movies_df[movies_df["roi"] > 0]
                .groupby(["director", "actor"])
                .agg(
                    films        = ("title",  "count"),
                    avg_roi      = ("roi",     "mean"),
                    total_rev    = ("revenue", "sum"),
                )
                .reset_index()
                .query("films >= 2")
                .sort_values("avg_roi", ascending=False)
                .head(10)
            )
            top_roi["avg_roi"]   = top_roi["avg_roi"].round(0).astype(int).astype(str) + "%"
            top_roi["total_rev"] = top_roi["total_rev"].apply(lambda x: f"${x/1e6:.0f}M")
            top_roi.columns      = ["Director", "Actor", "Films", "Avg ROI", "Total Revenue"]
            st.dataframe(top_roi, use_container_width=True, hide_index=True)

        st.divider()

        # ── Genre ROI ──────────────────────────────────────────
        st.subheader("Genre Combinations by Avg Revenue")

        genre_rev = (
            movies_df.groupby("genres_list")
            .agg(avg_revenue=("revenue", "mean"), count=("title", "count"))
            .reset_index()
            .query("count >= 5")
            .sort_values("avg_revenue", ascending=False)
            .head(10)
        )
        genre_rev["avg_revenue"] = genre_rev["avg_revenue"].apply(lambda x: f"${x/1e6:.0f}M")
        genre_rev.columns = ["Genre Combination", "Avg Revenue", "Films"]
        st.dataframe(genre_rev, use_container_width=True, hide_index=True)

        # ── Interactive filter ─────────────────────────────────
        st.divider()
        st.subheader("Explore by Director")

        directors = sorted(movies_df["director"].dropna().unique().tolist())
        selected  = st.selectbox("Select a Director", directors)

        if selected:
            dir_movies = movies_df[movies_df["director"] == selected][
                ["title", "release_year", "actor", "revenue", "roi", "genres_list"]
            ].sort_values("revenue", ascending=False)
            dir_movies["revenue"] = dir_movies["revenue"].apply(lambda x: f"${x/1e6:.0f}M")
            dir_movies["roi"]     = dir_movies["roi"].apply(lambda x: f"{x:.0f}%")
            dir_movies.columns    = ["Title", "Year", "Actor", "Revenue", "ROI", "Genre"]
            st.dataframe(dir_movies, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# TAB 3 — Similarity Search
# ══════════════════════════════════════════════════════════════
with tab3:
    st.header("Movie Similarity Search")
    st.markdown("Find movies with similar plot descriptions using semantic embeddings (Qdrant + sentence-transformers).")

    if not qdrant_ok or not emb_ok:
        st.warning("""
        **Qdrant or embedding model not available.**

        To enable similarity search:
        1. Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
        2. Run `notebooks/05_embeddings.ipynb` to index the movies
        3. Restart this dashboard
        """)

        if csv_ok:
            st.divider()
            st.subheader("Keyword Search (fallback)")
            keyword = st.text_input("Search movie overviews by keyword")
            if keyword:
                mask    = movies_df["overview"].str.contains(keyword, case=False, na=False)
                results = movies_df[mask][["title", "release_year", "director", "actor", "genres_list", "overview"]].head(10)
                if results.empty:
                    st.info("No movies found with that keyword.")
                else:
                    for _, row in results.iterrows():
                        with st.expander(f"🎬 {row['title']} ({int(row['release_year'])})"):
                            st.write(f"**Director:** {row['director']}  |  **Actor:** {row['actor']}")
                            st.write(f"**Genre:** {row['genres_list']}")
                            st.write(f"**Overview:** {row['overview'][:300]}...")
    else:
        # ── Search mode ────────────────────────────────────────
        search_mode = st.radio(
            "Search mode",
            ["Free-text search", "Movie-to-movie"],
            horizontal=True,
        )

        # ── Sidebar filters ────────────────────────────────────
        with st.sidebar:
            st.header("Filters")
            year_range  = st.slider("Release year", 1990, 2024, (1990, 2024))
            rating_min  = st.slider("Min IMDb rating", 0.0, 10.0, 0.0, 0.5)
            top_k       = st.slider("Results to show", 3, 10, 5)

        from qdrant_client.models import Filter, FieldCondition, Range

        query_filter = Filter(must=[
            FieldCondition(key="release_year", range=Range(gte=year_range[0], lte=year_range[1])),
            FieldCondition(key="imdb_rating",  range=Range(gte=rating_min)),
        ])

        if search_mode == "Free-text search":
            query_text = st.text_input("Describe the movie you're looking for",
                                       placeholder="e.g. a space adventure with aliens and intergalactic battles")
            search_btn = st.button("Search", type="primary")

            if search_btn and query_text:
                with st.spinner("Searching..."):
                    query_vec = emb_model.encode(query_text).tolist()
                    results   = qdrant.query_points(
                        collection_name=COLLECTION,
                        query=query_vec,
                        query_filter=query_filter,
                        limit=top_k,
                        with_payload=True,
                    )

                st.subheader(f"Top {top_k} results for: *{query_text}*")
                for rank, hit in enumerate(results.points, 1):
                    p = hit.payload
                    with st.expander(f"#{rank}  {p.get('node_id', 'Unknown')} ({p.get('release_year', '')})  —  score: {hit.score:.4f}"):
                        st.write(f"**Director:** {p.get('director', 'N/A')}  |  **Actor:** {p.get('actor', 'N/A')}")
                        st.write(f"**Genre:** {p.get('genres_list', 'N/A')}  |  **IMDb:** {p.get('imdb_rating', 'N/A')}")
                        st.write(f"**Overview:** {str(p.get('raw_text', ''))[:300]}...")

        else:
            if csv_ok:
                titles     = sorted(movies_df["title"].dropna().unique().tolist())
                seed_title = st.selectbox("Select a movie", titles)
                search_btn = st.button("Find similar movies", type="primary")

                if search_btn and seed_title:
                    seed_row = movies_df[movies_df["title"] == seed_title]
                    if seed_row.empty:
                        st.error("Movie not found in dataset.")
                    else:
                        seed_text = seed_row.iloc[0]["overview"]
                        with st.spinner("Searching..."):
                            seed_vec = emb_model.encode(str(seed_text)).tolist()
                            results  = qdrant.query_points(
                                collection_name=COLLECTION,
                                query=seed_vec,
                                query_filter=query_filter,
                                limit=top_k + 1,
                                with_payload=True,
                            )

                        st.subheader(f"Movies similar to: *{seed_title}*")
                        rank = 0
                        for hit in results.points:
                            if hit.payload.get("node_id") == seed_title:
                                continue
                            rank += 1
                            p = hit.payload
                            with st.expander(f"#{rank}  {p.get('node_id', 'Unknown')} ({p.get('release_year', '')})  —  score: {hit.score:.4f}"):
                                st.write(f"**Director:** {p.get('director', 'N/A')}  |  **Actor:** {p.get('actor', 'N/A')}")
                                st.write(f"**Genre:** {p.get('genres_list', 'N/A')}  |  **IMDb:** {p.get('imdb_rating', 'N/A')}")
                                st.write(f"**Overview:** {str(p.get('raw_text', ''))[:300]}...")
                            if rank >= top_k:
                                break

# ── Footer ─────────────────────────────────────────────────────
st.divider()
st.caption("Movie Collaboration Network Analysis  |  Techtators — BD & BI Capstone 2024  |  Neo4j + DuckDB + Qdrant + scikit-learn")
