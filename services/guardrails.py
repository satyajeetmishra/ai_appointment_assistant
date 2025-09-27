from typing import Optional, Dict

def needs_clarification(step1_conf: float, step2_conf: float, step3_conf: float, entities: Dict) -> Optional[str]:
    """
    Returns a reason string if confidence is too low or critical data is missing.
    Otherwise returns None (meaning everything looks fine).
    """
    if step1_conf < 0.5:
        return "Low OCR/text confidence."
    if not entities.get("department"):
        return "Missing department."
    if not entities.get("date_phrase") or not entities.get("time_phrase"):
        return "Ambiguous or missing date/time."
    if step2_conf < 0.6 or step3_conf < 0.6:
        return "Low extraction/normalization confidence."
    return None
