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
  private apiBase: string;

  constructor(apiBase: string = '/api') {
    this.sessionId = crypto.randomUUID();
    this.apiBase = apiBase;
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
      await fetch(`${this.apiBase}/telemetry`, {
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

  destroy() {
    clearInterval(this.flushInterval);
    this.flush(); // Final flush
  }
}

export const telemetry = new Telemetry('/api');

// Auto-track errors
if (typeof window !== 'undefined') {
  window.addEventListener('error', (e) => {
    telemetry.track('error', { message: e.message, stack: e.error?.stack });
  });

  window.addEventListener('unhandledrejection', (e) => {
    telemetry.track('unhandled_rejection', { reason: String(e.reason) });
  });
}