"""
Spark Utilities Module - Without JDBC Dependency
Common functions for Spark jobs using SQLAlchemy for database operations
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, split, lower, regexp_replace, concat_ws
from typing import Dict, List, Optional
from .config import SparkConfig
import logging
import pandas as pd
from sqlalchemy import create_engine, text
import math

logger = logging.getLogger(__name__)


class SparkSessionManager:
    """Manager for creating and managing Spark sessions."""
    
    _instance: Optional[SparkSession] = None
    
    @staticmethod
    def get_or_create_spark_session(app_name: str = SparkConfig.APP_NAME) -> SparkSession:
        """
        Get or create a Spark session.
        
        Args:
            app_name: Application name for Spark
            
        Returns:
            SparkSession instance
        """
        if SparkSessionManager._instance is None:
            try:
                builder = SparkSession.builder \
                    .appName(app_name) \
                    .config("spark.sql.shuffle.partitions", "200") \
                    .config("spark.sql.adaptive.enabled", "true")
                
                SparkSessionManager._instance = builder.getOrCreate()
                logger.info(f"Created Spark session: {app_name}")
            except Exception as e:
                logger.error(f"Error creating Spark session: {e}")
                raise
        
        return SparkSessionManager._instance
    
    @staticmethod
    def stop_spark_session():
        """Stop the Spark session."""
        if SparkSessionManager._instance is not None:
            try:
                SparkSessionManager._instance.stop()
                SparkSessionManager._instance = None
                logger.info("Stopped Spark session")
            except Exception as e:
                logger.error(f"Error stopping Spark session: {e}")


class DataFrameLoader:
    """Utility class for loading data from various sources."""
    
    @staticmethod
    def read_courses_from_db(spark: SparkSession) -> DataFrame:
        """
        Read courses from MySQL database using SQLAlchemy + Pandas.
        
        Args:
            spark: SparkSession
            
        Returns:
            DataFrame with courses
        """
        try:
            engine = create_engine(SparkConfig.DB_URL)
            
            with engine.connect() as conn:
                query = text(
                    """
                    SELECT
                        c.*,
                        s.name AS source_name
                    FROM courses c
                    LEFT JOIN sources s ON s.id = c.source_id
                    """
                )
                df_pandas = pd.read_sql(query, conn)
            
            # Replace NaN with None for proper null handling
            df_pandas = df_pandas.where(pd.notna(df_pandas), None)
            
            # Define schema explicitly to handle NULL values
            from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType, TimestampType
            schema = StructType([
                StructField("id", IntegerType(), False),
                StructField("source_id", IntegerType(), False),
                StructField("source_course_id", StringType(), False),
                StructField("title", StringType(), False),
                StructField("short_description", StringType(), True),
                StructField("full_description", StringType(), True),
                StructField("keywords", StringType(), True),
                StructField("topic", StringType(), True),
                StructField("language", StringType(), True),
                StructField("level", StringType(), True),
                StructField("course_url", StringType(), False),
                StructField("enrollment_url", StringType(), True),
                StructField("image_url", StringType(), True),
                StructField("last_updated_at_source", TimestampType(), True),
                StructField("created_at", TimestampType(), False),
                StructField("updated_at", TimestampType(), False),
                StructField("source_name", StringType(), True),
            ])
            
            df = spark.createDataFrame(df_pandas, schema=schema)
            logger.info(f"Loaded {df.count()} courses from database")
            return df
        except Exception as e:
            logger.error(f"Error loading courses from database: {e}")
            raise
    
    @staticmethod
    def read_csv(spark: SparkSession, path: str, header: bool = True) -> DataFrame:
        """
        Read data from CSV file.
        
        Args:
            spark: SparkSession
            path: Path to CSV file
            header: Whether first row is header
            
        Returns:
            DataFrame
        """
        return spark.read.csv(path, header=header, inferSchema=True)
    
    @staticmethod
    def read_json(spark: SparkSession, path: str) -> DataFrame:
        """
        Read data from JSON file.
        
        Args:
            spark: SparkSession
            path: Path to JSON file
            
        Returns:
            DataFrame
        """
        return spark.read.json(path)


class TextPreprocessor:
    """Utility class for text preprocessing."""
    
    @staticmethod
    def preprocess_text(df: DataFrame, text_columns: List[str]) -> DataFrame:
        """
        Preprocess text columns: lowercase, remove special chars, etc.
        
        Args:
            df: Input DataFrame
            text_columns: List of column names to preprocess
            
        Returns:
            DataFrame with preprocessed text
        """
        for col_name in text_columns:
            if col_name in df.columns:
                df = df.withColumn(
                    col_name,
                    lower(
                        regexp_replace(col(col_name), r"[^\w\s]", "")
                    )
                )
        
        return df
    
    @staticmethod
    def split_keywords(df: DataFrame, keyword_col: str, new_col: str = "keywords_array") -> DataFrame:
        """
        Split keywords string into array.
        
        Args:
            df: Input DataFrame
            keyword_col: Column name with comma/semicolon separated keywords
            new_col: Name of new column with array
            
        Returns:
            DataFrame with new keywords array column
        """
        return df.withColumn(
            new_col,
            split(regexp_replace(col(keyword_col), r"\s+", ""), ",")
        )
    
    @staticmethod
    def combine_text_features(
        df: DataFrame,
        text_columns: List[str],
        new_col: str = "combined_text"
    ) -> DataFrame:
        """
        Combine multiple text columns into one.
        
        Args:
            df: Input DataFrame
            text_columns: Columns to combine
            new_col: Name of new column
            
        Returns:
            DataFrame with combined text
        """
        # Filter only existing columns
        existing_cols = [c for c in text_columns if c in df.columns]
        
        if not existing_cols:
            return df.withColumn(new_col, col("title"))
        
        return df.withColumn(
            new_col,
            concat_ws(" ", *[col(c) for c in existing_cols])
        )


class DataFrameSaver:
    """Utility class for saving DataFrames."""

    @staticmethod
    def _ensure_similar_courses_schema(conn) -> None:
        """Ensure similar_courses has the columns expected by Spark jobs."""
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS similar_courses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id INT NOT NULL,
                    similar_course_id INT NOT NULL,
                    similarity DECIMAL(5,4) NOT NULL,
                    similar_course_title VARCHAR(255),
                    similar_course_topic VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        existing = {
            row[0]
            for row in conn.execute(text("SHOW COLUMNS FROM similar_courses")).fetchall()
        }

        if "similarity" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE similar_courses "
                    "ADD COLUMN similarity DECIMAL(5,4) NOT NULL DEFAULT 0"
                )
            )

        if "similar_course_title" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE similar_courses "
                    "ADD COLUMN similar_course_title VARCHAR(255)"
                )
            )

        if "similar_course_topic" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE similar_courses "
                    "ADD COLUMN similar_course_topic VARCHAR(100)"
                )
            )
    
    @staticmethod
    def save_to_csv(df: DataFrame, path: str, mode: str = "overwrite", header: bool = True):
        """
        Save DataFrame to CSV.
        
        Args:
            df: DataFrame to save
            path: Output path
            mode: Write mode (overwrite, append, etc.)
            header: Whether to write header
        """
        try:
            df.write.mode(mode).option("header", header).csv(path)
            logger.info(f"Saved DataFrame to {path}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    @staticmethod
    def save_to_json(df: DataFrame, path: str, mode: str = "overwrite"):
        """
        Save DataFrame to JSON.
        
        Args:
            df: DataFrame to save
            path: Output path
            mode: Write mode
        """
        try:
            df.write.mode(mode).json(path)
            logger.info(f"Saved DataFrame to {path}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    @staticmethod
    def save_to_parquet(df: DataFrame, path: str, mode: str = "overwrite"):
        """
        Save DataFrame to Parquet.
        
        Args:
            df: DataFrame to save
            path: Output path
            mode: Write mode
        """
        try:
            df.write.mode(mode).parquet(path)
            logger.info(f"Saved DataFrame to {path}")
        except Exception as e:
            logger.error(f"Error saving to Parquet: {e}")
    
    @staticmethod
    def save_to_db(
        df: DataFrame,
        table_name: str,
        mode: str = "overwrite",
        batch_size: int = 1000,
    ):
        """
        Save DataFrame to MySQL database using SQLAlchemy with streaming inserts.
        
        Args:
            df: DataFrame to save
            table_name: Target table name
            mode: Write mode (overwrite, append, etc.)
            batch_size: Rows per insert batch
        """
        try:
            engine = create_engine(SparkConfig.DB_URL)
            columns = df.columns

            if not columns:
                logger.info(f"No columns to save for table {table_name}")
                return

            insert_columns = ", ".join(f"`{c}`" for c in columns)
            insert_values = ", ".join(f":{c}" for c in columns)
            insert_stmt = text(
                f"INSERT INTO {table_name} ({insert_columns}) VALUES ({insert_values})"
            )

            total = 0
            with engine.begin() as conn:
                if table_name == "similar_courses":
                    DataFrameSaver._ensure_similar_courses_schema(conn)

                if mode == "overwrite":
                    conn.execute(text(f"DELETE FROM {table_name}"))

                batch = []
                for row in df.toLocalIterator():
                    row_dict = row.asDict(recursive=True)

                    # Normalize values (avoid numpy scalars/NaN)
                    for key, value in row_dict.items():
                        if value is None:
                            continue
                        if isinstance(value, float) and math.isnan(value):
                            row_dict[key] = None
                            continue
                        if hasattr(value, "item"):
                            try:
                                row_dict[key] = value.item()
                            except Exception:
                                pass

                    batch.append(row_dict)

                    if len(batch) >= batch_size:
                        conn.execute(insert_stmt, batch)
                        total += len(batch)
                        batch.clear()

                if batch:
                    conn.execute(insert_stmt, batch)
                    total += len(batch)

            logger.info(f"Saved {total} rows to {table_name}")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            raise


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
