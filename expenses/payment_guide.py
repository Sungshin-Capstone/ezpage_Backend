from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

class PaymentStrategy(Enum):
    LARGE_BILLS = "최소 화폐 수 위주"
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
            'US': CurrencyConfig('US', '$', [100, 50, 20, 10, 5, 1, 0.25, 0.10, 0.05, 0.01], 2),
            'CN': CurrencyConfig('CN', '¥', [100, 50, 20, 10, 5, 1, 0.5, 0.1, 0.05, 0.01], 2),
            'JP': CurrencyConfig('JP', '¥', [10000, 5000, 2000, 1000, 500, 100, 50, 10, 5, 1], 0)
        }

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
            return {"error": f"{strategy.value} 전략으로 지불 불가"}

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
            return {"error": f"{strategy.value} 전략으로 거스름돈 계산 불가"}

        return {
            "strategy": strategy.value,
            "change": change,
            "total_amount": change_amount
        }

    def process_transaction(self, country_code: str, food_price: float, wallet: Dict[float, int]) -> Dict:
        if country_code not in self.currencies:
            return {"error": "지원하지 않는 국가"}

        currency = self.currencies[country_code]
        food_price = self._round(food_price, currency.decimal_places)
        wallet_total = self._calculate_total(wallet)

        if wallet_total < food_price:
            return {
                "error": f"{currency.currency_symbol}{wallet_total}으로는 {currency.currency_symbol}{food_price} 결제 불가",
                "currency": currency.currency_symbol
            }

        recommendations = {"payment": {}, "change": {}}

        for strategy in [PaymentStrategy.LARGE_BILLS, PaymentStrategy.SMALL_BILLS]:
            pay = self._recommend_payment(food_price, wallet.copy(), currency, strategy)
            recommendations["payment"][strategy.value] = pay

            if "error" not in pay and pay["change"] > 0:
                change = self._recommend_change(pay["change"], currency, strategy)
                recommendations["change"][strategy.value] = change

        return {
            "currency": currency.currency_symbol,
            "food_price": food_price,
            "wallet_total": wallet_total,
            "recommendations": recommendations
        }
