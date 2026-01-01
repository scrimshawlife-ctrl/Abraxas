/**
 * AAL UI Kit - Card Component
 * Panel/container component with subtle cyan glow
 */

import React from "react";

export interface AalCardProps {
  /**
   * Card content
   */
  children: React.ReactNode;

  /**
   * Visual variant
   * @default "default"
   */
  variant?: "default" | "ghost";

  /**
   * Custom padding
   */
  padding?: number | string;

  /**
   * HTML element to render as
   * @default "section"
   */
  as?: keyof JSX.IntrinsicElements;

  /**
   * Additional CSS class names
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;

  /**
   * Click handler
   */
  onClick?: () => void;
}

export function AalCard({
  children,
  variant = "default",
  padding,
  as: Component = "section",
  className = "",
  style: inlineStyle,
  onClick,
}: AalCardProps) {
  const variantClass = variant === "ghost" ? "aal-card--ghost" : "";
  const combinedClassName = `aal-card ${variantClass} ${className}`.trim();

  const style: React.CSSProperties = { ...inlineStyle };
  if (padding !== undefined) {
    style.padding = typeof padding === "number" ? `${padding}px` : padding;
  }

  return (
    <Component className={combinedClassName} style={style} onClick={onClick}>
      {children}
    </Component>
  );
}
