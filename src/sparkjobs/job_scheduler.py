"""
Spark Job Scheduler
Simple scheduler to run Spark jobs periodically
"""
import logging
import schedule
import time
from datetime import datetime
from typing import Callable
import threading

logger = logging.getLogger(__name__)


class SparkJobScheduler:
    """Scheduler for running Spark jobs at specified intervals."""
    
    def __init__(self):
        self.jobs = []
        self.scheduler = schedule.Scheduler()
        self.is_running = False
        self.scheduler_thread = None
    
    def add_job(
        self,
        job_func: Callable,
        interval: int,
        interval_type: str = "hours",
        job_name: str = None
    ):
        """
        Add a job to the scheduler.
        
        Args:
            job_func: Function to execute
            interval: Interval amount
            interval_type: 'seconds', 'minutes', 'hours', 'days'
            job_name: Optional name for logging
        """
        job_name = job_name or job_func.__name__
        
        job = getattr(self.scheduler, f"every({interval}).{interval_type}")
        job.do(self._run_job, job_func=job_func, job_name=job_name)
        
        self.jobs.append({
            "name": job_name,
            "func": job_func,
            "interval": interval,
            "interval_type": interval_type
        })
        
        logger.info(f"Added job '{job_name}' to run every {interval} {interval_type}")
    
    def _run_job(self, job_func: Callable, job_name: str):
        """
        Wrapper to run a job with error handling and logging.
        
        Args:
            job_func: Job function to run
            job_name: Name of the job
        """
        logger.info(f"Starting job: {job_name} at {datetime.now()}")
        try:
            job_func()
            logger.info(f"Completed job: {job_name}")
        except Exception as e:
            logger.error(f"Error in job '{job_name}': {e}")
    
    def start(self, background: bool = True):
        """
        Start the scheduler.
        
        Args:
            background: Run in background thread if True
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting Spark Job Scheduler")
        
        if background:
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True
            )
            self.scheduler_thread.start()
            logger.info("Scheduler running in background")
        else:
            self._run_scheduler()
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            self.scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def get_job_status(self) -> dict:
        """
        Get status of all scheduled jobs.
        
        Returns:
            Dictionary with job information
        """
        status = {
            "is_running": self.is_running,
            "jobs": []
        }
        
        for job in self.jobs:
            scheduled_job = next(
                (j for j in self.scheduler.jobs if job["name"] in str(j)),
                None
            )
            status["jobs"].append({
                "name": job["name"],
                "interval": f"{job['interval']} {job['interval_type']}",
                "last_run": scheduled_job.last_run if scheduled_job else None,
                "next_run": scheduled_job.next_run if scheduled_job else None
            })
        
        return status


# ============== EXAMPLE USAGE ==============

if __name__ == "__main__":
    from __init__ import run_similarity_job, run_clustering_job, run_analytics_job
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create scheduler
    scheduler = SparkJobScheduler()
    
    # Add jobs
    scheduler.add_job(run_similarity_job, interval=6, interval_type="hours", job_name="similarity")
    scheduler.add_job(run_clustering_job, interval=12, interval_type="hours", job_name="clustering")
    scheduler.add_job(run_analytics_job, interval=1, interval_type="hours", job_name="analytics")
    
    # Start scheduler
    try:
        scheduler.start(background=True)
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.stop()
