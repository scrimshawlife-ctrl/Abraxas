/**
 * AAL UI Kit - Theme Switch Component
 * Toggle between dark/light modes with system preference support
 */

import React, { useEffect, useState } from "react";

export type Theme = "dark" | "light" | "system";

export interface AalThemeSwitchProps {
  /**
   * Default theme on mount
   * @default "system"
   */
  defaultTheme?: Theme;

  /**
   * Controlled theme value
   */
  theme?: Theme;

  /**
   * Theme change callback
   */
  onThemeChange?: (theme: Theme) => void;

  /**
   * Storage key for persistence
   * @default "aal-theme"
   */
  storageKey?: string;

  /**
   * Additional CSS class
   */
  className?: string;

  /**
   * Show labels instead of icons only
   */
  showLabels?: boolean;
}

const SunIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);

const MoonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const SystemIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8M12 17v4" />
  </svg>
);

export function AalThemeSwitch({
  defaultTheme = "system",
  theme: controlledTheme,
  onThemeChange,
  storageKey = "aal-theme",
  className = "",
  showLabels = false,
}: AalThemeSwitchProps) {
  const [internalTheme, setInternalTheme] = useState<Theme>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(storageKey);
      if (stored === "dark" || stored === "light" || stored === "system") {
        return stored;
      }
    }
    return defaultTheme;
  });

  const theme = controlledTheme ?? internalTheme;

  useEffect(() => {
    const root = document.documentElement;

    if (theme === "system") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", theme);
    }

    localStorage.setItem(storageKey, theme);
  }, [theme, storageKey]);

  const handleThemeChange = (newTheme: Theme) => {
    if (!controlledTheme) {
      setInternalTheme(newTheme);
    }
    onThemeChange?.(newTheme);
  };

  const themes: { value: Theme; icon: React.ReactNode; label: string }[] = [
    { value: "light", icon: <SunIcon />, label: "Light" },
    { value: "dark", icon: <MoonIcon />, label: "Dark" },
    { value: "system", icon: <SystemIcon />, label: "System" },
  ];

  return (
    <div
      className={`aal-theme-switch ${className}`.trim()}
      role="radiogroup"
      aria-label="Theme selection"
    >
      {themes.map(({ value, icon, label }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={theme === value}
          className={`aal-theme-switch__option ${theme === value ? "aal-theme-switch__option--active" : ""}`}
          onClick={() => handleThemeChange(value)}
          aria-label={label}
        >
          <span className="aal-theme-switch__icon" aria-hidden="true">{icon}</span>
          {showLabels && <span className="aal-theme-switch__label">{label}</span>}
        </button>
      ))}
    </div>
  );
}
