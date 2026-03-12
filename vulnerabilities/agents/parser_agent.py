"""Parser Agent - Extracts structured data from vulnerability reports"""
from typing import Dict, Any
from crewai import Agent, Task
from .base import BaseVulnerabilityAgent
import json

class ParserAgent(BaseVulnerabilityAgent):
    """
    Agent responsible for parsing and structuring vulnerability reports

    Role: Extract key information from raw vulnerability descriptions
    Goal: Convert unstructured text into structured data
    """

    def _create_agent(self) -> Agent:
        return Agent(
            role="Vulnerability Report Parser",
            goal="Extract and structure vulnerability information from raw reports",
            backstory="""You are an expert security analyst specialized in parsing
            vulnerability reports. You excel at identifying key information like
            vulnerability types, affected endpoints, attack vectors, and payloads
            from unstructured text.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def create_task(self, context: Dict[str, Any]) -> Task:
        """
        Create parsing task

        Args:
            context: Dict with 'raw_report' key containing the vulnerability description

        Returns:
            Task for parsing the report
        """
        description = f"""
        Parse the following vulnerability report and extract structured information:

        Report:
        {context.get('description', '')}

        Extract and return in JSON format:
        - vulnerability_type: (SQL_INJECTION, XSS, PATH_TRAVERSAL, CSRF, or IDOR)
        - endpoint: The affected URL endpoint
        - method: HTTP method (GET, POST, etc.)
        - parameter: The vulnerable parameter name (if applicable)
        - payload: The exploit payload (if provided)
        - confidence: Your confidence in the parsing (0.0-1.0)

        Additional context:
        - Target URL: {context.get('target_url', 'N/A')}
        - Type hint: {context.get('type', 'N/A')}
        - Endpoint hint: {context.get('endpoint', 'N/A')}
        - Method hint: {context.get('method', 'GET')}
        """

        return Task(
            description=description,
            agent=self.agent,
            expected_output="""A JSON object with the following structure:
            {
                "vulnerability_type": "string",
                "endpoint": "string",
                "method": "string",
                "parameter": "string or null",
                "payload": "string or null",
                "confidence": float,
                "reasoning": "string explaining the parsing decisions"
            }"""
        )

    def process_result(self, task_output: Any) -> Dict[str, Any]:
        """
        Process the task output

        Args:
            task_output: Raw output from the task

        Returns:
            Structured dictionary with parsed data
        """
        # CrewAI returns task output as string or structured data
        # We'll handle both cases

        try:
            if isinstance(task_output, str):
                # Try to extract JSON from the output
                result = json.loads(task_output)
            else:
                result = task_output

            return {
                "success": True,
                "data": result,
                "agent_type": "PARSER"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_output": str(task_output),
                "agent_type": "PARSER"
            }
