"""Dynamic Validator Agent - Validates vulnerabilities through dynamic testing"""
import json
from typing import Dict, Any
from crewai import Agent, Task
from .base import BaseVulnerabilityAgent


class DynamicValidatorAgent(BaseVulnerabilityAgent):
    """
    Agent responsible for dynamic vulnerability validation

    Role: Execute and validate vulnerabilities through dynamic testing
    Goal: Confirm or refute vulnerabilities through actual exploitation attempts
    """

    def _create_agent(self) -> Agent:
        return Agent(
            role="Dynamic Security Validator",
            goal="Validate vulnerabilities through dynamic testing and exploitation",
            backstory="""You are an expert penetration tester with extensive experience
            in dynamic application security testing. You excel at crafting exploits,
            analyzing HTTP responses, and determining if vulnerabilities are exploitable
            in real-world scenarios. You understand the difference between theoretical
            vulnerabilities and actual security risks.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def create_task(self, context: Dict[str, Any]) -> Task:
        """
        Create dynamic validation task

        Args:
            context: Dict with vulnerability info and dynamic analysis results

        Returns:
            Task for dynamic validation
        """
        vuln_type = context.get('vulnerability_type', 'UNKNOWN')
        endpoint = context.get('endpoint', 'N/A')
        dynamic_results = context.get('dynamic_analysis_result', {})

        description = f"""
        Perform dynamic validation for a reported {vuln_type} vulnerability.

        Vulnerability Details:
        - Type: {vuln_type}
        - Endpoint: {endpoint}
        - Method: {context.get('method', 'GET')}
        - Parameter: {context.get('parameter', 'N/A')}
        - Payload: {context.get('payload', 'N/A')}

        Dynamic Testing Results:
        {dynamic_results}

        Your tasks:
        1. Analyze the dynamic testing results
        2. Determine if the vulnerability is exploitable
        3. Assess the actual impact and severity
        4. Provide evidence-based reasoning

        Validation Criteria:
        - For SQL_INJECTION: Check for database errors, data leakage, authentication bypass
        - For XSS: Check if payload executed, DOM manipulation, script injection
        - For PATH_TRAVERSAL: Check if sensitive files accessed, directory listing
        - For CSRF: Check if state-changing operations succeeded without proper tokens
        - For IDOR: Check if unauthorized data access was successful

        Analyze:
        - HTTP response codes
        - Response body content
        - Response headers
        - Error messages
        - Response time anomalies

        Return your validation in JSON format.
        """

        return Task(
            description=description,
            agent=self.agent,
            expected_output="""A JSON object with the following structure:
            {
                "is_vulnerable": boolean,
                "exploitability": "CONFIRMED|PROBABLE|UNLIKELY|NOT_EXPLOITABLE",
                "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
                "confidence": float (0.0-1.0),
                "evidence": {
                    "response_code": int,
                    "indicators_found": [list of exploitation indicators],
                    "response_snippets": [relevant response excerpts]
                },
                "reasoning": "detailed explanation based on dynamic testing results",
                "impact_assessment": "description of actual impact if exploited",
                "recommendation": "remediation steps"
            }"""
        )

    def process_result(self, task_output: Any) -> Dict[str, Any]:
        """
        Process the dynamic validation task output

        Args:
            task_output: Raw output from the task

        Returns:
            Structured dictionary with validation results
        """
        try:
            if isinstance(task_output, str):
                result = json.loads(task_output)
            else:
                result = task_output

            return {
                "success": True,
                "data": result,
                "agent_type": "DYNAMIC_VALIDATOR"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_output": str(task_output),
                "agent_type": "DYNAMIC_VALIDATOR"
            }
