"""
REST API 클라이언트 (추상화 레이어)
"""

import requests
import hashlib
import hmac
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime
from config import config
from logger import log_api_call, log_api_error, log_retry, logger


class APIClient:
    """
    한국투자 Open API 클라이언트
    
    모든 REST API 호출을 추상화하여 에러 처리, 재시도 로직 포함
    """

    def __init__(self, token_manager):
        """
        APIClient 초기화
        
        Args:
            token_manager: TokenManager 인스턴스
        """
        self.base_url = config.api_base_url
        self.token_manager = token_manager
        self.max_retries = 3
        self.timeout = config.api_timeout

    def _get_headers(self, method: str = "GET", tr_id: str = None) -> Dict[str, str]:
        """
        API 요청 헤더 생성
        
        Args:
            method: HTTP 메서드 (GET/POST 등)
            tr_id: 선택적 거래 ID
            
        Returns:
            헤더 딕셔너리
        """
        token = self.token_manager.get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "appkey": config.appkey,
            "appsecret": config.appsecret,
            "tr_id": tr_id or self._get_tr_id_by_method(method),
        }
        return headers

    def _get_tr_id_by_method(self, method: str) -> str:
        """
        기본 TR ID를 메서드 기반으로 반환
        """
        if method == "POST":
            return config.tr_id_order_buy
        return config.tr_id_price

    def _get_tr_id_by_endpoint(self, endpoint: str, method: str) -> str:
        """
        엔드포인트별 TR ID 매핑
        """
        if endpoint.endswith("/quotations/inquire-price"):
            return config.tr_id_price
        if endpoint.endswith("/trading/inquire-balance"):
            return config.tr_id_balance
        if endpoint.endswith("/trading/order-cash"):
            return config.tr_id_order_buy
        if endpoint.endswith("/trading/inquire-daily-ccld"):
            return config.tr_id_order_status
        return self._get_tr_id_by_method(method)

    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """
        요청 서명 생성 (필요한 경우)
        
        Args:
            method: HTTP 메서드
            path: 요청 경로
            body: 요청 본문
            
        Returns:
            서명 정보 포함된 헤더
        """
        # Mock 환경에서는 기본 인증만 사용
        # 실제 환경에서 필요하면 구현
        return self._get_headers(method)

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        tr_id: str = None,
        allow_error_statuses: Optional[list[int]] = None,
    ) -> Dict[str, Any]:
        """
        GET 요청
        
        Args:
            endpoint: API 엔드포인트 (상대 경로)
            params: 쿼리 파라미터
            tr_id: 선택적 거래 ID
            allow_error_statuses: 허용할 HTTP 상태 코드 목록
            
        Returns:
            응답 JSON 데이터
            
        Raises:
            requests.RequestException: API 오류
        """
        url = f"{self.base_url}{endpoint}"
        tr_id = tr_id or self._get_tr_id_by_endpoint(endpoint, "GET")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                log_api_call(endpoint, "GET")
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self._get_headers("GET", tr_id),
                    timeout=self.timeout,
                    verify=False  # Mock 환경용
                )
                
                if response.status_code == 200:
                    return response.json()
                if allow_error_statuses and response.status_code in allow_error_statuses:
                    return self._build_error_response(response)
                elif response.status_code == 429:  # Rate limit
                    if attempt < self.max_retries:
                        log_retry(endpoint, attempt)
                        import time
                        time.sleep(5)  # 5초 대기 후 재시도
                        continue
                else:
                    error_msg = f"Status {response.status_code}"
                    log_api_error(endpoint, error_msg)
                    raise requests.RequestException(error_msg)
                    
            except requests.Timeout:
                if attempt < self.max_retries:
                    log_retry(endpoint, attempt)
                    import time
                    time.sleep(2)
                    continue
                else:
                    log_api_error(endpoint, "Timeout")
                    raise
            except Exception as e:
                log_api_error(endpoint, str(e))
                if attempt == self.max_retries:
                    raise
                import time
                time.sleep(2)
        
        raise requests.RequestException(f"Max retries exceeded for {endpoint}")

    def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        tr_id: str = None,
        allow_error_statuses: Optional[list[int]] = None,
    ) -> Dict[str, Any]:
        """
        POST 요청
        
        Args:
            endpoint: API 엔드포인트 (상대 경로)
            data: 요청 본문 데이터
            tr_id: 선택적 거래 ID
            allow_error_statuses: 허용할 HTTP 상태 코드 목록
            
        Returns:
            응답 JSON 데이터
            
        Raises:
            requests.RequestException: API 오류
        """
        url = f"{self.base_url}{endpoint}"
        body_json = json.dumps(data)
        tr_id = tr_id or self._get_tr_id_by_endpoint(endpoint, "POST")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                log_api_call(endpoint, "POST")
                
                response = requests.post(
                    url,
                    data=body_json,
                    headers=self._get_headers("POST", tr_id),
                    timeout=self.timeout,
                    verify=False  # Mock 환경용
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                if allow_error_statuses and response.status_code in allow_error_statuses:
                    return self._build_error_response(response)
                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        log_retry(endpoint, attempt)
                        import time
                        time.sleep(5)
                        continue
                else:
                    error_msg = f"Status {response.status_code} - {response.text}"
                    log_api_error(endpoint, error_msg)
                    raise requests.RequestException(error_msg)
                    
            except requests.Timeout:
                if attempt < self.max_retries:
                    log_retry(endpoint, attempt)
                    import time
                    time.sleep(2)
                    continue
                else:
                    log_api_error(endpoint, "Timeout")
                    raise
            except Exception as e:
                log_api_error(endpoint, str(e))
                if attempt == self.max_retries:
                    raise
                import time
                time.sleep(2)
        
        raise requests.RequestException(f"Max retries exceeded for {endpoint}")

    def _build_error_response(self, response):
        result = {"_status_code": response.status_code, "_raw_text": response.text}
        try:
            payload = response.json()
            if isinstance(payload, dict):
                result.update(payload)
        except ValueError:
            pass
        return result
