
from typing import Dict, Tuple, Optional
import json
import os
import re


try:
    from openai import OpenAI
    OPENAI_IMPORTED = True
except Exception as e:
    print(f"ERROR: OpenAI import failed: {e}")
    OPENAI_IMPORTED = False

SYSTEM_PROMPT = """
You are an expert medical appointment scheduler AI with comprehensive knowledge of medical specialties.
Your job is to extract appointment information from user messages and return strictly valid JSON.

TASK: From a user message, extract:
- department (medical specialty, Title Case, e.g., "Cardiology", "Dermatology", "Orthopedics")
- date_phrase (MUST be a concrete calendar date in ISO format YYYY-MM-DD, resolved for Asia/Kolkata)
- time_phrase (MUST be 24-hour HH:MM, no seconds)

DEPARTMENT/SPECIALTY INSTRUCTIONS:
- Use medical knowledge to choose the most appropriate specialty based on symptoms, conditions, body parts, or terms.
- If multiple specialties could apply, pick the most specific/relevant one.
- If the user says "doctor", "physician", "checkup", or it’s otherwise general, use "General Medicine".
- If no medical context is clear, use "General Medicine" by default.
- Return the standard specialty name in Title Case.

NORMALIZATION & CORRECTION REQUIREMENTS:
1) Correct obvious spelling or grammatical errors in date/time words (e.g., "todaay" -> "today", "tomorow" -> "tomorrow").
2) Resolve relative expressions (e.g., "today", "tomorrow", "this Monday", "next Friday", "upcoming Tuesday", "in two weeks")
   to a concrete ISO date using the user's local timezone Asia/Kolkata and the current date at runtime. Do not return relative words.
3) Time MUST be 24-hour format HH:MM (e.g., "3 pm" -> "15:00", "noon" -> "12:00", "midnight" -> "00:00").
4) If time is ambiguous but indicates a part of day, choose a sensible default:
   - morning -> 09:00
   - afternoon -> 14:00
   - evening -> 18:00
   - night -> 20:00
5) If the user provides multiple date/time options, choose the earliest feasible one unless a clear preference is stated.
6) If either date or time truly cannot be determined, set that specific field to null (do not fabricate), but still return valid JSON.

OUTPUT FORMAT (STRICT):
- Return ONLY valid JSON with EXACTLY these keys:
  {"department": "...", "date_phrase": "YYYY-MM-DD" or null, "time_phrase": "HH:MM" or null}
- No extra keys, no trailing commas, no explanations.

EXAMPLES:
"book dentist next Friday at 3pm"
-> {"department": "Dentistry", "date_phrase": "YYYY-MM-DD", "time_phrase": "15:00"}

"my back is killing me, need appointment tomorrow"
-> {"department": "Orthopedics", "date_phrase": "YYYY-MM-DD", "time_phrase": null}

"weird rash on my arm, can I see someone this week?"
-> {"department": "Dermatology", "date_phrase": "YYYY-MM-DD", "time_phrase": null}

"chest pain, urgent appointment"
-> {"department": "Cardiology", "date_phrase": null, "time_phrase": null}

"my kid needs vaccination"
-> {"department": "Pediatrics", "date_phrase": null, "time_phrase": null}

"migraine doctor friday 2pm"
-> {"department": "Neurology", "date_phrase": "YYYY-MM-DD", "time_phrase": "14:00"}

"checking my hair to doctor todaay evening at 8 pm"
-> {"department": "Dermatology", "date_phrase": "YYYY-MM-DD", "time_phrase": "20:00"}

"have fever will meet doctor this monday at 4 pm"
-> {"department": "General Medicine", "date_phrase": "YYYY-MM-DD", "time_phrase": "16:00"}
"""


def _get_client() -> Optional["OpenAI"]:
    """Create the OpenAI client using the current environment (lazy init)."""
    if not OPENAI_IMPORTED:
        print("ERROR: OpenAI library not installed. Run: pip install openai")
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"ERROR: OpenAI client initialization failed: {e}")
        return None

