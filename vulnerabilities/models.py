from django.db import models


class ScanReport(models.Model):
    """Represents an uploaded PDF scanner report"""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_findings = models.IntegerField(default=0)
    processed_findings = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scan_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ScanReport {self.file_name} - {self.status}"


class VulnerabilityReport(models.Model):
    """Vulnerability report submitted for triage"""

    VULNERABILITY_TYPES = [
        ("SQL_INJECTION", "SQL Injection"),
        ("XSS", "Cross-Site Scripting"),
        ("PATH_TRAVERSAL", "Path Traversal"),
        ("CSRF", "Cross-Site Request Forgery"),
        ("IDOR", "Insecure Direct Object Reference"),
    ]

    scan_report = models.ForeignKey(
        ScanReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="vulnerability_reports"
    )

    type = models.CharField(max_length=50, choices=VULNERABILITY_TYPES)
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10, default="GET")
    parameter = models.CharField(max_length=200, blank=True, null=True)
    payload = models.TextField(blank=True, null=True)
    description = models.TextField()
    target_url = models.URLField(max_length=500)

    can_auto_test = models.BooleanField(default=True)
    skip_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vulnerability_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.endpoint}"


class AnalysisResult(models.Model):
    """Analysis result from AI agents"""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    VALIDATION_CHOICES = [
        ("TRUE_POSITIVE", "True Positive"),
        ("FALSE_POSITIVE", "False Positive"),
        ("INCONCLUSIVE", "Inconclusive"),
    ]

    SEVERITY_CHOICES = [
        ("CRITICAL", "Critical"),
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
        ("INFO", "Informational"),
    ]

    report = models.OneToOneField(
        VulnerabilityReport,
        on_delete=models.CASCADE,
        related_name="analysis"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    validation_status = models.CharField(max_length=20, choices=VALIDATION_CHOICES, blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)

    static_analysis_result = models.JSONField(blank=True, null=True)
    dynamic_analysis_result = models.JSONField(blank=True, null=True)
    agent_reasoning = models.TextField(blank=True, null=True)

    llm_model_used = models.CharField(max_length=100, blank=True, null=True)
    total_tokens = models.IntegerField(blank=True, null=True)
    analysis_duration = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analysis_results"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis for {self.report} - {self.status}"


class AgentExecution(models.Model):
    """Tracks individual agent executions"""

    AGENT_TYPES = [
        ("PARSER", "Parser Agent"),
        ("STATIC_ANALYZER", "Static Analyzer Agent"),
        ("DYNAMIC_VALIDATOR", "Dynamic Validator Agent"),
        ("TRIAGE", "Triage Agent"),
        ("PDF_PARSER", "PDF Parser Agent"),
    ]

    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name="agent_executions"
    )

    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    input_data = models.JSONField(blank=True, null=True)
    output_data = models.JSONField(blank=True, null=True)

    llm_prompt = models.TextField(blank=True, null=True)
    llm_response = models.TextField(blank=True, null=True)
    tokens_used = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "agent_executions"
        ordering = ["started_at"]

    def __str__(self):
        return f"{self.get_agent_type_display()} - {self.analysis.report.id}"
