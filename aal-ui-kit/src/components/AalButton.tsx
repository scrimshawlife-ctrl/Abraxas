/**
 * AAL UI Kit - Button Component
 * Primary, secondary, and ghost button variants
 * Accessible: supports aria-label, keyboard navigation
 */

import React from "react";

export interface AalButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Button visual variant
   * @default "primary"
   */
  variant?: "primary" | "secondary" | "ghost";

  /**
   * Icon displayed before text
   */
  leftIcon?: React.ReactNode;

  /**
   * Icon displayed after text
   */
  rightIcon?: React.ReactNode;

  /**
   * Loading state - shows spinner and disables button
   */
  loading?: boolean;
}

export const AalButton = React.forwardRef<HTMLButtonElement, AalButtonProps>(
  (
    { variant = "primary", leftIcon, rightIcon, loading, children, className = "", disabled, ...rest },
    ref
  ) => {
    const variantClass = `aal-button--${variant}`;
    const loadingClass = loading ? "aal-button--loading" : "";
    const combinedClassName = `aal-button ${variantClass} ${loadingClass} ${className}`.trim();

    return (
      <button
        ref={ref}
        className={combinedClassName}
        disabled={disabled || loading}
        aria-busy={loading}
        {...rest}
      >
        {leftIcon && <span className="aal-button__icon-left" aria-hidden="true">{leftIcon}</span>}
        {children}
        {rightIcon && <span className="aal-button__icon-right" aria-hidden="true">{rightIcon}</span>}
      </button>
    );
  }
);

AalButton.displayName = "AalButton";
