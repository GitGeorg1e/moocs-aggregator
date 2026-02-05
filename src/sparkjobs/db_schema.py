"""
Database Schema for Spark Job Results
SQL queries to create necessary tables for storing Spark job outputs
"""

# ============== TABLE CREATION SCRIPTS ==============

CREATE_SIMILAR_COURSES_TABLE = """
CREATE TABLE IF NOT EXISTS similar_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    similar_course_id INT NOT NULL,
    similarity DECIMAL(5,4) NOT NULL,
    similar_course_title VARCHAR(255),
    similar_course_topic VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_pair UNIQUE(course_id, similar_course_id),
    CONSTRAINT fk_similar_courses_course
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    CONSTRAINT fk_similar_courses_similar
        FOREIGN KEY (similar_course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX idx_similar_courses_course_id ON similar_courses(course_id);
CREATE INDEX idx_similar_courses_similarity ON similar_courses(similarity DESC);
"""

CREATE_COURSE_CLUSTERS_TABLE = """
CREATE TABLE IF NOT EXISTS course_clusters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(255),
    topic VARCHAR(100),
    level VARCHAR(50),
    cluster_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_course_cluster UNIQUE(course_id),
    CONSTRAINT fk_course_clusters_course
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX idx_course_clusters_cluster_id ON course_clusters(cluster_id);
CREATE INDEX idx_course_clusters_topic ON course_clusters(topic);
CREATE INDEX idx_course_clusters_level ON course_clusters(level);
"""

CREATE_ANALYTICS_BY_SOURCE_TABLE = """
CREATE TABLE IF NOT EXISTS analytics_by_source (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT NOT NULL,
    source_name VARCHAR(255),
    num_courses INT,
    num_languages INT,
    num_topics INT,
    num_levels INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_analytics_source
        FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    CONSTRAINT unique_source UNIQUE(source_name)
);

CREATE INDEX idx_analytics_source_name ON analytics_by_source(source_name);
CREATE INDEX idx_analytics_source_id ON analytics_by_source(source_id);
"""

CREATE_ANALYTICS_BY_LANGUAGE_TABLE = """
CREATE TABLE IF NOT EXISTS analytics_by_language (
    id INT AUTO_INCREMENT PRIMARY KEY,
    language VARCHAR(10),
    num_courses INT,
    num_sources INT,
    num_topics INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_language UNIQUE(language)
);

CREATE INDEX idx_analytics_language ON analytics_by_language(language);
"""

CREATE_ANALYTICS_BY_LEVEL_TABLE = """
CREATE TABLE IF NOT EXISTS analytics_by_level (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level VARCHAR(50),
    num_courses INT,
    num_sources INT,
    num_languages INT,
    num_topics INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_level UNIQUE(level)
);

CREATE INDEX idx_analytics_level ON analytics_by_level(level);
"""

CREATE_ANALYTICS_BY_TOPIC_TABLE = """
CREATE TABLE IF NOT EXISTS analytics_by_topic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(100),
    num_courses INT,
    num_sources INT,
    num_languages INT,
    num_levels INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_topic UNIQUE(topic)
);

CREATE INDEX idx_analytics_topic ON analytics_by_topic(topic);
"""

# ============== HELPER QUERIES ==============

QUERY_SIMILAR_COURSES_FOR_COURSE = """
SELECT * FROM similar_courses 
WHERE course_id = %s 
ORDER BY similarity DESC 
LIMIT %s;
"""

QUERY_CLUSTER_COURSES = """
SELECT * FROM course_clusters 
WHERE cluster_id = %s 
ORDER BY similarity DESC;
"""

QUERY_TOP_CLUSTERS_BY_SIZE = """
SELECT cluster_id, COUNT(*) as cluster_size 
FROM course_clusters 
GROUP BY cluster_id 
ORDER BY cluster_size DESC;
"""

QUERY_CLUSTER_STATISTICS = """
SELECT 
    cluster_id,
    COUNT(*) as num_courses,
    COUNT(DISTINCT topic) as num_topics,
    COUNT(DISTINCT level) as num_levels,
    COUNT(DISTINCT source_name) as num_sources
FROM course_clusters c
JOIN courses co ON c.course_id = co.id
GROUP BY cluster_id
ORDER BY num_courses DESC;
"""

# ============== UTILITY FUNCTIONS ==============

def create_all_tables(connection):
    """
    Create all necessary tables for Spark job results.
    
    Args:
        connection: Database connection (PyMySQL or similar)
    """
    cursor = connection.cursor()
    
    tables = [
        CREATE_SIMILAR_COURSES_TABLE,
        CREATE_COURSE_CLUSTERS_TABLE,
        CREATE_ANALYTICS_BY_SOURCE_TABLE,
        CREATE_ANALYTICS_BY_LANGUAGE_TABLE,
        CREATE_ANALYTICS_BY_LEVEL_TABLE,
        CREATE_ANALYTICS_BY_TOPIC_TABLE,
    ]
    
    for create_table_sql in tables:
        try:
            cursor.execute(create_table_sql)
            connection.commit()
            print(f"Created table: {create_table_sql.split('TABLE')[1].split('(')[0].strip()}")
        except Exception as e:
            print(f"Error creating table: {e}")
            connection.rollback()
    
    cursor.close()


if __name__ == "__main__":
    import pymysql
    
    # Example usage
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            database="moocs_db",
            user="moocs_user",
            password="123456789",
            charset="utf8mb4",
        )
        
        create_all_tables(conn)
        conn.close()
        print("All tables created successfully!")
        
    except Exception as e:
        print(f"Database error: {e}")
