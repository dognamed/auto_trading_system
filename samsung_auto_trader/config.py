"""
환경변수 및 API 설정 로드
"""

import os
from dotenv import load_dotenv


class Config:
    """API 및 거래 설정"""

    def __init__(self):
        """환경변수 로드"""
        load_dotenv()
        
        # 환경변수에서 안전하게 로드
        self.account = os.getenv("GH_ACCOUNT")
        self.appkey = os.getenv("GH_APPKEY")
        self.appsecret = os.getenv("GH_APPSECRET")
        
        # 필수 환경변수 확인
        if not all([self.account, self.appkey, self.appsecret]):
            raise ValueError(
                "Missing required environment variables: "
                "GH_ACCOUNT, GH_APPKEY, GH_APPSECRET"
            )
        
        # API 기본 설정
        self.api_base_url = "https://openapivts.koreainvestment.com:29443"
        self.stock_code = "005930"  # 삼성전자
        self.account = os.getenv("GH_ACCOUNT") or "50177099-01"
        self.candidate_accounts = [self.account]
        alternate_account = self.account.replace("-", "")
        if alternate_account != self.account:
            self.candidate_accounts.append(alternate_account)
        
        # API TR ID 설정
        self.tr_id_price = "FHKST01010100"
        self.tr_id_balance = "VTTC8434R"
        self.tr_id_order_buy = "VTTC0012U"
        self.tr_id_order_sell = "VTTC0011U"
        self.tr_id_order_status = "VTTC0081R"
        
        # 거래 설정
        self.order_price_offset_buy = 2000  # 현재가에서 2000원 낮은 가격
        self.order_price_offset_sell = 2000  # 현재가에서 2000원 높은 가격
        self.order_quantity = 1  # 주문 수량 (1주)
        
        # 거래 시간 (시:분 형식)
        self.trading_start_time = "09:10"  # 09:10 AM
        self.trading_end_time = "15:30"    # 03:30 PM (15:30)
        
        # 폴링 설정
        self.polling_interval = 10  # 초 단위 (API 호출 최소화)
        self.order_call_interval = 10  # 주문 간 최소 대기 시간
        self.token_cache_file = "token_cache.json"

        # 시뮬레이션 계좌 설정
        self.simulated_cash = 1_000_000  # KRW
        self.simulated_holdings = {self.stock_code: 0}
        self.simulation_enabled = True
        
        # 잔고 조회 파라미터 기본값
        self.balance_params = {
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "Y",
            "FNCG_AMT_AUTO_RDPT_YN": "Y",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        
        # 타임아웃 설정
        self.api_timeout = 10  # 초


# 전역 설정 객체
config = Config()
