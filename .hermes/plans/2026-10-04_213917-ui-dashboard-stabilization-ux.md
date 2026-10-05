# Plan: Stabilize UI Dashboard & Build UX

**Date**: 2026-10-04
**Goal**: Stabilize the UI Dashboard (v2.0.0) by adding error boundaries, loading states, real-time updates via WebSocket, accessibility improvements, responsive design polish, and UX research-driven enhancements.

---

## Current Context / Assumptions

- **Dashboard Status**: Functional but minimal — React 18 + TypeScript + Vite + Tailwind + Recharts
- **API**: FastAPI service at `:8082` with 10 endpoints (artifacts, phase alignments, synchronicity, oracle bundles, narratives, ritual state, timechain, metrics)
- **Build**: TypeScript compiles, Vite builds (543 kB bundle)
- **Deployment**: Helm values + Dockerfile ready
- **UX Gaps Identified**:
  - No error boundaries or graceful degradation
  - No loading skeletons (spinners only)
  - No real-time updates (polling only, no WebSocket)
  - No accessibility audit (ARIA, keyboard nav, contrast)
  - No responsive breakpoint testing
  - No user-facing documentation or onboarding
  - No error reporting/telemetry
  - No theme customization
  - No offline support / PWA

---

## Architecture / Proposed Approach

**Two-phase approach**:
1. **Phase 1 — Stabilization (Week 1)**: Error boundaries, loading skeletons, WebSocket integration, accessibility audit, responsive polish, error reporting
2. **Phase 2 — UX Enhancement (Week 2)**: Onboarding flow, theme customization, offline/PWA support, telemetry, user testing prep

**Research tasks** integrated into each phase to validate UX decisions.

---

## Step-by-Step Tasks

### Phase 1: Stabilization

#### Task 1.1: Add React Error Boundary
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/components/ErrorBoundary.tsx`
```tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // TODO: Send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-red-800 mb-2">Something went wrong</h2>
          <p className="text-red-600 mb-4">{this.state.error?.message}</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Verification**: `npm run build` passes; wrap `<App />` in `main.tsx` with `<ErrorBoundary>`.

---

#### Task 1.2: Add Loading Skeletons (Replace Spinners)
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/components/LoadingSkeletons.tsx`
```tsx
export function MetricCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-8 bg-gray-200 rounded w-1/2"></div>
      <div className="text-4xl opacity-0">📦</div>
    </div>
  );
}

export function TableSkeleton(rows = 5) {
  return (
    <div className="overflow-x-auto animate-pulse">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-24"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-16"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-16"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-20"></div></th>
            <th className="pb-2"><div className="h-4 bg-gray-200 rounded w-20"></div></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i} className="border-b border-gray-100">
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
              <td className="py-2"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse space-y-3">
      <div className="h-6 bg-gray-200 rounded w-1/4"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}
```

**Integration**: Update hooks to return `isLoading` → render skeletons instead of "Loading..." text.

---

#### Task 1.3: WebSocket Integration for Real-time Updates
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/hooks/useWebSocket.ts`
```tsx
import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnect = true,
  reconnectInterval = 3000,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessage?.(data);
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        onClose?.();
        if (reconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        onError?.(error);
      };
    } catch (e) {
      console.error('WebSocket connection failed:', e);
      if (reconnect) {
        reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
      }
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnect, reconnectInterval]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, lastMessage, send, connect };
}
```

**Backend**: Add WebSocket endpoint to `abraxas/dashboard/api.py`:
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Call manager.broadcast() when artifacts/alignments/narratives change
```

**Frontend Integration**: Update hooks to use WebSocket for real-time updates, fallback to polling.

---

#### Task 1.4: Accessibility Audit & Fixes
**Research**: Run `axe-core` audit on built dashboard.

**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/accessibility-audit.ts`
```bash
# Install
npm install -D @axe-core/react axe-core

# Add to main.tsx (dev only)
if (import.meta.env.DEV) {
  import('@axe-core/react').then(axe => axe.default(React, ReactDOM, 1000));
}
```

**Checklist to fix**:
- [ ] All interactive elements have `aria-label` or visible text
- [ ] Color contrast ratios ≥ 4.5:1 (text) / 3:1 (UI elements)
- [ ] Keyboard navigation: Tab order, focus visible, skip links
- [ ] Semantic HTML: `<main>`, `<nav>`, `<section>`, `<article>`, `<aside>`
- [ ] ARIA live regions for dynamic content (alignments, warnings)
- [ ] Focus management in modals/drawers
- [ ] Reduced motion support (`prefers-reduced-motion`)

