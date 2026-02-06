"""
Tests for Spark utilities and job logic.

A local PySpark session is used; tests are skipped automatically if
PySpark / Java is not available.
"""

import pytest

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (
        StructType, StructField, StringType, IntegerType, TimestampType,
    )

    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PYSPARK_AVAILABLE, reason="PySpark is not installed"
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="module")
def spark():
    """Create a local SparkSession for the test module."""
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("moocs-test")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture()
def sample_courses_df(spark):
    """Return a small courses DataFrame that mirrors the DB schema."""
    from datetime import datetime

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

    now = datetime.now()
    rows = [
        (1, 1, "c1", "Intro to Python", "Learn Python", "Full desc",
         "python,programming", "Computer Science", "en", "Beginner",
         "https://example.com/1", None, None, None, now, now, "coursera"),
        (2, 1, "c2", "Advanced ML", "Machine learning", "Full ML desc",
         "ml,ai", "Data Science", "en", "Advanced",
         "https://example.com/2", None, None, None, now, now, "coursera"),
        (3, 2, "c3", "Linear Algebra", "Math fundamentals", "Full math desc",
         "math,algebra", "Mathematics", "en", "Intermediate",
         "https://example.com/3", None, None, None, now, now, "mit_ocw"),
        (4, 2, "c4", "Quantum Physics", "Quantum mechanics", "Full physics desc",
         "physics,quantum", "Physics", "en", "Advanced",
         "https://example.com/4", None, None, None, now, now, "mit_ocw"),
        (5, 1, "c5", "Web Development", "Build websites", "Full web desc",
         "html,css,js", "Computer Science", "es", "Beginner",
         "https://example.com/5", None, None, None, now, now, "coursera"),
    ]

    return spark.createDataFrame(rows, schema=schema)


# ==================================================================
# SparkConfig tests (no SparkSession needed)
# ==================================================================

class TestSparkConfig:
    """Verify sensible defaults in SparkConfig."""

    def test_default_values(self):
        from sparkjobs.config import SparkConfig

        assert SparkConfig.NUM_CLUSTERS >= 2
        assert 0 < SparkConfig.SIMILARITY_THRESHOLD < 1
        assert SparkConfig.TOP_N_SIMILAR_COURSES >= 1
        assert SparkConfig.MIN_TF_IDF_FEATURES >= 10

    def test_jdbc_url_format(self):
        from sparkjobs.config import SparkConfig

        assert SparkConfig.DB_JDBC_URL.startswith("jdbc:mysql://")

    def test_sqlalchemy_url_format(self):
        from sparkjobs.config import SparkConfig

        assert SparkConfig.DB_URL.startswith("mysql+pymysql://")


# ==================================================================
# TextPreprocessor tests
# ==================================================================

class TestTextPreprocessor:
    """Tests for sparkjobs.spark_utils.TextPreprocessor."""

    def test_preprocess_lowercases_text(self, sample_courses_df):
        from sparkjobs.spark_utils import TextPreprocessor

        df = TextPreprocessor.preprocess_text(sample_courses_df, ["title"])
        titles = [row.title for row in df.collect()]
        assert all(t == t.lower() for t in titles)

    def test_preprocess_removes_special_chars(self, spark):
        from sparkjobs.spark_utils import TextPreprocessor

        df = spark.createDataFrame([("Hello, World! #2024",)], ["text"])
        result = TextPreprocessor.preprocess_text(df, ["text"])
        text = result.collect()[0].text
        assert "#" not in text
        assert "!" not in text

    def test_preprocess_ignores_missing_column(self, sample_courses_df):
        from sparkjobs.spark_utils import TextPreprocessor

        # Should not raise even if the column doesn't exist
        df = TextPreprocessor.preprocess_text(sample_courses_df, ["nonexistent_col"])
        assert df.count() == sample_courses_df.count()

    def test_combine_text_features(self, sample_courses_df):
        from sparkjobs.spark_utils import TextPreprocessor

        df = TextPreprocessor.combine_text_features(
            sample_courses_df,
            text_columns=["title", "keywords"],
            new_col="combined",
        )
        row = df.select("combined").first()
        assert row.combined is not None
        # Combined should contain content from both columns
        assert "python" in row.combined.lower() or "intro" in row.combined.lower()

    def test_combine_text_features_missing_cols(self, sample_courses_df):
        from sparkjobs.spark_utils import TextPreprocessor

        df = TextPreprocessor.combine_text_features(
            sample_courses_df,
            text_columns=["no_such_col_a", "no_such_col_b"],
            new_col="combined",
        )
        # Falls back to title column
        assert "combined" in df.columns

    def test_split_keywords(self, sample_courses_df):
        from sparkjobs.spark_utils import TextPreprocessor

        df = TextPreprocessor.split_keywords(sample_courses_df, "keywords", "kw_arr")
        row = df.filter(df.id == 1).select("kw_arr").first()
        assert isinstance(row.kw_arr, list)
        assert len(row.kw_arr) >= 1


