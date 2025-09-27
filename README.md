
## README.md

# AI Appointment Scheduler Assistant

An **LLM-powered FastAPI backend** that extracts and normalizes medical appointment details from natural language (or OCR-scanned images) into structured JSON.
The LLM (OpenAI GPT-4/4-mini) handles natural language, spelling errors, and relative dates/times;
Python provides deterministic validation and API serving.

---

## 1. Features

* **Medical Department Extraction** – Uses medical context to classify (e.g., Cardiology, Dermatology, General Medicine).
* **Date & Time Resolution** – Converts phrases like
  *today*, *tomorrow*, *this/next/upcoming Monday*, *evening at 8 pm* into ISO formats:

  * Date: `YYYY-MM-DD`
  * Time: `HH:MM` (24-hour)
* **OCR Support** – Accepts an uploaded image; text is extracted with Tesseract before LLM parsing.
* **Structured API Responses** – Returns step-wise JSON with confidence scores and final appointment object.

---

## 2. Architecture

```
ai_appointment_assistant/
│
├─ app.py                      # FastAPI entry point & API routes
│
├─ models/
│  └─ schemas.py               # Pydantic models for each pipeline step and final output
│
├─ services/
│  ├─ llm_extraction.py        # OpenAI GPT call + SYSTEM_PROMPT for ISO-normalized date/time
│  ├─ normalization.py         # Minimal validator (regex checks only)
│  ├─ ocr_service.py           # OCR text extraction using pytesseract
│  └─ guardrails.py            # Confidence/required-field checks
│
├─ requirements.txt
└─ README.md
```

**Processing Flow**

```
text/image → OCR (if image) → LLM Extraction (dept/date/time) →
Validation/Normalization (ISO date & time) → Guardrails (confidence) → JSON Response
```

---

## 3. Setup Instructions

### Prerequisites

* Python 3.10+
* [ngrok](https://ngrok.com/) (optional, for public demo)
* An [OpenAI API key](https://platform.openai.com/)

### Clone & Install

```bash
git clone https://github.com/satyajeetmishra/ai_appointment_assistant.git
cd ai_appointment_assistant
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# (or CMD: .venv\Scripts\activate)
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-openai-key
```

### Run the Server

```bash
uvicorn app:app --reload
```

* Local URL: `http://127.0.0.1:8000`
* Interactive docs: `http://127.0.0.1:8000/docs`

---

## 4. Optional: Public Demo with ngrok

Expose your local FastAPI server:

```bash
ngrok config add-authtoken <your_ngrok_token>
ngrok http 8000
```

ngrok will display a public URL like:

```
Forwarding https://<random-id>.ngrok-free.app -> http://localhost:8000
```

Use this public URL in sample requests (cURL, Postman, etc.).

---

## 5. API Endpoints

### Health

```
GET /health
```

Response:

```json
{"status": "healthy"}
```

### Appointment Parsing

```
POST /api/v1/appointments/parse
Content-Type: multipart/form-data
Fields:
  text  (string, optional)
  image (file, optional)
```

At least one field is required.

Success example:

```json
{
  "step1": {"raw_text":"book dentist next Friday at 3pm","confidence":0.95},
  "step2": {
    "entities": {
      "department":"Dentistry",
      "date_phrase":"2025-10-03",
      "time_phrase":"15:00"
    },
    "entities_confidence":0.9
  },
  "step3": {
    "normalized": {"date":"2025-10-03","time":"15:00","tz":"Asia/Kolkata"},
    "normalization_confidence":0.95
  },
  "appointment": {
    "department":"Dentistry",
    "date":"2025-10-03",
    "time":"15:00",
    "tz":"Asia/Kolkata"
  },
  "status":"ok"
}
```

---

## 6. Sample Requests

### Local (CMD Prompt on Windows)

**Health check**

```cmd
curl -X GET "http://127.0.0.1:8000/health"
```

**Text-only appointment**

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/appointments/parse" -F "text=book dentist next Friday at 3pm"
```

**Typo + fuzzy time**

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/appointments/parse" -F "text=checking my hair to doctor todaay evening at 8 pm"
```

**Relative date (“this Monday”)**

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/appointments/parse" -F "text=have fever will meet doctor this Monday at 4 pm"
```

**Image OCR (replace with your image path)**

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/appointments/parse" -F "image=@C:\path\to\image.png"
```

> For ngrok or cloud instance, simply replace `http://127.0.0.1:8000` with your public URL.

---


## 7. Key Design Choices

* **LLM-first**: OpenAI GPT handles language understanding, spelling corrections, and conversion to ISO date/time.
* **Minimal Python normalization**: Only validates final date/time format (`YYYY-MM-DD`, `HH:MM`) and attaches timezone.
* **Confidence scoring**: Each stage provides a numeric confidence so the UI can request clarification if needed.

---

## 8. License

MIT License – free for personal or commercial use.

---

**Quick start recap**

```bash
git clone https://github.com/satyajeetmishra/ai_appointment_assistant.git
cd ai_appointment_assistant
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# add OPENAI_API_KEY to .env
uvicorn app:app --reload
```

Then test using the cURL commands above or via `http://127.0.0.1:8000/docs`.

---

This README includes everything required for submission:

* **Working backend demo instructions** (local/ngrok)
* **GitHub repo setup**
* **Architecture overview**
* **API usage with sample cURL/Command Prompt commands**
* **Screen recording guide**

