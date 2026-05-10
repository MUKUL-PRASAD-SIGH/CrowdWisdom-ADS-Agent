import json
import logging
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import threading
import sys
import os

# Import our flow
from main import _run_full_flow

app = FastAPI(title="CrowdWisdom Ads AI API")

# Allow CORS for local React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State management for the running pipeline
class PipelineState:
    def __init__(self):
        self.is_running = False
        self.status_message = "Idle"
        self.run_summary = None

state = PipelineState()
OUTPUTS_DIR = Path("outputs")

# Mount outputs so the frontend can fetch videos, audio, and images
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

class RunRequest(BaseModel):
    niche: str = "trading education stock market signals"

def execute_pipeline(niche: str):
    global state
    state.is_running = True
    state.status_message = f"Starting pipeline for niche: {niche}..."
    state.run_summary = None
    
    try:
        # We redirect stdout so we could capture logs if needed, but for now we just run it
        print(f"Executing pipeline in background for: {niche}")
        _run_full_flow(niche)
        
        # Once done, read the summary
        summary_path = OUTPUTS_DIR / "run_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                state.run_summary = json.load(f)
        state.status_message = "Pipeline completed successfully!"
    except Exception as e:
        print(f"Pipeline error: {e}")
        state.status_message = f"Pipeline failed: {str(e)}"
    finally:
        state.is_running = False

@app.post("/api/run")
def start_pipeline(req: RunRequest, background_tasks: BackgroundTasks):
    global state
    if state.is_running:
        return JSONResponse(status_code=400, content={"message": "Pipeline is already running."})
    
    # Run in background thread
    thread = threading.Thread(target=execute_pipeline, args=(req.niche,))
    thread.start()
    return {"message": "Pipeline started."}

@app.get("/api/status")
def get_status():
    global state
    return {
        "is_running": state.is_running,
        "status_message": state.status_message,
        "summary": state.run_summary
    }

def extract_json_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
        # Try pure JSON first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
            
        # Try extracting from ```json ... ``` blocks
        import re
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
    return None

@app.get("/api/results")
def get_results():
    # Read the latest JSON outputs
    results = {}
    files = ["ads_raw.json", "pain_concepts.json", "ad_script.json", "run_summary.json"]
    for file in files:
        path = OUTPUTS_DIR / file
        if path.exists():
            data = extract_json_from_file(path)
            if data:
                results[file.split(".")[0]] = data
    
    # Check media
    audio_path = OUTPUTS_DIR / "audio" / "voiceover.mp3"
    video_path = OUTPUTS_DIR / "videos" / "final_ad.mp4"
    
    results["media"] = {
        "has_audio": audio_path.exists(),
        "has_video": video_path.exists(),
        "audio_url": "/outputs/audio/voiceover.mp3" if audio_path.exists() else None,
        "video_url": "/outputs/videos/final_ad.mp4" if video_path.exists() else None,
    }
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
