"""
통합 로깅 모듈
"""

import logging
from datetime import datetime


def setup_logger(name: str = "auto_trader") -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        
    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 반환 (중복 설정 방지)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 파일 핸들러
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"trading_{timestamp}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 로그 포맷
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 전역 로거
logger = setup_logger()


def log_auth(action: str, detail: str = ""):
    """인증 관련 로그"""
    msg = f"[AUTH] {action}"
    if detail:
        msg += f" - {detail}"
    logger.info(msg)


def log_price(price: int, symbol: str = "005930"):
    """현재가 로그"""
    logger.info(f"[PRICE] {symbol}: {price:,} KRW")


def log_order(order_type: str, price: int, quantity: int, order_id: str = ""):
    """주문 로그"""
    msg = f"[ORDER] {order_type.upper()} @ {price:,} KRW x {quantity}"
    if order_id:
        msg += f" (ID: {order_id})"
    logger.info(msg)


def log_holdings(cash: int, holdings: dict):
    """보유 자산 로그"""
    logger.info(f"[HOLDINGS] Cash: {cash:,} KRW")
    for symbol, qty in holdings.items():
        logger.info(f"           {symbol}: {qty} shares")


def log_api_call(endpoint: str, method: str = "GET"):
    """API 호출 로그"""
    logger.debug(f"[API] {method} {endpoint}")


def log_api_error(endpoint: str, error: str):
    """API 에러 로그"""
    logger.error(f"[API ERROR] {endpoint} - {error}")


def log_retry(endpoint: str, attempt: int):
    """재시도 로그"""
    logger.warning(f"[RETRY] {endpoint} (attempt {attempt})")


def log_trading_window(status: str):
    """거래 시간 로그"""
    logger.info(f"[TRADING WINDOW] {status}")


def log_execution_confirmation(order_type: str, confirmed: bool):
    """주문 실행 확인 로그"""
    status = "CONFIRMED" if confirmed else "NOT_CONFIRMED"
    logger.info(f"[EXECUTION] {order_type.upper()} {status}")
