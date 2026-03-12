import json as _json
from typing import Dict, Optional
from .http_client import HTTPClient


class PayloadExecutor:
    """Executes vulnerability payloads for dynamic testing"""
    
    def __init__(self):
        self.client = HTTPClient()
    
    def execute_sql_injection(
        self,
        url: str,
        endpoint: str,
        parameter: str,
        payload: str,
        method: str = 'GET'
    ) -> Dict:
        """Execute SQL injection payload"""
        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        if method.upper() == 'GET':
            params = {parameter: payload}
            response = self.client.get(full_url, params=params)
        else:
            data = {parameter: payload}
            response = self.client.post(full_url, data=data)
        
        return {
            'payload': payload,
            'response': response,
            'vulnerable': self._check_sql_injection_response(response)
        }
    
    def execute_xss(
        self,
        url: str,
        endpoint: str,
        parameter: str,
        payload: str,
        method: str = 'GET'
    ) -> Dict:
        """Execute XSS payload — tries DOM-based detection via headless browser, falls back to HTTP reflection check"""
        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Try DOM XSS detection via headless browser first
        dom_vulnerable = self._check_dom_xss(url, endpoint, parameter, payload)
        if dom_vulnerable is not None:
            return {
                'payload': payload,
                'response': {'body': '', 'status_code': 0, 'success': True, 'dom_xss_detected': dom_vulnerable},
                'vulnerable': dom_vulnerable,
                'detection_method': 'dom_browser'
            }

        # Fall back to HTTP reflection check
        if method.upper() == 'GET':
            params = {parameter: payload}
            response = self.client.get(full_url, params=params)
        else:
            data = {parameter: payload}
            response = self.client.post(full_url, data=data)

        return {
            'payload': payload,
            'response': response,
            'vulnerable': self._check_xss_response(response, payload),
            'detection_method': 'http_reflection'
        }
    
    def execute_path_traversal(
        self,
        url: str,
        endpoint: str,
        parameter: str,
        payload: str,
        method: str = 'GET'
    ) -> Dict:
        """Execute path traversal payload"""
        base_dir = "/".join(endpoint.rstrip("/").split("/")[:-1])
        full_url = f"{url.rstrip('/')}/{base_dir.lstrip('/')}/{payload.lstrip('/')}"

        response = self.client.get(full_url)
        
        return {
            'payload': payload,
            'response': response,
            'vulnerable': self._check_path_traversal_response(response)
        }
    
    def execute_csrf(
        self,
        url: str,
        endpoint: str,
        payload,
        method: str = 'POST'
    ) -> Dict:
        """Execute CSRF payload: login to get session cookie, then send cross-origin request"""
        parsed = {}
        if isinstance(payload, str):
            try:
                parsed = _json.loads(payload)
            except Exception:
                pass
        elif isinstance(payload, dict):
            parsed = payload

        # Step 1: login to obtain session token
        token = None
        credentials = parsed.get('credentials', {})
        if credentials:
            login_path = parsed.get('login_url', '/rest/user/login')
            login_url = f"{url.rstrip('/')}/{login_path.lstrip('/')}"
            login_resp = self.client.post(login_url, json=credentials)
            if login_resp.get('success'):
                try:
                    token = _json.loads(login_resp['body'])['authentication']['token']
                except Exception:
                    pass

        # Step 2: build headers simulating cross-origin request with session cookie
        headers = {'Origin': 'http://evil-attacker.com'}
        if token:
            headers['Cookie'] = f'token={token}'

        # Step 3: parse form_data string into dict
        form_data = {}
        for pair in parsed.get('form_data', '').split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                form_data[k] = v

        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = self.client.request(method, full_url, data=form_data, headers=headers)

        return {
            'payload': payload,
            'response': response,
            'vulnerable': self._check_csrf_response(response)
        }
    
    def execute_idor(
        self,
        url: str,
        endpoint: str,
        parameter: str,
        payload: str,
        method: str = 'GET'
    ) -> Dict:
        """Execute IDOR payload (access unauthorized resource)"""
        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"

        # If payload is "param=value" format, extract just the value to avoid double-encoding
        payload_value = payload
        if parameter and '=' in payload:
            key, val = payload.split('=', 1)
            if key.strip() == parameter:
                payload_value = val

        if method.upper() == 'GET':
            params = {parameter: payload_value} if parameter else None
            response = self.client.get(full_url, params=params)
        else:
            data = {parameter: payload_value}
            response = self.client.post(full_url, data=data)
        
        return {
            'payload': payload,
            'response': response,
            'vulnerable': self._check_idor_response(response)
        }
    
    def _check_sql_injection_response(self, response: Dict) -> bool:
        """Check if response indicates SQL injection vulnerability"""
        if not response.get('success'):
            return False
        
        body = response.get('body', '').lower()
        sql_errors = [
            'sql syntax',
            'mysql_fetch',
            'warning: mysql',
            'unclosed quotation',
            'quoted string',
            'sqlite_error',
            'postgresql error'
        ]
        
        return any(error in body for error in sql_errors) or response.get('status_code') == 500
    
    def _check_dom_xss(self, url: str, endpoint: str, parameter: str, payload: str) -> Optional[bool]:
        """Use Playwright headless browser to detect DOM XSS by checking if an alert dialog fires"""
        try:
            from playwright.sync_api import sync_playwright
            from urllib.parse import quote

            dom_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}?{parameter}={quote(payload)}"
            xss_triggered = []

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.on("dialog", lambda dialog: (
                    xss_triggered.append(dialog.message),
                    dialog.accept()
                ))
                page.goto(dom_url, wait_until="networkidle")
                browser.close()

            return len(xss_triggered) > 0
        except ImportError:
            return None  # Playwright not available, fall back to HTTP

    def _check_xss_response(self, response: Dict, payload: str) -> bool:
        """Check if HTTP response indicates server-side XSS reflection in HTML context"""
        if not response.get('success'):
            return False

        body = response.get('body', '')
        content_type = response.get('headers', {}).get('Content-Type', '')
        return payload in body and 'text/html' in content_type
    
    def _check_path_traversal_response(self, response: Dict) -> bool:
        """Check if response indicates path traversal vulnerability"""
        if not response.get('success'):
            return False

        return response.get('status_code') == 200 and len(response.get('body', '')) > 0
    
    def _check_csrf_response(self, response: Dict) -> bool:
        """Check if request succeeded without CSRF token"""
        if not response.get('success'):
            return False
        
        # If request succeeds (2xx), CSRF protection is missing
        status_code = response.get('status_code', 0)
        return 200 <= status_code < 300
    
    def _check_idor_response(self, response: Dict) -> bool:
        """Check if unauthorized resource access succeeded"""
        if not response.get('success'):
            return False
        
        status_code = response.get('status_code', 0)
        return status_code == 200
    
    def close(self):
        """Clean up resources"""
        self.client.close()
