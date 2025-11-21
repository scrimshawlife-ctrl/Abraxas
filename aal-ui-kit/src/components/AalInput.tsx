/**
 * AAL UI Kit - Input Component
 * Text input field with AAL styling
 */

import React from "react";

export interface AalInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  /**
   * Input label (optional)
   */
  label?: string;

  /**
   * Left icon/element
   */
  leftIcon?: React.ReactNode;

  /**
   * Right icon/element
   */
  rightIcon?: React.ReactNode;

  /**
   * Size variant
   * @default "md"
   */
  size?: "sm" | "md" | "lg";

  /**
   * Error state
   */
  error?: boolean;

  /**
   * Helper/error text
   */
  helperText?: string;
}

export function AalInput({
  label,
  leftIcon,
  rightIcon,
  size = "md",
  error = false,
  helperText,
  className = "",
  style,
  ...inputProps
}: AalInputProps) {
  const sizeClass = size !== "md" ? `aal-input--${size}` : "";
  const errorClass = error ? "aal-input--error" : "";
  const combinedClassName = `aal-input ${sizeClass} ${errorClass} ${className}`.trim();

  return (
    <div className="aal-input-wrapper">
      {label && <label className="aal-input-label">{label}</label>}
      <div className={`aal-input-container ${leftIcon ? "has-left-icon" : ""} ${rightIcon ? "has-right-icon" : ""}`}>
        {leftIcon && <span className="aal-input-icon aal-input-icon--left">{leftIcon}</span>}
        <input className={combinedClassName} style={style} {...inputProps} />
        {rightIcon && <span className="aal-input-icon aal-input-icon--right">{rightIcon}</span>}
      </div>
      {helperText && (
        <span className={`aal-input-helper ${error ? "aal-input-helper--error" : ""}`}>
          {helperText}
        </span>
      )}
    </div>
  );
}
