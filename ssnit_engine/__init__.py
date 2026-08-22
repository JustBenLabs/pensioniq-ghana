"""
SSNIT Actuarial Engine v1.0
Educational / estimation engine for Act 766 / Act 883 pathways.
"""
from .engine import (
    BenefitEvent,
    MasterBenefitResult,
    PaymentTiming,
    calculate_master_benefit,
    master_result_summary,
    calculate_pension_right,
    calculate_contributions,
    calculate_retirement_age,
)

__all__ = [
    "BenefitEvent",
    "MasterBenefitResult",
    "PaymentTiming",
    "calculate_master_benefit",
    "master_result_summary",
    "calculate_pension_right",
    "calculate_contributions",
    "calculate_retirement_age",
]
