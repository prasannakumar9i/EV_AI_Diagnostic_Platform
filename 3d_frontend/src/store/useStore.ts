import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  cacheStatus?: 'hit' | 'miss';
  timestamp: number;
}

interface DiagnosticData {
  batteryHealth: number;
  faults: string[];
  recommendations: string[];
  motorStatus: 'optimal' | 'warning' | 'critical';
  metrics: {
    voltage: number;
    current: number;
    temperature: number;
  };
}

interface AppState {
  messages: Message[];
  diagnosticData: DiagnosticData | null;
  insights: any[] | null;
  isLoading: boolean;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setDiagnosticData: (data: DiagnosticData) => void;
  setInsights: (insights: any[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  messages: [
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to EV AI Diagnostic Platform. How can I assist you with your vehicle today?',
      timestamp: Date.now(),
    },
  ],
  diagnosticData: null,
  insights: null,
  isLoading: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...message, id: Math.random().toString(36).substring(7), timestamp: Date.now() },
      ],
    })),
  setDiagnosticData: (data) => set({ diagnosticData: data }),
  setInsights: (insights) => set({ insights }),
  setLoading: (loading) => set({ isLoading: loading }),
}));
