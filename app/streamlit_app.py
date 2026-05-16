import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from sentence_transformers import SentenceTransformer
import networkx as nx
from pyvis.network import Network
import tempfile
import os

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Movie Collaboration Network",
    page_icon="🎬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16213e 0%, #0f3460 100%);
        border-right: 1px solid #e94560;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #16213e, #0f3460);
        border: 1px solid #e94560;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.2);
    }
    [data-testid="stMetricValue"] {
        color: #e94560 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #a8b2d8 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    h1 {
        background: linear-gradient(90deg, #e94560, #0f3460);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }
    h2, h3 {
        color: #e94560 !important;
        border-bottom: 2px solid #e94560;
        padding-bottom: 8px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #c23152) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 35px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(233, 69, 96, 0.6) !important;
    }
    .stInfo {
        background: rgba(15, 52, 96, 0.5) !important;
        border-left: 4px solid #e94560 !important;
        border-radius: 8px !important;
    }
    .stSuccess {
        background: rgba(2, 195, 154, 0.1) !important;
        border-left: 4px solid #02C39A !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #0f3460;
        border-radius: 10px;
        overflow: hidden;
    }
    .stSelectbox > div > div {
        background: #16213e !important;
        border: 1px solid #e94560 !important;
        border-radius: 8px !important;
        color: white !important;
    }
    .stSlider > div > div > div {
        background: #e94560 !important;
    }
    .stTextArea > div > div > textarea {
        background: #16213e !important;
        border: 1px solid #e94560 !important;
        border-radius: 8px !important;
        color: white !important;
    }
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #16213e, #0f3460) !important;
        border: 1px solid #e94560 !important;
        border-radius: 8px !important;
        color: white !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI   = os.environ.get("NEO4J_URI",   "neo4j://127.0.0.1:7687")
NEO4J_USER  = os.environ.get("NEO4J_USER",  "neo4j")
NEO4J_PASS  = os.environ.get("NEO4J_PASS",  "Manuvamshi@12")
CLEAN_CSV   = os.environ.get("CLEAN_CSV",   "/Users/manoharnaddunoori/BD&BI_Capstone/data/movies_cleaned.csv")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
COLLECTION  = "movie_overviews"

# ── Cached Connections ────────────────────────────────────────────────────────
@st.cache_resource
def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        return driver
    except Exception as e:
        st.error(f"Neo4j connection failed: {e}")
        return None

@st.cache_resource
def get_qdrant_client():
    try:
        return QdrantClient(host=QDRANT_HOST, port=6333)
    except Exception as e:
        st.error(f"Qdrant connection failed: {e}")
        return None

@st.cache_resource
def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data
def load_movies():
    return pd.read_csv(CLEAN_CSV)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/movie.png", width=80)
st.sidebar.title("🎬 Techtators")
st.sidebar.markdown("**Movie Collaboration Network Analysis**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Overview",
     "🕸️ Collaboration Network",
     "📊 ROI Analysis",
     "🔍 Similarity Search",
     "🤖 ROI Predictor"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Business Question:**")
st.sidebar.info(
    "Which collaboration networks between actors and directors "
    "have the greatest impact on the commercial success of films?"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 1 — Overview
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if page == "🏠 Overview":
    st.title("🎬 Movie Collaboration Network Analysis")
    st.markdown("**Techtators — BD & BI Capstone | SRH University**")
    st.markdown("---")

    # Load data
    df = load_movies()
    driver = get_neo4j_driver()

    if driver is None:
        st.error("Neo4j is not available. Please start Neo4j Desktop.")
        st.stop()

    # Get actual Neo4j movie count
    with driver.session() as session:
        result = session.run("MATCH (m:Movie) RETURN COUNT(m) AS count")
        movie_count = result.single()['count']

    # Hero banner
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #16213e 0%, #0f3460 50%, #e94560 100%);
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(233, 69, 96, 0.3);
    ">
        <h2 style="color: white; font-size: 1.5rem; margin: 0; border: none;">
            🎬 Analyzing {movie_count:,} films across 1,400 directors and 1,243 actors
        </h2>
        <p style="color: #a8b2d8; margin-top: 10px; font-size: 1rem;">
            Powered by Neo4j Graph Database · Qdrant Vector Search · scikit-learn ML
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Movies",    f"{movie_count:,}")
    col2.metric("Avg IMDb Rating", f"{df['imdb_rating'].mean():.2f}")
    col3.metric("Avg ROI",         f"{df['roi'].mean():.0f}%")
    col4.metric("Year Range",      f"{int(df['release_year'].min())}–{int(df['release_year'].max())}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Graph Database Stats")
        with driver.session() as session:
            nodes = session.run(
                "MATCH (n) RETURN labels(n) AS label, COUNT(n) AS count")
            node_df = pd.DataFrame([dict(r) for r in nodes])
            node_df['label'] = node_df['label'].apply(lambda x: x[0])
        st.dataframe(node_df, use_container_width=True)

    with col2:
        st.subheader("🎭 Top Genres by Avg Revenue")
        top_genres = df.groupby('genres_list')['revenue'].mean()\
            .sort_values(ascending=False).head(8).reset_index()
        top_genres.columns = ['Genre', 'Avg Revenue']
        top_genres['Avg Revenue'] = top_genres['Avg Revenue'] / 1e6
        fig = px.bar(top_genres, x='Avg Revenue', y='Genre',
                     orientation='h', color='Avg Revenue',
                     color_continuous_scale='teal',
                     labels={'Avg Revenue': 'Avg Revenue ($M)'},
                     title='Top Genres by Average Revenue ($M)')
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🏆 Top 10 Collaboration Networks by Total Revenue")
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Director)-[r:COLLABORATED_WITH]->(a:Actor)
            WHERE r.movies >= 2
            MATCH (d)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a)
            RETURN d.name AS Director, a.name AS Actor,
                   r.movies AS Films,
                   ROUND(AVG(m.roi), 2) AS Avg_ROI,
                   ROUND(SUM(m.revenue)/1e9, 3) AS Total_Revenue_B,
                   ROUND(AVG(m.imdb_rating), 2) AS Avg_Rating
            ORDER BY Total_Revenue_B DESC
            LIMIT 10
        """)
        top_df = pd.DataFrame([dict(r) for r in result])
    st.dataframe(top_df, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 2 — Collaboration Network
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🕸️ Collaboration Network":
    st.title("🕸️ Collaboration Network Explorer")
    st.markdown("Explore director-actor collaboration networks from the Neo4j graph database.")
    st.markdown("---")

    driver = get_neo4j_driver()
    if driver is None:
        st.error("Neo4j is not available.")
        st.stop()

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Filters")
        min_movies  = st.slider("Min films together", 2, 5, 2)
        min_revenue = st.slider("Min total revenue ($B)", 0.0, 3.0, 0.0, 0.1)
        limit       = st.slider("Max collaborations shown", 10, 50, 20)

    with col2:
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Director)-[r:COLLABORATED_WITH]->(a:Actor)
                WHERE r.movies >= $min_movies
                MATCH (d)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a)
                WITH d.name AS director, a.name AS actor,
                     r.movies AS films,
                     ROUND(SUM(m.revenue)/1e9, 3) AS total_rev,
                     ROUND(AVG(m.roi), 2) AS avg_roi
                WHERE total_rev >= $min_revenue
                RETURN director, actor, films, total_rev, avg_roi
                ORDER BY total_rev DESC
                LIMIT $limit
            """, min_movies=min_movies,
                 min_revenue=min_revenue * 1e9,
                 limit=limit)
            collab_df = pd.DataFrame([dict(r) for r in result])

        if len(collab_df) == 0:
            st.warning("No collaborations found. Try lowering the thresholds.")
        else:
            G = nx.DiGraph()
            for _, row in collab_df.iterrows():
                G.add_node(row['director'], type='director',
                           color='#028090', size=25)
                G.add_node(row['actor'], type='actor',
                           color='#02C39A', size=20)
                G.add_edge(row['director'], row['actor'],
                           weight=row['films'],
                           title=f"Films: {row['films']} | "
                                 f"Revenue: ${row['total_rev']}B | "
                                 f"ROI: {row['avg_roi']}%")

            net = Network(height="500px", width="100%",
                          bgcolor="#0E1117", font_color="white")
            net.from_nx(G)
            net.set_options("""
            var options = {
                "nodes": {"font": {"size": 12}},
                "edges": {"arrows": {"to": {"enabled": true}}},
                "physics": {"stabilization": {"iterations": 100}}
            }
            """)

            with tempfile.NamedTemporaryFile(
                    delete=False, suffix='.html', mode='w') as f:
                net.save_graph(f.name)
                html_file = f.name

            with open(html_file, 'r') as f:
                html_content = f.read()

            st.components.v1.html(html_content, height=520)
            os.unlink(html_file)

    st.markdown("---")
    st.subheader("📋 Collaboration Data")
    if len(collab_df) > 0:
        st.dataframe(collab_df, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 3 — ROI Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📊 ROI Analysis":
    st.title("📊 ROI Analysis")
    st.markdown("Compare ROI with vs without specific director-actor collaborations.")
    st.markdown("---")

    driver = get_neo4j_driver()
    if driver is None:
        st.error("Neo4j is not available.")
        st.stop()

    df = load_movies()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Collaborations by ROI")
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Director)-[r:COLLABORATED_WITH]->(a:Actor)
                WHERE r.movies >= 2
                MATCH (d)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a)
                RETURN d.name AS Director, a.name AS Actor,
                       r.movies AS Films,
                       ROUND(AVG(m.roi), 2) AS Avg_ROI
                ORDER BY Avg_ROI DESC
                LIMIT 10
            """)
            roi_df = pd.DataFrame([dict(r) for r in result])

        roi_df['Label'] = roi_df['Director'] + '\n+ ' + roi_df['Actor']
        fig = px.bar(roi_df, x='Avg_ROI', y='Label',
                     orientation='h',
                     color='Avg_ROI',
                     color_continuous_scale='teal',
                     title='Top 10 Collaborations by Avg ROI (%)',
                     labels={'Avg_ROI': 'Avg ROI (%)', 'Label': ''})
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("With vs Without Actor — ROI Comparison")
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Director)-[r:COLLABORATED_WITH]->(a:Actor)
                WHERE r.movies >= 2
                MATCH (d)-[:DIRECTED]->(m1:Movie)<-[:ACTED_IN]-(a)
                MATCH (d)-[:DIRECTED]->(m2:Movie)
                WHERE NOT (a)-[:ACTED_IN]->(m2)
                WITH d.name AS Director, a.name AS Actor,
                     ROUND(AVG(m1.roi), 2) AS ROI_With,
                     ROUND(AVG(m2.roi), 2) AS ROI_Without
                RETURN Director, Actor, ROI_With, ROI_Without,
                       ROUND(ROI_With - ROI_Without, 2) AS Difference
                ORDER BY Difference DESC
                LIMIT 8
            """)
            with_df = pd.DataFrame([dict(r) for r in result])

        with_df['Label'] = with_df['Director'] + '\n+ ' + with_df['Actor']
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='With Actor',
                              x=with_df['Label'],
                              y=with_df['ROI_With'],
                              marker_color='#028090'))
        fig2.add_trace(go.Bar(name='Without Actor',
                              x=with_df['Label'],
                              y=with_df['ROI_Without'],
                              marker_color='#FF6B6B'))
        fig2.update_layout(barmode='group',
                           title='ROI With vs Without Collaboration',
                           height=450,
                           xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Revenue Trend Over Years")
    yearly = df.groupby('release_year').agg(
        avg_revenue=('revenue', 'mean'),
        total_movies=('title', 'count')
    ).reset_index()
    yearly['avg_revenue_M'] = yearly['avg_revenue'] / 1e6
    fig3 = px.line(yearly, x='release_year', y='avg_revenue_M',
                   title='Average Revenue per Movie Over Years ($M)',
                   labels={'release_year': 'Year',
                           'avg_revenue_M': 'Avg Revenue ($M)'},
                   color_discrete_sequence=['#02C39A'])
    st.plotly_chart(fig3, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 4 — Similarity Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🔍 Similarity Search":
    st.title("🔍 Film Similarity Search")
    st.markdown("Find similar films using semantic search over movie overviews.")
    st.markdown("---")

    client = get_qdrant_client()
    model  = get_embedding_model()

    if client is None:
        st.error("Qdrant is not available. Please start Docker.")
        st.stop()

    query_text = st.text_area(
        "Describe a film concept:",
        placeholder="e.g. two strangers stranded in space must trust each other to survive",
        height=100
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        min_roi    = st.slider("Min ROI (%)", -100, 1000, 0, 50)
    with col2:
        min_rating = st.slider("Min IMDB Rating", 0.0, 10.0, 0.0, 0.5)
    with col3:
        top_k      = st.slider("Number of results", 3, 10, 5)

    if st.button("🔍 Search", type="primary"):
        if query_text.strip():
            with st.spinner("Searching..."):
                query_vector = model.encode(query_text).tolist()
                results = client.query_points(
                    collection_name=COLLECTION,
                    query=query_vector,
                    limit=top_k,
                    with_payload=True,
                    query_filter=Filter(
                        must=[
                            FieldCondition(key='roi',
                                           range=Range(gte=min_roi)),
                            FieldCondition(key='imdb_rating',
                                           range=Range(gte=min_rating))
                        ]
                    )
                )

            st.markdown("---")
            st.subheader(f"Top {top_k} Similar Films")

            for i, hit in enumerate(results.points):
                with st.expander(
                    f"#{i+1} — {hit.payload['title']} "
                    f"(Score: {hit.score:.4f})", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("IMDB Rating", hit.payload['imdb_rating'])
                    col2.metric("ROI",         f"{hit.payload['roi']}%")
                    col3.metric("Revenue",
                                f"${hit.payload['revenue']/1e6:.0f}M")
                    col4.metric("Similarity",  f"{hit.score:.3f}")

                    st.markdown(
                        f"**Director:** {hit.payload['director']} "
                        f"| **Actor:** {hit.payload['actor']}")
                    st.markdown(f"**Genre:** {hit.payload['genre']}")
                    st.markdown(
                        f"**Overview:** {hit.payload['raw_text'][:300]}...")

                    roi = hit.payload['roi']
                    if roi > 200:
                        st.success("✅ High ROI — Strong investment candidate")
                    elif roi > 0:
                        st.warning("⚠️ Moderate ROI — Proceed with caution")
                    else:
                        st.error("❌ Negative ROI — High risk")
        else:
            st.warning("Please enter a film concept to search.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 5 — ROI Predictor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🤖 ROI Predictor":
    st.title("🤖 Collaboration ROI Predictor")
    st.markdown("Predict whether a director-actor collaboration will achieve high ROI.")
    st.markdown("---")

    df = load_movies()

    col1, col2 = st.columns(2)
    with col1:
        director = st.selectbox("Select Director",
                                sorted(df['director'].unique()))
    with col2:
        actor = st.selectbox("Select Actor",
                             sorted(df['actor'].unique()))

    if st.button("🎯 Predict ROI", type="primary"):
        director_movies = df[df['director'] == director]
        actor_movies    = df[df['actor'] == actor]
        shared_movies   = df[(df['director'] == director) &
                             (df['actor'] == actor)]

        col1, col2, col3 = st.columns(3)
        col1.metric("Director's Avg ROI",
                    f"{director_movies['roi'].mean():.0f}%")
        col2.metric("Actor's Avg ROI",
                    f"{actor_movies['roi'].mean():.0f}%")
        col3.metric("Shared Films", f"{len(shared_movies)}")

        if len(shared_movies) > 0:
            avg_roi = shared_movies['roi'].mean()
            st.markdown("---")
            st.subheader("📊 Historical Collaboration Performance")
            st.dataframe(
                shared_movies[['title', 'release_year', 'revenue',
                               'roi', 'imdb_rating']],
                use_container_width=True
            )
            if avg_roi > 200:
                st.success(
                    f"✅ Strong collaboration — Avg ROI: {avg_roi:.0f}%")
            elif avg_roi > 0:
                st.warning(
                    f"⚠️ Moderate collaboration — Avg ROI: {avg_roi:.0f}%")
            else:
                st.error(
                    f"❌ Weak collaboration — Avg ROI: {avg_roi:.0f}%")
        else:
            st.info("No shared films found. This would be a new collaboration.")
            avg_director_roi = director_movies['roi'].mean()
            avg_actor_roi    = actor_movies['roi'].mean()
            predicted_roi    = (avg_director_roi + avg_actor_roi) / 2
            st.metric(
                "Predicted ROI (avg of individual performance)",
                f"{predicted_roi:.0f}%")