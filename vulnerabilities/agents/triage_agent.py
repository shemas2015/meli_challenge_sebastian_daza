"""Triage Agent - Makes final determination on vulnerability validity"""
import json
from typing import Dict, Any
from crewai import Agent, Task
from .base import BaseVulnerabilityAgent


class TriageAgent(BaseVulnerabilityAgent):
    """
    Agent responsible for final vulnerability triage

    Role: Synthesize all analysis results and make final determination
    Goal: Classify vulnerabilities as TRUE_POSITIVE, FALSE_POSITIVE, or INCONCLUSIVE
    """

    def _create_agent(self) -> Agent:
        return Agent(
            role="Security Vulnerability Triager",
            goal="Make final determination on vulnerability validity based on all available evidence",
            backstory="""You are a seasoned application security lead with years of
            experience in vulnerability management and triage. You excel at synthesizing
            information from multiple sources (static analysis, dynamic testing, security
            research) to make accurate, well-reasoned decisions about vulnerability validity.
            You understand the difference between theoretical risks and practical exploits.
            You are thorough, analytical, and always provide clear reasoning for your decisions.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def create_task(self, context: Dict[str, Any]) -> Task:
        """
        Create triage task

        Args:
            context: Dict with all analysis results

        Returns:
            Task for final triage decision
        """
        vuln_type = context.get('vulnerability_type', 'UNKNOWN')
        endpoint = context.get('endpoint', 'N/A')
        dynamic_result = context.get('dynamic_validation', {})

        description = f"""
        Perform final triage on a reported {vuln_type} vulnerability.

        Vulnerability Report:
        - Type: {vuln_type}
        - Endpoint: {endpoint}
        - Method: {context.get('method', 'GET')}
        - Parameter: {context.get('parameter', 'N/A')}
        - Description: {context.get('description', 'N/A')}

        Dynamic Validation Results:
        {dynamic_result}

        Your tasks:
        1. Review the dynamic validation evidence
        2. Make final determination: TRUE_POSITIVE, FALSE_POSITIVE, or INCONCLUSIVE
        3. Assign final severity rating
        4. Provide comprehensive reasoning

        Decision Criteria:
        - TRUE_POSITIVE: Confirmed exploitation in dynamic testing
        - FALSE_POSITIVE: No evidence of vulnerability, or vulnerability not exploitable
        - INCONCLUSIVE: Conflicting evidence, insufficient data, or edge case

        Severity Guidelines (for TRUE_POSITIVE):
        - CRITICAL: Remote code execution, authentication bypass, data breach
        - HIGH: SQL injection, XSS in sensitive contexts, privilege escalation
        - MEDIUM: CSRF on important operations, limited IDOR
        - LOW: Information disclosure, minor CSRF
        - INFO: Best practice violations, no direct security impact

        Consider:
        - Quality and clarity of dynamic evidence
        - Exploitability and impact
        - False positive indicators (WAF, rate limiting, honeypots)

        Return your final triage decision in JSON format.
        """

        return Task(
            description=description,
            agent=self.agent,
            expected_output="""A JSON object with the following structure:
            {
                "validation_status": "TRUE_POSITIVE|FALSE_POSITIVE|INCONCLUSIVE",
                "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO|null",
                "confidence_score": float (0.0-1.0),
                "reasoning": "comprehensive explanation synthesizing all evidence",
                "evidence_summary": {
                    "static_analysis": "summary of static findings",
                    "dynamic_testing": "summary of dynamic findings",
                    "consistency": "assessment of evidence consistency"
                },
                "recommendation": "next steps for remediation or further investigation",
                "false_positive_indicators": [list of any FP indicators found],
                "exploitability_assessment": "practical exploitability analysis",
                "business_impact": "potential business impact if exploited"
            }"""
        )

    def process_result(self, task_output: Any) -> Dict[str, Any]:
        """
        Process the triage task output

        Args:
            task_output: Raw output from the task

        Returns:
            Structured dictionary with final triage decision
        """
        try:
            if isinstance(task_output, str):
                result = json.loads(task_output)
            else:
                result = task_output

            return {
                "success": True,
                "data": result,
                "agent_type": "TRIAGE"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_output": str(task_output),
                "agent_type": "TRIAGE"
            }
