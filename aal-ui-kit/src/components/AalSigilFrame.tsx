/**
 * AAL UI Kit - Sigil Frame Component
 * Circular frame for icons/glyphs with tone variants
 */

import React from "react";

export interface AalSigilFrameProps {
  /**
   * Icon or glyph content
   */
  children?: React.ReactNode;

  /**
   * Color theme
   * - cyan: general/system
   * - yellow: forecasting/analytics
   * - magenta: creative/music/emotional
   * @default "cyan"
   */
  tone?: "cyan" | "yellow" | "magenta";

  /**
   * Size (diameter) in pixels
   * @default 40
   */
  size?: number;

  /**
   * Additional CSS class names
   */
  className?: string;
}

export function AalSigilFrame({
  children,
  tone = "cyan",
  size = 40,
  className = "",
}: AalSigilFrameProps) {
  const toneClass = tone !== "cyan" ? `aal-sigil-frame--${tone}` : "";
  const combinedClassName = `aal-sigil-frame ${toneClass} ${className}`.trim();

  const style: React.CSSProperties = {
    width: `${size}px`,
    height: `${size}px`,
    minWidth: `${size}px`,
    minHeight: `${size}px`,
  };

  return (
    <div className={combinedClassName} style={style}>
      {children}
    </div>
  );
}
