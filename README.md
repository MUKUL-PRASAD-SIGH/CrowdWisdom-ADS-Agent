# README
# CrowdWisdomTrading Ads AI Agent

An automated pipeline for generating 60-second direct-response video ads for the CrowdWisdomTrading brand using CrewAI, Meta Ads scraping, LLMs, AI image generation, and Remotion.

## Features
- **Data-Driven:** Scrapes the latest successful Meta Ads via Apify.
- **Pain Point Extraction:** Analyses ads to extract psychological triggers and marketing angles.
- **Automated Scripting:** Fetches brand context from Google Drive and combines it with extracted insights to create a 7-scene ad script.
- **Full Video Production:** Generates background visuals (Pollinations.ai), Voiceover (ElevenLabs), and renders a final vertical MP4 using Remotion.

## Prerequisites
1. Python 3.10+
2. Node.js 18+ (for Remotion)

## Setup
1. Clone the repository
2. `python -m venv venv`
3. Activate venv (`source venv/bin/activate` or `venv\Scripts\activate`)
4. `pip install -r requirements.txt`
5. `cd remotion && npm install && cd ..`
6. Copy `.env.example` to `.env` and fill in your API keys (OpenRouter, Apify, ElevenLabs, Google Drive File ID).

## Usage
Run the full pipeline:
```bash
python main.py
```

Run a specific step:
```bash
python main.py --step research
python main.py --step extract
python main.py --step script
python main.py --step video
```
