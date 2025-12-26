/**
 * AAL UI Kit - Tag Component
 * Small badge/pill for labels and categories
 */

import React from "react";

export interface AalTagProps {
  /**
   * Tag label text
   */
  children: React.ReactNode;

  /**
   * Optional icon
   */
  icon?: React.ReactNode;

  /**
   * Additional CSS class names
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;
}

export function AalTag({ children, icon, className = "", style }: AalTagProps) {
  const combinedClassName = `aal-tag ${className}`.trim();

  return (
    <span className={combinedClassName} style={style}>
      {icon && <span className="aal-tag__icon">{icon}</span>}
      {children}
    </span>
  );
}
