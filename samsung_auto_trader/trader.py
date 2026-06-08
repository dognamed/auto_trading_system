"""
거래 로직 (메인 알고리즘)
"""

import time
from datetime import datetime
from config import config
from market_data import MarketDataClient
from account import AccountClient
from orders import OrdersClient
from logger import (
    logger, log_trading_window, log_price, 
    log_holdings, log_order, log_execution_confirmation
)


class AutoTrader:
    """자동거래 엔진"""

    def __init__(self, api_client, dry_run: bool = False):
        """
        AutoTrader 초기화
        
        Args:
            api_client: APIClient 인스턴스
            dry_run: 시뮬레이션 모드 여부
        """
        self.api_client = api_client
        self.market_data = MarketDataClient(api_client)
        self.account = AccountClient(api_client, dry_run=dry_run)
        self.orders = OrdersClient(api_client, self.account, dry_run=dry_run)
        self.stock_code = config.stock_code
        self.is_running = False

    def _is_trading_window_open(self) -> bool:
        """
        현재 시간이 거래 시간인지 확인
        
        Returns:
            거래 시간이면 True, 아니면 False
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        start_time = config.trading_start_time  # "09:10"
        end_time = config.trading_end_time      # "15:30"
        
        # 평일 확인 (월~금)
        is_weekday = now.weekday() < 5  # 0~4: 월~금
        
        is_in_window = start_time <= current_time <= end_time
        
        return is_weekday and is_in_window

    def _execute_trading_cycle(self):
        """
        한 번의 거래 사이클 실행
        
        단계:
        1. 현재가 조회
        2. 계좌 잔액/보유주식 확인
        3. 매수 주문 (현재가 - 2000원)
        4. 매도 주문 (현재가 + 2000원)
        5. 주문 실행 확인
        """
        try:
            logger.info("=" * 60)
            logger.info("Trading cycle started")
            logger.info("=" * 60)
            
            # Step 1: 현재가 조회
            logger.info("[Step 1] Getting current price...")
            current_price = self.market_data.get_current_price()
            
            if not current_price or current_price <= 0:
                logger.error("Failed to get current price, skipping cycle")
                return False
            
            log_price(current_price, self.stock_code)
            
            # Step 2: 계좌 정보 확인 (주문 전)
            logger.info("[Step 2] Checking account before orders...")
            account_info_before = self.account.get_account_info()
            
            if not account_info_before:
                logger.error("Failed to get account info, skipping cycle")
                return False
            
            cash_before = account_info_before["cash"]
            holdings_before = account_info_before["holdings"]
            holding_qty_before = holdings_before.get(self.stock_code, 0)
            
            log_holdings(cash_before, holdings_before)
            logger.info(f"Holdings before: {holding_qty_before} shares")
            
            # Step 3: 매수 주문
            logger.info("[Step 3] Placing buy order...")
            buy_price = current_price - config.order_price_offset_buy
            buy_qty = config.order_quantity
            
            logger.info(f"Buy price: {buy_price:,} KRW (current: {current_price:,} - offset: {config.order_price_offset_buy})")
            buy_order_id = self.orders.place_order("buy", buy_price, buy_qty)
            
            if not buy_order_id:
                logger.warning("Failed to place buy order, continuing...")
            else:
                logger.info(f"Buy order placed: {buy_order_id}")
                time.sleep(config.order_call_interval)  # API 호출 간격 확보
            
            # Step 4: 매도 주문
            logger.info("[Step 4] Placing sell order...")
            sell_price = current_price + config.order_price_offset_sell
            sell_qty = config.order_quantity
            
            logger.info(f"Sell price: {sell_price:,} KRW (current: {current_price:,} + offset: {config.order_price_offset_sell})")
            sell_order_id = self.orders.place_order("sell", sell_price, sell_qty)
            
            if not sell_order_id:
                logger.warning("Failed to place sell order, continuing...")
            else:
                logger.info(f"Sell order placed: {sell_order_id}")
            
            # Step 5: 주문 실행 확인
            logger.info("[Step 5] Verifying order execution...")
            time.sleep(config.order_call_interval)  # 체결 확인 전 대기
            
            account_info_after = self.account.get_account_info()
            
            if account_info_after:
                cash_after = account_info_after["cash"]
                holdings_after = account_info_after["holdings"]
                holding_qty_after = holdings_after.get(self.stock_code, 0)
                
                log_holdings(cash_after, holdings_after)
                logger.info(f"Holdings after: {holding_qty_after} shares")
                
                # 매수 체결 확인
                buy_confirmed = self.orders.verify_order_execution(
                    "buy", buy_qty, holding_qty_after
                )
                
                # 매도 체결 확인
                sell_confirmed = self.orders.verify_order_execution(
                    "sell", sell_qty, holding_qty_after
                )
                
                # 결과 로깅
                logger.info(f"Buy execution: {'CONFIRMED' if buy_confirmed else 'NOT_CONFIRMED'}")
                logger.info(f"Sell execution: {'CONFIRMED' if sell_confirmed else 'NOT_CONFIRMED'}")
            else:
                logger.warning("Failed to verify account after orders")
            
            logger.info("=" * 60)
            logger.info("Trading cycle completed")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during trading cycle: {e}", exc_info=True)
            return False

    def start(self):
        """거래 시작"""
        self.is_running = True
        logger.info("Auto trader started")
        log_trading_window("STARTED")
        
        try:
            while self.is_running:
                # 거래 시간 확인
                if not self._is_trading_window_open():
                    current_time = datetime.now().strftime("%H:%M")
                    logger.debug(f"Outside trading window ({current_time}), waiting...")
                    log_trading_window("CLOSED")
                    time.sleep(60)  # 1분 대기
                    continue
                
                # 거래 사이클 실행
                self._execute_trading_cycle()
                
                # 폴링 간격
                logger.info(f"Next cycle in {config.polling_interval} seconds...")
                time.sleep(config.polling_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error in trading loop: {e}", exc_info=True)
            self.stop()

    def stop(self):
        """거래 중지"""
        self.is_running = False
        logger.info("Auto trader stopped")
        log_trading_window("STOPPED")

    def run_once(self):
        """한 번의 거래 사이클만 실행 (테스트용)"""
        logger.info("Running single trading cycle (test mode)...")
        return self._execute_trading_cycle()
