"""
Module 1: Identity AWS Retry & Snapshot Management
Implements retry decorator for AWS Rekognition calls and cleanup jobs for old snapshots.

Key Features:
- Retry decorator for handling network timeouts and transient AWS errors
- Exponential backoff strategy
- CleanupSnapshot job to delete snapshots older than 90 days
- Graceful degradation for failed recognition attempts
"""

import logging
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for decorator
F = TypeVar('F', bound=Callable[..., Any])


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class AWSRetryDecorator:
    """
    Decorator for AWS API calls with configurable retry logic.
    Handles transient network errors, timeouts, and rate limiting.
    """
    
    # Default configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1  # seconds
    DEFAULT_MAX_DELAY = 60  # seconds
    DEFAULT_STRATEGY = RetryStrategy.EXPONENTIAL
    
    # Retry-able AWS error codes
    RETRYABLE_ERRORS = [
        'ServiceUnavailable',
        'ThrottlingException',
        'RequestLimitExceeded',
        'InternalServerError',
        'ProvisionedThroughputExceededException',
        'TimeoutError',
        'ConnectionError',
        'BotoCoreError'
    ]
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        strategy: RetryStrategy = DEFAULT_STRATEGY,
        on_retry_callback: Optional[Callable] = None
    ):
        """
        Initialize retry decorator configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (exponential backoff)
            max_delay: Maximum delay between retries
            strategy: Retry strategy (exponential, linear, fixed)
            on_retry_callback: Optional callback function when retry occurs
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.on_retry_callback = on_retry_callback
    
    def __call__(self, func: F) -> F:
        """Decorator implementation."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self._retry_logic(func, args, kwargs)
        return wrapper
    
    def _retry_logic(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Function return value
        
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt}/{self.max_retries} for {func.__name__}")
                
                return func(*args, **kwargs)
            
            except Exception as e:
                error_type = type(e).__name__
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    logger.error(f"❌ Non-retryable error in {func.__name__}: {error_type}")
                    raise
                
                last_exception = e
                
                # Don't retry if we've exhausted attempts
                if attempt >= self.max_retries:
                    logger.error(f"❌ Max retries ({self.max_retries}) exhausted for {func.__name__}")
                    raise
                
                # Calculate delay
                delay = self._calculate_backoff_delay(attempt)
                logger.warning(f"⚠️ {error_type} in {func.__name__}, retrying in {delay:.2f}s...")
                
                # Call optional callback
                if self.on_retry_callback:
                    try:
                        self.on_retry_callback(attempt, delay, e, func.__name__)
                    except Exception as cb_error:
                        logger.warning(f"⚠️ Callback error: {cb_error}")
                
                # Wait before retry
                time.sleep(delay)
        
        # Should not reach here, but just in case
        raise last_exception or Exception(f"Failed to execute {func.__name__}")
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is worth retrying.
        
        Args:
            error: Exception to check
        
        Returns:
            True if error is retryable
        """
        error_str = str(error)
        
        # Check for known retryable error patterns
        for retryable in self.RETRYABLE_ERRORS:
            if retryable in error_str:
                return True
        
        # Check for timeout errors
        if isinstance(error, (TimeoutError, OSError)):
            return True
        
        return False
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate backoff delay based on strategy.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            # Exponential backoff: 1, 2, 4, 8, ...
            delay = self.initial_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            # Linear backoff: 1, 2, 3, 4, ...
            delay = self.initial_delay * (attempt + 1)
        else:  # FIXED
            # Fixed delay
            delay = self.initial_delay
        
        # Cap at maximum delay
        return min(delay, self.max_delay)


# ============================================================================
# SNAPSHOT CLEANUP SERVICE
# ============================================================================

class SnapshotCleanupService:
    """
    Service to manage cleanup of old snapshot files.
    Deletes unknown person snapshots older than 90 days.
    """
    
    # Configuration
    RETENTION_DAYS = 90
    SNAPSHOT_DIRS = [
        Path("data/snapshots/unknown"),
        Path("data/snapshots/faces"),
        Path("data/enrollment_photos/rejected")
    ]
    
    def __init__(self):
        """Initialize snapshot cleanup service."""
        logger.info(f"✅ SnapshotCleanupService initialized (retention: {self.RETENTION_DAYS} days)")
    
    def cleanup_old_snapshots(self) -> Dict:
        """
        Delete snapshot files older than RETENTION_DAYS.
        
        Returns:
            {
                'success': bool,
                'directories_processed': int,
                'files_deleted': int,
                'disk_space_freed_mb': float,
                'errors': List[str],
                'message': str
            }
        """
        job_name = "Snapshot Cleanup"
        start_time = datetime.now()
        
        logger.info(f"🧹 Starting {job_name}...")
        
        results = {
            'success': True,
            'directories_processed': 0,
            'files_deleted': 0,
            'disk_space_freed_mb': 0.0,
            'errors': [],
            'deleted_files': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        cutoff_timestamp = cutoff_date.timestamp()
        
        logger.info(f"🗑️ Deleting snapshots older than {cutoff_date.date()}")
        
        for snapshot_dir in self.SNAPSHOT_DIRS:
            if not snapshot_dir.exists():
                logger.debug(f"ℹ️ Snapshot directory does not exist: {snapshot_dir}")
                continue
            
            try:
                results['directories_processed'] += 1
                logger.info(f"📁 Processing directory: {snapshot_dir}")
                
                # Find all files in directory
                for file_path in snapshot_dir.glob('**/*'):
                    if not file_path.is_file():
                        continue
                    
                    # Get file modification time
                    file_mtime = file_path.stat().st_mtime
                    
                    # Check if file is older than retention period
                    if file_mtime < cutoff_timestamp:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        
                        try:
                            file_path.unlink()  # Delete file
                            results['files_deleted'] += 1
                            results['disk_space_freed_mb'] += file_size_mb
                            results['deleted_files'].append(str(file_path))
                            logger.debug(f"🗑️ Deleted: {file_path.name} ({file_size_mb:.2f} MB)")
                        except Exception as e:
                            error_msg = f"Failed to delete {file_path}: {e}"
                            results['errors'].append(error_msg)
                            logger.error(f"❌ {error_msg}")
            
            except Exception as e:
                error_msg = f"Error processing directory {snapshot_dir}: {e}"
                results['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Finalize results
        duration = (datetime.now() - start_time).total_seconds()
        
        if results['files_deleted'] > 0:
            logger.info(
                f"✅ {job_name} completed: "
                f"Deleted {results['files_deleted']} files, "
                f"freed {results['disk_space_freed_mb']:.2f} MB in {duration:.2f}s"
            )
        else:
            logger.info(f"ℹ️ {job_name} completed: No files to delete")
        
        results['message'] = (
            f"Deleted {results['files_deleted']} snapshot files "
            f"({results['disk_space_freed_mb']:.2f} MB freed)"
        )
        results['duration_seconds'] = duration
        
        return results
    
    def get_snapshot_statistics(self) -> Dict:
        """
        Get statistics about snapshot storage.
        
        Returns:
            {
                'total_files': int,
                'total_size_mb': float,
                'old_files': int (> 90 days),
                'by_directory': {dir: {count, size_mb, old_count}}
            }
        """
        stats = {
            'total_files': 0,
            'total_size_mb': 0.0,
            'old_files': 0,
            'by_directory': {}
        }
        
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        cutoff_timestamp = cutoff_date.timestamp()
        
        for snapshot_dir in self.SNAPSHOT_DIRS:
            if not snapshot_dir.exists():
                continue
            
            dir_stats = {
                'count': 0,
                'size_mb': 0.0,
                'old_count': 0
            }
            
            for file_path in snapshot_dir.glob('**/*'):
                if not file_path.is_file():
                    continue
                
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                file_mtime = file_path.stat().st_mtime
                
                dir_stats['count'] += 1
                dir_stats['size_mb'] += file_size_mb
                stats['total_files'] += 1
                stats['total_size_mb'] += file_size_mb
                
                if file_mtime < cutoff_timestamp:
                    dir_stats['old_count'] += 1
                    stats['old_files'] += 1
            
            stats['by_directory'][str(snapshot_dir)] = dir_stats
        
        return stats


# ============================================================================
# FASTAPI INTEGRATION HELPERS
# ============================================================================

def create_aws_retry_decorator(
    max_retries: int = AWSRetryDecorator.DEFAULT_MAX_RETRIES,
    initial_delay: float = AWSRetryDecorator.DEFAULT_INITIAL_DELAY,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
) -> AWSRetryDecorator:
    """
    Factory function to create an AWS retry decorator.
    
    Usage:
        @create_aws_retry_decorator(max_retries=3)
        def search_faces_by_image(image_bytes):
            # AWS API call here
            return results
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries
        strategy: Backoff strategy
    
    Returns:
        AWSRetryDecorator instance
    """
    return AWSRetryDecorator(
        max_retries=max_retries,
        initial_delay=initial_delay,
        strategy=strategy
    )


def get_snapshot_cleanup_service() -> SnapshotCleanupService:
    """
    Factory function to create SnapshotCleanupService instance.
    Can be used as FastAPI dependency.
    """
    return SnapshotCleanupService()
