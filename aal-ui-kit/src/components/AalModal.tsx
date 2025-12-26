/**
 * AAL UI Kit - Modal Component
 * Accessible modal dialog with focus trapping
 */

import React, { useEffect, useRef, useCallback } from "react";

export interface AalModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;

  /**
   * Close handler
   */
  onClose: () => void;

  /**
   * Modal title
   */
  title?: string;

  /**
   * Modal content
   */
  children: React.ReactNode;

  /**
   * Footer content (buttons, etc.)
   */
  footer?: React.ReactNode;

  /**
   * Size variant
   * @default "md"
   */
  size?: "sm" | "md" | "lg" | "full";

  /**
   * Close on backdrop click
   * @default true
   */
  closeOnBackdrop?: boolean;

  /**
   * Close on Escape key
   * @default true
   */
  closeOnEscape?: boolean;

  /**
   * Additional CSS class
   */
  className?: string;
}

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);

export function AalModal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  closeOnBackdrop = true,
  closeOnEscape = true,
  className = "",
}: AalModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);

  // Handle escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === "Escape") {
        onClose();
      }
    },
    [closeOnEscape, onClose]
  );

  // Focus trap
  useEffect(() => {
    if (!isOpen) return;

    previousActiveElement.current = document.activeElement;
    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    // Focus the modal
    const focusableElements = modalRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusableElements && focusableElements.length > 0) {
      focusableElements[0].focus();
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";

      // Restore focus
      if (previousActiveElement.current instanceof HTMLElement) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, handleKeyDown]);

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdrop && e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="aal-modal-backdrop"
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={modalRef}
        className={`aal-modal aal-modal--${size} ${className}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "aal-modal-title" : undefined}
      >
        {title && (
          <div className="aal-modal__header">
            <h2 id="aal-modal-title" className="aal-modal__title">
              {title}
            </h2>
            <button
              type="button"
              className="aal-modal__close"
              onClick={onClose}
              aria-label="Close modal"
            >
              <CloseIcon />
            </button>
          </div>
        )}

        <div className="aal-modal__body">{children}</div>

        {footer && <div className="aal-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}

// Confirm dialog helper
export interface AalConfirmProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "default";
}

export function AalConfirm({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "default",
}: AalConfirmProps) {
  return (
    <AalModal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <div className="aal-modal__actions">
          <button
            type="button"
            className="aal-button aal-button--ghost"
            onClick={onClose}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`aal-button ${variant === "danger" ? "aal-button--danger" : "aal-button--primary"}`}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmLabel}
          </button>
        </div>
      }
    >
      <p className="aal-body">{message}</p>
    </AalModal>
  );
}
