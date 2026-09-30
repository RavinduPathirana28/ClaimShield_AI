import React from 'react';

/**
 * AmbientBackground
 * Provides physical optical depth and subtle luminous atmospheric variations behind glass surfaces.
 * Specially calibrated for Apple VisionOS / iOS style light & dark frosted glass refraction:
 * - In light theme: soft, elegant pastel chromatic glows (azure, periwinkle, teal, lilac)
 *   that diffuse through frosted glass surfaces without washing out.
 * - In dark theme: rich, deep primary, cyan, and violet atmospheric blooms.
 * - Hardware-accelerated GPU transforms with slow, peaceful drifting.
 */
export default function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden select-none"
    >
      {/* 1. Top right primary ambient light orb - slow drifting animation */}
      <div className="absolute -top-[12%] -right-[6%] h-[580px] w-[580px] rounded-full bg-gradient-to-br from-blue-500/28 via-indigo-500/22 to-primary/18 blur-[95px] will-change-transform animate-ambient-1 dark:from-primary/20 dark:to-indigo-500/20" />

      {/* 2. Upper-left sky/cyan ambient light orb */}
      <div className="absolute top-[14%] left-[4%] h-[520px] w-[520px] rounded-full bg-gradient-to-tr from-cyan-400/26 via-sky-500/22 to-blue-400/18 blur-[100px] will-change-transform animate-ambient-2 dark:from-sky-500/16 dark:to-cyan-500/12" />

      {/* 3. Center upper ambient light orb - sits directly behind verification input card for real glass refraction */}
      <div className="absolute top-[22%] left-[26%] h-[580px] w-[620px] rounded-full bg-gradient-to-br from-sky-400/30 via-indigo-400/24 to-blue-500/18 blur-[110px] will-change-transform animate-ambient-3 dark:from-primary/16 dark:to-indigo-500/14" />

      {/* 4. Center lower ambient light orb - sits directly behind verification results / empty state card */}
      <div className="absolute top-[54%] left-[32%] h-[560px] w-[580px] rounded-full bg-gradient-to-tr from-indigo-300/28 via-cyan-400/22 to-purple-400/18 blur-[110px] will-change-transform animate-ambient-4 dark:from-indigo-600/16 dark:to-cyan-600/12" />

      {/* 5. Center-right violet/indigo ambient light orb */}
      <div className="absolute top-[48%] -right-[8%] h-[540px] w-[540px] rounded-full bg-gradient-to-bl from-indigo-500/24 via-purple-500/18 to-blue-600/16 blur-[105px] will-change-transform animate-ambient-1 dark:from-indigo-500/16 dark:to-purple-500/14" />

      {/* 6. Bottom-left blue/teal ambient light orb */}
      <div className="absolute -bottom-[10%] left-[2%] h-[580px] w-[580px] rounded-full bg-gradient-to-tr from-sky-400/24 via-blue-600/20 to-indigo-500/16 blur-[100px] will-change-transform animate-ambient-2 dark:from-blue-600/18 dark:to-sky-600/15" />
    </div>
  );
}
