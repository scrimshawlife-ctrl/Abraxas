# Abraxas Mystical Trading Application

## Overview

Abraxas is a mystical trading application that combines financial market analysis with esoteric elements like runes, sigils, and oracles. The application provides an alternative interface for market predictions through ritual-based trading algorithms, VC analysis, social trend monitoring, and mystical symbolism generation. It features a dark, premium aesthetic inspired by fintech platforms like Robinhood and Coinbase, enhanced with occult theming.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### September 28, 2025
- **Authentication Migration Complete**: Successfully replaced mock user authentication with proper Replit Auth integration using Google OAuth 2.0
- **Security Enhancement**: All watchlist API endpoints now properly authenticated and scoped to logged-in users
- **Database Updates**: Updated users table with OAuth profile fields (email, firstName, lastName, profileImageUrl) while preserving watchlist relationships
- **Frontend Authentication**: Implemented useAuth hook, Landing page for logged-out users, and conditional rendering based on authentication state
- **User Experience**: App now properly handles login/logout flow with redirect to /api/login and /api/logout endpoints
- **Session Security**: Added secure cookie configuration with SameSite protection and proper session management
- **Data Model Updates**: Enhanced watchlist system with user-specific access control and proper ownership validation
- **Code Quality**: Fixed QueryClientProvider double-wrapping and improved overall authentication architecture

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript in strict mode
- **Build Tool**: Vite with hot module replacement and runtime error overlay
- **UI Framework**: shadcn/ui components built on Radix UI primitives
- **Styling**: Tailwind CSS with custom design system featuring dark mode by default
- **State Management**: TanStack React Query for server state management
- **Component Architecture**: Modular component structure with examples directory for development

### Backend Architecture
- **Runtime**: Node.js with ES modules
- **Framework**: Express.js server with TypeScript support
- **Database**: PostgreSQL with Drizzle ORM as the primary data layer, with SQLite fallback support
- **Authentication**: Passport.js with Google OAuth 2.0 strategy
- **Session Management**: Express sessions with secure cookie configuration
- **WebSocket**: Real-time communication using WebSocket server for live data updates

### Design System
- **Theme**: Dual-mode design system (dark primary, light optional) with mystical purple and golden amber accents
- **Typography**: Inter font family for UI, JetBrains Mono for data/numbers
- **Color Palette**: Deep charcoal backgrounds with elevated surfaces, mystical purple primary, golden amber accents
- **Components**: Consistent spacing system using Tailwind utilities with custom hover and elevation effects

### Core Features
- **Ritual System**: Mystical trading algorithm that generates market predictions based on rune combinations and esoteric features
- **VC Oracle**: Venture capital analysis system with market forecasting and sector predictions
- **Social Trends**: Real-time social media sentiment analysis and trend monitoring
- **Sigil Generator**: Traditional sigil creation system for intention manifestation
- **Metrics Dashboard**: System performance tracking with accuracy measurements and data source monitoring

### Data Models
- **Users**: OAuth-authenticated users with profile information
- **Ritual Runs**: Trading ritual executions with rune combinations and prediction results
- **Sigils**: Generated mystical symbols with core phrases and generation methods
- **Social Trends**: Aggregated social media data with sentiment and momentum scores
- **System Metrics**: Performance snapshots and accuracy tracking

## External Dependencies

### Database Services
- **PostgreSQL**: Primary database with Neon serverless support
- **Drizzle ORM**: Type-safe database operations with schema migrations
- **SQLite**: Development fallback database using better-sqlite3

### Authentication Services
- **Google OAuth 2.0**: Primary authentication provider
- **Passport.js**: Authentication middleware with session management

### UI and Styling
- **Radix UI**: Unstyled, accessible component primitives
- **Tailwind CSS**: Utility-first CSS framework with custom design tokens
- **shadcn/ui**: Pre-built component library with consistent styling
- **Lucide Icons**: Modern icon library for interface elements

### Development Tools
- **Vite**: Fast build tool with TypeScript support and HMR
- **TanStack React Query**: Powerful data fetching and caching library
- **React Hook Form**: Form validation with Zod schema validation
- **ESBuild**: Fast bundling for production builds

### Optional Integrations
- **OpenAI API**: AI-powered content generation (configurable)
- **Anthropic API**: Alternative AI provider (configurable) 
- **Twitter/X API**: Social media data collection (configurable)
- **WebSocket**: Real-time data streaming for live updates

### Deployment
- **Replit**: Primary deployment platform with auto-build configuration
- **Node.js 20**: Runtime environment with ES module support