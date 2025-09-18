'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { CornerDownLeft, Mic, X, Bot } from 'lucide-react';

interface Message {
  text: string;
  sender: 'user' | 'ai';
}

export default function AIAgentPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hello Officer. How can I assist you today?", sender: 'ai' },
  ]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = () => {
    if (inputValue.trim() === '') return;

    const userMessage: Message = { text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = { text: `Searching for: "${inputValue}"...`, sender: 'ai' };
      setMessages(prev => [...prev, aiResponse]);
    }, 500);

    setInputValue('');
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <AnimatePresence>
        {isExpanded ? (
          <motion.div
            initial={{ width: 56, height: 56, opacity: 0 }}
            animate={{ width: 400, height: 600, opacity: 1 }}
            exit={{ width: 56, height: 56, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
            className="bg-background/80 backdrop-blur-md border border-blue-500/30 rounded-lg shadow-2xl shadow-blue-500/20 overflow-hidden flex flex-col"
          >
            <div className="flex items-center justify-between p-3 border-b border-blue-500/30">
                <p className="text-sm font-medium text-blue-300 px-2">AI Assistant</p>
                <Button variant="ghost" size="icon" onClick={() => setIsExpanded(false)} className="h-8 w-8 text-blue-300 hover:bg-blue-500/10 hover:text-white">
                    <X className="h-4 w-4" />
                </Button>
            </div>

            <div className="flex-grow p-4 space-y-4 overflow-y-auto">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`rounded-lg px-4 py-2 max-w-xs text-sm shadow-md ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-muted/60 text-foreground/90'
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-blue-500/30">
              <div className="relative">
                <Input
                  placeholder="Ask anything..."
                  className="bg-background/70 border-blue-500/30 rounded-full pr-24 focus:ring-2 focus:ring-blue-500/50"
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center">
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-blue-300 hover:text-white">
                      <Mic className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-blue-300 hover:text-white" onClick={handleSubmit}>
                      <CornerDownLeft className="h-4 w-4" />
                    </Button>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            <Button
              className="w-16 h-16 bg-blue-600/90 hover:bg-blue-500 rounded-full shadow-lg shadow-blue-500/30 flex items-center justify-center animate-pulse-slow"
              onClick={() => setIsExpanded(true)}
            >
              <Bot className="h-8 w-8 text-white" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
