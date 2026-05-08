# Scale-Up Reasoning
## BD & BI Capstone — Movie Collaboration Network Analysis
## Techtators Team

---

## 1. Current Setup (Proof of Concept)

| Component | Tool | Scale |
|---|---|---|
| Data Cleaning & ETL | DuckDB (local, in-memory) | 3,146 rows, single CSV |
| Graph Database | Neo4j Desktop (local) | 5,748 nodes, 12,486 relationships |
| ML Pipeline | scikit-learn (single machine) | ~200KB feature matrix |
| Vector Search | Qdrant (local Docker container) | 3,146 embeddings, 384-dim |
| Orchestration | Manual Jupyter notebooks | No scheduling, no monitoring |
| Dashboard | Streamlit (local) | Single user, localhost only |

---

## 2. The 5 Vs of Our Dataset

| V | Description | Our Dataset |
|---|---|---|
| **Volume** | How much data | 3,146 clean movies from 1M raw rows |
| **Velocity** | How fast data arrives | Static snapshot, updated annually on Kaggle |
| **Variety** | How many data types | Structured (ratings, revenue) + Unstructured (overview, tagline) |
| **Veracity** | How trustworthy the data is | Real IMDb + TMDb data, cleaned and validated |
| **Value** | How useful the data is | Directly answers casting decisions for production companies |

---

## 3. ETL — DuckDB vs Apache Spark

### Current: DuckDB (local)
DuckDB is an in-process analytical SQL engine that runs entirely on a single machine. Our working set is approximately 200MB after cleaning, which sits two orders of magnitude below the DuckDB practical ceiling. At this scale, DuckDB dominates on every dimension: sub-second queries, zero infrastructure cost, and a familiar SQL interface.

### Production Alternative: Apache Spark
Apache Spark is the industry standard for distributed data processing. It partitions data across a cluster and runs transformations in parallel, which becomes necessary once the dataset no longer fits in a single machine's RAM.

| Dimension | DuckDB | Apache Spark |
|---|---|---|
| Data volume | < 100 GB single node | 100 GB – multi-TB distributed |
| Query latency | Sub-second (in-process) | Seconds to minutes per job |
| Infrastructure | Laptop, zero ops | Cluster (YARN / Kubernetes) |
| Learning curve | Low (standard SQL) | Moderate (Spark fundamentals) |
| Cost | Free | Cluster compute cost |

**Threshold:** ~100 GB working set is the crossover point. Our 200MB dataset sits well below this band. We would migrate to Spark once the working set crosses ~50 GB, which is well above any plausible 5x growth path of our current dataset.

**Migration path:** The DuckDB SQL cleaning logic maps directly to Spark DataFrame transformations. The ETL steps (filter, cast, calculate ROI) are expressible in PySpark with minimal API changes.

---

## 4. Graph Database — Neo4j Desktop vs Neo4j AuraDB vs Neo4j Enterprise

### Current: Neo4j Desktop (local)
Neo4j Desktop runs a single-instance Neo4j server on the local machine. It handles our graph comfortably (5,748 nodes, 12,486 relationships) with millisecond query times.

### Production Alternative: Neo4j AuraDB → Neo4j Enterprise

| Dimension | Neo4j Desktop | Neo4j AuraDB (Cloud) | Neo4j Enterprise |
|---|---|---|---|
| Deployment | Local machine | Fully managed cloud | Self-hosted cluster |
| Scale | ~millions of nodes | Tens of millions of nodes | Billions of nodes |
| High availability | None | Built-in | Clustering + failover |
| Ops burden | Manual | Zero ops | Moderate |
| Cost | Free | Subscription | License + infrastructure |

**Threshold:** Neo4j Desktop handles our current graph comfortably. At 10x scale (~500K nodes, ~5M relationships), we would migrate to Neo4j AuraDB. At 100x scale (5M+ nodes) with multi-tenant production requirements, Neo4j Enterprise with clustering would be required.

**Migration path:** Connection string change only. All Cypher queries and GDS calls are identical across Desktop, AuraDB, and Enterprise. No code changes required beyond the URI and credentials.

---

## 5. ML Pipeline — scikit-learn vs Spark MLlib

### Current: scikit-learn (single machine)
scikit-learn runs entirely in-process on a single machine. Our feature matrix is approximately 3,146 rows × 12 columns (~200KB), which trains in under one second. scikit-learn is the correct tool at this scale.

