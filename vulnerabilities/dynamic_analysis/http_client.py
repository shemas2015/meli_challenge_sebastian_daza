import requests
from typing import Dict, Optional
from requests.exceptions import RequestException


class HTTPClient:
    """HTTP client wrapper for vulnerability testing"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
    
    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request and return structured response
        """
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'response_time': response.elapsed.total_seconds(),
                'url': response.url,
            }
        
        except RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
            }
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Dict:
        """GET request"""
        return self.request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> Dict:
        """POST request"""
        return self.request('POST', url, data=data, json=json, **kwargs)
    
    def put(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> Dict:
        """PUT request"""
        return self.request('PUT', url, data=data, json=json, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Dict:
        """DELETE request"""
        return self.request('DELETE', url, **kwargs)
    
    def close(self):
        """Close session"""
        self.session.close()
