from dataclasses import dataclass
from typing import Optional

@dataclass
class FinancialSnapshot:
    company: str  # Company name
    date: str  # or datetime.date is also OK
    assets: Optional[float]
    liabilities: Optional[float]
    equity_gross: Optional[float]
    revenue: Optional[float]
    operating_income: Optional[float]