### Production Alternative: Spark MLlib
Spark MLlib is the distributed machine learning library built on Apache Spark. It is necessary when the feature matrix no longer fits in a single machine's RAM.

| Dimension | scikit-learn | Spark MLlib |
|---|---|---|
| Data volume | < 100 GB in memory | 100 GB – multi-TB distributed |
| API breadth | Wide (dozens of algorithms) | Narrower (distributed-friendly subset) |
| Predict latency | Microseconds (in-process) | Seconds per Spark job |
| Infrastructure | Pip install, runs on laptop | Cluster (YARN / Kubernetes) |
| Learning curve | Low | Moderate |

**Threshold:** ~100 GB feature matrix is the crossover point. Our ~200KB matrix sits four orders of magnitude below this band. We would migrate to Spark MLlib once the feature matrix crosses ~50 GB.

**Migration path:** The scikit-learn Pipeline shape (ColumnTransformer + RandomForestClassifier) maps to Spark MLlib's Pipeline API with similar step names. The main difference is replacing pandas DataFrames with Spark DataFrames as the input.

---

## 6. Vector Search — Qdrant Local vs Qdrant Cloud

### Current: Qdrant Local (Docker)
Qdrant runs as a single Docker container on the local machine. Our collection holds 3,146 vectors at 384 dimensions, which is trivial for a local instance.

### Production Alternative: Qdrant Cloud

| Dimension | Qdrant Local | Qdrant Cloud |
|---|---|---|
| Vector count | Millions (single node) | Billions (managed cluster) |
| Sharding | None | Automatic |
| Replication | None | Built-in |
| Ops burden | Manual Docker management | Zero ops |
| Cost | Free | Subscription |

**Threshold:** Qdrant local handles up to several million vectors on a single node without performance degradation. At a few million vectors or when multi-tenant deployment is required, Qdrant Cloud is the operational answer.

**Migration path:** Client code is identical. Only the host URL and API key change. No query or upsert code needs to be modified.

---

## 7. Orchestration — Manual Notebooks vs Apache Airflow

### Current: Manual Jupyter notebooks
Each pipeline step is triggered manually in Jupyter. There is no scheduling, error handling, retry logic, or alerting. This is acceptable for a proof-of-concept with a static dataset.

### Production Alternative: Apache Airflow

| Dimension | Manual Jupyter | Apache Airflow |
|---|---|---|
| Scheduling | None (manual) | Cron-based DAGs |
| Error handling | None | Retry + alerting |
| Monitoring | None | Grafana + Prometheus |
| Dependency management | Manual | DAG dependency graph |
| Infrastructure | None | Airflow server + workers |

**Threshold:** Any production deployment with daily or real-time data updates requires orchestration. The most critical upgrade for our pipeline would be automating the ETL → Neo4j load → GDS analytics → ML re-train cycle on a daily schedule tied to box office API updates.

**Migration path:** Each notebook becomes an Airflow PythonOperator or BashOperator inside a DAG. The dependency graph is already implicit in our notebook numbering (01 → 02 → 03 → 04 → 05).

---

## 8. Recommended Scale-Up Path

```
Current (PoC)        →    10x Scale           →    100x Scale
──────────────────────────────────────────────────────────────
DuckDB (local)       →    DuckDB + S3 Parquet  →    Apache Spark
Neo4j Desktop        →    Neo4j AuraDB         →    Neo4j Enterprise
scikit-learn         →    scikit-learn + S3    →    Spark MLlib
Qdrant local         →    Qdrant Cloud         →    Qdrant Cloud (sharded)
Manual Jupyter       →    Apache Airflow       →    Airflow + Kubernetes
Streamlit (local)    →    Streamlit Cloud      →    Custom React + API
```

---

## 9. Conclusion

Our current stack is well suited for exploratory analysis and prototyping at small scale. Every tool choice was made deliberately: DuckDB for fast in-process SQL, Neo4j Desktop for local graph storage, scikit-learn for rapid ML iteration, Qdrant for lightweight vector search, and Streamlit for quick dashboard prototyping.

The natural upgrade path moves from local single-machine tools toward cloud-native distributed systems as data volume and velocity increase. The two most critical upgrades for our specific use case are moving Neo4j to AuraDB (because the collaboration network graph is the core of our analysis and needs to stay current) and automating the pipeline with Airflow (because manual notebook execution is not viable for a production system ingesting daily box office data).
