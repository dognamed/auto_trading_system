"""
계좌 정보 조회 (잔액, 보유주식)
"""

from typing import Optional, Dict, List
from config import config
from logger import log_holdings, logger


class AccountClient:
    """계좌 정보 조회"""

    def __init__(self, api_client, dry_run: bool = False):
        """
        AccountClient 초기화
        
        Args:
            api_client: APIClient 인스턴스
            dry_run: 시뮬레이션 모드 여부
        """
        self.api_client = api_client
        self.account = config.account
        self.stock_code = config.stock_code
        self.candidate_accounts = config.candidate_accounts
        self.dry_run = dry_run
        self.simulated_cash = config.simulated_cash
        self.simulated_holdings = dict(config.simulated_holdings)

    def _get_account_summary(self) -> Optional[Dict[str, any]]:
        """
        잔고 및 보유 정보 통합 조회
        """
        if self.dry_run:
            logger.info("[SIMULATION] Using simulated account state")
            return {
                "cash": self.simulated_cash,
                "holdings": self.simulated_holdings,
            }

        for candidate in self.candidate_accounts:
            try:
                endpoint = "/uapi/domestic-stock/v1/trading/inquire-balance"
                params = {
                    "CANO": candidate,
                    "ACNT_PRDT_CD": "01",
                    **config.balance_params,
                }
                response = self.api_client.get(
                    endpoint,
                    params=params,
                    tr_id=config.tr_id_balance,
                    allow_error_statuses=[400, 401, 403],
                )
                
                if not response:
                    logger.warning(f"Balance response is empty for account candidate {candidate}")
                    continue

                output1 = response.get("output1") or []
                output2 = response.get("output2") or []
                if output1 or output2:
                    self.account = candidate
                    return self._parse_account_response(response)

                logger.warning(
                    f"Account summary failed for candidate {candidate}: {response.get('_raw_text') or response}"
                )
            except Exception as e:
                logger.error(f"Failed to fetch account summary for {candidate}: {e}")

        logger.error("All account candidates failed for account summary")
        return None

    def _parse_account_response(self, response: Dict[str, any]) -> Dict[str, any]:
        holdings: Dict[str, int] = {}
        cash = 0

        output1 = response.get("output1") or []
        if isinstance(output1, list):
            for item in output1:
                symbol = item.get("pdno")
                qty = int(item.get("hldg_qty", 0))
                if symbol and qty > 0:
                    holdings[symbol] = qty

        output2 = response.get("output2") or []
        if isinstance(output2, list) and output2:
            cash = int(output2[0].get("dnca_tot_amt", 0))

        return {
            "cash": cash,
            "holdings": holdings,
        }

    def apply_simulated_trade(self, order_type: str, price: int, quantity: int):
        """
        시뮬레이션 모드에서 주문 결과를 계좌 상태에 반영합니다.
        """
        if order_type.lower() == "buy":
            self.simulated_cash -= price * quantity
            self.simulated_holdings[self.stock_code] = (
                self.simulated_holdings.get(self.stock_code, 0) + quantity
            )
        elif order_type.lower() == "sell":
            self.simulated_cash += price * quantity
            self.simulated_holdings[self.stock_code] = max(
                0,
                self.simulated_holdings.get(self.stock_code, 0) - quantity
            )

    def get_balance(self) -> Optional[int]:
        """
        사용 가능한 현금 조회
        """
        summary = self._get_account_summary()
        if summary is None:
            return None
        cash = summary.get("cash", 0)
        logger.debug(f"Account balance: {cash:,} KRW")
        return cash

    def get_holdings(self) -> Dict[str, int]:
        """
        보유 주식 조회
        """
        summary = self._get_account_summary()
        if summary is None:
            return {}
        holdings = summary.get("holdings", {})
        return holdings

    def get_account_info(self) -> Optional[Dict[str, any]]:
        """
        계좌 정보 통합 조회
        """
        summary = self._get_account_summary()
        if summary is None:
            return None
        return summary

    def get_holding_quantity(self, symbol: str = None) -> int:
        """
        특정 종목 보유 수량 조회
        """
        if symbol is None:
            symbol = self.stock_code
        holdings = self.get_holdings()
        return holdings.get(symbol, 0)
