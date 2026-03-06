"""
Shared SOC (Standard Occupational Classification) helpers for the data pipeline.
O*NET and BLS use slightly different code formats; we normalize to XX-XXXX.00 for matching.
"""


def normalize_soc(code: str) -> str:
    """
    Normalize occupation code to O*NET-style XX-XXXX.00 (e.g. 15-1252.00).
    Handles 6-digit (XX-XXXX), 8-digit (XX-XXXX.XX), and digit-only strings.
    """
    code = str(code).strip()
    digits = code.replace(".", "").replace("-", "").replace(" ", "")
    if len(digits) >= 8:
        return f"{digits[:2]}-{digits[2:6]}.{digits[6:8]}"
    if len(digits) >= 6:
        return f"{digits[:2]}-{digits[2:6]}.00"
    return code
