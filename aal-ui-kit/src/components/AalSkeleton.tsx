/**
 * AAL UI Kit - Skeleton Component
 * Loading placeholder with shimmer animation
 */

import React from "react";

export interface AalSkeletonProps {
  /**
   * Skeleton variant
   * @default "text"
   */
  variant?: "text" | "circular" | "rectangular";

  /**
   * Width (CSS value)
   */
  width?: string | number;

  /**
   * Height (CSS value)
   */
  height?: string | number;

  /**
   * Animation enabled
   * @default true
   */
  animate?: boolean;

  /**
   * Number of lines (for text variant)
   */
  lines?: number;

  /**
   * Additional CSS class
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;
}

export function AalSkeleton({
  variant = "text",
  width,
  height,
  animate = true,
  lines = 1,
  className = "",
  style,
}: AalSkeletonProps) {
  const baseStyle: React.CSSProperties = {
    width: width ?? (variant === "text" ? "100%" : undefined),
    height: height ?? (variant === "text" ? "1em" : variant === "circular" ? width : undefined),
    ...style,
  };

  if (variant === "text" && lines > 1) {
    return (
      <div className={`aal-skeleton-group ${className}`.trim()}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`aal-skeleton aal-skeleton--text ${animate ? "aal-skeleton--animate" : ""}`}
            style={{
              ...baseStyle,
              width: i === lines - 1 ? "80%" : "100%", // Last line shorter
            }}
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`aal-skeleton aal-skeleton--${variant} ${animate ? "aal-skeleton--animate" : ""} ${className}`.trim()}
      style={baseStyle}
      aria-hidden="true"
    />
  );
}

// Preset skeleton components
export function AalSkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`aal-card ${className}`.trim()}>
      <div className="aal-row-md" style={{ marginBottom: 16 }}>
        <AalSkeleton variant="circular" width={40} height={40} />
        <div style={{ flex: 1 }}>
          <AalSkeleton width="60%" height={16} style={{ marginBottom: 8 }} />
          <AalSkeleton width="40%" height={12} />
        </div>
      </div>
      <AalSkeleton lines={3} />
    </div>
  );
}

export function AalSkeletonAvatar({ size = 40 }: { size?: number }) {
  return <AalSkeleton variant="circular" width={size} height={size} />;
}