---

#### Task 1.5: Responsive Design Polish
**Breakpoints to test**: 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide)

**Tasks**:
- [ ] Dashboard grid: 1 col (<640px), 2 col (640-1024px), 5 col (>1024px) for metrics
- [ ] Tables: Horizontal scroll on mobile, sticky headers
- [ ] Charts: ResponsiveContainer works at all widths
- [ ] Navigation: Collapsible sidebar on mobile
- [ ] Touch targets: ≥44px for buttons/links
- [ ] Text scaling: `rem` units, no horizontal overflow

---

#### Task 1.6: Error Reporting & Telemetry
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/services/telemetry.ts`
```tsx
interface TelemetryEvent {
  event: string;
  properties?: Record<string, any>;
  timestamp: string;
  userId?: string;
  sessionId: string;
}

class Telemetry {
  private queue: TelemetryEvent[] = [];
  private sessionId: string;
  private flushInterval: number;

  constructor() {
    this.sessionId = crypto.randomUUID();
    this.flushInterval = window.setInterval(() => this.flush(), 30000);
  }

  track(event: string, properties?: Record<string, any>) {
    this.queue.push({
      event,
      properties,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
    });
  }

  private async flush() {
    if (this.queue.length === 0) return;
    const events = this.queue.splice(0, this.queue.length);
    try {
      await fetch('/api/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events }),
        keepalive: true,
      });
    } catch (e) {
      console.error('Telemetry flush failed:', e);
      this.queue.unshift(...events); // Re-queue on failure
    }
  }
}

export const telemetry = new Telemetry();

// Auto-track errors
window.addEventListener('error', (e) => {
  telemetry.track('error', { message: e.message, stack: e.error?.stack });
});

window.addEventListener('unhandledrejection', (e) => {
  telemetry.track('unhandled_rejection', { reason: e.reason });
});
```

**Backend endpoint**: Add `/api/telemetry` to `abraxas/dashboard/api.py`.

---

### Phase 2: UX Enhancement

#### Task 2.1: Onboarding Flow
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/components/OnboardingFlow.tsx`
```tsx
import { useState } from 'react';
import { createPortal } from 'react-dom';

interface Step {
  id: string;
  title: string;
  content: React.ReactNode;
  action?: { label: string; onClick: () => void };
}

const STEPS: Step[] = [
  { id: 'welcome', title: 'Welcome to Abraxas', content: <p>Real-time symbolic intelligence dashboard for multi-domain cascade prediction.</p> },
  { id: 'metrics', title: 'System Overview', content: <p>Top cards show live artifact counts, oracle runs, phase alignments, and ritual executions.</p> },
  { id: 'alignments', title: 'Phase Alignments', content: <p>Timeline shows cross-domain phase alignments with strength and domains.</p> },
  { id: 'weather', title: 'Memetic Weather', content: <p>Synchronicity map shows domain→domain coupling with lag and confidence.</p> },
  { id: 'narratives', title: 'Resonance Narratives', content: <p>Human-readable summaries with motifs, constraints, and evidence gating.</p> },
];

export function OnboardingFlow({ onComplete, isOpen, onClose }: { onComplete: () => void; isOpen: boolean; onClose: () => void }) {
  const [step, setStep] = useState(0);
  if (!isOpen) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Step {step + 1} of {STEPS.length}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        <h3 className="text-lg font-semibold mb-2">{current.title}</h3>
        <div className="prose mb-6">{current.content}</div>
        <div className="flex justify-between">
          {step > 0 && <button onClick={() => setStep(s => s - 1)} className="px-4 py-2 border rounded hover:bg-gray-50">Back</button>}
          <button 
            onClick={isLast ? onComplete : () => setStep(s => s + 1)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {isLast ? 'Get Started' : 'Next'}
          </button>
        </div>
        <div className="flex justify-center mt-4 gap-1">
          {STEPS.map((_, i) => (
            <div key={i} className={`w-2 h-2 rounded-full ${i === step ? 'bg-blue-600' : 'bg-gray-300'}`} />
          ))}
        </div>
      </div>
    </div>,
    document.body
  );
}
```

