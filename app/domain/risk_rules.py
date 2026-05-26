from pydantic import BaseModel
from typing import List, Optional


class RiskRule(BaseModel):
    rule_id: str
    description: str
    weight: float


class RiskAnalysisResult(BaseModel):
    risk_score: float
    risk_level: str                     # "Informational" | "Low" | "Medium" | "High"
    risk_reasons: List[str]
    risky_snippet: str = ""             # Exact triggering phrase (6-12 words)
    exposed_party: str = "Unknown"      # Named party bearing the risk
    risk_category: str = "General"      # Power Imbalance | Financial Exposure | Dispute Risk | etc.
