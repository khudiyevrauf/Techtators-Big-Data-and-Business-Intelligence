// ── 0. Find Import Folder Path ────────────────────────────────────────────────
CALL dbms.listConfig() YIELD name, value
WHERE name = 'server.directories.import'
RETURN value;


//  1. Create Constraints
CREATE CONSTRAINT movie_title IF NOT EXISTS
FOR (m:Movie) REQUIRE m.title IS UNIQUE;

CREATE CONSTRAINT director_name IF NOT EXISTS
FOR (d:Director) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT actor_name IF NOT EXISTS
FOR (a:Actor) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT genre_name IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE;

// 2. Load Movie Nodes
LOAD CSV WITH HEADERS FROM 'file:///movies_cleaned.csv' AS row
MERGE (m:Movie {title: row.title})
SET m.release_year       = toInteger(row.release_year),
    m.runtime            = toFloat(row.runtime),
    m.budget             = toFloat(row.budget),
    m.revenue            = toFloat(row.revenue),
    m.imdb_rating        = toFloat(row.imdb_rating),
    m.roi                = toFloat(row.roi),
    m.overview           = row.overview,
    m.tagline            = row.tagline,
    m.original_language  = row.original_language,
    m.release_date       = row.release_date;

// 3. Load Director Nodes + DIRECTED Relationship
LOAD CSV WITH HEADERS FROM 'file:///movies_cleaned.csv' AS row
MERGE (d:Director {name: row.director})
MERGE (m:Movie {title: row.title})
MERGE (d)-[:DIRECTED]->(m);

// 4. Load Actor Nodes + ACTED_IN Relationship
LOAD CSV WITH HEADERS FROM 'file:///movies_cleaned.csv' AS row
MERGE (a:Actor {name: row.actor})
MERGE (m:Movie {title: row.title})
MERGE (a)-[:ACTED_IN]->(m);

// 5. Load Genre Nodes + BELONGS_TO Relationship
LOAD CSV WITH HEADERS FROM 'file:///movies_cleaned.csv' AS row
MERGE (g:Genre {name: row.genres_list})
MERGE (m:Movie {title: row.title})
MERGE (m)-[:BELONGS_TO]->(g);

// 6. Create COLLABORATED_WITH Relationship
LOAD CSV WITH HEADERS FROM 'file:///movies_cleaned.csv' AS row
MATCH (d:Director {name: row.director})
MATCH (a:Actor {name: row.actor})
MERGE (d)-[r:COLLABORATED_WITH]->(a)
ON CREATE SET r.movies = 1,
              r.total_revenue = toFloat(row.revenue)
ON MATCH SET  r.movies = r.movies + 1,
              r.total_revenue = r.total_revenue + toFloat(row.revenue);

//7. Verify Nodes 
MATCH (n) RETURN labels(n), COUNT(n);

// 8. Verify Relationships 
MATCH ()-[r]->() RETURN type(r), COUNT(r);

// 9. Visualize Blockbuster Collaboration Network
MATCH (d:Director)-[:COLLABORATED_WITH]->(a:Actor)
MATCH (d)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a)
WHERE m.revenue > 500000000
RETURN d, a, m
LIMIT 15;

// Another query for showing relationship in more understanding way(Collaborated with)
MATCH (d:Director)-[r:COLLABORATED_WITH]->(a:Actor)
WHERE r.movies >= 3
RETURN d, r, a
LIMIT 20
