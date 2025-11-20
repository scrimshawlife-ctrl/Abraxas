/**
 * AAL UI Kit - Metric Card Component
 * Standardized metric display with icon, label, value, and optional trend
 */

import React from "react";
import { AalCard } from "./AalCard";
import { AalSigilFrame } from "./AalSigilFrame";
import { AalTag } from "./AalTag";

export interface AalMetricCardProps {
  /**
   * Metric label/title
   */
  label: string;

  /**
   * Metric value (number or formatted string)
   */
  value: string | number;

  /**
   * Optional icon to display in sigil frame
   */
  icon?: React.ReactNode;

  /**
   * Color theme for sigil frame
   * @default "cyan"
   */
  tone?: "cyan" | "yellow" | "magenta";

  /**
   * Optional trend indicator
   */
  trend?: {
    direction: "up" | "down" | "neutral";
    value: string;
  };

  /**
   * Optional tag/badge
   */
  tag?: string;

  /**
   * Optional description text
   */
  description?: string;

  /**
   * Click handler
   */
  onClick?: () => void;

  /**
   * Additional CSS class names
   */
  className?: string;
}

export function AalMetricCard({
  label,
  value,
  icon,
  tone = "cyan",
  trend,
  tag,
  description,
  onClick,
  className = "",
}: AalMetricCardProps) {
  const isClickable = !!onClick;

  return (
    <AalCard
      variant="ghost"
      className={className}
      as="div"
      style={{
        cursor: isClickable ? "pointer" : "default",
        transition: "all 0.2s ease",
      }}
      onClick={onClick}
    >
      <div className="aal-stack-md">
        {/* Icon and Label Row */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {icon && (
            <AalSigilFrame tone={tone} size={32}>
              {icon}
            </AalSigilFrame>
          )}
          <div style={{ flex: 1 }}>
            <h3
              className="aal-heading-md"
              style={{ fontSize: "14px", marginBottom: "4px" }}
            >
              {label}
            </h3>
            {tag && <AalTag>{tag}</AalTag>}
          </div>
        </div>

        {/* Value Display */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          <span
            className="aal-heading-md"
            style={{
              fontSize: "24px",
              color: "var(--aal-color-text)",
              fontFamily: "monospace",
            }}
          >
            {value}
          </span>

          {trend && (
            <span
              className="aal-body"
              style={{
                fontSize: "13px",
                color:
                  trend.direction === "up"
                    ? "#00D4FF"
                    : trend.direction === "down"
                    ? "#FF3EF6"
                    : "var(--aal-color-muted)",
              }}
            >
              {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"}{" "}
              {trend.value}
            </span>
          )}
        </div>

        {/* Optional Description */}
        {description && (
          <p className="aal-body" style={{ fontSize: "12px" }}>
            {description}
          </p>
        )}
      </div>
    </AalCard>
  );
}
