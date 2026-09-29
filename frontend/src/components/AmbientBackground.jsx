import React from 'react';

/**
 * AmbientBackground
 * Provides physical depth and subtle luminous atmospheric variations behind glass surfaces.
 * Uses existing theme palette tokens (primary blue, sky, indigo) with heavy blur.
 * Fixed in background with pointer-events-none so it doesn't interfere with interactions or scrolling.
 */
export default function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden select-none"
    >
      {/* Top right primary ambient light orb */}
      <div className="absolute -top-[10%] -right-[5%] h-[560px] w-[560px] rounded-full bg-primary/20 blur-[85px] dark:bg-primary/20" />
      {/* Upper-center sky/cyan ambient light orb */}
      <div className="absolute top-[22%] left-[10%] h-[480px] w-[480px] rounded-full bg-sky-500/18 blur-[90px] dark:bg-sky-500/15" />
      {/* Center-right indigo ambient light orb */}
      <div className="absolute top-[52%] -right-[6%] h-[520px] w-[520px] rounded-full bg-indigo-500/16 blur-[95px] dark:bg-indigo-500/16" />
      {/* Bottom-left blue ambient light orb */}
      <div className="absolute -bottom-[8%] left-[6%] h-[540px] w-[540px] rounded-full bg-blue-600/16 blur-[90px] dark:bg-blue-600/18" />
    </div>
  );
}
