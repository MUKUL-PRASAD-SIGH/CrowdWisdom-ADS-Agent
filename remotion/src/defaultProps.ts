// src/defaultProps.ts
// Fallback props for Remotion Studio preview when props.json is missing
import { AdVideoProps } from "./types";
import fs from "fs";
import path from "path";

const propsPath = path.resolve(__dirname, "props.json");

let loadedProps: Partial<AdVideoProps> = {};
try {
  if (fs.existsSync(propsPath)) {
    loadedProps = JSON.parse(fs.readFileSync(propsPath, "utf-8"));
  }
} catch (e) {
  console.warn("Could not load props.json, using defaults.", e);
}

const defaultProps: AdVideoProps = {
  durationSeconds: 60,
  fps: 30,
  brandName: "CrowdWisdomTrading",
  brandColor: "#00D4AA",
  callToAction: "Click Here to Learn More",
  audioPath: "", // Provide a local mp3 path if previewing
  scenes: [
    {
      sceneNumber: 1,
      durationSeconds: 3,
      imagePath: "",
      voiceoverText: "Are you losing money in the markets?",
      onScreenText: "STOP LOSING MONEY",
      backgroundMusicMood: "tense",
    },
    {
      sceneNumber: 2,
      durationSeconds: 7,
      imagePath: "",
      voiceoverText: "Most retail traders trade purely on emotion instead of data. That's why 90% fail.",
      onScreenText: "90% OF RETAIL TRADERS FAIL",
      backgroundMusicMood: "tense",
    },
    // ... add more mock scenes if needed for preview
  ],
  ...loadedProps,
};

export default defaultProps;
