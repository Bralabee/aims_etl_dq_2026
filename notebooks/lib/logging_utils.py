"""
AIMS Data Platform - Logging Utilities
======================================

Consistent logging setup and utilities for notebooks with progress tracking
and phase management.

Usage:
    from notebooks.lib.logging_utils import setup_notebook_logger, log_phase_start
    
    # Setup logger
    logger = setup_notebook_logger("my_notebook")
    logger.info("Processing started")
    
    # Use phase decorators
    @log_phase_start("Data Loading")
    def load_data():
        ...
    
    # Track progress
    with ProgressTracker("Processing files", total=100) as tracker:
        for i in range(100):
            process_file(i)
            tracker.update()
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, Union

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# LOGGING SETUP
# =============================================================================

# Registry of configured loggers
_configured_loggers: Dict[str, logging.Logger] = {}


def setup_notebook_logger(
    name: str,
    level: Union[str, int] = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    propagate: bool = False
) -> logging.Logger:
    """
    Set up a consistent logger for notebooks.
    
    Creates a logger with standardized formatting that works well in both
    Jupyter notebooks and command-line execution.
    
    Args:
        name: Logger name (typically notebook or module name).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Custom log format string (optional).
        log_file: Optional file path to write logs to.
        propagate: Whether to propagate to parent loggers.
    
    Returns:
        logging.Logger: Configured logger instance.
    
    Example:
        >>> logger = setup_notebook_logger("data_processing")
        >>> logger.info("Processing started")
        2026-01-19 10:30:00 | INFO     | data_processing | Processing started
        
        >>> # With file logging
        >>> logger = setup_notebook_logger(
        ...     "pipeline",
        ...     level="DEBUG",
        ...     log_file="logs/pipeline.log"
        ... )
    """
    # Return existing logger if already configured
    if name in _configured_loggers:
        logger = _configured_loggers[name]
        # Update level if different
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level)
        return logger
    
    # Create new logger
    logger = logging.getLogger(name)
    
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(log_path), mode="a")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = propagate
    
    # Cache the configured logger
    _configured_loggers[name] = logger
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with defaults.
    
    Args:
        name: Logger name.
    
    Returns:
        logging.Logger: Logger instance.
    
    Example:
        >>> logger = get_logger("my_module")
        >>> logger.info("Hello!")
    """
    if name in _configured_loggers:
        return _configured_loggers[name]
    return setup_notebook_logger(name)


# =============================================================================
# PHASE LOGGING DECORATORS
# =============================================================================

def log_phase_start(
    phase_name: str,
    logger: Optional[logging.Logger] = None
) -> Callable[[F], F]:
    """
    Decorator to log the start of a processing phase.
    
    Args:
        phase_name: Name of the phase being started.
        logger: Optional logger instance (creates default if not provided).
    
    Returns:
        Decorated function.
    
    Example:
        >>> @log_phase_start("Data Validation")
        ... def validate_data(df):
        ...     # validation logic
        ...     return df
        
        >>> validate_data(my_df)
        2026-01-19 10:30:00 | INFO | phase | ▶ Starting: Data Validation
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or get_logger("phase")
            _logger.info(f"▶ Starting: {phase_name}")
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def log_phase_end(
    phase_name: str,
    logger: Optional[logging.Logger] = None
) -> Callable[[F], F]:
    """
    Decorator to log the end of a processing phase.
    
    Args:
        phase_name: Name of the phase being completed.
        logger: Optional logger instance.
    
    Returns:
        Decorated function.
    
    Example:
        >>> @log_phase_end("Data Validation")
        ... def validate_data(df):
        ...     return df
        
        >>> validate_data(my_df)
        2026-01-19 10:30:05 | INFO | phase | ✓ Completed: Data Validation
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            _logger = logger or get_logger("phase")
            _logger.info(f"✓ Completed: {phase_name}")
            return result
        return wrapper  # type: ignore
    return decorator


