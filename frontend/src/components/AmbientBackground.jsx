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
      <div className="absolute -top-[12%] -right-[6%] h-[520px] w-[520px] rounded-full bg-primary/10 blur-[120px] dark:bg-primary/15" />
      {/* Center-left sky/cyan ambient light orb */}
      <div className="absolute top-[32%] -left-[8%] h-[480px] w-[480px] rounded-full bg-sky-500/8 blur-[130px] dark:bg-sky-500/12" />
      {/* Bottom-right indigo/violet ambient light orb */}
      <div className="absolute -bottom-[10%] right-[10%] h-[560px] w-[560px] rounded-full bg-indigo-500/8 blur-[140px] dark:bg-indigo-500/12" />
    </div>
  );
}
