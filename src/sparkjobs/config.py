"""
Spark Jobs Configuration Module
"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class SparkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Spark settings
    spark_app_name: str = "MOOCs-Aggregator-Spark"
    spark_master: str = "local[*]"

    # Database settings (MySQL)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "moocs_user"
    db_password: str = "123456789"
    db_name: str = "moocs_db"

    # ML settings
    min_tf_idf_features: int = 100
    num_clusters: int = 10
    similarity_threshold: float = 0.3
    top_n_similar_courses: int = 5

    # Output paths
    spark_output_dir: str = "/tmp/spark_output"
    spark_checkpoint_dir: str = "/tmp/spark_checkpoint"


settings = SparkSettings()


class SparkConfig:
    """Configuration for Spark jobs."""
    
    # Spark settings
    APP_NAME = settings.spark_app_name
    MASTER = settings.spark_master
    
    # Database settings (MySQL)
    DB_HOST = settings.db_host
    DB_PORT = settings.db_port
    DB_USER = settings.db_user
    DB_PASSWORD = settings.db_password
    DB_NAME = settings.db_name
    
    # Database connection string (for JDBC)
    DB_JDBC_URL = f"jdbc:mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DB_JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
    
    # SQLAlchemy connection string (MySQL)
    DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # ML settings
    MIN_TF_IDF_FEATURES = settings.min_tf_idf_features
    NUM_CLUSTERS = settings.num_clusters
    SIMILARITY_THRESHOLD = settings.similarity_threshold
    TOP_N_SIMILAR_COURSES = settings.top_n_similar_courses
    
    # Output paths
    OUTPUT_DIR = settings.spark_output_dir
    CHECKPOINT_DIR = settings.spark_checkpoint_dir
    
    # Model paths
    TFIDF_MODEL_PATH = os.path.join(OUTPUT_DIR, "tfidf_model")
    SIMILARITY_RESULTS_PATH = os.path.join(OUTPUT_DIR, "similarity_results")
    CLUSTERING_RESULTS_PATH = os.path.join(OUTPUT_DIR, "clustering_results")
    ANALYTICS_RESULTS_PATH = os.path.join(OUTPUT_DIR, "analytics_results")
    
    @staticmethod
    def get_spark_config() -> dict:
        """Get Spark configuration dictionary."""
        return {
            "spark.app.name": SparkConfig.APP_NAME,
            "spark.master": SparkConfig.MASTER,
            "spark.sql.shuffle.partitions": "200",
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
        }
