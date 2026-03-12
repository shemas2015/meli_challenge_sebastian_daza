import io
import threading

import pypdf

from django.db import close_old_connections

from ..models import VulnerabilityReport, ScanReport
from ..agents.pdf_parser_agent import PDFParserAgent
from .vulnerability_analysis import VulnerabilityAnalysisService


class ScanReportService:

    def process_scan_report(
        self,
        scan_report_id: int,
        pdf_bytes: bytes,
        llm_provider: str = "anthropic",
    ):
        """Start background processing of a scan report PDF."""

        def _run():
            close_old_connections()
            try:
                scan_report = ScanReport.objects.get(id=scan_report_id)
                scan_report.status = "PROCESSING"
                scan_report.save()

                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                pdf_text = '\n'.join(page.extract_text() or '' for page in reader.pages)

                if not pdf_text.strip():
                    scan_report.status = "FAILED"
                    scan_report.error_message = "Could not extract text from PDF"
                    scan_report.save()
                    return

                parser = PDFParserAgent(llm_provider)
                findings = parser.extract_vulnerabilities(pdf_text)

                scan_report.total_findings = len(findings)
                scan_report.save()

                analysis_service = VulnerabilityAnalysisService(llm_provider=llm_provider)

                for finding in findings:
                    can_auto_test, skip_reason = PDFParserAgent.validate_finding(finding)

                    if can_auto_test:
                        analysis_service.analyze_vulnerability(
                            vulnerability_data=finding,
                            run_dynamic=True,
                            scan_report=scan_report,
                        )
                    else:
                        VulnerabilityReport.objects.create(
                            scan_report=scan_report,
                            type=finding.get("type") if finding.get("type") in
                                 ["SQL_INJECTION", "XSS", "PATH_TRAVERSAL", "CSRF", "IDOR"]
                                 else "SQL_INJECTION",
                            endpoint=finding.get("endpoint", ""),
                            method=finding.get("method", "GET"),
                            parameter=finding.get("parameter", ""),
                            payload=finding.get("payload", ""),
                            description=finding.get("description", ""),
                            target_url=finding.get("target_url", "http://unknown"),
                            can_auto_test=False,
                            skip_reason=skip_reason,
                        )

                    scan_report.processed_findings += 1
                    scan_report.save()

                scan_report.status = "COMPLETED"
                scan_report.save()

            except Exception as e:
                try:
                    scan_report = ScanReport.objects.get(id=scan_report_id)
                    scan_report.status = "FAILED"
                    scan_report.error_message = str(e)
                    scan_report.save()
                except Exception:
                    pass
            finally:
                close_old_connections()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
