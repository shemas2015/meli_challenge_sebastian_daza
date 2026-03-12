"""Repository layer for data access"""

from .base import BaseRepository
from .analysis_result_repository import AnalysisResultRepository
__all__ = [
    "BaseRepository",
    "AnalysisResultRepository",
]
