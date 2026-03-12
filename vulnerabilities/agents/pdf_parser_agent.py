"""PDF Parser Agent - Extracts vulnerability findings from scanner PDF reports"""
import json
import re
from typing import List, Dict, Any, Optional

from crewai import Agent, Task, Crew, Process

from .base import LLMProvider

VALID_TYPES = ["SQL_INJECTION", "XSS", "PATH_TRAVERSAL", "CSRF", "IDOR"]
REQUIRED_FIELDS = ["type", "endpoint", "description", "target_url"]


class PDFParserAgent:
    """
    Extracts structured vulnerability findings from raw PDF scanner report text.
    Returns a list of findings, each validated for auto-testing eligibility.
    """

    def __init__(self, llm_provider: str = "anthropic", llm_model: Optional[str] = None):
        self.llm = LLMProvider.get_llm(llm_provider, llm_model, temperature=0.1)
        self.agent = Agent(
            role="Security Report Analyst",
            goal="Extract all vulnerability findings from scanner reports as structured JSON",
            backstory=(
                "You are an expert security analyst who reads vulnerability scanner reports "
                "and extracts structured data from each finding with high precision."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def extract_vulnerabilities(self, pdf_text: str) -> List[Dict[str, Any]]:
        """
        Extract a list of vulnerability findings from PDF text.

        Args:
            pdf_text: Raw text extracted from the scanner PDF report

        Returns:
            List of finding dicts with vulnerability data
        """
        task = Task(
            description=f"""
Analyze this vulnerability scanner report and extract ALL vulnerability findings.

For each finding return a JSON object with:
- type: one of SQL_INJECTION, XSS, PATH_TRAVERSAL, CSRF, IDOR
- endpoint: the affected URL path (e.g. /rest/products/search)
- method: HTTP method (GET, POST, PUT, DELETE, PATCH), default GET
- parameter: vulnerable parameter name (or null if unknown)
- payload: example exploit payload string (or null if unknown). IMPORTANT: for CSRF findings, if the report contains a JSON block labeled "Payload (auto-test)" or similar with fields like "credentials", "login_url", "form_data", extract that entire JSON object as a compact single-line string for this field.
- description: brief description of the vulnerability
- target_url: base URL of the target application (e.g. http://juice-shop:3000)
- run_dynamic_analysis: always true
- llm_provider: always "anthropic"

Return ONLY a valid JSON array of finding objects. No extra text outside the array.
If a field cannot be determined from the report, set it to null.

Report content:
{pdf_text[:8000]}
            """,
            agent=self.agent,
            expected_output="A JSON array of vulnerability finding objects.",
        )

        crew = Crew(agents=[self.agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()

        raw = result.raw if hasattr(result, "raw") else str(result)
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        raw = match.group(1).strip() if match else raw.strip()

        return json.loads(raw)

    @staticmethod
    def validate_finding(finding: Dict[str, Any]):
        """
        Check if a finding has enough data for automatic testing.

        Returns:
            (can_auto_test: bool, skip_reason: str)
        """
        missing = [f for f in REQUIRED_FIELDS if not finding.get(f)]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        if finding.get("type") not in VALID_TYPES:
            return False, f"Unknown vulnerability type: {finding.get('type')!r}"
        return True, ""
