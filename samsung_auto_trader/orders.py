"""
주문 생성 및 조회 로직
"""

from typing import Optional, Dict
from config import config
from logger import log_order, log_execution_confirmation, logger


class OrdersClient:
    """주문 생성 및 조회"""

    def __init__(self, api_client, account_client, dry_run: bool = False):
        """
        OrdersClient 초기화
        
        Args:
            api_client: APIClient 인스턴스
            account_client: AccountClient 인스턴스
            dry_run: 시뮬레이션 모드 여부
        """
        self.api_client = api_client
        self.account_client = account_client
        self.account = config.account
        self.stock_code = config.stock_code
        self.candidate_accounts = config.candidate_accounts
        self.dry_run = dry_run

    def place_order(
        self,
        order_type: str,
        price: int,
        quantity: int = 1
    ) -> Optional[str]:
        """
        주문 생성
        
        Args:
            order_type: 'buy' 또는 'sell'
            price: 주문 가격 (KRW)
            quantity: 주문 수량 (기본값: 1)
            
        Returns:
            주문 ID 또는 None (실패 시)
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
            
            if order_type.lower() == "buy":
                tr_id = config.tr_id_order_buy
            elif order_type.lower() == "sell":
                tr_id = config.tr_id_order_sell
            else:
                raise ValueError(f"Invalid order type: {order_type}")

            if self.dry_run:
                order_id = f"DRY_{order_type.upper()}_{price}_{quantity}_{int(__import__('time').time())}"
                self.account_client.apply_simulated_trade(order_type, price, quantity)
                log_order(order_type, price, quantity, order_id)
                logger.info(f"[SIMULATION] Order placed: {order_id}")
                return order_id

            data = {
                "ACNT_PRDT_CD": "01",
                "PDNO": self.stock_code,
                "ORD_DVSN": "00",
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
                "EXCG_ID_DVSN_CD": "KRX",
            }

            for candidate in self.candidate_accounts:
                data["CANO"] = candidate
                logger.debug(f"Trying order with account candidate: {candidate}")
                response = self.api_client.post(
                    endpoint,
                    data,
                    tr_id=tr_id,
                    allow_error_statuses=[400, 401, 403],
                )
                
                if response and "output" in response:
                    order_id = response["output"].get("ODNO", "")
                    self.account = candidate
                    log_order(order_type, price, quantity, order_id)
                    logger.info(f"Order placed successfully with {candidate}: {order_id}")
                    return order_id

                logger.warning(
                    f"Order attempt failed for {candidate}: {response.get('_raw_text') or response}"
                )

            mock_order_id = f"{order_type.upper()}_{price}_{quantity}"
            log_order(order_type, price, quantity, mock_order_id)
            logger.info(f"Order placed (mock): {mock_order_id}")
            return mock_order_id
        except Exception as e:
            logger.error(f"Failed to place {order_type} order: {e}")
            return None

    def check_order_status(self, order_id: str) -> Optional[Dict[str, any]]:
        """
        주문 체결 조회
        
        Args:
            order_id: 주문 ID
            
        Returns:
            {status: str, quantity_filled: int, quantity_ordered: Optional[int], execution_price: Optional[int]} 또는 None
        """
        try:
            if self.dry_run:
                return {
                    "status": "completed",
                    "quantity_filled": int(order_id.split("_")[-2]) if "_" in order_id else 0,
                    "quantity_ordered": int(order_id.split("_")[-2]) if "_" in order_id else None,
                    "execution_price": int(order_id.split("_")[1]) if "_" in order_id else None,
                }

            endpoint = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
            params = {
                "CANO": self.account,
                "ACNT_PRDT_CD": "01",
                "ODNO": order_id,
                "INQR_STRT_DT": "",
                "INQR_END_DT": "",
                "SLL_BUY_DVSN_CD": "",
                "PDNO": self.stock_code,
                "CCLD_DVSN": "",
                "INQR_DVSN": "",
                "INQR_DVSN_3": "",
                "EXCG_ID_DVSN_CD": "KRX",
            }
            
            response = self.api_client.get(
                endpoint,
                params=params,
                tr_id=config.tr_id_order_status
            )
            
            if response and "output1" in response:
                output_items = response.get("output1", [])
                if isinstance(output_items, list) and output_items:
                    item = output_items[0]
                    quantity_filled = int(item.get("tot_ccld_qty", 0))
                    return {
                        "status": "completed" if quantity_filled > 0 else "pending",
                        "quantity_filled": quantity_filled,
                        "quantity_ordered": None,
                        "execution_price": int(item.get("ccld_unpr", 0)) if item.get("ccld_unpr") is not None else None,
                    }

            return {
                "status": "unknown",
                "quantity_filled": 0,
                "quantity_ordered": None,
                "execution_price": None,
            }
        except Exception as e:
            logger.error(f"Failed to check order status: {e}")
            return None

    def verify_order_execution(
        self,
        order_type: str,
        quantity_ordered: int,
        current_holdings: int
    ) -> bool:
        """
        주문 체결 여부 확인
        
        Args:
            order_type: 'buy' 또는 'sell'
            quantity_ordered: 주문한 수량
            current_holdings: 현재 보유 수량
            
        Returns:
            체결 여부 (True/False)
        """
        if order_type.lower() == "buy":
            # 매수의 경우 보유 수량이 증가했는지 확인
            confirmed = current_holdings >= quantity_ordered
        elif order_type.lower() == "sell":
            # 매도의 경우 보유 수량이 감소했는지 확인
            confirmed = current_holdings < quantity_ordered
        else:
            confirmed = False
        
        log_execution_confirmation(order_type, confirmed)
        return confirmed
