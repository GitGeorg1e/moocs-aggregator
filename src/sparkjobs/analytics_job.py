"""
Analytics Job
Computes aggregated statistics and analytics on courses and clusters.
"""
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, countDistinct, avg, min, max, collect_list, struct

from .spark_utils import (
    SparkSessionManager, DataFrameLoader, DataFrameSaver, setup_logging
)
from .config import SparkConfig

logger = logging.getLogger(__name__)


class AnalyticsJob:
    """Job for computing course analytics."""
    
    def __init__(self):
        self.spark = SparkSessionManager.get_or_create_spark_session(
            app_name="Course-Analytics-Job"
        )
        self.saver = DataFrameSaver()
    
    def run(self):
        """Execute the analytics job."""
        try:
            logger.info("Starting Course Analytics Job")
            
            # Load courses
            courses_df = DataFrameLoader.read_courses_from_db(self.spark)
            logger.info(f"Loaded {courses_df.count()} courses")
            
            # Compute various analytics
            stats = self._compute_overall_stats(courses_df)
            source_stats = self._compute_source_stats(courses_df)
            language_stats = self._compute_language_stats(courses_df)
            level_stats = self._compute_level_stats(courses_df)
            topic_stats = self._compute_topic_stats(courses_df)
            
            # Save results
            self._save_analytics(stats, source_stats, language_stats, level_stats, topic_stats)
            
            logger.info("Course Analytics Job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in Course Analytics Job: {e}")
            raise
    
    def _compute_overall_stats(self, courses_df: DataFrame) -> dict:
        """
        Compute overall statistics.
        
        Args:
            courses_df: Courses DataFrame
            
        Returns:
            Dictionary with statistics
        """
        logger.info("Computing overall statistics")
        
        total_courses = courses_df.count()
        unique_sources = courses_df.select(countDistinct("source_name")).collect()[0][0]
        unique_languages = courses_df.select(countDistinct("language")).collect()[0][0]
        unique_topics = courses_df.select(countDistinct("topic")).collect()[0][0]
        
        stats = {
            "total_courses": total_courses,
            "unique_sources": unique_sources,
            "unique_languages": unique_languages,
            "unique_topics": unique_topics
        }
        
        logger.info(f"Overall stats: {stats}")
        return stats
    
    def _compute_source_stats(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute statistics by source.
        
        Args:
            courses_df: Courses DataFrame
            
        Returns:
            DataFrame with source statistics
        """
        logger.info("Computing source statistics")
        
        source_stats = courses_df.groupBy("source_id", "source_name").agg(
            count("id").alias("num_courses"),
            countDistinct("language").alias("num_languages"),
            countDistinct("topic").alias("num_topics"),
            countDistinct("level").alias("num_levels")
        ).orderBy(col("num_courses").desc())
        
        source_stats.show()
        return source_stats
    
    def _compute_language_stats(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute statistics by language.
        
        Args:
            courses_df: Courses DataFrame
            
        Returns:
            DataFrame with language statistics
        """
        logger.info("Computing language statistics")
        
        language_stats = courses_df.groupBy("language").agg(
            count("id").alias("num_courses"),
            countDistinct("source_name").alias("num_sources"),
            countDistinct("topic").alias("num_topics")
        ).orderBy(col("num_courses").desc())
        
        language_stats.show()
        return language_stats
    
    def _compute_level_stats(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute statistics by level.
        
        Args:
            courses_df: Courses DataFrame
            
        Returns:
            DataFrame with level statistics
        """
        logger.info("Computing level statistics")
        
        level_stats = courses_df.groupBy("level").agg(
            count("id").alias("num_courses"),
            countDistinct("source_name").alias("num_sources"),
            countDistinct("language").alias("num_languages"),
            countDistinct("topic").alias("num_topics")
        ).orderBy(col("num_courses").desc())
        
        level_stats.show()
        return level_stats
    
    def _compute_topic_stats(self, courses_df: DataFrame) -> DataFrame:
        """
        Compute statistics by topic.
        
        Args:
            courses_df: Courses DataFrame
            
        Returns:
            DataFrame with topic statistics
        """
        logger.info("Computing topic statistics")
        
        topic_stats = courses_df.groupBy("topic").agg(
            count("id").alias("num_courses"),
            countDistinct("source_name").alias("num_sources"),
            countDistinct("language").alias("num_languages"),
            countDistinct("level").alias("num_levels")
        ).orderBy(col("num_courses").desc())
        
        topic_stats.show()
        return topic_stats
    
    def _save_analytics(
        self,
        overall_stats: dict,
        source_stats: DataFrame,
        language_stats: DataFrame,
        level_stats: DataFrame,
        topic_stats: DataFrame
    ):
        """
        Save analytics results.
        
        Args:
            overall_stats: Overall statistics dictionary
            source_stats: Source statistics DataFrame
            language_stats: Language statistics DataFrame
            level_stats: Level statistics DataFrame
            topic_stats: Topic statistics DataFrame
        """
        logger.info("Saving analytics results")
        
        # Save DataFrames to CSV
        self.saver.save_to_csv(
            source_stats,
            f"{SparkConfig.ANALYTICS_RESULTS_PATH}/source_stats"
        )
        
        self.saver.save_to_csv(
            language_stats,
            f"{SparkConfig.ANALYTICS_RESULTS_PATH}/language_stats"
        )
        
        self.saver.save_to_csv(
            level_stats,
            f"{SparkConfig.ANALYTICS_RESULTS_PATH}/level_stats"
        )
        
        self.saver.save_to_csv(
            topic_stats,
            f"{SparkConfig.ANALYTICS_RESULTS_PATH}/topic_stats"
        )
        
        # Save to database
        try:
            self.saver.save_to_db(source_stats, "analytics_by_source", mode="overwrite")
            self.saver.save_to_db(language_stats, "analytics_by_language", mode="overwrite")
            self.saver.save_to_db(level_stats, "analytics_by_level", mode="overwrite")
            self.saver.save_to_db(topic_stats, "analytics_by_topic", mode="overwrite")
            logger.info("Saved analytics to database")
        except Exception as e:
            logger.warning(f"Could not save analytics to database: {e}")
        
        # Log overall stats
        logger.info(f"Overall Statistics: {overall_stats}")


def main():
    """Main entry point."""
    setup_logging()
    job = AnalyticsJob()
    job.run()


if __name__ == "__main__":
    main()