def log_phase(
    phase_name: str,
    logger: Optional[logging.Logger] = None
) -> Callable[[F], F]:
    """
    Decorator to log both start and end of a processing phase with timing.
    
    Combines log_phase_start and log_phase_end with execution timing.
    
    Args:
        phase_name: Name of the phase.
        logger: Optional logger instance.
    
    Returns:
        Decorated function.
    
    Example:
        >>> @log_phase("Data Processing")
        ... def process_data(df):
        ...     # processing logic
        ...     return df
        
        >>> process_data(my_df)
        2026-01-19 10:30:00 | INFO | phase | ▶ Starting: Data Processing
        2026-01-19 10:30:05 | INFO | phase | ✓ Completed: Data Processing (5.23s)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or get_logger("phase")
            _logger.info(f"▶ Starting: {phase_name}")
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                _logger.info(f"✓ Completed: {phase_name} ({elapsed:.2f}s)")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                _logger.error(f"✗ Failed: {phase_name} ({elapsed:.2f}s) - {e}")
                raise
        return wrapper  # type: ignore
    return decorator


# =============================================================================
# PROGRESS TRACKING
# =============================================================================

@dataclass
class ProgressTracker:
    """
    Progress tracker for long-running operations.
    
    Provides visual progress updates suitable for notebook environments.
    
    Attributes:
        description: Description of the operation.
        total: Total number of items to process.
        log_interval: How often to log progress (items or percentage).
        logger: Logger instance to use.
    
    Example:
        >>> # As context manager
        >>> with ProgressTracker("Processing files", total=100) as tracker:
        ...     for file in files:
        ...         process(file)
        ...         tracker.update()
        
        >>> # Manual usage
        >>> tracker = ProgressTracker("Loading data", total=1000)
        >>> tracker.start()
        >>> for batch in batches:
        ...     process(batch)
        ...     tracker.update(len(batch))
        >>> tracker.finish()
    """
    
    description: str
    total: Optional[int] = None
    log_interval: int = 10  # Log every N% or N items
    logger: Optional[logging.Logger] = None
    
    # Internal state
    _current: int = field(default=0, init=False, repr=False)
    _start_time: Optional[float] = field(default=None, init=False, repr=False)
    _last_log_percent: int = field(default=0, init=False, repr=False)
    _logger: logging.Logger = field(init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Initialize the logger."""
        self._logger = self.logger or get_logger("progress")
    
    def start(self) -> "ProgressTracker":
        """
        Start progress tracking.
        
        Returns:
            Self for chaining.
        """
        self._current = 0
        self._start_time = time.perf_counter()
        self._last_log_percent = 0
        
        if self.total:
            self._logger.info(f"⏳ {self.description} (0/{self.total})")
        else:
            self._logger.info(f"⏳ {self.description}")
        
        return self
    
    def update(self, n: int = 1) -> None:
        """
        Update progress by n items.
        
        Args:
            n: Number of items completed (default: 1).
        """
        self._current += n
        
        if self.total:
            percent = int((self._current / self.total) * 100)
            
            # Log at intervals
            if percent >= self._last_log_percent + self.log_interval:
                elapsed = time.perf_counter() - (self._start_time or 0)
                rate = self._current / elapsed if elapsed > 0 else 0
                remaining = (self.total - self._current) / rate if rate > 0 else 0
                
                self._logger.info(
                    f"📊 {self.description}: {percent}% "
                    f"({self._current}/{self.total}) "
                    f"[{elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining]"
                )
                self._last_log_percent = percent
    
    def finish(self, message: Optional[str] = None) -> float:
        """
        Finish progress tracking.
        
        Args:
            message: Optional completion message.
        
        Returns:
            Total elapsed time in seconds.
        """
        elapsed = time.perf_counter() - (self._start_time or 0)
        
        if message:
            self._logger.info(f"✅ {self.description}: {message} ({elapsed:.2f}s)")
        else:
            items_msg = f" ({self._current} items)" if self._current else ""
            self._logger.info(f"✅ {self.description} completed{items_msg} ({elapsed:.2f}s)")
        
        return elapsed
    
    def __enter__(self) -> "ProgressTracker":
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if exc_type is None:
            self.finish()
        else:
            elapsed = time.perf_counter() - (self._start_time or 0)
            self._logger.error(
                f"❌ {self.description} failed after {elapsed:.2f}s: {exc_val}"
            )


# =============================================================================
# EXECUTION METRICS
# =============================================================================

