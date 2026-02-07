"""
Spark Jobs Configuration.

All settings are read from environment variables / ``.env`` file.
Access them via the module-level ``SparkConfig`` instance::

    from sparkjobs.config import SparkConfig

    SparkConfig.APP_NAME
    SparkConfig.DB_URL
    SparkConfig.SIMILARITY_THRESHOLD
"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class _SparkSettings(BaseSettings):
    """Internal settings loader — prefer using ``SparkConfig`` below."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Spark
    spark_app_name: str = "MOOCs-Aggregator-Spark"
    spark_master: str = "local[*]"

    # Database (MySQL)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "moocs_user"
    db_password: str = "123456789"
    db_name: str = "moocs_db"

    # ML parameters
    min_tf_idf_features: int = 100
    num_clusters: int = 10
    similarity_threshold: float = 0.3
    top_n_similar_courses: int = 5

    # Output paths
    spark_output_dir: str = "/tmp/spark_output"
    spark_checkpoint_dir: str = "/tmp/spark_checkpoint"


_settings = _SparkSettings()


class SparkConfig:
    """
    Public, read-only configuration namespace used by every Spark job.

    Derived values (JDBC URL, model paths, …) are computed once at import
    time so they stay consistent across the whole pipeline.
    """

    # ── Spark ──────────────────────────────────────────────────────────
    APP_NAME: str = _settings.spark_app_name
    MASTER: str = _settings.spark_master

    # ── Database ───────────────────────────────────────────────────────
    DB_HOST: str = _settings.db_host
    DB_PORT: int = _settings.db_port
    DB_USER: str = _settings.db_user
    DB_PASSWORD: str = _settings.db_password
    DB_NAME: str = _settings.db_name

    DB_JDBC_URL: str = f"jdbc:mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DB_JDBC_DRIVER: str = "com.mysql.cj.jdbc.Driver"
    DB_URL: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # ── ML ─────────────────────────────────────────────────────────────
    MIN_TF_IDF_FEATURES: int = _settings.min_tf_idf_features
    NUM_CLUSTERS: int = _settings.num_clusters
    SIMILARITY_THRESHOLD: float = _settings.similarity_threshold
    TOP_N_SIMILAR_COURSES: int = _settings.top_n_similar_courses

    # ── Output / model paths ──────────────────────────────────────────
    OUTPUT_DIR: str = _settings.spark_output_dir
    CHECKPOINT_DIR: str = _settings.spark_checkpoint_dir

    TFIDF_MODEL_PATH: str = os.path.join(OUTPUT_DIR, "tfidf_model")
    SIMILARITY_RESULTS_PATH: str = os.path.join(OUTPUT_DIR, "similarity_results")
    CLUSTERING_RESULTS_PATH: str = os.path.join(OUTPUT_DIR, "clustering_results")
    ANALYTICS_RESULTS_PATH: str = os.path.join(OUTPUT_DIR, "analytics_results")

    @staticmethod
    def get_spark_config() -> dict:
        """Return a dict suitable for ``SparkSession.builder.config(...)``."""
        return {
            "spark.app.name": SparkConfig.APP_NAME,
            "spark.master": SparkConfig.MASTER,
            "spark.sql.shuffle.partitions": "200",
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
        }
