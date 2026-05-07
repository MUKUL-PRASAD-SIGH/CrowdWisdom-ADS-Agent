// src/AdVideo.tsx
import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  spring,
} from "remotion";
import { AdVideoProps } from "./types";

export const AdVideo: React.FC<AdVideoProps> = ({
  scenes,
  audioPath,
  brandName,
  brandColor,
  callToAction,
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  let startFrame = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#111" }}>
      {/* Background Audio Voiceover */}
      {audioPath && <Audio src={`file://${audioPath}`} />}

      {/* Render each scene in sequence */}
      {scenes.map((scene, index) => {
        const sceneDurationFrames = Math.floor(scene.durationSeconds * fps);
        const currentStart = startFrame;
        startFrame += sceneDurationFrames;

        const isLastScene = index === scenes.length - 1;

        return (
          <Sequence
            key={scene.sceneNumber}
            from={currentStart}
            durationInFrames={sceneDurationFrames}
          >
            <SceneContent
              scene={scene}
              brandColor={brandColor}
              isLastScene={isLastScene}
              brandName={brandName}
              callToAction={callToAction}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent: React.FC<{
  scene: any;
  brandColor: string;
  isLastScene: boolean;
  brandName: string;
  callToAction: string;
}> = ({ scene, brandColor, isLastScene, brandName, callToAction }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Simple zoom-in effect for the background image
  const scale = 1 + frame / (fps * 10);

  // Pop-in effect for the text
  const textScale = spring({
    frame,
    fps,
    config: { damping: 12 },
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {scene.imagePath ? (
        <Img
          src={`file://${scene.imagePath}`}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
            filter: "brightness(0.6)", // Darken background slightly
          }}
        />
      ) : (
        <AbsoluteFill style={{ backgroundColor: "#222" }} />
      )}

      {/* Centered Text Overlay */}
      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: "40px",
        }}
      >
        <h1
          style={{
            fontFamily: "sans-serif",
            fontSize: "80px",
            fontWeight: "bold",
            color: "white",
            textAlign: "center",
            textShadow: "2px 4px 10px rgba(0,0,0,0.8)",
            transform: `scale(${textScale})`,
            margin: 0,
          }}
        >
          {scene.onScreenText}
        </h1>
      </AbsoluteFill>

      {/* Call to Action for Last Scene */}
      {isLastScene && (
        <AbsoluteFill
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            paddingBottom: "200px",
          }}
        >
          <div
            style={{
              backgroundColor: brandColor,
              color: "#000",
              padding: "30px 60px",
              borderRadius: "20px",
              fontSize: "60px",
              fontWeight: "bold",
              fontFamily: "sans-serif",
              boxShadow: "0px 10px 30px rgba(0,0,0,0.5)",
              transform: `scale(${spring({
                frame: frame - 15, // Delay the button pop-in slightly
                fps,
              })})`,
            }}
          >
            {callToAction}
          </div>
          <div
            style={{
              marginTop: "20px",
              color: "white",
              fontSize: "40px",
              fontFamily: "sans-serif",
              fontWeight: "bold",
              opacity: Math.min(1, Math.max(0, (frame - 30) / 10)),
            }}
          >
            {brandName}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
