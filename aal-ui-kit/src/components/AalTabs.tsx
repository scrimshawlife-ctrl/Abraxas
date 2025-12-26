/**
 * AAL UI Kit - Tabs Component
 * Tab navigation with AAL styling
 */

import React, { useState } from "react";

export interface AalTab {
  /**
   * Unique tab identifier
   */
  id: string;

  /**
   * Tab label
   */
  label: React.ReactNode;

  /**
   * Optional icon
   */
  icon?: React.ReactNode;

  /**
   * Tab content
   */
  content: React.ReactNode;

  /**
   * Disabled state
   */
  disabled?: boolean;
}

export interface AalTabsProps {
  /**
   * Tab definitions
   */
  tabs: AalTab[];

  /**
   * Default active tab id
   */
  defaultTab?: string;

  /**
   * Controlled active tab
   */
  activeTab?: string;

  /**
   * Tab change callback
   */
  onTabChange?: (tabId: string) => void;

  /**
   * Additional CSS class names
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;
}

export function AalTabs({
  tabs,
  defaultTab,
  activeTab: controlledActiveTab,
  onTabChange,
  className = "",
  style,
}: AalTabsProps) {
  const [internalActiveTab, setInternalActiveTab] = useState(
    defaultTab || tabs[0]?.id || ""
  );

  const activeTab = controlledActiveTab ?? internalActiveTab;

  const handleTabClick = (tabId: string, disabled?: boolean) => {
    if (disabled) return;
    if (!controlledActiveTab) {
      setInternalActiveTab(tabId);
    }
    onTabChange?.(tabId);
  };

  const activeContent = tabs.find((tab) => tab.id === activeTab)?.content;

  return (
    <div className={`aal-tabs ${className}`.trim()} style={style}>
      <div className="aal-tabs-list" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-disabled={tab.disabled}
            className={`aal-tab ${activeTab === tab.id ? "aal-tab--active" : ""} ${tab.disabled ? "aal-tab--disabled" : ""}`}
            onClick={() => handleTabClick(tab.id, tab.disabled)}
            disabled={tab.disabled}
          >
            {tab.icon && <span className="aal-tab__icon">{tab.icon}</span>}
            <span className="aal-tab__label">{tab.label}</span>
          </button>
        ))}
      </div>
      <div className="aal-tabs-content" role="tabpanel">
        {activeContent}
      </div>
    </div>
  );
}
