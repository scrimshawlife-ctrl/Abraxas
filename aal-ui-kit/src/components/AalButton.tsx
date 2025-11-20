/**
 * AAL UI Kit - Button Component
 * Primary, secondary, and ghost button variants
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
}

export const AalButton = React.forwardRef<HTMLButtonElement, AalButtonProps>(
  (
    { variant = "primary", leftIcon, rightIcon, children, className = "", ...rest },
    ref
  ) => {
    const variantClass = `aal-button--${variant}`;
    const combinedClassName = `aal-button ${variantClass} ${className}`.trim();

    return (
      <button ref={ref} className={combinedClassName} {...rest}>
        {leftIcon && <span className="aal-button__icon-left">{leftIcon}</span>}
        {children}
        {rightIcon && <span className="aal-button__icon-right">{rightIcon}</span>}
      </button>
    );
  }
);

AalButton.displayName = "AalButton";
