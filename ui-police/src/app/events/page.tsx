'use client';

import AIAgentPanel from '@/components/ai-agent';

export default function EventsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <h1 className="text-3xl font-bold mb-4">Events & Alerts</h1>
      <div className="space-y-4">{/* Placeholder for events list */}</div>
      <AIAgentPanel />
    </div>
  );
}
