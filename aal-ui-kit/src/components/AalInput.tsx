/**
 * AAL UI Kit - Input Component
 * Text input field with AAL styling
 * Accessible: proper label association, aria-invalid, aria-describedby
 */

import React, { useId } from "react";

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
  id: providedId,
  ...inputProps
}: AalInputProps) {
  const generatedId = useId();
  const inputId = providedId || generatedId;
  const helperId = `${inputId}-helper`;

  const sizeClass = size !== "md" ? `aal-input--${size}` : "";
  const errorClass = error ? "aal-input--error" : "";
  const combinedClassName = `aal-input ${sizeClass} ${errorClass} ${className}`.trim();

  return (
    <div className="aal-input-wrapper">
      {label && (
        <label className="aal-input-label" htmlFor={inputId}>
          {label}
        </label>
      )}
      <div className={`aal-input-container ${leftIcon ? "has-left-icon" : ""} ${rightIcon ? "has-right-icon" : ""}`}>
        {leftIcon && <span className="aal-input-icon aal-input-icon--left" aria-hidden="true">{leftIcon}</span>}
        <input
          id={inputId}
          className={combinedClassName}
          style={style}
          aria-invalid={error}
          aria-describedby={helperText ? helperId : undefined}
          {...inputProps}
        />
        {rightIcon && <span className="aal-input-icon aal-input-icon--right" aria-hidden="true">{rightIcon}</span>}
      </div>
      {helperText && (
        <span
          id={helperId}
          className={`aal-input-helper ${error ? "aal-input-helper--error" : ""}`}
          role={error ? "alert" : undefined}
        >
          {helperText}
        </span>
      )}
    </div>
  );
}
