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
      {/* Top right primary ambient light orb - slow drifting animation */}
      <div className="absolute -top-[12%] -right-[6%] h-[580px] w-[580px] rounded-full bg-gradient-to-br from-blue-500/28 via-indigo-500/22 to-primary/18 blur-[95px] will-change-transform animate-ambient-1 dark:from-primary/20 dark:to-indigo-500/20" />

      {/* Upper-center sky/cyan ambient light orb */}
      <div className="absolute top-[18%] left-[6%] h-[520px] w-[520px] rounded-full bg-gradient-to-tr from-cyan-400/26 via-sky-500/22 to-blue-400/18 blur-[100px] will-change-transform animate-ambient-2 dark:from-sky-500/16 dark:to-cyan-500/12" />

      {/* Center-right violet/indigo ambient light orb */}
      <div className="absolute top-[50%] -right-[8%] h-[540px] w-[540px] rounded-full bg-gradient-to-bl from-indigo-500/24 via-purple-500/18 to-blue-600/16 blur-[105px] will-change-transform animate-ambient-3 dark:from-indigo-500/16 dark:to-purple-500/14" />

      {/* Bottom-left blue/teal ambient light orb */}
      <div className="absolute -bottom-[10%] left-[4%] h-[580px] w-[580px] rounded-full bg-gradient-to-tr from-sky-400/24 via-blue-600/20 to-indigo-500/16 blur-[100px] will-change-transform animate-ambient-4 dark:from-blue-600/18 dark:to-sky-600/15" />
    </div>
  );
}
