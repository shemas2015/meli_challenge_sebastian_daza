"""Django REST Framework Serializers"""
from rest_framework import serializers
from .models import VulnerabilityReport, AnalysisResult, AgentExecution, ScanReport


class AgentExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecution
        fields = [
            'id',
            'analysis',
            'agent_type',
            'started_at',
            'completed_at',
            'success',
            'error_message',
            'llm_prompt',
            'llm_response',
            'tokens_used'
        ]
        read_only_fields = ['id']


class ScanReportVulnerabilitySerializer(serializers.ModelSerializer):
    analysis_status = serializers.CharField(source='analysis.status', default=None)
    validation_status = serializers.CharField(source='analysis.validation_status', default=None)
    severity = serializers.CharField(source='analysis.severity', default=None)

    class Meta:
        model = VulnerabilityReport
        fields = ["id", "type", "endpoint", "method", "parameter", "payload", "description",
                  "can_auto_test", "skip_reason", "analysis_status", "validation_status", "severity"]


class ScanReportDetailVulnerabilitySerializer(serializers.ModelSerializer):
    analysis_status = serializers.CharField(source='analysis.status', default=None)
    validation_status = serializers.CharField(source='analysis.validation_status', default=None)
    severity = serializers.CharField(source='analysis.severity', default=None)
    confidence_score = serializers.FloatField(source='analysis.confidence_score', default=None)
    agent_reasoning = serializers.CharField(source='analysis.agent_reasoning', default=None)
    dynamic_analysis_result = serializers.JSONField(source='analysis.dynamic_analysis_result', default=None)
    agent_executions = AgentExecutionSerializer(source='analysis.agent_executions', many=True, read_only=True)

    class Meta:
        model = VulnerabilityReport
        fields = ["id", "type", "endpoint", "method", "parameter", "payload", "description",
                  "can_auto_test", "skip_reason", "analysis_status", "validation_status",
                  "severity", "confidence_score", "agent_reasoning", "dynamic_analysis_result",
                  "agent_executions"]


class ScanReportSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    vulnerability_reports = ScanReportVulnerabilitySerializer(many=True, read_only=True)

    def get_progress(self, obj):
        return f"{obj.processed_findings}/{obj.total_findings}"

    class Meta:
        model = ScanReport
        fields = ["id", "file_name", "status", "total_findings", "processed_findings", "progress",
                  "error_message", "created_at", "vulnerability_reports"]


class ScanReportDetailSerializer(ScanReportSerializer):
    vulnerability_reports = ScanReportDetailVulnerabilitySerializer(many=True, read_only=True)


class VulnerabilityReportSerializer(serializers.ModelSerializer):
    """
    Serializer for VulnerabilityReport model

    Used for creating and reading vulnerability reports.
    """

    class Meta:
        model = VulnerabilityReport
        fields = [
            'id',
            'type',
            'endpoint',
            'method',
            'parameter',
            'payload',
            'description',
            'target_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnalysisResultSerializer(serializers.ModelSerializer):
    """
    Serializer for AnalysisResult model

    Used for reading analysis results with nested agent executions.
    """
    agent_executions = AgentExecutionSerializer(
        many=True,
        read_only=True,
    )
    report = VulnerabilityReportSerializer(read_only=True)

    class Meta:
        model = AnalysisResult
        fields = [
            'id',
            'report',
            'status',
            'validation_status',
            'severity',
            'confidence_score',
            'dynamic_analysis_result',
            'agent_reasoning',
            'llm_model_used',
            'created_at',
            'updated_at',
            'agent_executions'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VulnerabilityAnalysisRequestSerializer(serializers.Serializer):
    """
    Serializer for vulnerability analysis request

    Used for POST /api/vulnerabilities/analyze endpoint.
    """
    # Vulnerability report data
    type = serializers.ChoiceField(
        choices=[
            'SQL_INJECTION',
            'XSS',
            'PATH_TRAVERSAL',
            'CSRF',
            'IDOR'
        ],
        required=True,
        help_text="Type of vulnerability"
    )
    endpoint = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Vulnerable endpoint path"
    )
    method = serializers.ChoiceField(
        choices=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        default='GET',
        help_text="HTTP method"
    )
    parameter = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Vulnerable parameter name"
    )
    payload = serializers.CharField(
        required=True,
        help_text="Exploit payload"
    )
    description = serializers.CharField(
        required=True,
        help_text="Vulnerability description"
    )
    target_url = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Target application URL (supports internal hostnames e.g. http://juice-shop:3000)"
    )
    # Analysis options
    run_dynamic_analysis = serializers.BooleanField(
        default=True,
        help_text="Run dynamic analysis (requires target_url)"
    )
    llm_provider = serializers.ChoiceField(
        choices=['openai', 'anthropic', 'google'],
        default='anthropic',
        help_text="LLM provider to use"
    )
    llm_model = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Specific LLM model (optional, uses provider default)"
    )

    def validate(self, data):
        if data.get('run_dynamic_analysis') and not data.get('target_url'):
            raise serializers.ValidationError(
                "target_url is required when run_dynamic_analysis is True"
            )
        return data


class VulnerabilityAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for vulnerability analysis response

    Used for response from POST /api/vulnerabilities/analyze endpoint.
    """
    report_id = serializers.IntegerField(
        help_text="ID of created vulnerability report"
    )
    analysis_id = serializers.IntegerField(
        help_text="ID of created analysis result"
    )
    status = serializers.CharField(
        help_text="Analysis status"
    )
    message = serializers.CharField(
        help_text="Status message"
    )
