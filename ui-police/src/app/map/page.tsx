'use client';

import AIAgentPanel from '@/components/ai-agent';

export default function MapPage() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <h1 className="text-3xl font-bold mb-4">Map View</h1>
      <div className="flex-1 bg-muted rounded-lg">{/* Placeholder for the map */}</div>
      <AIAgentPanel />
    </div>
  );
}
