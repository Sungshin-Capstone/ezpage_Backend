import requests
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta

class ExchangeRateService:
    BASE_URL = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    AUTH_KEY = "64gnpBzqaKlDucfSbJJyD04bsPbprTNv"
    CACHE_KEY = "exchange_rates"
    CACHE_TIMEOUT = 3600  # 1시간

    @classmethod
    def get_exchange_rates(cls):
        """캐시된 환율 정보를 가져오거나 API를 호출하여 새로운 환율 정보를 가져옵니다."""
        cached_rates = cache.get(cls.CACHE_KEY)
        if cached_rates:
            return cached_rates

        today = datetime.now().strftime("%Y%m%d")
        params = {
            'authkey': cls.AUTH_KEY,
            'searchdate': today,
            'data': 'AP01'
        }

        try:
            response = requests.get(cls.BASE_URL, params=params)
            response.raise_for_status()
            rates = response.json()

            # 환율 정보를 딕셔너리로 변환
            exchange_rates = {}
            for rate in rates:
                if rate['result'] == 1:  # 성공적인 응답만 처리
                    cur_unit = rate['cur_unit'].replace('(100)', '')  # JPY(100) -> JPY
                    exchange_rates[cur_unit] = {
                        'rate': Decimal(rate['deal_bas_r'].replace(',', '')),
                        'name': rate['cur_nm']
                    }

            # KRW는 항상 1.0
            exchange_rates['KRW'] = {'rate': Decimal('1.0'), 'name': '한국 원'}

            # 캐시에 저장
            cache.set(cls.CACHE_KEY, exchange_rates, cls.CACHE_TIMEOUT)
            return exchange_rates

        except Exception as e:
            # API 호출 실패 시 기본 환율 반환
            return {
                'USD': {'rate': Decimal('1350.0'), 'name': '미국 달러'},
                'JPY': {'rate': Decimal('9.0'), 'name': '일본 옌'},
                'CNY': {'rate': Decimal('190.0'), 'name': '중국 위안'},
                'KRW': {'rate': Decimal('1.0'), 'name': '한국 원'}
            }

    @classmethod
    def get_exchange_rate(cls, currency_code):
        """특정 통화의 환율을 가져옵니다."""
        rates = cls.get_exchange_rates()
        return rates.get(currency_code, {'rate': Decimal('1.0'), 'name': 'Unknown'}) 