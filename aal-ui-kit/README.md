# AAL UI Kit v1.0

**Applied Alchemy Labs Design System**

A React + TypeScript component library and theme for the AAL "myth-tech" brand aesthetic.

---

## Overview

The AAL UI Kit provides a cohesive visual language for Applied Alchemy Labs applications, featuring:

- **Dark, neon-on-black aesthetic** with cyan, yellow, and magenta accents
- **CSS theme** via custom properties and utility classes
- **React + TypeScript components** for rapid UI development
- **Consistent spacing, typography, and interaction patterns**

---

## Features

### Theme System

**`styles/aal-theme.css`**

- CSS custom properties for colors, spacing, shadows, and typography
- Global dark gradient background
- Utility classes for layout, typography, and common patterns
- Responsive and accessible by default

**Core Colors:**
- **Cyan** (`#00D4FF`) - Primary accent for system/general features
- **Neon Yellow** (`#F8FF59`) - Forecasting, analytics, insights
- **Magenta** (`#FF3EF6`) - Creative, music, emotional content
- **Dark Base** (`#0A0A0A`, `#1C1C1E`, `#2A2A2F`) - Backgrounds and surfaces

### Components

**All components are fully typed with TypeScript and designed for composition.**

- **`AalShell`** - Page layout wrapper with optional title/subtitle
- **`AalCard`** - Panel/container component with subtle cyan glow
- **`AalButton`** - Primary, secondary, and ghost button variants
- **`AalTag`** - Small badge/pill for labels and categories
- **`AalDivider`** - Subtle horizontal separator
- **`AalSigilFrame`** - Circular frame for icons/glyphs with tone variants (cyan/yellow/magenta)

---

## Installation & Usage

### 1. Import the Theme CSS

Add this import to your app's entry point (e.g., `src/main.tsx`, `src/index.tsx`):

```tsx
import "../aal-ui-kit/styles/aal-theme.css";
```

Adjust the relative path based on your project structure.

### 2. Import Components

```tsx
import {
  AalShell,
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../aal-ui-kit/src";
```

### 3. Wrap Your App

Use `AalShell` as the outermost layout wrapper for pages:

```tsx
<AalShell
  title="Applied Alchemy Labs"
  subtitle="Myth-tech systems for music, meaning, and foresight"
>
  {/* Your content */}
</AalShell>
```

### 4. Build UI with Components

```tsx
<AalCard>
  <AalTag icon={<Sparkles />}>Featured</AalTag>
  <h2 className="aal-heading-md">Abraxas Oracle</h2>
  <p className="aal-body">
    Mystical trading insights powered by symbolic computation.
  </p>
  <AalButton variant="primary">Open Console</AalButton>
</AalCard>
```

---

## Component API

### `<AalShell>`

Layout wrapper for full-page content.

**Props:**
- `title?: string` - Page title (rendered as `h1` with `.aal-heading-xl`)
- `subtitle?: string` - Page subtitle (rendered with `.aal-body`)
- `children: React.ReactNode` - Page content
- `maxWidth?: number | string` - Max width of inner container (default: `1120`)

### `<AalCard>`

Container for content sections.

**Props:**
- `children: React.ReactNode`
- `variant?: "default" | "ghost"` - Default has shadow/glow, ghost is more transparent
- `padding?: number | string` - Custom padding (default: `18px`)
- `as?: keyof JSX.IntrinsicElements` - HTML element type (default: `"section"`)
- `className?: string` - Additional CSS classes

### `<AalButton>`

Interactive button with multiple variants.

**Props:**
- `variant?: "primary" | "secondary" | "ghost"` - Visual style (default: `"primary"`)
- `leftIcon?: React.ReactNode` - Icon before text
- `rightIcon?: React.ReactNode` - Icon after text
- `children: React.ReactNode` - Button label
- ...all standard `<button>` HTML attributes

### `<AalTag>`

Small badge/pill for labels.

**Props:**
- `children: React.ReactNode`
- `icon?: React.ReactNode` - Optional icon
- `className?: string`

### `<AalDivider>`

Horizontal separator.

**Props:**
- None (renders `<hr className="aal-divider" />`)

### `<AalSigilFrame>`

Circular frame for icons/glyphs with colored tone.

**Props:**
- `children?: React.ReactNode` - Icon or glyph
- `tone?: "cyan" | "yellow" | "magenta"` - Color theme (default: `"cyan"`)
- `size?: number` - Diameter in pixels (default: `40`)
- `className?: string`

---

## Utility Classes

### Typography

- `.aal-heading-xl` - Large page titles (32-40px, uppercase, wide tracking)
- `.aal-heading-md` - Section headings (~20px, uppercase, wider tracking)
- `.aal-body` - Body text (~15px, muted color)

### Layout

- `.aal-page` - Full-height page container
- `.aal-page-inner` - Centered content area with max-width
- `.aal-stack-md` - Vertical spacing between children
- `.aal-row-sm` - Horizontal spacing between children

### Component Classes

All components use BEM-style classes:
- `.aal-card`, `.aal-card--ghost`
- `.aal-button`, `.aal-button--primary`, `.aal-button--secondary`, `.aal-button--ghost`
- `.aal-tag`
- `.aal-divider`
- `.aal-sigil-frame`, `.aal-sigil-frame--yellow`, `.aal-sigil-frame--magenta`

---

## Design Principles

1. **Myth-tech aesthetic** - Blend of mystical/occult symbolism with modern tech UI
2. **High contrast** - Neon accents on deep black for readability and visual impact
3. **Minimal but expressive** - Clean layouts with strategic use of glow effects
4. **Composable** - Small, focused components that work together
5. **Accessible** - Proper semantic HTML, keyboard navigation, ARIA where needed

---

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ JavaScript
- CSS Grid and Flexbox

---

## License

Proprietary - Applied Alchemy Labs © 2025

---

## Changelog

### v1.0 (2025-01-15)
- Initial release
- Core theme with CSS custom properties
- 6 foundational components
- Typography and layout utilities
