"""Agent Orchestrator - Coordinates the multi-agent vulnerability analysis workflow"""
from typing import Dict, Any, Optional
from crewai import Crew, Process
import re
import time

from .parser_agent import ParserAgent
from .dynamic_validator_agent import DynamicValidatorAgent
from .triage_agent import TriageAgent


class VulnerabilityAnalysisOrchestrator:
    """
    Orchestrates the multi-agent vulnerability analysis workflow

    Workflow:
    1. Parser Agent: Extract structured data from report
    2. Dynamic Validator Agent: Execute dynamic tests
    3. Triage Agent: Make final determination
    """

    def __init__(
        self,
        llm_provider: str = "anthropic",
        llm_model: Optional[str] = None,
        temperature: float = 0.1
    ):
        """
        Initialize orchestrator with agents

        Args:
            llm_provider: LLM provider to use (openai, anthropic, google)
            llm_model: Specific model name (optional)
            temperature: Temperature for LLM (0.0-1.0)
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.temperature = temperature

        # Initialize agents
        self.parser_agent = ParserAgent(llm_provider, llm_model, temperature)
        self.dynamic_validator_agent = DynamicValidatorAgent(llm_provider, llm_model, temperature)
        self.triage_agent = TriageAgent(llm_provider, llm_model, temperature)

    @staticmethod
    def _extract_raw(crew_output) -> str:
        """Extract plain JSON string from a CrewOutput, stripping markdown code blocks."""
        raw = crew_output.raw if hasattr(crew_output, 'raw') else str(crew_output)
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        return match.group(1).strip() if match else raw.strip()

    def analyze_vulnerability(
        self,
        report_data: Dict[str, Any],
        dynamic_analysis_result: Optional[Dict[str, Any]] = None,
        run_dynamic: bool = True
    ) -> Dict[str, Any]:
        """
        Run the vulnerability analysis workflow.

        Args:
            report_data: Vulnerability report data
            dynamic_analysis_result: Results from dynamic analysis tools (optional)
            run_dynamic: Whether to run dynamic analysis (requires running app)

        Returns:
            Complete analysis results with triage decision
        """
        start_time = time.time()
        results = {
            "parser": None,
            "dynamic_validator": None,
            "triage": None,
            "metadata": {
                "llm_provider": self.llm_provider,
                "llm_model": self.llm_model,
                "analysis_duration": 0,
                "total_tokens": 0
            }
        }

        try:
            # Step 1: Parse the vulnerability report
            print("\n[1/4] Running Parser Agent...")
            parser_task = self.parser_agent.create_task(report_data)

            parser_crew = Crew(
                agents=[self.parser_agent.agent],
                tasks=[parser_task],
                process=Process.sequential,
                verbose=True
            )
            parser_output = parser_crew.kickoff()
            results["parser"] = self.parser_agent.process_result(self._extract_raw(parser_output))

            # Extract parsed data for next steps — must be a plain dict for unpacking
            parsed_data = results["parser"].get("data", {})
            if not isinstance(parsed_data, dict):
                parsed_data = {}


            # Step 2: Dynamic Validation (optional)
            if run_dynamic and dynamic_analysis_result is not None:
                print("\n[2/3] Running Dynamic Validator Agent...")
                dynamic_context = {
                    **parsed_data,
                    "dynamic_analysis_result": dynamic_analysis_result
                }
                dynamic_task = self.dynamic_validator_agent.create_task(dynamic_context)
                dynamic_crew = Crew(
                    agents=[self.dynamic_validator_agent.agent],
                    tasks=[dynamic_task],
                    process=Process.sequential,
                    verbose=True
                )
                dynamic_output = dynamic_crew.kickoff()
                results["dynamic_validator"] = self.dynamic_validator_agent.process_result(self._extract_raw(dynamic_output))
            else:
                print("\n[2/3] Skipping Dynamic Validator Agent (not requested or no running app)")
                results["dynamic_validator"] = {
                    "success": True,
                    "data": {"skipped": True, "reason": "Dynamic analysis not requested or running application not available"},
                    "agent_type": "DYNAMIC_VALIDATOR"
                }

            # Step 3: Final Triage
            print("\n[3/3] Running Triage Agent...")
            triage_context = {
                **parsed_data,
                "description": report_data.get("description", ""),
                "dynamic_validation": results["dynamic_validator"].get("data", {})
            }
            triage_task = self.triage_agent.create_task(triage_context)
            triage_crew = Crew(
                agents=[self.triage_agent.agent],
                tasks=[triage_task],
                process=Process.sequential,
                verbose=True
            )
            triage_output = triage_crew.kickoff()
            results["triage"] = self.triage_agent.process_result(self._extract_raw(triage_output))

            # Calculate total duration
            end_time = time.time()
            results["metadata"]["analysis_duration"] = end_time - start_time

            print(f"\n✓ Analysis complete in {results['metadata']['analysis_duration']:.2f}s")

        except Exception as e:
            print(f"\n✗ Analysis failed: {str(e)}")
            results["error"] = str(e)
            results["metadata"]["analysis_duration"] = time.time() - start_time

        return results
        

    def get_final_verdict(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract final verdict from analysis results

        Args:
            analysis_results: Results from analyze_vulnerability()

        Returns:
            Final verdict with validation status, severity, and confidence
        """
        triage_data = analysis_results.get("triage", {}).get("data", {})

        return {
            "validation_status": triage_data.get("validation_status", "INCONCLUSIVE"),
            "severity": triage_data.get("severity"),
            "confidence_score": triage_data.get("confidence_score", 0.0),
            "reasoning": triage_data.get("reasoning", ""),
            "recommendation": triage_data.get("recommendation", ""),
            "analysis_duration": analysis_results.get("metadata", {}).get("analysis_duration", 0)
        }
