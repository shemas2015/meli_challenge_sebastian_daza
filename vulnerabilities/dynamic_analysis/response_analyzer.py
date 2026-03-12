from typing import Dict
import json as _json

class ResponseAnalyzer:
    """Analyzes HTTP responses for vulnerability indicators"""
    
    def analyze(self, response: Dict, vulnerability_type: str) -> Dict:
        """
        Analyze response based on vulnerability type
        """
        if vulnerability_type == 'SQL_INJECTION':
            return self.analyze_sql_injection(response)
        elif vulnerability_type == 'XSS':
            return self.analyze_xss(response)
        elif vulnerability_type == 'PATH_TRAVERSAL':
            return self.analyze_path_traversal(response)
        elif vulnerability_type == 'CSRF':
            return self.analyze_csrf(response)
        elif vulnerability_type == 'IDOR':
            return self.analyze_idor(response)
        else:
            return {'error': f'Unknown vulnerability type: {vulnerability_type}'}
    
    def analyze_sql_injection(self, response: Dict) -> Dict:
        """Analyze response for SQL injection indicators"""
        if not response.get('success'):
            return {
                'vulnerable': False,
                'reason': 'Request failed',
                'confidence': 0.0
            }
        
        body = response.get('body', '').lower()
        status_code = response.get('status_code', 0)
        
        sql_error_patterns = [
            'sql syntax',
            'mysql_fetch',
            'warning: mysql',
            'unclosed quotation',
            'quoted string not properly terminated',
            'sqlite_error',
            'postgresql error',
            'ora-00',
            'pg_query()',
        ]
        
        found_patterns = [p for p in sql_error_patterns if p in body]
        
        if found_patterns or status_code == 500:
            return {
                'vulnerable': True,
                'reason': f'SQL error detected: {found_patterns}',
                'confidence': 0.9,
                'indicators': found_patterns
            }
        
        return {
            'vulnerable': False,
            'reason': 'No SQL injection indicators found',
            'confidence': 0.1
        }
    
    def analyze_xss(self, response: Dict) -> Dict:
        """Analyze response for XSS indicators"""
        if not response.get('success'):
            return {
                'vulnerable': False,
                'reason': 'Request failed',
                'confidence': 0.0
            }

        # DOM XSS detected by Playwright headless browser
        if 'dom_xss_detected' in response:
            dom_result = response['dom_xss_detected']
            return {
                'vulnerable': dom_result,
                'reason': 'DOM XSS confirmed by Playwright headless browser' if dom_result else 'DOM XSS not detected by Playwright headless browser',
                'confidence': 0.95 if dom_result else 0.3,
            }

        body = response.get('body', '')

        xss_indicators = ['<script>', 'onerror=', 'onclick=', 'javascript:', '<iframe']
        found_indicators = [ind for ind in xss_indicators if ind in body.lower()]

        if found_indicators:
            return {
                'vulnerable': True,
                'reason': f'XSS payload reflected: {found_indicators}',
                'confidence': 0.8,
                'indicators': found_indicators
            }

        return {
            'vulnerable': False,
            'reason': 'Payload not reflected or sanitized',
            'confidence': 0.2
        }
    
    def analyze_path_traversal(self, response: Dict) -> Dict:
        """Analyze response for path traversal indicators"""
        if not response.get('success'):
            return {
                'vulnerable': False,
                'reason': 'Request failed',
                'confidence': 0.0
            }
        
        body = response.get('body', '').lower()
        
        file_indicators = [
            'root:',
            '/etc/passwd',
            '[boot loader]',
            'windows\\system32'
        ]
        
        found_indicators = [ind for ind in file_indicators if ind in body]
        
        if found_indicators:
            return {
                'vulnerable': True,
                'reason': f'System file content detected: {found_indicators}',
                'confidence': 0.95,
                'indicators': found_indicators
            }
        
        return {
            'vulnerable': False,
            'reason': 'No file system indicators found',
            'confidence': 0.1
        }
    
    def analyze_csrf(self, response: Dict) -> Dict:
        """Analyze response for CSRF vulnerability"""
        if not response.get('success'):
            return {
                'vulnerable': False,
                'reason': 'Request failed',
                'confidence': 0.0
            }
        
        status_code = response.get('status_code', 0)
        
        if 200 <= status_code < 300:
            return {
                'vulnerable': True,
                'reason': 'Request succeeded without CSRF token',
                'confidence': 0.7
            }
        elif status_code == 403:
            return {
                'vulnerable': False,
                'reason': 'CSRF protection detected (403 Forbidden)',
                'confidence': 0.9
            }
        
        return {
            'vulnerable': False,
            'reason': f'Unexpected status code: {status_code}',
            'confidence': 0.5
        }
    
    def analyze_idor(self, response: Dict) -> Dict:
        """Analyze response for IDOR vulnerability"""

        if not response.get('success'):
            return {
                'vulnerable': False,
                'reason': 'Request failed',
                'confidence': 0.0
            }

        status_code = response.get('status_code', 0)
        body = response.get('body', '')

        if status_code in (401, 403):
            return {
                'vulnerable': False,
                'reason': f'Access denied ({status_code})',
                'confidence': 0.9
            }

        if status_code == 200:
            # Try to detect non-empty JSON data array to avoid false positives
            try:
                parsed = _json.loads(body)
                data = parsed.get('data')
                if isinstance(data, list) and len(data) > 0:
                    return {
                        'vulnerable': True,
                        'reason': f'Unauthorized resource accessed successfully — {len(data)} record(s) returned',
                        'confidence': 0.9
                    }
                elif isinstance(data, list) and len(data) == 0:
                    return {
                        'vulnerable': False,
                        'reason': 'Response returned empty data array — access may be restricted or request was malformed',
                        'confidence': 0.6
                    }
                elif data is not None:
                    return {
                        'vulnerable': True,
                        'reason': 'Unauthorized resource accessed successfully',
                        'confidence': 0.75
                    }
            except (_json.JSONDecodeError, AttributeError):
                pass

            # Non-JSON response with content
            if len(body) > 0:
                return {
                    'vulnerable': True,
                    'reason': 'Unauthorized resource accessed successfully',
                    'confidence': 0.75
                }

        return {
            'vulnerable': False,
            'reason': f'Status code: {status_code}',
            'confidence': 0.5
        }
