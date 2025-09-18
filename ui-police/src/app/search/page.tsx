'use client';

import AIAgentPanel from '@/components/ai-agent';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { mockEvents } from '@/lib/mock-data';
import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredEvents, setFilteredEvents] = useState(mockEvents);

  const handleSearch = () => {
    const lowercasedTerm = searchTerm.toLowerCase();
    const results = mockEvents.filter(event => 
      event.type.toLowerCase().includes(lowercasedTerm) ||
      event.description.toLowerCase().includes(lowercasedTerm) ||
      event.cameraName.toLowerCase().includes(lowercasedTerm)
    );
    setFilteredEvents(results);
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <h1 className="text-3xl font-bold mb-4">AI-Powered Search</h1>
      <div className="max-w-xl mx-auto">
        <div className="flex w-full items-center space-x-2">
            <Input 
              type="text" 
              placeholder="e.g., 'a person in a red shirt'"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button type="submit" onClick={handleSearch}>Search</Button>
        </div>
        <div className="mt-8 space-y-4">
            {filteredEvents.map((event) => (
              <Card key={event.id} className={`${event.severity === 'high' ? 'border-red-500' : ''}`}>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg">{event.type} at {event.cameraName}</CardTitle>
                  <div className={`flex items-center gap-2 text-sm ${event.severity === 'high' ? 'text-red-500' : event.severity === 'medium' ? 'text-orange-500' : 'text-yellow-500'}`}>
                    <AlertTriangle className="h-4 w-4"/> 
                    <span>{event.severity.charAt(0).toUpperCase() + event.severity.slice(1)}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{event.description}</p>
                  <p className="text-xs text-muted-foreground mt-2">{new Date(event.timestamp).toLocaleString()}</p>
                </CardContent>
              </Card>
            ))}
        </div>
      </div>
      <AIAgentPanel />
    </div>
  );
}
