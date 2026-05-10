# 🧠 CrowdWisdomTrading AI Ads Studio

An end-to-end automated pipeline that generates high-converting, 60-second direct-response video ads for the CrowdWisdomTrading brand. It combines Meta Ads scraping, LLM orchestration, AI image generation, Voiceover TTS, and Remotion rendering into a single click—now powered by a stunning React web interface.

## ✨ Key Features
- **Data-Driven Intelligence:** Scrapes the latest successful Meta Ads via Apify.
- **Psychological Extraction:** Analyses ad copy to extract pain points, winning hooks, and marketing angles.
- **Automated Scripting:** Fetches brand context from Google Drive and combines it with extracted insights to create a high-retention 7-scene ad script.
- **Full Video Production:** Automatically generates background visuals (Pollinations.ai), professional Voiceover (ElevenLabs), and renders a final vertical MP4 (Remotion).
- **Resilient AI Pipeline:** Powered by Google Gemini (`gemini-2.5-flash`) with exponential retry backoff, ensuring zero rate-limit crashes.
- **Premium Web UI:** A beautiful, glassmorphism React interface to track live progress and preview generated assets.

---

## 🏗️ Architecture Flow

1. **User Input** ➔ Enters niche in React UI.
2. **FastAPI Backend** ➔ Triggers CrewAI pipeline via background thread.
3. **CrewAI Agents:**
   - 🕵️ **Ad Researcher:** Scrapes Meta Ad Library via Apify.
   - 🧬 **Pain Point Extractor:** Synthesizes `pain_concepts.json`.
   - ✍️ **Script Writer:** Generates a 60s `ad_script.json`.
   - 🎬 **Video Producer:** 
     - Calls Pollinations API for scene images.
     - Calls ElevenLabs API for Voiceover.
     - Executes `npx remotion render` to compile `final_ad.mp4`.
4. **Output Delivery** ➔ React UI streams the generated Video, Audio, and JSON insights directly to the browser.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (Required for Video Rendering & UI)
- API Keys: Google Gemini, Apify, ElevenLabs

### 2. Backend Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # (Windows)
source venv/bin/activate # (Mac/Linux)

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure API Keys
cp .env.example .env
# Open .env and add your GEMINI_API_KEY, APIFY_API_TOKEN, ELEVENLABS_API_KEY
```

### 3. Video Renderer Setup (Remotion)
```bash
cd remotion
npm install
cd ..
```

### 4. Frontend Setup (React)
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Usage

### Option A: Run via Premium Web UI (Recommended)
This starts both the FastAPI backend and the React frontend.
1. **Start the API Server** (Terminal 1):
   ```bash
   python api.py
   ```
2. **Start the UI** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser. Enter your niche and click **"Generate AI Ad Pipeline"**.

### Option B: Run via CLI
If you prefer running headless scripts:
```bash
# Run the full pipeline
python main.py

# Run specific steps for testing
python main.py --step research
python main.py --step extraction
python main.py --step script
python main.py --step production
```

## 📂 Output Structure
All generated files are saved to the `outputs/` directory:
- `ads_raw.json` - Scraped competitor ads
- `pain_concepts.json` - AI Marketing DNA & Hooks
- `ad_script.json` - Final 7-scene script
- `audio/voiceover.mp3` - ElevenLabs AI Voice
- `images/scene_X.jpg` - Generated visuals
- `videos/final_ad.mp4` - Final rendered video
