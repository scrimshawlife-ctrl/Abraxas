/**
 * AAL UI Kit - Shell Component
 * Layout wrapper for full-page content
 */

import React from "react";
import "../../styles/aal-theme.css";

export interface AalShellProps {
  /**
   * Page title (rendered as h1)
   */
  title?: string;

  /**
   * Page subtitle/description
   */
  subtitle?: string;

  /**
   * Page content
   */
  children: React.ReactNode;

  /**
   * Maximum width of content container
   * @default 1120
   */
  maxWidth?: number | string;

  /**
   * Additional CSS class names
   */
  className?: string;
}

export function AalShell({
  title,
  subtitle,
  children,
  maxWidth = 1120,
  className = "",
}: AalShellProps) {
  const maxWidthStyle =
    typeof maxWidth === "number" ? `${maxWidth}px` : maxWidth;

  return (
    <div className={`aal-page ${className}`}>
      <div className="aal-page-inner" style={{ maxWidth: maxWidthStyle }}>
        {(title || subtitle) && (
          <header className="aal-stack-md">
            {title && <h1 className="aal-heading-xl">{title}</h1>}
            {subtitle && <p className="aal-body">{subtitle}</p>}
          </header>
        )}
        {children}
      </div>
    </div>
  );
}