def llm_extract_entities(raw_text: str) -> Tuple[Dict[str, Optional[str]], float]:
    """Extract appointment entities using pure LLM approach (lazy client)."""
    if not raw_text or not raw_text.strip():
        print("DEBUG: Empty input text")
        return {"department": None, "date_phrase": None, "time_phrase": None}, 0.0

    client = _get_client()
    if client is None:
        return {"department": None, "date_phrase": None, "time_phrase": None}, 0.0

    try:
        user_prompt = f'Extract appointment info from: "{raw_text.strip()}"'
        print(f"DEBUG LLM: Input text: '{raw_text}'")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        print(f"DEBUG LLM: Raw response: '{content}'")

        entities = _parse_llm_response(content)
        print(f"DEBUG LLM: Parsed entities: {entities}")

        entities = _validate_entities(entities)
        print(f"DEBUG LLM: Validated entities: {entities}")

        confidence = _calculate_confidence(entities, raw_text)
        print(f"DEBUG LLM: Final confidence: {confidence}")

        return entities, confidence

    except Exception as e:
        print(f"ERROR LLM: Extraction failed - {e}")
        import traceback
        traceback.print_exc()
        return {"department": None, "date_phrase": None, "time_phrase": None}, 0.1

def _parse_llm_response(content: str) -> Dict[str, Optional[str]]:
    """Parse LLM response and extract JSON."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    json_pattern = r'\{[^{}]*"department"[^{}]*"date_phrase"[^{}]*"time_phrase"[^{}]*\}'
    json_match = re.search(json_pattern, content)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    print("DEBUG: Falling back to manual JSON extraction")
    return _manual_extract(content)

def _manual_extract(content: str) -> Dict[str, Optional[str]]:
    entities = {"department": None, "date_phrase": None, "time_phrase": None}

    # department
    for pattern in [
        r'"department":\s*"([^"]*)"',
        r'department["\s]*:[\s"]*([^",}\n]*)',
        r'Department:\s*([^\n,]*)'
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            entities["department"] = m.group(1).strip()
            break

    # date_phrase
    for pattern in [
        r'"date_phrase":\s*"([^"]*)"',
        r'date_phrase["\s]*:[\s"]*([^",}\n]*)',
        r'Date:\s*([^\n,]*)'
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            entities["date_phrase"] = m.group(1).strip()
            break

    # time_phrase
    for pattern in [
        r'"time_phrase":\s*"([^"]*)"',
        r'time_phrase["\s]*:[\s"]*([^",}\n]*)',
        r'Time:\s*([^\n,]*)'
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            entities["time_phrase"] = m.group(1).strip()
            break

    return entities

def _validate_entities(entities: Dict) -> Dict[str, Optional[str]]:
    dept = entities.get("department")
    if isinstance(dept, str):
        dept = dept.strip()
        if dept.lower() in ["", "null", "none"]:
            dept = None
    else:
        dept = None

    date_phrase = entities.get("date_phrase")
    if isinstance(date_phrase, str):
        date_phrase = date_phrase.strip()
        if date_phrase.lower() in ["", "null", "none"]:
            date_phrase = None
    else:
        date_phrase = None

    time_phrase = entities.get("time_phrase")
    if isinstance(time_phrase, str):
        time_phrase = time_phrase.strip()
        if time_phrase.lower() in ["", "null", "none"]:
            time_phrase = None
    else:
        time_phrase = None

    return {"department": dept, "date_phrase": date_phrase, "time_phrase": time_phrase}

def _calculate_confidence(entities: Dict, original_text: str) -> float:
    non_null = sum(1 for v in entities.values() if v is not None)
    base_scores = {0: 0.2, 1: 0.6, 2: 0.8, 3: 0.9}
    conf = base_scores.get(non_null, 0.9)

    if entities.get("department") and entities.get("date_phrase") and entities.get("time_phrase"):
        conf = min(conf + 0.05, 0.95)
    elif entities.get("department") and entities.get("date_phrase"):
        conf = min(conf + 0.03, 0.92)

    if len(original_text.strip()) < 8:
        conf *= 0.85
    if not entities.get("department"):
        conf *= 0.7

    return round(max(conf, 0.1), 2)
