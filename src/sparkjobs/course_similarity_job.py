"""
Course Similarity Job
Computes TF-IDF vectors and similarity between courses.
Creates a similar_courses table with recommendations.
"""
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, desc, rank, expr, lit, when
from pyspark.sql.window import Window
from pyspark.storagelevel import StorageLevel
from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from pyspark.ml import Pipeline
from pyspark.ml.functions import vector_to_array
from .spark_utils import (
    SparkSessionManager, DataFrameLoader, TextPreprocessor,
    DataFrameSaver, setup_logging
)
from .config import SparkConfig

logger = logging.getLogger(__name__)


class CourseSimilarityJob:
    """Job for computing course similarities using TF-IDF."""
    
    def __init__(self):
        self.spark = SparkSessionManager.get_or_create_spark_session(
            app_name="Course-Similarity-Job"
        )
        self.saver = DataFrameSaver()
    
    def run(self):
        """Execute the similarity job."""
        try:
            logger.info("Starting Course Similarity Job")
            
            # Load courses
            courses_df = DataFrameLoader.read_courses_from_db(self.spark)
            logger.info(f"Loaded {courses_df.count()} courses")
            
            # Prepare data
            prepared_df = self._prepare_data(courses_df)
            
            # Compute TF-IDF
            tfidf_df = self._compute_tfidf(prepared_df)
            
            # Compute similarities
            similarity_df = self._compute_similarities(tfidf_df)
            
            # Save results
            self._save_results(similarity_df)
            
            logger.info("Course Similarity Job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in Course Similarity Job: {e}")
            raise
    
    def _prepare_data(self, courses_df: DataFrame) -> DataFrame:
        """
        Prepare course data for similarity computation.
        
        Args:
            courses_df: Raw courses DataFrame
            
        Returns:
            Prepared DataFrame
        """
        logger.info("Preparing course data")
        
        # Combine relevant text fields
        df = TextPreprocessor.combine_text_features(
            courses_df,
            text_columns=["title", "short_description", "keywords", "topic"],
            new_col="combined_text"
        )
        
        # Preprocess text
        df = TextPreprocessor.preprocess_text(df, ["combined_text"])
        
        # Handle null values
        df = df.fillna({"combined_text": ""})
        
        # Select relevant columns
        df = df.select(
            col("id").alias("course_id"),
            col("title"),
            col("combined_text"),
            col("topic"),
            col("level"),
            col("source_name")
        )
        
        return df
    
    def _compute_tfidf(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute TF-IDF vectors for courses.
        
        Args:
            courses_df: Prepared courses DataFrame
            
        Returns:
            DataFrame with TF-IDF vectors
        """
        logger.info("Computing TF-IDF vectors")
        
        # Tokenize text
        tokenizer = Tokenizer(inputCol="combined_text", outputCol="words")
        
        # Hash and TF
        hashing_tf = HashingTF(
            inputCol="words",
            outputCol="raw_features",
            numFeatures=SparkConfig.MIN_TF_IDF_FEATURES
        )
        
        # IDF
        idf = IDF(
            inputCol="raw_features",
            outputCol="tfidf_features",
            minDocFreq=2
        )
        
        # Pipeline
        pipeline = Pipeline(stages=[tokenizer, hashing_tf, idf])
        model = pipeline.fit(courses_df)
        tfidf_df = model.transform(courses_df)
        
        # Save model for future use
        logger.info(f"Saving TF-IDF model to {SparkConfig.TFIDF_MODEL_PATH}")
        model.write().overwrite().save(SparkConfig.TFIDF_MODEL_PATH)
        
        return tfidf_df
    
    def _compute_similarities(self, tfidf_df: DataFrame) -> DataFrame:
        """
        Compute cosine similarity between courses.
        
        Args:
            tfidf_df: DataFrame with TF-IDF vectors
            
        Returns:
            DataFrame with similarity pairs
        """
        logger.info("Computing cosine similarities")
        
        # Convert tfidf_features to dense for similarity computation
        tfidf_df = tfidf_df.withColumn(
            "tfidf_dense",
            col("tfidf_features")
        )
        
        # Self-join to compute similarities
        df1 = tfidf_df.select(
            col("course_id").alias("course_id_1"),
            col("tfidf_dense").alias("tfidf_1"),
            col("title").alias("title_1"),
            col("topic").alias("topic_1")
        )
        
        df2 = tfidf_df.select(
            col("course_id").alias("course_id_2"),
            col("tfidf_dense").alias("tfidf_2"),
            col("title").alias("title_2"),
            col("topic").alias("topic_2")
        )
        
        # Self join
        joined = df1.crossJoin(df2).filter(col("course_id_1") < col("course_id_2"))
        
        # Compute cosine similarity using Spark SQL (avoid Python workers)
        joined = joined.withColumn("vec1", vector_to_array(col("tfidf_1"))).withColumn(
            "vec2", vector_to_array(col("tfidf_2"))
        )
        joined = joined.withColumn(
            "dot",
            expr("aggregate(zip_with(vec1, vec2, (x, y) -> x * y), 0D, (acc, x) -> acc + x)")
        ).withColumn(
            "norm1",
            expr("sqrt(aggregate(vec1, 0D, (acc, x) -> acc + x * x))")
        ).withColumn(
            "norm2",
            expr("sqrt(aggregate(vec2, 0D, (acc, x) -> acc + x * x))")
        )

        similarity_df = joined.withColumn(
            "similarity",
            when((col("norm1") == 0) | (col("norm2") == 0), lit(0.0)).otherwise(
                col("dot") / (col("norm1") * col("norm2"))
            )
        ).select(
            col("course_id_1"),
            col("course_id_2"),
            col("title_1"),
            col("title_2"),
            col("topic_1"),
            col("topic_2"),
            col("similarity")
        )
        
        # Filter by threshold
        similarity_df = similarity_df.filter(
            col("similarity") >= SparkConfig.SIMILARITY_THRESHOLD
        )
        
        return similarity_df
    
    def _save_results(self, similarity_df: DataFrame):
        """
        Save similarity results to database and files.
        
        Args:
            similarity_df: DataFrame with similarity pairs
        """
        logger.info("Saving similarity results")
        
        # Create similar_courses table format
        # Each course gets its top N similar courses
        window_spec = Window.partitionBy("course_id_1").orderBy(desc("similarity"))
        
        similar_courses = similarity_df.withColumn(
            "rank",
            rank().over(window_spec)
        ).filter(
            col("rank") <= SparkConfig.TOP_N_SIMILAR_COURSES
        ).select(
            col("course_id_1").alias("course_id"),
            col("course_id_2").alias("similar_course_id"),
            col("similarity"),
            col("title_2").alias("similar_course_title"),
            col("topic_2").alias("similar_course_topic")
        )
        
        # Materialize once to avoid recomputing the expensive similarity graph
        similar_courses = similar_courses.persist(StorageLevel.MEMORY_AND_DISK)
        similar_courses.count()

        try:
            # Save to CSV
            self.saver.save_to_csv(
                similar_courses,
                SparkConfig.SIMILARITY_RESULTS_PATH
            )

            # Save to database (if table exists)
            try:
                self.saver.save_to_db(
                    similar_courses,
                    "similar_courses",
                    mode="overwrite"
                )
            except Exception as e:
                logger.warning(f"Could not save to database: {e}")
        finally:
            similar_courses.unpersist()


def main():
    """Main entry point."""
    setup_logging()
    job = CourseSimilarityJob()
    job.run()


if __name__ == "__main__":
    main()