@dataclass
class ExecutionMetrics:
    """
    Collect and report execution metrics for notebook cells or functions.
    
    Example:
        >>> metrics = ExecutionMetrics("Data Pipeline")
        >>> with metrics.track("Load"):
        ...     df = load_data()
        >>> with metrics.track("Transform"):
        ...     df = transform(df)
        >>> metrics.report()
    """
    
    name: str
    logger: Optional[logging.Logger] = None
    _phases: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _start_time: Optional[float] = field(default=None, init=False)
    _logger: logging.Logger = field(init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Initialize logger."""
        self._logger = self.logger or get_logger("metrics")
        self._start_time = time.perf_counter()
    
    @contextmanager
    def track(self, phase_name: str) -> Generator[None, None, None]:
        """
        Track execution time for a phase.
        
        Args:
            phase_name: Name of the phase to track.
        
        Yields:
            None
        
        Example:
            >>> with metrics.track("Data Loading"):
            ...     df = pd.read_parquet("data.parquet")
        """
        start = time.perf_counter()
        start_dt = datetime.now()
        error = None
        
        try:
            yield
        except Exception as e:
            error = str(e)
            raise
        finally:
            elapsed = time.perf_counter() - start
            self._phases.append({
                "phase": phase_name,
                "start_time": start_dt.isoformat(),
                "duration_seconds": round(elapsed, 3),
                "status": "error" if error else "success",
                "error": error,
            })
    
    def add_metric(self, name: str, value: Any) -> None:
        """
        Add a custom metric.
        
        Args:
            name: Metric name.
            value: Metric value.
        """
        self._phases.append({
            "phase": f"metric:{name}",
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })
    
    def report(self, detailed: bool = True) -> Dict[str, Any]:
        """
        Generate execution report.
        
        Args:
            detailed: Include detailed phase breakdown.
        
        Returns:
            Dict with execution metrics.
        """
        total_time = time.perf_counter() - (self._start_time or 0)
        
        # Calculate phase summary
        phase_times = [
            p for p in self._phases
            if "duration_seconds" in p
        ]
        
        report = {
            "name": self.name,
            "total_duration_seconds": round(total_time, 3),
            "phases_count": len(phase_times),
            "success_count": sum(1 for p in phase_times if p["status"] == "success"),
            "error_count": sum(1 for p in phase_times if p["status"] == "error"),
        }
        
        if detailed:
            report["phases"] = self._phases
        
        # Log summary
        self._logger.info(
            f"📈 {self.name} Metrics: "
            f"{report['phases_count']} phases, "
            f"{report['total_duration_seconds']:.2f}s total"
        )
        
        return report
    
    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert phase metrics to a DataFrame.
        
        Returns:
            pd.DataFrame with phase metrics.
        """
        import pandas as pd
        
        phase_data = [p for p in self._phases if "duration_seconds" in p]
        return pd.DataFrame(phase_data)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_dataframe_info(
    df: "pd.DataFrame",
    name: str = "DataFrame",
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log summary information about a DataFrame.
    
    Args:
        df: DataFrame to summarize.
        name: Display name for the DataFrame.
        logger: Logger to use.
    
    Example:
        >>> log_dataframe_info(df, "Sales Data")
        2026-01-19 10:30:00 | INFO | df | Sales Data: 10,000 rows × 15 cols, 12.5 MB
    """
    _logger = logger or get_logger("df")
    
    rows, cols = df.shape
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    null_count = df.isnull().sum().sum()
    null_pct = (null_count / (rows * cols)) * 100 if rows * cols > 0 else 0
    
    _logger.info(
        f"📋 {name}: {rows:,} rows × {cols} cols, "
        f"{memory_mb:.1f} MB, {null_pct:.1f}% nulls"
    )


def log_dict_summary(
    data: Dict[str, Any],
    name: str = "Data",
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log summary of a dictionary.
    
    Args:
        data: Dictionary to summarize.
        name: Display name.
        logger: Logger to use.
    """
    _logger = logger or get_logger("dict")
    
    _logger.info(f"📦 {name}: {len(data)} keys")
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            _logger.info(f"  • {key}: {len(value)} items")
        elif isinstance(value, dict):
            _logger.info(f"  • {key}: {len(value)} keys")
        else:
            _logger.info(f"  • {key}: {value}")


@contextmanager
def timed_operation(
    description: str,
    logger: Optional[logging.Logger] = None
) -> Generator[None, None, None]:
    """
    Context manager for timing an operation.
    
    Args:
        description: Operation description.
        logger: Logger to use.
    
    Yields:
        None
    
    Example:
        >>> with timed_operation("Loading large dataset"):
        ...     df = pd.read_parquet("large_file.parquet")
        Loading large dataset...
        Loading large dataset completed in 5.23s
    """
    _logger = logger or get_logger("timer")
    
    _logger.info(f"⏱️ {description}...")
    start = time.perf_counter()
    
    try:
        yield
        elapsed = time.perf_counter() - start
        _logger.info(f"⏱️ {description} completed in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.perf_counter() - start
        _logger.error(f"⏱️ {description} failed after {elapsed:.2f}s: {e}")
        raise


def create_run_id() -> str:
    """
    Create a unique run identifier.
    
    Returns:
        str: Unique run ID based on timestamp.
    
    Example:
        >>> run_id = create_run_id()
        >>> print(run_id)
        run_20260119_103045
    """
    return datetime.now().strftime("run_%Y%m%d_%H%M%S")
