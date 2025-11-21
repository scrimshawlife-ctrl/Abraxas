/**
 * AAL UI Kit - Select Component
 * Dropdown select with AAL styling
 */

import React, { useState, useRef, useEffect, useId } from "react";

export interface AalSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface AalSelectProps {
  options: AalSelectOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  className?: string;
}

const ChevronIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M6 9l6 6 6-6" />
  </svg>
);

export function AalSelect({
  options,
  value: controlledValue,
  defaultValue,
  onChange,
  placeholder = "Select...",
  label,
  disabled = false,
  error = false,
  helperText,
  className = "",
}: AalSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [internalValue, setInternalValue] = useState(defaultValue || "");
  const selectRef = useRef<HTMLDivElement>(null);
  const id = useId();

  const value = controlledValue ?? internalValue;
  const selectedOption = options.find((opt) => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (optValue: string) => {
    if (!controlledValue) setInternalValue(optValue);
    onChange?.(optValue);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsOpen(!isOpen);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div className={`aal-select-wrapper ${className}`.trim()} ref={selectRef}>
      {label && (
        <label className="aal-select-label" id={`${id}-label`}>
          {label}
        </label>
      )}
      <button
        type="button"
        className={`aal-select ${isOpen ? "aal-select--open" : ""} ${error ? "aal-select--error" : ""} ${disabled ? "aal-select--disabled" : ""}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby={label ? `${id}-label` : undefined}
      >
        <span className={`aal-select__value ${!selectedOption ? "aal-select__placeholder" : ""}`}>
          {selectedOption?.label || placeholder}
        </span>
        <span className={`aal-select__chevron ${isOpen ? "aal-select__chevron--open" : ""}`}>
          <ChevronIcon />
        </span>
      </button>
      {isOpen && (
        <ul className="aal-select__dropdown" role="listbox">
          {options.map((opt) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={opt.value === value}
              aria-disabled={opt.disabled}
              className={`aal-select__option ${opt.value === value ? "aal-select__option--selected" : ""} ${opt.disabled ? "aal-select__option--disabled" : ""}`}
              onClick={() => !opt.disabled && handleSelect(opt.value)}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
      {helperText && (
        <span className={`aal-select-helper ${error ? "aal-select-helper--error" : ""}`}>
          {helperText}
        </span>
      )}
    </div>
  );
}