# ==================================================================
# Analytics-style aggregation tests
# ==================================================================

class TestAnalyticsAggregation:
    """Verify that typical analytics aggregations produce expected output."""

    def test_count_by_source(self, sample_courses_df):
        from pyspark.sql.functions import count

        result = (
            sample_courses_df
            .groupBy("source_name")
            .agg(count("id").alias("num_courses"))
            .collect()
        )
        source_map = {row.source_name: row.num_courses for row in result}
        assert source_map["coursera"] == 3
        assert source_map["mit_ocw"] == 2

    def test_count_by_language(self, sample_courses_df):
        from pyspark.sql.functions import count

        result = (
            sample_courses_df
            .groupBy("language")
            .agg(count("id").alias("num_courses"))
            .collect()
        )
        lang_map = {row.language: row.num_courses for row in result}
        assert lang_map["en"] == 4
        assert lang_map["es"] == 1

    def test_count_by_level(self, sample_courses_df):
        from pyspark.sql.functions import count

        result = (
            sample_courses_df
            .groupBy("level")
            .agg(count("id").alias("num_courses"))
            .collect()
        )
        level_map = {row.level: row.num_courses for row in result}
        assert level_map["Beginner"] == 2
        assert level_map["Advanced"] == 2
        assert level_map["Intermediate"] == 1

    def test_count_by_topic(self, sample_courses_df):
        from pyspark.sql.functions import count

        result = (
            sample_courses_df
            .groupBy("topic")
            .agg(count("id").alias("num_courses"))
            .collect()
        )
        topic_map = {row.topic: row.num_courses for row in result}
        assert topic_map["Computer Science"] == 2
        assert topic_map["Data Science"] == 1

    def test_distinct_sources_count(self, sample_courses_df):
        from pyspark.sql.functions import countDistinct

        row = sample_courses_df.select(
            countDistinct("source_name").alias("cnt")
        ).first()
        assert row.cnt == 2


# ==================================================================
# TF-IDF pipeline smoke test
# ==================================================================

class TestTfidfPipeline:
    """Quick smoke test for the TF-IDF feature extraction pipeline."""

    def test_tfidf_produces_vectors(self, sample_courses_df):
        from pyspark.ml.feature import HashingTF, IDF, Tokenizer
        from pyspark.ml import Pipeline
        from sparkjobs.spark_utils import TextPreprocessor

        # Prepare text
        df = TextPreprocessor.combine_text_features(
            sample_courses_df,
            text_columns=["title", "keywords"],
            new_col="combined_text",
        )
        df = TextPreprocessor.preprocess_text(df, ["combined_text"])
        df = df.fillna({"combined_text": ""})

        # Build mini pipeline
        tokenizer = Tokenizer(inputCol="combined_text", outputCol="words")
        hashing_tf = HashingTF(inputCol="words", outputCol="raw_features", numFeatures=50)
        idf = IDF(inputCol="raw_features", outputCol="tfidf_features", minDocFreq=1)

        pipeline = Pipeline(stages=[tokenizer, hashing_tf, idf])
        model = pipeline.fit(df)
        result = model.transform(df)

        assert "tfidf_features" in result.columns
        assert result.count() == 5
        # Every row should have a non-null vector
        null_count = result.filter(result.tfidf_features.isNull()).count()
        assert null_count == 0
