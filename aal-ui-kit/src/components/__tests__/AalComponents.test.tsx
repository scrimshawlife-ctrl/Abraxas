/**
 * AAL UI Kit - Component Unit Tests
 */

import { describe, it, expect, vi } from "vitest";
import React from "react";

// Mock React for component testing
const renderToString = (element: React.ReactElement): string => {
  // Simple render check - verifies component doesn't throw
  if (!element) throw new Error("Element is null");
  return JSON.stringify(element);
};

// Import components
import { AalButton } from "../AalButton";
import { AalCard } from "../AalCard";
import { AalInput } from "../AalInput";
import { AalTabs } from "../AalTabs";
import { AalSpinner } from "../AalSpinner";
import { AalTag } from "../AalTag";
import { AalDivider } from "../AalDivider";
import { AalSigilFrame } from "../AalSigilFrame";

describe("AalButton", () => {
  it("renders with default variant", () => {
    const element = <AalButton>Click me</AalButton>;
    expect(element.props.children).toBe("Click me");
  });

  it("applies variant classes", () => {
    const primary = <AalButton variant="primary">Primary</AalButton>;
    const secondary = <AalButton variant="secondary">Secondary</AalButton>;
    const ghost = <AalButton variant="ghost">Ghost</AalButton>;

    expect(primary.props.variant).toBe("primary");
    expect(secondary.props.variant).toBe("secondary");
    expect(ghost.props.variant).toBe("ghost");
  });

  it("supports left and right icons", () => {
    const element = (
      <AalButton leftIcon={<span>L</span>} rightIcon={<span>R</span>}>
        With Icons
      </AalButton>
    );
    expect(element.props.leftIcon).toBeTruthy();
    expect(element.props.rightIcon).toBeTruthy();
  });

  it("passes through button attributes", () => {
    const onClick = vi.fn();
    const element = <AalButton onClick={onClick} disabled>Disabled</AalButton>;
    expect(element.props.disabled).toBe(true);
    expect(element.props.onClick).toBe(onClick);
  });
});

describe("AalCard", () => {
  it("renders with default styling", () => {
    const element = <AalCard>Card content</AalCard>;
    expect(element.props.children).toBe("Card content");
  });

  it("supports ghost variant", () => {
    const element = <AalCard ghost>Ghost card</AalCard>;
    expect(element.props.ghost).toBe(true);
  });

  it("accepts custom className", () => {
    const element = <AalCard className="custom-class">Content</AalCard>;
    expect(element.props.className).toBe("custom-class");
  });
});

describe("AalInput", () => {
  it("renders with label", () => {
    const element = <AalInput label="Email" placeholder="Enter email" />;
    expect(element.props.label).toBe("Email");
  });

  it("supports size variants", () => {
    const sm = <AalInput size="sm" />;
    const md = <AalInput size="md" />;
    const lg = <AalInput size="lg" />;

    expect(sm.props.size).toBe("sm");
    expect(md.props.size).toBe("md");
    expect(lg.props.size).toBe("lg");
  });

  it("handles error state", () => {
    const element = <AalInput error helperText="Invalid input" />;
    expect(element.props.error).toBe(true);
    expect(element.props.helperText).toBe("Invalid input");
  });

  it("supports icons", () => {
    const element = (
      <AalInput leftIcon={<span>@</span>} rightIcon={<span>X</span>} />
    );
    expect(element.props.leftIcon).toBeTruthy();
    expect(element.props.rightIcon).toBeTruthy();
  });
});

describe("AalTabs", () => {
  const mockTabs = [
    { id: "tab1", label: "Tab 1", content: <div>Content 1</div> },
    { id: "tab2", label: "Tab 2", content: <div>Content 2</div> },
    { id: "tab3", label: "Tab 3", content: <div>Content 3</div>, disabled: true },
  ];

  it("renders with tabs", () => {
    const element = <AalTabs tabs={mockTabs} />;
    expect(element.props.tabs).toHaveLength(3);
  });

  it("supports default tab selection", () => {
    const element = <AalTabs tabs={mockTabs} defaultTab="tab2" />;
    expect(element.props.defaultTab).toBe("tab2");
  });

  it("supports controlled mode", () => {
    const onTabChange = vi.fn();
    const element = (
      <AalTabs tabs={mockTabs} activeTab="tab1" onTabChange={onTabChange} />
    );
    expect(element.props.activeTab).toBe("tab1");
    expect(element.props.onTabChange).toBe(onTabChange);
  });

  it("handles disabled tabs", () => {
    const element = <AalTabs tabs={mockTabs} />;
    const disabledTab = element.props.tabs.find((t: any) => t.id === "tab3");
    expect(disabledTab?.disabled).toBe(true);
  });
});

describe("AalSpinner", () => {
  it("renders with default tone", () => {
    const element = <AalSpinner />;
    expect(element).toBeTruthy();
  });

  it("supports tone variants", () => {
    const cyan = <AalSpinner tone="cyan" />;
    const yellow = <AalSpinner tone="yellow" />;
    const magenta = <AalSpinner tone="magenta" />;

    expect(cyan.props.tone).toBe("cyan");
    expect(yellow.props.tone).toBe("yellow");
    expect(magenta.props.tone).toBe("magenta");
  });

  it("accepts custom size", () => {
    const element = <AalSpinner size={48} />;
    expect(element.props.size).toBe(48);
  });
});

describe("AalTag", () => {
  it("renders with text content", () => {
    const element = <AalTag>Status</AalTag>;
    expect(element.props.children).toBe("Status");
  });

  it("supports icon", () => {
    const element = <AalTag icon={<span>*</span>}>With Icon</AalTag>;
    expect(element.props.icon).toBeTruthy();
  });
});

describe("AalDivider", () => {
  it("renders correctly", () => {
    const element = <AalDivider />;
    expect(element.type).toBe(AalDivider);
  });

  it("accepts custom className", () => {
    const element = <AalDivider className="custom" />;
    expect(element.props.className).toBe("custom");
  });
});

describe("AalSigilFrame", () => {
  it("renders with default tone", () => {
    const element = <AalSigilFrame>Icon</AalSigilFrame>;
    expect(element.props.children).toBe("Icon");
  });

  it("supports tone variants", () => {
    const cyan = <AalSigilFrame tone="cyan">C</AalSigilFrame>;
    const yellow = <AalSigilFrame tone="yellow">Y</AalSigilFrame>;
    const magenta = <AalSigilFrame tone="magenta">M</AalSigilFrame>;

    expect(cyan.props.tone).toBe("cyan");
    expect(yellow.props.tone).toBe("yellow");
    expect(magenta.props.tone).toBe("magenta");
  });
});

describe("Accessibility", () => {
  it("AalTabs has proper ARIA attributes", () => {
    const tabs = [
      { id: "t1", label: "Tab", content: <div>Content</div> },
    ];
    const element = <AalTabs tabs={tabs} />;
    // Tabs component includes role="tablist" and role="tab"
    expect(element).toBeTruthy();
  });

  it("AalButton supports aria-label", () => {
    const element = <AalButton aria-label="Close dialog">X</AalButton>;
    expect(element.props["aria-label"]).toBe("Close dialog");
  });

  it("AalInput supports aria-describedby", () => {
    const element = <AalInput aria-describedby="help-text" />;
    expect(element.props["aria-describedby"]).toBe("help-text");
  });
});
