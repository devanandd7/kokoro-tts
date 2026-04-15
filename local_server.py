import io
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
import soundfile as sf
import numpy as np
from kokoro import KPipeline

# ── Language Map ───────────────────────────────────────────────────────────────
LANG_CODE = {
    "hi":    "h",   # Hindi
    "en-us": "a",   # American English
    "en-gb": "b",   # British English
}

DEFAULT_VOICE = {
    "hi":    "hf_alpha",
    "en-us": "af_heart",
    "en-gb": "bf_emma",
}

# ── Request Schema ─────────────────────────────────────────────────────────────
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: Literal["hi", "en-us", "en-gb"] = "en-us"
    voice: Optional[str] = None
    speed: float = Field(1.0, ge=0.5, le=2.0)

# ── FastAPI Instance ───────────────────────────────────────────────────────────
app = FastAPI(title="Kokoro TTS API (Local)", version="1.0.0")

# Allow all browser origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache pipelines so we don't reload models for every request
pipelines = {}

def get_pipeline(lang_code):
    if lang_code not in pipelines:
        print(f"Loading pipeline for {lang_code}...")
        pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return pipelines[lang_code]

@app.get("/")
def health():
    return {"status": "ok", "service": "Kokoro TTS (Local Localhost)", "version": "1.0.0"}

@app.get("/voices")
def voices():
    return {
        "hi":    {"default": "hf_alpha", "voices": ["hf_alpha", "hf_beta", "hm_omega", "hm_psi"]},
        "en-us": {"default": "af_heart",  "voices": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael"]},
        "en-gb": {"default": "bf_emma",   "voices": ["bf_emma", "bf_isabella", "bm_george", "bm_lewis"]},
    }

@app.post("/tts")
def tts(req: TTSRequest):
    lang_code = LANG_CODE.get(req.language)
    if not lang_code:
        raise HTTPException(400, f"Unsupported language: {req.language}")

    voice = req.voice or DEFAULT_VOICE[req.language]

    try:
        pipeline = get_pipeline(lang_code)
        chunks = []
        for _, _, audio in pipeline(req.text, voice=voice, speed=req.speed):
            if audio is not None and len(audio) > 0:
                chunks.append(audio)

        if not chunks:
            raise HTTPException(500, "No audio generated")

        full_audio = np.concatenate(chunks)
        buf = io.BytesIO()
        sf.write(buf, full_audio, samplerate=24000, format="WAV")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="audio/wav",
            headers={"Content-Disposition": 'attachment; filename="speech.wav"'},
        )
    except Exception as e:
        raise HTTPException(500, f"TTS error: {str(e)}")

@app.get("/tts")
def tts_get(text: str, language: str = "en-us", voice: Optional[str] = None, speed: float = 1.0):
    return tts(TTSRequest(text=text, language=language, voice=voice, speed=speed))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Kokoro TTS Local Server on http://0.0.0.0:{port}")
    uvicorn.run("local_server:app", host="0.0.0.0", port=port, reload=False)
