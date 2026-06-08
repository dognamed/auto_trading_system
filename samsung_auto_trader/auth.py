"""
토큰 인증 및 캐싱 관리
"""

import json
import time
from datetime import datetime
from typing import Optional
from config import config
from logger import log_auth, logger


class TokenManager:
    """토큰 인증 및 캐싱"""

    def __init__(self):
        """토큰 캐시 초기화"""
        self.cache_file = config.token_cache_file
        self.token = None
        self.token_issued_date = None
        self.api_base_url = config.api_base_url

    def _load_cached_token(self) -> Optional[dict]:
        """
        캐시된 토큰 로드
        
        Returns:
            캐시된 토큰 정보 (있으면) 또는 None
        """
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)

                token = data.get("token")
                expires_at = data.get("expires_at")
                if not token or not expires_at:
                    log_auth("No valid cached token found")
                    return None

                # expires_at may be ISO string or epoch
                try:
                    # ISO 형식 시도
                    expiry_dt = datetime.fromisoformat(expires_at)
                except Exception:
                    try:
                        # 정수(epoch)인 경우
                        expiry_dt = datetime.fromtimestamp(float(expires_at))
                    except Exception:
                        log_auth("Invalid expires_at in cache")
                        return None

                if expiry_dt > datetime.now():
                    log_auth("Token reused from cache", f"Expires at: {expiry_dt.isoformat()}")
                    return {"access_token": token, "expires_at": expiry_dt.isoformat()}
                else:
                    log_auth("Cached token expired", f"Expired at: {expiry_dt.isoformat()}")
                    return None
        except (FileNotFoundError, json.JSONDecodeError):
            log_auth("No valid cached token found")
            return None

    def _save_token_to_cache(self, token: str):
        """
        토큰을 캐시에 저장
        
        Args:
            token: 저장할 토큰
        """
        # 기본적으로 24시간 유효로 저장하되, 실제 만료정보가 있으면 덮어쓰기
        expires_at = (datetime.now() + 
                      __import__('datetime').timedelta(days=1)).isoformat()
        cache_data = {
            "token": token,
            "expires_at": expires_at,
            "timestamp": datetime.now().isoformat()
        }
        try:
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            log_auth("Token cached for today")
        except IOError as e:
            logger.error(f"Failed to save token cache: {e}")

    def get_token(self) -> str:
        """
        토큰 획득 (캐시 우선)
        
        Returns:
            유효한 토큰 문자열
            
        Raises:
            ValueError: 토큰 발급 실패 시
        """
        # 캐시된 토큰 확인
        cached_token = self._load_cached_token()
        if cached_token:
            # _load_cached_token may return a dict with access_token
            if isinstance(cached_token, dict):
                token_val = cached_token.get("access_token") or cached_token.get("token")
            else:
                token_val = cached_token

            if token_val:
                self.token = token_val
                return self.token

        # 새 토큰 발급 요청
        log_auth("Requesting new token from API")
        token = self._request_new_token()

        if not token:
            raise ValueError("Failed to obtain authentication token")

        self.token = token
        # _request_new_token already attempts to save cache with expiry, but ensure fallback
        try:
            self._save_token_to_cache(token)
        except Exception:
            pass
        return self.token

    def _request_new_token(self) -> Optional[str]:
        """
        API에서 새 토큰 발급
        
        Returns:
            발급받은 토큰 또는 None
        """
        import requests
        import hashlib
        import hmac
        import base64
        
        try:
            # 토큰 발급 엔드포인트
            endpoint = f"{self.api_base_url}/oauth2/tokenP"
            
            # 요청 데이터
            payload = {
                "grant_type": "client_credentials",
                "appkey": config.appkey,
                "appsecret": config.appsecret
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 요청 전송
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=config.api_timeout,
                verify=False  # Mock 환경용
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")

                # 만료 정보 파싱: Open API 예시에서 access_token_token_expired 또는 expires_in 사용
                expires_at = None
                if data.get("access_token_token_expired"):
                    try:
                        expires_at = data.get("access_token_token_expired")
                    except Exception:
                        expires_at = None
                elif data.get("expires_in"):
                    try:
                        expires_at = (datetime.now() + __import__('datetime').timedelta(seconds=int(data.get("expires_in")))).isoformat()
                    except Exception:
                        expires_at = None

                if token:
                    # 캐시에 만료시간 포함하여 저장
                    try:
                        cache_data = {"token": token}
                        if expires_at:
                            cache_data["expires_at"] = expires_at
                        else:
                            cache_data["expires_at"] = (datetime.now() + __import__('datetime').timedelta(days=1)).isoformat()
                        with open(self.cache_file, "w") as f:
                            json.dump(cache_data, f, indent=2)
                    except Exception:
                        logger.warning("Failed to write token cache with expiry, continuing")

                    log_auth("New token obtained successfully", f"Expires at: {cache_data.get('expires_at')}")
                    return token
            else:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Token request error: {e}")
            return None

    def invalidate_cache(self):
        """캐시된 토큰 무효화"""
        try:
            import os
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            log_auth("Token cache invalidated")
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")


# 전역 토큰 관리자
token_manager = TokenManager()
