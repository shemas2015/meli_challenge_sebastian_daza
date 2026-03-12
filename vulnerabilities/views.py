"""Django REST Framework Views"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import VulnerabilityReport, AnalysisResult, ScanReport
from .serializers import (
    VulnerabilityReportSerializer,
    AnalysisResultSerializer,
    ScanReportSerializer,
    ScanReportDetailSerializer,
)
from .repositories.analysis_result_repository import AnalysisResultRepository
from .services import ScanReportService


class VulnerabilityReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: Get all vulnerability reports
    retrieve: Get a specific vulnerability report by ID
    """
    queryset = VulnerabilityReport.objects.all().order_by('-created_at')
    serializer_class = VulnerabilityReportSerializer


class AnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: Get all analysis results
    retrieve: Get a specific analysis result by ID
    by_status: Filter by status
    by_validation_status: Filter by validation status
    """
    queryset = AnalysisResult.objects.select_related('report').all().order_by('-created_at')
    serializer_class = AnalysisResultSerializer
    repository = AnalysisResultRepository()

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        analysis_status = request.query_params.get('status')
        if not analysis_status:
            return Response({"error": "status parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        limit = int(request.query_params.get('limit', 100))
        results = self.repository.get_by_status(analysis_status, limit)
        return Response(self.get_serializer(results, many=True).data)

    @action(detail=False, methods=['get'])
    def by_validation_status(self, request):
        validation_status = request.query_params.get('validation_status')
        if not validation_status:
            return Response({"error": "validation_status parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        limit = int(request.query_params.get('limit', 100))
        results = self.repository.get_by_validation_status(validation_status, limit)
        return Response(self.get_serializer(results, many=True).data)


class ScanReportUploadView(APIView):
    """
    POST /api/vulnerabilities/upload  — Upload a PDF scanner report for automated triage.
    GET  /api/vulnerabilities/upload/<id>/ — Check processing status.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({'error': 'file must be a PDF'}, status=status.HTTP_400_BAD_REQUEST)

        llm_provider = request.data.get('llm_provider', 'anthropic')
        pdf_bytes = pdf_file.read()

        scan_report = ScanReport.objects.create(file_name=pdf_file.name)
        ScanReportService().process_scan_report(scan_report.id, pdf_bytes, llm_provider)

        return Response(ScanReportSerializer(scan_report).data, status=status.HTTP_202_ACCEPTED)

    def get(self, request, pk=None):
        if pk is None:
            scan_reports = ScanReport.objects.prefetch_related('vulnerability_reports__analysis').all()
            return Response(ScanReportSerializer(scan_reports, many=True).data)
        try:
            scan_report = ScanReport.objects.prefetch_related(
                'vulnerability_reports__analysis__agent_executions'
            ).get(pk=pk)
        except ScanReport.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScanReportDetailSerializer(scan_report).data)
