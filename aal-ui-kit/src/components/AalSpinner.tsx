/**
 * AAL UI Kit - Spinner Component
 * Loading indicator with AAL styling
 */

import React from "react";

export interface AalSpinnerProps {
  /**
   * Size in pixels
   * @default 24
   */
  size?: number;

  /**
   * Color tone
   * @default "cyan"
   */
  tone?: "cyan" | "yellow" | "magenta";

  /**
   * Additional CSS class names
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;
}

export function AalSpinner({
  size = 24,
  tone = "cyan",
  className = "",
  style: inlineStyle,
}: AalSpinnerProps) {
  const toneClass = tone !== "cyan" ? `aal-spinner--${tone}` : "";
  const combinedClassName = `aal-spinner ${toneClass} ${className}`.trim();

  const style: React.CSSProperties = {
    width: `${size}px`,
    height: `${size}px`,
    ...inlineStyle,
  };

  return (
    <div className={combinedClassName} style={style}>
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeOpacity="0.2"
          strokeWidth="3"
        />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
