"""Configuration constants for the Job-Shop Scheduling application."""

from typing import Final

# Solver Configuration
DEFAULT_NUM_WORKERS: Final[int] = 8
DEFAULT_TIME_LIMIT: Final[float] = 30.0
MIN_TIME_LIMIT: Final[float] = 0.0
MAX_TIME_LIMIT: Final[float] = 300.0

# Visualization Configuration
DEFAULT_GANTT_HEIGHT: Final[int] = 520
DEFAULT_OUTPUT_PATH: Final[str] = "output/gantt.png"
MAINTENANCE_COLOR: Final[str] = "#94a3b8"
MAKESPAN_LINE_COLOR: Final[str] = "firebrick"
MARKER_LINE_WIDTH: Final[float] = 0.6

# UI Configuration
DEFAULT_UI_TIME_LIMIT: Final[float] = 8.0
BASELINE_SCENARIO: Final[str] = "preparation_commandes"

# Logging Configuration
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
