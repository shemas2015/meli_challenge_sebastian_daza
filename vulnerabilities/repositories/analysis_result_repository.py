"""Analysis Result Repository"""
from typing import Optional, List
from django.core.exceptions import ObjectDoesNotExist

from ..models import AnalysisResult
from .base import BaseRepository


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """
    Read-only repository for AnalysisResult model

    Provides query operations for analysis results.
    Write operations are handled by Django ORM in the service layer.
    """

    def get_by_id(self, id: int) -> Optional[AnalysisResult]:
        """
        Get analysis result by ID

        Args:
            id: Analysis result ID

        Returns:
            AnalysisResult if found, None otherwise
        """
        try:
            return AnalysisResult.objects.select_related('report').get(pk=id)
        except ObjectDoesNotExist:
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[AnalysisResult]:
        """
        Get all analysis results with pagination

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of AnalysisResult objects
        """
        return list(
            AnalysisResult.objects.select_related('report').all()[offset:offset + limit]
        )

    def exists(self, id: int) -> bool:
        """
        Check if analysis result exists

        Args:
            id: Analysis result ID

        Returns:
            True if exists, False otherwise
        """
        return AnalysisResult.objects.filter(pk=id).exists()

    def count(self) -> int:
        """
        Count total analysis results

        Returns:
            Total number of results
        """
        return AnalysisResult.objects.count()

    # Custom query methods specific to AnalysisResult

    def get_by_report_id(self, report_id: int) -> Optional[AnalysisResult]:
        """
        Get analysis result by vulnerability report ID

        Args:
            report_id: VulnerabilityReport ID

        Returns:
            AnalysisResult if found, None otherwise
        """
        try:
            return AnalysisResult.objects.select_related('report').get(report_id=report_id)
        except ObjectDoesNotExist:
            return None

    def get_by_status(self, status: str, limit: int = 100) -> List[AnalysisResult]:
        """
        Get analysis results by status

        Args:
            status: Status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
            limit: Maximum number of records

        Returns:
            List of AnalysisResult objects
        """
        return list(
            AnalysisResult.objects.select_related('report')
            .filter(status=status)[:limit]
        )

    def get_by_validation_status(
        self,
        validation_status: str,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Get analysis results by validation status

        Args:
            validation_status: Validation status (TRUE_POSITIVE, FALSE_POSITIVE, INCONCLUSIVE)
            limit: Maximum number of records

        Returns:
            List of AnalysisResult objects
        """
        return list(
            AnalysisResult.objects.select_related('report')
            .filter(validation_status=validation_status)[:limit]
        )

