"""
Course Clustering Job
Performs K-means clustering on courses based on their features.
"""
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, desc, row_number
from pyspark.sql.window import Window
from pyspark.ml.feature import HashingTF, IDF, Tokenizer, StandardScaler, VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

from .spark_utils import (
    SparkSessionManager, DataFrameLoader, TextPreprocessor,
    DataFrameSaver, setup_logging
)
from .config import SparkConfig

logger = logging.getLogger(__name__)


class CourseClusteringJob:
    """Job for clustering courses using K-means."""
    
    def __init__(self):
        self.spark = SparkSessionManager.get_or_create_spark_session(
            app_name="Course-Clustering-Job"
        )
        self.saver = DataFrameSaver()
        self.num_clusters = SparkConfig.NUM_CLUSTERS
    
    def run(self):
        """Execute the clustering job."""
        try:
            logger.info("Starting Course Clustering Job")
            
            # Load courses
            courses_df = DataFrameLoader.read_courses_from_db(self.spark)
            logger.info(f"Loaded {courses_df.count()} courses")
            
            # Prepare data
            prepared_df = self._prepare_data(courses_df)
            
            # Compute features
            features_df = self._compute_features(prepared_df)
            
            # Perform clustering
            clustered_df, model = self._perform_clustering(features_df)
            
            # Analyze and save results
            self._analyze_and_save_results(clustered_df, model, prepared_df)
            
            logger.info("Course Clustering Job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in Course Clustering Job: {e}")
            raise
    
    def _prepare_data(self, courses_df: DataFrame) -> DataFrame:
        """
        Prepare course data for clustering.
        
        Args:
            courses_df: Raw courses DataFrame
            
        Returns:
            Prepared DataFrame
        """
        logger.info("Preparing course data for clustering")
        
        # Combine text features
        df = TextPreprocessor.combine_text_features(
            courses_df,
            text_columns=["title", "short_description", "keywords", "topic"],
            new_col="combined_text"
        )
        
        # Preprocess text
        df = TextPreprocessor.preprocess_text(df, ["combined_text"])
        
        # Handle nulls
        df = df.fillna({
            "combined_text": "",
            "level": "intermediate",
            "language": "en",
            "topic": "general"
        })
        
        # Select relevant columns
        df = df.select(
            col("id").alias("course_id"),
            col("title"),
            col("combined_text"),
            col("topic"),
            col("level"),
            col("language"),
            col("source_name")
        )
        
        return df
    
    def _compute_features(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute TF-IDF features for courses.
        
        Args:
            courses_df: Prepared courses DataFrame
            
        Returns:
            DataFrame with features
        """
        logger.info("Computing TF-IDF features for clustering")
        
        # Tokenize
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
        
        # Scaler for normalization
        scaler = StandardScaler(
            inputCol="tfidf_features",
            outputCol="scaled_features",
            withMean=False,
            withStd=True
        )
        
        # Pipeline
        pipeline = Pipeline(stages=[tokenizer, hashing_tf, idf, scaler])
        model = pipeline.fit(courses_df)
        features_df = model.transform(courses_df)
        
        # Save model
        logger.info(
            f"Saving feature extraction model to {SparkConfig.CLUSTERING_RESULTS_PATH}/feature_model"
        )
        model.write().overwrite().save(
            f"{SparkConfig.CLUSTERING_RESULTS_PATH}/feature_model"
        )
        
        return features_df
    
    def _perform_clustering(self, features_df: DataFrame):
        """
        Perform K-means clustering.
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            Tuple of (clustered DataFrame, KMeans model)
        """
        logger.info(f"Performing K-means clustering with k={self.num_clusters}")
        
        # K-means
        kmeans = KMeans(
            k=self.num_clusters,
            seed=42,
            maxIter=20,
            featuresCol="scaled_features"
        )
        
        model = kmeans.fit(features_df)
        clustered_df = model.transform(features_df)
        
        # Evaluate
        evaluator = ClusteringEvaluator(
            featuresCol="scaled_features",
            predictionCol="prediction",
            metricName="silhouette"
        )
        silhouette_score = evaluator.evaluate(clustered_df)
        logger.info(f"Silhouette score: {silhouette_score:.4f}")
        
        # Save model
        logger.info(
            f"Saving K-means model to {SparkConfig.CLUSTERING_RESULTS_PATH}/kmeans_model"
        )
        model.write().overwrite().save(
            f"{SparkConfig.CLUSTERING_RESULTS_PATH}/kmeans_model"
        )
        
        return clustered_df, model
    
    def _analyze_and_save_results(self, clustered_df: DataFrame, model, original_df: DataFrame):
        """
        Analyze clustering results and save to database.
        
        Args:
            clustered_df: DataFrame with cluster assignments
            model: KMeans model
            original_df: Original prepared DataFrame
        """
        logger.info("Analyzing and saving clustering results")
        
        # Combine with original data
        result_df = original_df.select(
            col("course_id"),
            col("title"),
            col("topic"),
            col("level")
        ).join(
            clustered_df.select(col("course_id"), col("prediction").alias("cluster_id")),
            "course_id"
        )
        
        # Analyze cluster compositions
        cluster_stats = result_df.groupBy("cluster_id").agg(
            {"course_id": "count"}
        ).withColumnRenamed("count(course_id)", "num_courses").orderBy(desc("num_courses"))
        
        logger.info("Cluster distribution:")
        cluster_stats.show()
        
        # Save main results to CSV
        self.saver.save_to_csv(
            result_df,
            SparkConfig.CLUSTERING_RESULTS_PATH
        )
        
        # Save cluster stats
        self.saver.save_to_csv(
            cluster_stats,
            f"{SparkConfig.CLUSTERING_RESULTS_PATH}/cluster_stats"
        )
        
        # Save to database
        try:
            self.saver.save_to_db(
                result_df,
                "course_clusters",
                mode="overwrite"
            )
            logger.info("Saved results to course_clusters table")
        except Exception as e:
            logger.warning(f"Could not save to database: {e}")
        
        # Get cluster centers
        centers = model.clusterCenters()
        logger.info(f"Number of cluster centers: {len(centers)}")
        for i, center in enumerate(centers):
            logger.info(f"Cluster {i} center size: {len(center)}")


def main():
    """Main entry point."""
    setup_logging()
    job = CourseClusteringJob()
    job.run()


if __name__ == "__main__":
    main()
