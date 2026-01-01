/**
 * AAL UI Kit - Divider Component
 * Subtle horizontal separator
 */

import React from "react";

export interface AalDividerProps {
  /**
   * Additional CSS class names
   */
  className?: string;
}

export function AalDivider({ className = "" }: AalDividerProps) {
  const combinedClassName = `aal-divider ${className}`.trim();

  return <hr className={combinedClassName} />;
}
