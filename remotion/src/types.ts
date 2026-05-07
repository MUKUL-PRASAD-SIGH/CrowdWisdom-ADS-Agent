// src/types.ts
// Shared TypeScript interfaces for the AdVideo composition

export interface SceneData {
  /** Scene index (1-based) */
  sceneNumber: number;
  /** Duration of this scene in seconds */
  durationSeconds: number;
  /** Absolute path to the AI-generated background image */
  imagePath: string;
  /** Voiceover text for this scene (also used for subtitles) */
  voiceoverText: string;
  /** Large text overlay shown on screen */
  onScreenText: string;
  /** Background music mood tag */
  backgroundMusicMood: string;
}

export interface AdVideoProps {
  /** Array of scene data objects (7 scenes for a 60s ad) */
  scenes: SceneData[];
  /** Absolute path to the voiceover MP3 */
  audioPath: string;
  /** Brand name shown in the outro */
  brandName: string;
  /** Call-to-action text shown in the final scene */
  callToAction: string;
  /** Primary brand colour (hex) */
  brandColor: string;
  /** Total duration in seconds */
  durationSeconds: number;
  /** Frames per second */
  fps: number;
}
