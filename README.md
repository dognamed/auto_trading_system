# 🤖 Samsung Electronics Auto Trading System

한국투자증권(Korea Investment & Securities) **Open API**를 사용한 **삼성전자(005930)** 자동거래 시스템입니다.

- 🎯 **삼성전자만 거래** — 단순하고 집중된 전략
- 🔄 **REST API 기반** — WebSocket 미지원 환경에서도 동작
- 🛡️ **드라이런/시뮬레이션 지원** — 실제 계좌 조회 실패 시에도 100만원 가정으로 거래 검증 가능
- 📊 **자동화된 거래 사이클** — 현재가 조회 → 계좌 확인 → 매수/매도 → 실행 확인
- ⏰ **거래시간 제한** — 09:10 ~ 15:30 (평일)
- 🔐 **토큰 캐싱** — 인증 효율성 향상
- 📝 **상세 로깅** — 콘솔과 파일에 기록

---

## 📋 목차

- [프로젝트 구조](#-프로젝트-구조)
- [기술 스택](#-기술-스택)
- [설치](#-설치)
- [환경 설정](#-환경-설정)
- [사용 방법](#-사용-방법)
- [거래 로직](#-거래-로직)
- [드라이 런 모드](#-드라이-런-모드)
- [문제 해결](#-문제-해결)
- [참고사항](#-참고사항)

---

## 📁 프로젝트 구조

```
auto_trading_system/
├── README.md
├── .gitignore
└── samsung_auto_trader/
    ├── main.py
    ├── config.py
    ├── auth.py
    ├── api_client.py
    ├── market_data.py
    ├── account.py
    ├── orders.py
    ├── trader.py
    ├── logger.py
    ├── token_cache.json
    ├── requirements.txt
```

### 핵심 모듈

| 모듈 | 클래스 | 역할 |
|------|--------|------|
| `auth.py` | `TokenManager` | OAuth 토큰 발급 및 캐싱 |
| `api_client.py` | `APIClient` | REST API 호출 추상화, 헤더/재시도/타임아웃 처리 |
| `market_data.py` | `MarketDataClient` | 현재가 조회 |
| `account.py` | `AccountClient` | 계좌 잔액 및 보유 정보 조회 |
| `orders.py` | `OrdersClient` | 주문 생성/조회 및 체결 확인 |
| `trader.py` | `AutoTrader` | 자동 거래 사이클 관리 |

---

## 🛠️ 기술 스택

- Python 3.9+
- `requests`
- `python-dotenv`
- 한국투자증권 Open API (REST)
- `logging` 기반 파일/콘솔 로깅

---

## 🚀 설치

### 1) 저장소 클론

```bash
git clone https://github.com/dognamed/auto_trading_system.git
cd auto_trading_system
```

### 2) Python 버전 확인

```bash
python --version
```

### 3) 의존성 설치

```bash
pip install -r samsung_auto_trader/requirements.txt
```

---

## ⚙️ 환경 설정

### 1) 한국투자증권 Open API 신청

- [한국투자증권 API 포털](https://apiportal.koreainvestment.com/)에서 모의투자용 앱키/앱시크릿 발급
- `GH_ACCOUNT`, `GH_APPKEY`, `GH_APPSECRET` 준비

### 2) `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 만들고 다음 내용을 추가하세요:

```env
GH_ACCOUNT=50177099-01
GH_APPKEY=your_demo_appkey_here
GH_APPSECRET=your_demo_appsecret_here
```

> `.env` 파일은 절대 커밋하지 마세요.

---

## 📖 사용 방법

### 1) 테스트 모드

한 번의 거래 사이클만 실행합니다.

```bash
cd samsung_auto_trader
python main.py --mode test
```

### 2) 연속 거래 모드

거래 시간 동안 반복 실행합니다.

```bash
python main.py --mode run
```

### 3) 드라이 런 모드

실제 API 주문 없이 로직만 실행합니다.

```bash
python main.py --mode test --dry-run
```

또는 연속 실행:

```bash
python main.py --mode run --dry-run
```

---

## 💡 거래 로직

자동 거래는 다음과 같은 흐름으로 진행됩니다:

1. 현재가 조회 (`MarketDataClient`)
2. 계좌 잔액 및 보유 정보 조회 (`AccountClient`)
3. 매수 주문 생성 (`OrdersClient`)
4. 매도 주문 생성 (`OrdersClient`)
5. 주문 체결 여부 및 거래 결과 확인

### 기본 전략

- 매수 가격 = 현재가 - 2,000원
- 매도 가격 = 현재가 + 2,000원
- 주문 수량 = 1주
- 거래 사이클 대기 시간은 `config.polling_interval`
- 주문 간 최소 대기 시간은 `config.order_call_interval`

---

## 🧪 드라이 런 모드

`--dry-run` 모드를 사용하면 실제 계좌 조회 또는 주문 호출 없이 로직만 실행됩니다.

- 기본 시뮬레이션 현금: **1,000,000 KRW**
- 초기 보유: **005930 0주**
- 실제 API 호출이 실패하는 환경에서도 자동 거래 흐름 검증 가능
- 시뮬레이션 주문은 `DRY_BUY...` / `DRY_SELL...` 식별자 형태로 생성됩니다.

---

## 🔧 문제 해결

### 실제 계좌 조회 실패 시

모의 거래 API나 계좌 필드 호환성 문제로 실제 잔고 조회가 실패할 수 있습니다.

이 경우 `--dry-run` 모드로 테스트하면 100만원 가정 기반 거래 시나리오를 확인할 수 있습니다.

### 계좌번호 형식

코드는 `12345678-01`과 `1234567801` 두 가지 형식을 모두 시도합니다.

### 토큰 캐시

`token_cache.json` 파일로 인증 토큰을 캐시합니다. 필요 시 해당 파일을 삭제하면 재발급합니다.

---

## 📌 참고사항

- 이 프로젝트는 학습/개발용 예제입니다.
- 실거래 적용 시 전략, 리스크 관리, 예외 처리 등을 추가해야 합니다.
- 이 코드는 책임 제한 없이 제공됩니다.
