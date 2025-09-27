
from dotenv import load_dotenv
load_dotenv() 
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from models.schemas import Step1Output, Step2Output, Step3Output, FinalAppointment, Entities, Normalized
from services.ocr_service import ocr_from_image, passthrough_text
from services.llm_extraction import llm_extract_entities  
from services.normalization import normalize
from services.guardrails import needs_clarification
import tempfile
import os

app = FastAPI(title="AI Appointment Scheduler Assistant", version="1.0.0")

@app.post("/api/v1/appointments/parse")
async def parse(text: str = Form(None), image: UploadFile = File(None)):
    """
    Parse appointment request from text or image using pure LLM extraction
    """
    # Step 1: OCR or direct text
    if text and text.strip():
        raw_text, s1_conf = passthrough_text(text)
    elif image:
        suffix = os.path.splitext(image.filename or "")[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await image.read())
            tmp_path = tmp.name
        try:
            raw_text, s1_conf = ocr_from_image(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        # No input at all
        response_data = {
            "step1": {"raw_text": "", "confidence": 0.0},
            "step2": {"entities": {"date_phrase": None, "time_phrase": None, "department": None}, "entities_confidence": 0.0},
            "step3": {"normalized": {"date": None, "time": None, "tz": "Asia/Kolkata"}, "normalization_confidence": 0.0},
            "appointment": None,
            "status": "needs_clarification",
            "message": "Provide either text or an image."
        }
        return JSONResponse(content=response_data)

    step1 = Step1Output(raw_text=raw_text, confidence=s1_conf)

    # Step 2: Direct LLM entity extraction
    print(f"DEBUG - Calling LLM directly for: '{raw_text}'")
    ents_dict, s2_conf = llm_extract_entities(raw_text)
    step2 = Step2Output(entities=Entities(**ents_dict), entities_confidence=s2_conf)

    # Step 3: Normalize to standard date/time
    norm_dict, s3_conf = normalize(step2.entities.date_phrase, step2.entities.time_phrase)
    step3 = Step3Output(
        normalized=Normalized(**norm_dict),
        normalization_confidence=s3_conf
    )

    # Guardrail checks
    reason = needs_clarification(
        step1.confidence,
        step2.entities_confidence,
        step3.normalization_confidence,
        ents_dict
    )

    if reason:
        response_data = {
            "step1": step1.dict(),
            "step2": step2.dict(),
            "step3": step3.dict(),
            "appointment": None,
            "status": "needs_clarification",
            "message": reason
        }
        return JSONResponse(content=response_data)

    # Step 4: Final structured JSON
    appointment = FinalAppointment(
        department=step2.entities.department,
        date=step3.normalized.date,
        time=step3.normalized.time,
        tz=step3.normalized.tz
    )

    response_data = {
        "step1": step1.dict(),
        "step2": step2.dict(),
        "step3": step3.dict(),
        "appointment": appointment.dict(),
        "status": "ok"
    }
    return JSONResponse(content=response_data)

@app.get("/")
async def root():
    return {"message": "AI Appointment Scheduler Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
