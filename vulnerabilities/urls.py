"""URL Configuration for vulnerabilities app"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VulnerabilityReportViewSet, AnalysisResultViewSet, ScanReportUploadView

router = DefaultRouter()
router.register(r'reports', VulnerabilityReportViewSet, basename='vulnerability-report')
router.register(r'analyses', AnalysisResultViewSet, basename='analysis-result')

urlpatterns = [
    path('upload', ScanReportUploadView.as_view(), name='scan-report-upload'),
    path('uploads/', ScanReportUploadView.as_view(), name='scan-report-list'),
    path('uploads/<int:pk>/', ScanReportUploadView.as_view(), name='scan-report-status'),
    path('', include(router.urls)),
]
