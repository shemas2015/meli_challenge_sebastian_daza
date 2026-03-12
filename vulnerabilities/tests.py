import io
import json
import threading
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client

from .models import ScanReport, VulnerabilityReport, AnalysisResult, AgentExecution
from .agents.pdf_parser_agent import PDFParserAgent
from .dynamic_analysis.response_analyzer import ResponseAnalyzer
from .dynamic_analysis.analyzer import DynamicAnalyzer
from .services.vulnerability_analysis import VulnerabilityAnalysisService
from .services.scan_report import ScanReportService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes (no content stream, yields no extractable text)."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )


def _orchestrator_ok_result():
    return {
        "parser": {"agent_type": "PARSER", "success": True, "data": {}},
        "dynamic_validator": {"agent_type": "DYNAMIC_VALIDATOR", "success": True, "data": {}},
        "triage": {
            "agent_type": "TRIAGE",
            "success": True,
            "data": {
                "validation_status": "TRUE_POSITIVE",
                "severity": "HIGH",
                "confidence_score": 0.9,
                "reasoning": "confirmed",
            },
        },
        "metadata": {"llm_provider": "anthropic", "llm_model": None, "analysis_duration": 1.0},
    }


# ---------------------------------------------------------------------------
# 1. API Endpoints
# ---------------------------------------------------------------------------

class ScanReportUploadAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.upload_url = "/api/vulnerabilities/upload"
        self.list_url = "/api/vulnerabilities/uploads/"

    def test_upload_no_file_returns_400(self):
        response = self.client.post(self.upload_url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json()["error"].lower())

    def test_upload_non_pdf_returns_400(self):
        fake_txt = io.BytesIO(b"not a pdf")
        fake_txt.name = "report.txt"
        response = self.client.post(self.upload_url, {"file": fake_txt})
        self.assertEqual(response.status_code, 400)
        self.assertIn("pdf", response.json()["error"].lower())

    @patch("vulnerabilities.services.scan_report.ScanReportService.process_scan_report")
    def test_upload_valid_pdf_returns_202_and_creates_scan_report(self, mock_process):
        pdf = io.BytesIO(_make_pdf_bytes())
        pdf.name = "report.pdf"
        response = self.client.post(self.upload_url, {"file": pdf})
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn("id", data)
        self.assertTrue(ScanReport.objects.filter(id=data["id"]).exists())
        mock_process.assert_called_once()

    def test_list_scan_reports_returns_200(self):
        ScanReport.objects.create(file_name="a.pdf")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_get_scan_report_detail_returns_200(self):
        scan = ScanReport.objects.create(file_name="b.pdf")
        response = self.client.get(f"/api/vulnerabilities/uploads/{scan.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], scan.id)

    def test_get_scan_report_not_found_returns_404(self):
        response = self.client.get("/api/vulnerabilities/uploads/99999/")
        self.assertEqual(response.status_code, 404)


class VulnerabilityReportAPITest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_list_reports_returns_200(self):
        response = self.client.get("/api/vulnerabilities/reports/")
        self.assertEqual(response.status_code, 200)

    def test_list_analyses_returns_200(self):
        response = self.client.get("/api/vulnerabilities/analyses/")
        self.assertEqual(response.status_code, 200)

    def test_by_status_missing_param_returns_400(self):
        response = self.client.get("/api/vulnerabilities/analyses/by_status/")
        self.assertEqual(response.status_code, 400)

    def test_by_validation_status_missing_param_returns_400(self):
        response = self.client.get("/api/vulnerabilities/analyses/by_validation_status/")
        self.assertEqual(response.status_code, 400)

    def test_by_status_with_param_returns_200(self):
        response = self.client.get("/api/vulnerabilities/analyses/by_status/?status=COMPLETED")
        self.assertEqual(response.status_code, 200)

    def test_by_validation_status_with_param_returns_200(self):
        response = self.client.get("/api/vulnerabilities/analyses/by_validation_status/?validation_status=TRUE_POSITIVE")
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# 2. PDFParserAgent.validate_finding
# ---------------------------------------------------------------------------

class ValidateFindingTest(TestCase):

    def _base(self):
        return {
            "type": "SQL_INJECTION",
            "endpoint": "/rest/products/search",
            "description": "SQLi via q param",
            "target_url": "http://localhost:3000",
        }

    def test_complete_valid_finding(self):
        can, reason = PDFParserAgent.validate_finding(self._base())
        self.assertTrue(can)
        self.assertEqual(reason, "")

    def test_missing_endpoint(self):
        f = self._base()
        del f["endpoint"]
        can, reason = PDFParserAgent.validate_finding(f)
        self.assertFalse(can)
        self.assertIn("endpoint", reason)

    def test_missing_multiple_fields(self):
        can, reason = PDFParserAgent.validate_finding({})
        self.assertFalse(can)
        for field in ["type", "endpoint", "description", "target_url"]:
            self.assertIn(field, reason)

    def test_invalid_type(self):
        f = self._base()
        f["type"] = "BUFFER_OVERFLOW"
        can, reason = PDFParserAgent.validate_finding(f)
        self.assertFalse(can)
        self.assertIn("BUFFER_OVERFLOW", reason)

    def test_all_required_present_but_unknown_type(self):
        f = self._base()
        f["type"] = "RCE"
        can, reason = PDFParserAgent.validate_finding(f)
        self.assertFalse(can)
        self.assertIn("Unknown vulnerability type", reason)


# ---------------------------------------------------------------------------
# 3. ResponseAnalyzer (no HTTP — pure logic)
# ---------------------------------------------------------------------------

class ResponseAnalyzerTest(TestCase):

    def setUp(self):
        self.analyzer = ResponseAnalyzer()

    def _ok(self, body="", status_code=200, extra=None):
        r = {"success": True, "body": body, "status_code": status_code}
        if extra:
            r.update(extra)
        return r

    def _fail(self):
        return {"success": False}

    # SQL Injection
    def test_sql_injection_error_in_body(self):
        r = self.analyzer.analyze(self._ok(body="SQLITE_ERROR: incomplete input"), "SQL_INJECTION")
        self.assertTrue(r["vulnerable"])
        self.assertGreater(r["confidence"], 0.5)

    def test_sql_injection_500_status(self):
        r = self.analyzer.analyze(self._ok(status_code=500), "SQL_INJECTION")
        self.assertTrue(r["vulnerable"])

    def test_sql_injection_clean_response(self):
        r = self.analyzer.analyze(self._ok(body="[]"), "SQL_INJECTION")
        self.assertFalse(r["vulnerable"])

    def test_sql_injection_failed_request(self):
        r = self.analyzer.analyze(self._fail(), "SQL_INJECTION")
        self.assertFalse(r["vulnerable"])

    # XSS
    def test_xss_payload_reflected(self):
        r = self.analyzer.analyze(self._ok(body="<script>alert(1)</script>"), "XSS")
        self.assertTrue(r["vulnerable"])

    def test_xss_dom_detected_by_playwright(self):
        r = self.analyzer.analyze(self._ok(extra={"dom_xss_detected": True}), "XSS")
        self.assertTrue(r["vulnerable"])
        self.assertGreaterEqual(r["confidence"], 0.9)

    def test_xss_not_reflected(self):
        r = self.analyzer.analyze(self._ok(body="safe content"), "XSS")
        self.assertFalse(r["vulnerable"])

    # CSRF
    def test_csrf_200_means_vulnerable(self):
        r = self.analyzer.analyze(self._ok(status_code=200), "CSRF")
        self.assertTrue(r["vulnerable"])

    def test_csrf_403_means_protected(self):
        r = self.analyzer.analyze(self._ok(status_code=403), "CSRF")
        self.assertFalse(r["vulnerable"])

    # Path Traversal
    def test_path_traversal_etc_passwd(self):
        r = self.analyzer.analyze(self._ok(body="root:/root:/bin/bash"), "PATH_TRAVERSAL")
        self.assertTrue(r["vulnerable"])

    def test_path_traversal_no_indicators(self):
        r = self.analyzer.analyze(self._ok(body="not found"), "PATH_TRAVERSAL")
        self.assertFalse(r["vulnerable"])

    # IDOR
    def test_idor_200_with_data(self):
        body = json.dumps({"data": [{"id": 1, "name": "secret"}]})
        r = self.analyzer.analyze(self._ok(body=body), "IDOR")
        self.assertTrue(r["vulnerable"])

    def test_idor_401_means_protected(self):
        r = self.analyzer.analyze(self._ok(status_code=401), "IDOR")
        self.assertFalse(r["vulnerable"])

    # Unknown type
    def test_unknown_type_returns_error(self):
        r = self.analyzer.analyze(self._ok(), "UNKNOWN")
        self.assertIn("error", r)


# ---------------------------------------------------------------------------
# 4. DynamicAnalyzer (mocked HTTP)
# ---------------------------------------------------------------------------

class DynamicAnalyzerTest(TestCase):

    def setUp(self):
        self.analyzer = DynamicAnalyzer()

    def _mock_executor(self, body="", status_code=200):
        response = {"success": True, "body": body, "status_code": status_code}
        mock = MagicMock(return_value={"response": response})
        return mock

    def test_sql_injection_routes_correctly(self):
        with patch.object(self.analyzer.executor, "execute_sql_injection",
                          self._mock_executor(body="SQLITE_ERROR", status_code=500)) as m:
            result = self.analyzer.analyze(
                vulnerability_type="SQL_INJECTION",
                target_url="http://localhost:3000",
                endpoint="/rest/products/search",
                parameter="q",
                payload="' OR 1=1--",
            )
            m.assert_called_once()
        self.assertIn("vulnerable", result)
        self.assertIn("analysis", result)

    def test_unknown_vulnerability_type_returns_error(self):
        result = self.analyzer.analyze(
            vulnerability_type="RCE",
            target_url="http://localhost:3000",
            endpoint="/shell",
            parameter="cmd",
            payload="ls",
        )
        self.assertFalse(result["vulnerable"])
        self.assertIn("error", result)

    def test_xss_routes_correctly(self):
        with patch.object(self.analyzer.executor, "execute_xss",
                          self._mock_executor(body="<script>alert(1)</script>")) as m:
            result = self.analyzer.analyze(
                vulnerability_type="XSS",
                target_url="http://localhost:3000",
                endpoint="/search",
                parameter="q",
                payload="<script>alert(1)</script>",
            )
            m.assert_called_once()
        self.assertEqual(result["vulnerability_type"], "XSS")


# ---------------------------------------------------------------------------
# 5. VulnerabilityAnalysisService
# ---------------------------------------------------------------------------

MOCK_ORCHESTRATOR_RESULT = _orchestrator_ok_result()


class VulnerabilityAnalysisServiceTest(TestCase):

    def _vulnerability_data(self):
        return {
            "type": "SQL_INJECTION",
            "endpoint": "/rest/products/search",
            "method": "GET",
            "parameter": "q",
            "payload": "' OR 1=1--",
            "description": "SQLi in search",
            "target_url": "http://localhost:3000",
        }

    @patch("vulnerabilities.services.vulnerability_analysis.VulnerabilityAnalysisOrchestrator")
    def test_analyze_no_dynamic_creates_report_and_analysis(self, MockOrch):
        MockOrch.return_value.analyze_vulnerability.return_value = MOCK_ORCHESTRATOR_RESULT
        MockOrch.return_value.get_final_verdict.return_value = {
            "validation_status": "TRUE_POSITIVE",
            "severity": "HIGH",
            "confidence_score": 0.9,
            "reasoning": "confirmed",
        }
        MockOrch.return_value.llm_provider = "anthropic"
        MockOrch.return_value.llm_model = None

        svc = VulnerabilityAnalysisService()
        result = svc.analyze_vulnerability(self._vulnerability_data(), run_dynamic=False)

        self.assertEqual(result["status"], "COMPLETED")
        report = VulnerabilityReport.objects.get(id=result["report_id"])
        analysis = AnalysisResult.objects.get(id=result["analysis_id"])
        self.assertEqual(report.type, "SQL_INJECTION")
        self.assertEqual(analysis.status, "COMPLETED")
        self.assertEqual(analysis.validation_status, "TRUE_POSITIVE")
        self.assertIsNone(analysis.dynamic_analysis_result)

    @patch("vulnerabilities.services.vulnerability_analysis.VulnerabilityAnalysisOrchestrator")
    def test_analyze_with_dynamic_saves_dynamic_result(self, MockOrch):
        MockOrch.return_value.analyze_vulnerability.return_value = MOCK_ORCHESTRATOR_RESULT
        MockOrch.return_value.get_final_verdict.return_value = {
            "validation_status": "TRUE_POSITIVE",
            "severity": "HIGH",
            "confidence_score": 0.9,
            "reasoning": "confirmed",
        }
        MockOrch.return_value.llm_provider = "anthropic"
        MockOrch.return_value.llm_model = None

        dynamic_result = {"vulnerable": True, "confidence": 0.9}
        with patch("vulnerabilities.services.vulnerability_analysis.DynamicAnalyzer") as MockDyn:
            MockDyn.return_value.analyze.return_value = dynamic_result
            svc = VulnerabilityAnalysisService()
            result = svc.analyze_vulnerability(self._vulnerability_data(), run_dynamic=True)

        analysis = AnalysisResult.objects.get(id=result["analysis_id"])
        self.assertEqual(analysis.dynamic_analysis_result, dynamic_result)

    @patch("vulnerabilities.services.vulnerability_analysis.VulnerabilityAnalysisOrchestrator")
    def test_analyze_orchestrator_failure_sets_failed_status(self, MockOrch):
        MockOrch.return_value.analyze_vulnerability.side_effect = RuntimeError("LLM timeout")
        MockOrch.return_value.llm_provider = "anthropic"
        MockOrch.return_value.llm_model = None

        svc = VulnerabilityAnalysisService()
        result = svc.analyze_vulnerability(self._vulnerability_data(), run_dynamic=False)

        self.assertEqual(result["status"], "FAILED")
        analysis = AnalysisResult.objects.get(id=result["analysis_id"])
        self.assertEqual(analysis.status, "FAILED")
        self.assertIn("LLM timeout", analysis.agent_reasoning)

    @patch("vulnerabilities.services.vulnerability_analysis.VulnerabilityAnalysisOrchestrator")
    def test_analyze_creates_agent_executions(self, MockOrch):
        MockOrch.return_value.analyze_vulnerability.return_value = MOCK_ORCHESTRATOR_RESULT
        MockOrch.return_value.get_final_verdict.return_value = {
            "validation_status": "TRUE_POSITIVE",
            "severity": "HIGH",
            "confidence_score": 0.9,
            "reasoning": "confirmed",
        }
        MockOrch.return_value.llm_provider = "anthropic"
        MockOrch.return_value.llm_model = None

        svc = VulnerabilityAnalysisService()
        result = svc.analyze_vulnerability(self._vulnerability_data(), run_dynamic=False)

        analysis = AnalysisResult.objects.get(id=result["analysis_id"])
        executions = AgentExecution.objects.filter(analysis=analysis)
        self.assertEqual(executions.count(), 3)
        types = set(executions.values_list("agent_type", flat=True))
        self.assertIn("PARSER", types)
        self.assertIn("DYNAMIC_VALIDATOR", types)
        self.assertIn("TRIAGE", types)


# ---------------------------------------------------------------------------
# 6. ScanReportService
# ---------------------------------------------------------------------------

class ScanReportServiceTest(TestCase):

    def _run_sync(self, scan_report_id, pdf_bytes, llm_provider="anthropic"):
        """Run process_scan_report synchronously, blocking the thread and preserving the DB connection."""
        with patch.object(threading.Thread, "start", lambda self: self.run()), \
             patch("vulnerabilities.services.scan_report.close_old_connections"):
            ScanReportService().process_scan_report(scan_report_id, pdf_bytes, llm_provider)

    def test_blank_pdf_sets_failed_status(self):
        scan = ScanReport.objects.create(file_name="blank.pdf")
        # _make_pdf_bytes() yields no extractable text — page has no content stream
        self._run_sync(scan.id, _make_pdf_bytes())
        scan.refresh_from_db()
        self.assertEqual(scan.status, "FAILED")
        self.assertIn("text", scan.error_message.lower())

    @patch("vulnerabilities.services.scan_report.PDFParserAgent.extract_vulnerabilities")
    @patch("vulnerabilities.services.scan_report.VulnerabilityAnalysisService.analyze_vulnerability")
    def test_valid_finding_triggers_analysis(self, mock_analyze, mock_extract):
        mock_extract.return_value = [{
            "type": "SQL_INJECTION",
            "endpoint": "/rest/products/search",
            "description": "SQLi",
            "target_url": "http://localhost:3000",
            "method": "GET",
            "parameter": "q",
            "payload": "' OR 1=1--",
        }]
        mock_analyze.return_value = {"status": "COMPLETED", "report_id": 1, "analysis_id": 1, "message": "ok"}

        pdf_with_text = _make_pdf_bytes()

        scan = ScanReport.objects.create(file_name="report.pdf")

        with patch("pypdf.PdfReader") as MockReader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Vulnerability Report: SQL injection found"
            MockReader.return_value.pages = [mock_page]
            self._run_sync(scan.id, pdf_with_text)

        scan.refresh_from_db()
        self.assertEqual(scan.status, "COMPLETED")
        self.assertEqual(scan.total_findings, 1)
        mock_analyze.assert_called_once()

    @patch("vulnerabilities.services.scan_report.PDFParserAgent.extract_vulnerabilities")
    def test_invalid_finding_creates_report_with_skip_reason(self, mock_extract):
        mock_extract.return_value = [{
            "type": "SQL_INJECTION",
            # missing endpoint, description, target_url
        }]

        scan = ScanReport.objects.create(file_name="report.pdf")

        with patch("pypdf.PdfReader") as MockReader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Some report text"
            MockReader.return_value.pages = [mock_page]
            self._run_sync(scan.id, _make_pdf_bytes())

        scan.refresh_from_db()
        self.assertEqual(scan.status, "COMPLETED")
        reports = VulnerabilityReport.objects.filter(scan_report=scan)
        self.assertEqual(reports.count(), 1)
        report = reports.first()
        self.assertFalse(report.can_auto_test)
        self.assertIn("Missing", report.skip_reason)