**Trigger**: Show on first visit (localStorage flag).

---

#### Task 2.2: Theme Customization (Light/Dark/System)
**File**: `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/src/hooks/useTheme.ts`
```tsx
import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as Theme) || 'system';
    }
    return 'system';
  });

  useEffect(() => {
    const root = document.documentElement;
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    root.classList.toggle('dark', isDark);
    localStorage.setItem('theme', theme);
  }, [theme]);

  return { theme, setTheme };
}
```

**Tailwind**: Add `dark:` variants to all components, update `tailwind.config.js`:
```js
module.exports = {
  darkMode: 'class',
  // ...
}
```

---

#### Task 2.3: PWA / Offline Support
**Files**:
- `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/public/manifest.json`
- `/Users/appliedalchemylabs/Abraxas/dashboard/frontend/public/sw.js` (Workbox)

```json
// manifest.json
{
  "name": "Abraxas Dashboard",
  "short_name": "Abraxas",
  "description": "Real-time symbolic intelligence dashboard",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f9fafb",
  "theme_color": "#3b82f6",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

```js
// vite.config.ts - add PWA plugin
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false, // use public/manifest.json
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.*\/api\/.*/,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache', expiration: { maxEntries: 100, maxAgeSeconds: 3600 } },
          },
        ],
      },
    }),
  ],
});
```

---

#### Task 2.4: UX Research & User Testing Prep
**Research Tasks** (do before implementing Phase 2):
1. **Competitive Analysis**: Review 3-5 similar dashboards (Grafana, Kibana, custom ML dashboards) for patterns
2. **Heuristic Evaluation**: Run Nielsen's 10 heuristics on current dashboard
3. **User Interviews**: 5-7 target users (analysts, operators) — 30 min each
4. **Task-based Usability Test**: "Find the latest phase alignment", "Check ritual execution history", "View forecast accuracy for 24h horizon"
5. **Synthesize Findings**: Prioritize fixes by severity × frequency

**Deliverable**: `/Users/appliedalchemylabs/Abraxas/dashboard/UX_RESEARCH.md` with findings and prioritized recommendations.

---

## Tests / Validation

| Task | Validation Command | Expected |
|------|-------------------|----------|
| Error Boundary | `npm run build` + manual error throw | Catches error, shows fallback |
| Skeletons | `npm run build` + slow network throttle | Skeletons show during load |
| WebSocket | `npm run dev` + backend WS | Real-time updates without refresh |
| Accessibility | `npx axe-cli dist/` | 0 critical/serious violations |
| Responsive | Chrome DevTools device toolbar | No horizontal scroll at 375px+ |
| PWA | Lighthouse PWA audit | Score ≥ 90 |
| Build | `npm run build` | Exit 0, dist/ created |

---

## Risks, Tradeoffs, Open Questions

### Risks
1. **WebSocket complexity**: Adds backend state, connection management, reconnection logic
2. **Bundle size**: Recharts + PWA + telemetry may push bundle > 600 kB
3. **Accessibility debt**: Retrofitting is harder than building accessible from start
4. **Browser compatibility**: WebSocket/PWA features need polyfills for older browsers

### Tradeoffs
- **WebSocket vs Polling**: WebSocket = real-time but more complex; Polling = simple but stale data
- **PWA vs Native**: PWA = cross-platform, no app store; Native = better OS integration
- **Dark mode**: Adds CSS complexity but high user expectation

### Open Questions
1. **WebSocket auth**: How to authenticate WS connections? (JWT in query param? Cookie?)
2. **Telemetry privacy**: What data is acceptable to collect? (No PII, only usage patterns)
3. **Theme persistence**: Per-user (requires auth) or per-browser (localStorage)?
4. **Offline behavior**: What features work offline? (Read cached artifacts only?)
4. **Onboarding skip**: Can users dismiss permanently? (Yes, localStorage flag)
5. **Error reporting backend**: Self-hosted (Sentry self-hosted?) or SaaS?

---

## Commit Strategy
- Phase 1: `feat: error boundary`, `feat: loading skeletons`, `feat: websocket real-time`, `feat: accessibility fixes`, `feat: responsive polish`, `feat: error telemetry`
- Phase 2: `feat: onboarding flow`, `feat: theme customization`, `feat: PWA offline support`, `docs: UX research findings`

All commits to `main`, push after each task.