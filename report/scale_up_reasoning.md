# Scale-Up Reasoning
## BD & BI Capstone — Movie Collaboration Network Analysis

---

## Current Setup (Small Scale)

Our current pipeline processes 3,146 movies using the following tools:

| Tool | Role | Current Scale |
|---|---|---|
| DuckDB | Data cleaning + analytical queries | 3,146 rows, single CSV |
| Neo4j Desktop | Graph database | 5,748 nodes, 12,486 relationships |
| Python / Pandas | Data exploration | In-memory processing |
| Jupyter Notebook | Development environment | Local machine |
| GitHub | Version control | Single repo |

---

## The 5 Vs of Our Dataset

| V | Description | Our Dataset |
|---|---|---|
| **Volume** | How much data | 3,146 clean movies from 1M raw rows |
| **Velocity** | How fast data arrives | Static dataset, updated annually on Kaggle |
| **Variety** | How many data types | Structured (ratings, revenue) + Unstructured (overview, tagline) |
| **Veracity** | How trustworthy the data is | Real IMDb + TMDb data, cleaned and validated |
| **Value** | How useful the data is | Directly answers casting decisions for production companies |

---

## Scale-Up Scenarios

### Scenario 1 — 10x Scale (30,000 movies)
If the dataset grows to 30,000 movies with real-time box office updates:

| Tool | Current | Upgrade | Reason |
|---|---|---|---|
| DuckDB | Local CSV | DuckDB + S3 Parquet | Handle larger files efficiently |
| Neo4j Desktop | Local instance | Neo4j AuraDB (Cloud) | Scalable cloud graph database |
| Python | Jupyter Notebook | Scheduled Python scripts | Automate pipeline runs |
| Storage | Local CSV | AWS S3 / Google Cloud Storage | Reliable cloud storage |
| Orchestration | Manual | Apache Airflow | Schedule and monitor pipeline |

### Scenario 2 — 100x Scale (300,000+ movies + streaming data)
If the pipeline needs to process real-time box office data and social media trends:

| Tool | Current | Upgrade | Reason |
|---|---|---|---|
| DuckDB | Local | Apache Spark | Distributed processing for massive datasets |
| Neo4j | Desktop | Neo4j Enterprise Cluster | High availability graph database |
| Streaming | None | Apache Kafka | Real-time data ingestion |
| ML | scikit-learn | Spark MLlib | Distributed machine learning |
| Orchestration | Manual | Apache Airflow + Kubernetes | Container-based pipeline management |
| Monitoring | None | Grafana + Prometheus | Real-time pipeline monitoring |

---

## Current Bottlenecks

### 1. Data Volume
Our raw dataset is 1M rows but we only use 3,146 after cleaning. At scale we would retain more rows by improving cleaning logic rather than dropping sparse records.

### 2. Static Data
Currently the dataset is a one-time snapshot. A real production system would need daily updates from box office APIs like IMDb Pro or The Numbers to keep collaboration ROI figures current.

### 3. Single Machine Processing
DuckDB and Neo4j Desktop both run on a single local machine. For larger datasets this becomes a bottleneck and cloud-based solutions would be required.

### 4. Manual Pipeline
Currently each step is run manually in Jupyter. At scale this would need to be fully automated with scheduling, error handling and alerting.

### 5. Graph Size
Neo4j Desktop handles our current graph comfortably but at 100x scale (500K+ nodes, 2M+ relationships) a clustered Neo4j Enterprise or a distributed graph solution like Amazon Neptune would be needed.

---

## Recommended Scale-Up Path


Current          →    10x Scale        →    100x Scale
─────────────────────────────────────────────────────
DuckDB (local)   →    DuckDB + S3      →    Apache Spark
Neo4j Desktop    →    Neo4j AuraDB     →    Neo4j Enterprise
Jupyter          →    Airflow DAGs     →    Airflow + Kubernetes
Local CSV        →    S3 Parquet       →    Data Lake
Manual runs      →    Scheduled jobs   →    Real-time streaming



---

## Why These Choices

**DuckDB → Spark**: DuckDB is excellent for single-machine analytics but does not distribute across multiple nodes. Apache Spark is the industry standard for distributed data processing.

**Neo4j Desktop → AuraDB → Enterprise**: Neo4j AuraDB is the managed cloud version requiring no infrastructure management. Neo4j Enterprise adds clustering, high availability and advanced security for production workloads.

**CSV → Parquet**: Parquet is a columnar storage format that is 3-5x faster to query and 60-70% smaller than CSV at scale. We already export Parquet in our ETL pipeline.

**Manual → Airflow**: Apache Airflow allows scheduling, monitoring and dependency management for complex data pipelines. It ensures the pipeline runs reliably and alerts on failures.

---

## Conclusion

Our current stack is well suited for exploratory analysis and prototyping at small scale. The natural upgrade path moves from local single-machine tools toward cloud-native distributed systems as data volume and velocity increase. The most critical upgrade for our specific use case would be moving Neo4j to the cloud and automating the pipeline with Airflow, as the collaboration network graph is the core of our analysis and needs to stay current with real-world box office data.