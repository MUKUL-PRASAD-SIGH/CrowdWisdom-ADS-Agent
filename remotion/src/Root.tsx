// src/Root.tsx
// Registers all Remotion compositions
import React from "react";
import { Composition } from "remotion";
import { AdVideo, AdVideoProps } from "./AdVideo";
import defaultProps from "./defaultProps";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="AdVideo"
        component={AdVideo}
        durationInFrames={1800}   // 60 seconds × 30 fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
    </>
  );
};
