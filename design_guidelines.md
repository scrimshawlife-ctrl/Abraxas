# Design Guidelines for Abraxas Mystical Trading Application

## Design Approach
**Reference-Based Approach**: Drawing inspiration from premium fintech platforms like Robinhood and Coinbase, combined with dark mystical aesthetics similar to esoteric gaming interfaces and occult-themed applications.

## Core Design Elements

### A. Color Palette
**Dark Mode Primary** (application default):
- Background: 220 15% 8% (deep charcoal)
- Surface: 220 15% 12% (elevated dark)
- Primary: 280 65% 60% (mystical purple)
- Accent: 45 85% 65% (golden amber) - used sparingly for key actions
- Text Primary: 0 0% 95% (near white)
- Text Secondary: 0 0% 70% (muted gray)
- Success: 120 50% 50% (muted green)
- Warning: 30 80% 60% (amber)
- Error: 0 70% 60% (muted red)

**Light Mode** (optional toggle):
- Background: 220 20% 97%
- Surface: 0 0% 100%
- Primary: 280 70% 50%
- Same accent and semantic colors adjusted for contrast

### B. Typography
- **Primary Font**: Inter (via Google Fonts CDN)
- **Accent Font**: JetBrains Mono (for data/numbers)
- **Hierarchy**: 
  - Headers: 600-700 weight
  - Body: 400-500 weight
  - Data/Numbers: JetBrains Mono, 500 weight

### C. Layout System
**Tailwind Spacing**: Consistent use of 2, 4, 6, 8, 12, 16 units
- Micro spacing: p-2, m-2
- Standard spacing: p-4, m-4, gap-4
- Section spacing: p-8, m-8
- Large spacing: p-16, m-16

### D. Component Library

**Navigation**:
- Dark sidebar with mystical iconography
- Top navigation bar with user avatar and quick actions
- Breadcrumb navigation for deep sections

**Core UI Elements**:
- Cards with subtle borders and soft shadows
- Form inputs with dark styling and purple focus states
- Buttons with gradient backgrounds for primary actions
- Data tables with alternating row colors
- Modal overlays with backdrop blur

**Mystical Elements**:
- Rune symbols as decorative elements
- Geometric patterns in section dividers
- Subtle glow effects on interactive elements
- Sigil-inspired loading states

**Data Displays**:
- Financial charts with dark themes and purple/amber accents
- Trend indicators with arrow icons
- Progress bars with mystical styling
- Metric cards with large numbers and context

### E. Key Sections Design

**Dashboard**: 
- Grid layout with metric cards
- Central ritual initiation area
- Recent activity feed
- Real-time trend updates

**Ritual Interface**:
- Ceremonial form layout with rune selections
- Watchlist input with autocomplete
- Results display with mystical presentation
- Historical ritual archive

**VC Oracle**:
- Analysis input form with industry/region selectors
- Prediction displays with confidence indicators
- Trend visualization with charts

**Social Trends**:
- Feed-style layout for trend updates
- Tag cloud visualization
- Real-time update indicators

### F. Images
**No Large Hero Image**: This is a utility-focused application
**Supporting Imagery**:
- Subtle mystical background patterns
- Rune/sigil icons throughout interface
- Geometric accent elements
- Dark texture overlays for depth

### G. Interactions
- Smooth transitions (200-300ms)
- Hover states with subtle glow effects
- Loading states with mystical animations
- Real-time update notifications
- Minimal, purposeful micro-interactions

This design balances professional financial interface requirements with the mystical theming, ensuring usability while maintaining the esoteric atmosphere.