"""
삼성전자 자동거래 시스템 - 메인 진입점
"""

import sys
import argparse
from config import config
from auth import token_manager
from api_client import APIClient
from trader import AutoTrader
from logger import logger


def main():
    """프로그램 진입점"""
    
    parser = argparse.ArgumentParser(
        description="Samsung Electronics Auto Trading System"
    )
    parser.add_argument(
        "--mode",
        choices=["run", "test"],
        default="run",
        help="Run mode: 'run' for continuous trading, 'test' for single cycle"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no actual orders, only log)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("╔═══════════════════════════════════════════════════════════╗")
        logger.info("║      Samsung Electronics Auto Trading System v1.0         ║")
        logger.info("║              (Mock Trading Environment)                   ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")
        logger.info("")
        
        # 설정 로그
        logger.info(f"Configuration:")
        logger.info(f"  Stock Code: {config.stock_code}")
        logger.info(f"  Trading Window: {config.trading_start_time} ~ {config.trading_end_time}")
        logger.info(f"  Order Offset: Buy -{config.order_price_offset_buy} KRW, Sell +{config.order_price_offset_sell} KRW")
        logger.info(f"  Order Quantity: {config.order_quantity} shares")
        logger.info(f"  Polling Interval: {config.polling_interval} seconds")
        logger.info(f"  Account: {config.account}")
        logger.info(f"  Dry Run: {args.dry_run}")
        logger.info("")
        
        # 토큰 발급
        logger.info("Authenticating...")
        token = token_manager.get_token()
        logger.info("✓ Authentication successful")
        logger.info("")
        
        # API 클라이언트 생성
        api_client = APIClient(token_manager)
        
        # 자동거래 시작
        trader = AutoTrader(api_client, dry_run=args.dry_run)
        
        if args.mode == "test":
            logger.info("Running in TEST mode (single cycle only)")
            logger.info("")
            success = trader.run_once()
            if success:
                logger.info("Test completed successfully")
                sys.exit(0)
            else:
                logger.error("Test failed")
                sys.exit(1)
        else:
            logger.info("Running in CONTINUOUS mode")
            logger.info(f"Press Ctrl+C to stop")
            logger.info("")
            trader.start()
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
