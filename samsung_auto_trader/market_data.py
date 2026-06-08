"""
시장 데이터 조회 (현재가 등)
"""

from typing import Optional
from config import config
from logger import log_price, logger


class MarketDataClient:
    """현재가 및 시장 데이터 조회"""

    def __init__(self, api_client):
        """
        MarketDataClient 초기화
        
        Args:
            api_client: APIClient 인스턴스
        """
        self.api_client = api_client
        self.stock_code = config.stock_code

    def get_current_price(self) -> Optional[int]:
        """
        현재가 조회
        
        Returns:
            현재가 (정수, KRW) 또는 None (조회 실패 시)
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
            
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",  # J: 장내
                "FID_INPUT_ISCD": self.stock_code,
            }
            
            response = self.api_client.get(
                endpoint,
                params=params,
                tr_id=config.tr_id_price
            )
            
            if response and "output" in response:
                price_str = response["output"].get("stck_prpr")
                if price_str is not None:
                    price = int(price_str)
                    log_price(price, self.stock_code)
                    return price
            
            logger.error("Price response did not contain expected output")
            return None
        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            return None

    def get_market_status(self) -> Optional[str]:
        """
        시장 상태 조회
        
        Returns:
            시장 상태 ('open', 'closed', 등) 또는 None
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-market-status"
            
            response = self.api_client.get(endpoint)
            
            if response and "output" in response:
                status = response["output"].get("market_status")
                return status
            return None
            
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return None
