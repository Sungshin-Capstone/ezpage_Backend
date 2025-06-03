from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

class PaymentStrategy(Enum):
    LARGE_BILLS = "최대 화폐 수 위주"
    SMALL_BILLS = "잔돈 우선 위주"

@dataclass
class CurrencyConfig:
    country_code: str
    currency_symbol: str
    denominations: List[float]
    decimal_places: int

class IntegratedPaymentSystem:
    def __init__(self):
        self.currencies = {
            'USD': CurrencyConfig('US', '$', [100, 50, 20, 10, 5, 1, 0.25, 0.10, 0.05, 0.01], 2),
            'CNY': CurrencyConfig('CN', '¥', [100, 50, 20, 10, 5, 1, 0.5, 0.1, 0.05, 0.01], 2),
            'JPY': CurrencyConfig('JP', '¥', [10000, 5000, 2000, 1000, 500, 100, 50, 10, 5, 1], 0),
            'KRW': CurrencyConfig('KR', '₩', [50000, 10000, 5000, 1000, 500, 100, 50, 10], 0)
        }

    def _get_currency_config(self, currency_code: str) -> CurrencyConfig | None:
        return self.currencies.get(currency_code.upper())

    def _round(self, amount: float, places: int) -> float:
        return float(Decimal(str(amount)).quantize(Decimal('0.' + '0' * places), rounding=ROUND_HALF_UP))

    def _calculate_total(self, wallet: Dict[float, int]) -> float:
        """지갑의 총 금액을 계산합니다."""
        return sum(float(denom) * quantity for denom, quantity in wallet.items())

    def _recommend_payment(self, amount: float, wallet: Dict[float, int], currency: CurrencyConfig, strategy: PaymentStrategy) -> Dict:
        denominations = currency.denominations if strategy == PaymentStrategy.LARGE_BILLS else list(reversed(currency.denominations))
        remaining = self._round(amount, currency.decimal_places)
        used = {}

        for denom in denominations:
            if remaining <= 0:
                break
            count = min(int(remaining // denom), wallet.get(denom, 0))
            if count > 0:
                used[denom] = count
                remaining = self._round(remaining - denom * count, currency.decimal_places)

        total_paid = self._calculate_total(used)
        change = self._round(total_paid - amount, currency.decimal_places)

        if remaining > 0:
            return {"error": f"{strategy.value} 전략으로 지불 불가: {self._round(remaining, currency.decimal_places)} {currency.currency_symbol} 부족"}

        return {
            "strategy": strategy.value,
            "used": used,
            "total_paid": total_paid,
            "change": change
        }

    def _recommend_change(self, change_amount: float, currency: CurrencyConfig, strategy: PaymentStrategy) -> Dict:
        denominations = currency.denominations if strategy == PaymentStrategy.LARGE_BILLS else list(reversed(currency.denominations))
        remaining = self._round(change_amount, currency.decimal_places)
        change = {}

        for denom in denominations:
            if remaining <= 0:
                break
            count = int(remaining // denom)
            if count > 0:
                change[denom] = count
                remaining = self._round(remaining - denom * count, currency.decimal_places)

        if remaining > 0:
            return {"error": f"{strategy.value} 전략으로 거스름돈 계산 불가: {self._round(remaining, currency.decimal_places)} {currency.currency_symbol} 잔돈 부족"}

        return {
            "strategy": strategy.value,
            "change": change,
            "total_amount": change_amount
        }

    def process_transaction(self, currency_code: str, amount: float, wallet: Dict[float, int]) -> Dict:
        currency = self._get_currency_config(currency_code)
        if not currency:
            return {"error": f"지원하지 않는 화폐 코드: {currency_code}"}

        amount = self._round(amount, currency.decimal_places)
        wallet_total = self._calculate_total(wallet)

        if wallet_total < amount:
            return {
                "error": f"{currency.currency_symbol}{wallet_total}으로는 {currency.currency_symbol}{amount} 결제 불가",
                "currency": currency.currency_symbol
            }

        recommendations = {"payment": {}, "change": {}}

        for strategy in [PaymentStrategy.LARGE_BILLS, PaymentStrategy.SMALL_BILLS]:
            pay = self._recommend_payment(amount, wallet.copy(), currency, strategy)
            recommendations["payment"][strategy.value] = pay

            if "error" not in pay and pay.get('change', 0) > 0:
                change = self._recommend_change(pay["change"], currency, strategy)
                recommendations["change"][strategy.value] = change
            elif "error" not in pay and pay.get('change', 0) <= 0:
                recommendations["change"][strategy.value] = {}

        return {
            "currency": currency.currency_symbol,
            "food_price": amount,
            "wallet_total": wallet_total,
            "recommendations": recommendations
        }
