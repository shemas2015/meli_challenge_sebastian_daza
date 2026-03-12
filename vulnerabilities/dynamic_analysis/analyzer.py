from typing import Dict
from .payload_executor import PayloadExecutor
from .response_analyzer import ResponseAnalyzer


class DynamicAnalyzer:
    """Main dynamic analysis orchestrator"""
    
    def __init__(self):
        self.executor = PayloadExecutor()
        self.analyzer = ResponseAnalyzer()
    
    def analyze(
        self,
        vulnerability_type: str,
        target_url: str,
        endpoint: str,
        parameter: str,
        payload: str,
        method: str = 'GET'
    ) -> Dict:
        """
        Execute payload and analyze response
        """
        # Execute payload
        if vulnerability_type == 'SQL_INJECTION':
            result = self.executor.execute_sql_injection(
                target_url, endpoint, parameter, payload, method
            )
        elif vulnerability_type == 'XSS':
            result = self.executor.execute_xss(
                target_url, endpoint, parameter, payload, method
            )
        elif vulnerability_type == 'PATH_TRAVERSAL':
            result = self.executor.execute_path_traversal(
                target_url, endpoint, parameter, payload, method
            )
        elif vulnerability_type == 'CSRF':
            result = self.executor.execute_csrf(
                target_url, endpoint, payload, method
            )
        elif vulnerability_type == 'IDOR':
            result = self.executor.execute_idor(
                target_url, endpoint, parameter, payload, method
            )
        else:
            return {
                'error': f'Unknown vulnerability type: {vulnerability_type}',
                'vulnerable': False
            }
        
        # Analyze response
        analysis = self.analyzer.analyze(result.get('response', {}), vulnerability_type)
        
        return {
            'vulnerability_type': vulnerability_type,
            'payload': payload,
            'response': result.get('response'),
            'analysis': analysis,
            'vulnerable': analysis.get('vulnerable', False),
            'confidence': analysis.get('confidence', 0.0)
        }
    
    def close(self):
        """Clean up resources"""
        self.executor.close()
