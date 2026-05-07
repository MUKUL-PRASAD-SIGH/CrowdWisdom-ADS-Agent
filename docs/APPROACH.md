# Approach Documentation

## Architecture
The system uses the `CrewAI Flow` framework to orchestrate a 4-step pipeline.

1. **Ad Researcher Agent:** Uses Apify (`apify/facebook-ads-library-scraper`) to scrape Meta Ads for the target niche over the last 30 days. It filters the top 10 ads by estimated reach.
2. **Pain Extractor Agent:** An LLM processes the scraped ad copy to extract core pain points, emotional triggers, and successful CTAs, outputting a structured JSON schema.
3. **Script Writer Agent:** Uses `gdown` or Google Service Account to fetch brand context from a Google Drive document. Combines this with the extracted pain points to generate a 60-second, 7-scene video script using a proven Pain-Agitate-Solution marketing framework.
4. **Video Producer Agent:**
   - Generates AI images for each scene using Pollinations.ai (free, no API key).
   - Generates voiceover using ElevenLabs.
   - Writes a `props.json` file to the `remotion/src` folder.
   - Executes `npx remotion render` to generate the final `.mp4`.

## Tools Used
- **CrewAI & CrewAI Flow:** Agent orchestration and state management.
- **Apify:** `ApifyAdsTool` wraps the Apify Python client to run actors.
- **Google Drive API:** `GDriveTool` fetches text/pdf/json context.
- **Pollinations.ai:** `ImageGenTool` requests free image generation via HTTP GET.
- **ElevenLabs:** `ElevenLabsTool` uses their TTS API.
- **Remotion:** A React-based video rendering framework called via CLI.

## Scale & Error Handling
- **Flow State:** State is preserved across flow steps. If a step fails, it attempts to load fallback data from the `outputs/` directory to allow continuation.
- **Retries:** All network tools (`Apify`, `GDrive`, `ElevenLabs`, `Pollinations`) use the `tenacity` library for robust exponential backoff retries.
- **Logging:** `loguru` handles asynchronous, rotated file logging and colorised console output.
- **Modularity:** Steps can be run individually using `python main.py --step <step_name>`, allowing for rapid iteration of specific parts of the pipeline without re-running expensive upstream tasks.
