import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Send, Bot, User, Database, Zap, Search, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';
import axios from 'axios';

export function Assistant() {
  const { messages, addMessage, isLoading, setLoading } = useStore();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    addMessage({ role: 'user', content: userMessage });
    setLoading(true);

    try {
      // Mocking API call to /ask
      // In production, this would be: const response = await axios.post('/ask', { question: userMessage });
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockResponse = {
        answer: `Based on current diagnostic data, the EV battery overheating is likely due to high ambient temperatures and rapid charging cycles. I recommend monitoring the coolant flow and reducing the charge rate to 50kW.`,
        sources: ['Battery Thermal Management System (BTMS) Manual', 'Vehicle Diagnostic Log #482'],
        cacheStatus: Math.random() > 0.5 ? 'hit' : 'miss' as 'hit' | 'miss',
      };

      addMessage({
        role: 'assistant',
        content: mockResponse.answer,
        sources: mockResponse.sources,
        cacheStatus: mockResponse.cacheStatus,
      });
    } catch (error) {
      addMessage({ role: 'assistant', content: 'Sorry, I encountered an error processing your request.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-24 pb-8 px-6 h-screen flex flex-col max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6 glass-panel px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-neon-blue/20 flex items-center justify-center">
            <Bot className="text-neon-blue w-6 h-6" />
          </div>
          <div>
            <h2 className="font-bold text-lg neon-glow-blue">AI DIAGNOSTIC ASSISTANT</h2>
            <div className="flex items-center gap-2 text-xs text-white/40">
              <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
              SYSTEM ONLINE | RAG ACTIVE | CAG ENABLED
            </div>
          </div>
        </div>
      </div>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-6 pr-4 scroll-smooth"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' ? 'bg-neon-green/20 text-neon-green' : 'bg-neon-blue/20 text-neon-blue'
              }`}>
                {msg.role === 'user' ? <User className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
              </div>

              <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`glass-panel p-4 text-sm leading-relaxed ${
                  msg.role === 'user' ? 'bg-neon-green/10 border-neon-green/20' : 'bg-neon-blue/10 border-neon-blue/20'
                }`}>
                  {msg.content}
                </div>

                {msg.role === 'assistant' && (msg.sources || msg.cacheStatus) && (
                  <div className="flex flex-wrap gap-2">
                    {msg.cacheStatus && (
                      <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${
                        msg.cacheStatus === 'hit' ? 'bg-neon-green/20 text-neon-green' : 'bg-white/10 text-white/40'
                      }`}>
                        <Zap className="w-3 h-3" />
                        CAG {msg.cacheStatus}
                      </div>
                    )}
                    {msg.sources?.map((source, i) => (
                      <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 text-white/40 text-[10px] font-bold uppercase tracking-wider border border-white/10">
                        <Database className="w-3 h-3" />
                        {source}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-neon-blue/20 flex items-center justify-center text-neon-blue">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
            <div className="glass-panel p-4 bg-neon-blue/10 border-neon-blue/20">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-neon-blue animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-neon-blue animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-neon-blue animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="mt-6 relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your EV's health, battery performance, or diagnostics..."
          className="w-full glass-panel bg-white/5 border-white/10 px-6 py-4 pr-16 text-white placeholder:text-white/20 focus:outline-none focus:border-neon-blue/50 transition-all"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-neon-blue text-black flex items-center justify-center hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}
