import { motion } from 'motion/react';
import { Database, Zap, Cpu, Github, ExternalLink, Network, ShieldCheck, Server, Activity } from 'lucide-react';

const technologies = [
  {
    title: 'RAG (Retrieval Augmented Generation)',
    description: 'Our AI assistant leverages RAG to retrieve real-time data from vehicle manuals, diagnostic logs, and technical documentation to provide accurate, context-aware answers.',
    icon: Database,
    color: 'text-neon-blue',
  },
  {
    title: 'CAG (Cache Augmented Generation)',
    description: 'To ensure ultra-low latency, CAG caches frequently asked diagnostic queries and common vehicle states, reducing processing time by up to 85%.',
    icon: Zap,
    color: 'text-neon-green',
  },
  {
    title: 'ML Diagnostic Models',
    description: 'Custom-trained machine learning models analyze battery cell health, motor efficiency, and thermal patterns to predict faults before they occur.',
    icon: Cpu,
    color: 'text-neon-blue',
  },
];

export function About() {
  return (
    <div className="pt-24 pb-16 px-6 max-w-7xl mx-auto space-y-16">
      <div className="text-center max-w-3xl mx-auto space-y-6">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl font-black tracking-tighter neon-glow-blue uppercase"
        >
          PLATFORM ARCHITECTURE
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-white/60 text-lg leading-relaxed"
        >
          The EV AI Diagnostic Platform is built on a distributed intelligence network designed for high-performance electric vehicle monitoring and predictive maintenance.
        </motion.p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {technologies.map((tech, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 + 0.2 }}
            className="glass-panel p-8 hover:bg-white/10 transition-all group"
          >
            <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform ${tech.color}`}>
              <tech.icon className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold mb-4 tracking-tight uppercase">{tech.title}</h3>
            <p className="text-white/40 text-sm leading-relaxed">{tech.description}</p>
          </motion.div>
        ))}
      </div>

      <div className="glass-panel p-12 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-neon-blue/10 blur-[100px] -z-10" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-neon-green/10 blur-[100px] -z-10" />
        
        <div className="flex items-center gap-3 mb-12">
          <Network className="text-neon-blue w-6 h-6" />
          <h2 className="text-2xl font-black tracking-tight uppercase">SYSTEM DATA FLOW</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center">
          <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-white/5 border border-white/10 text-center">
            <Activity className="w-10 h-10 text-neon-blue" />
            <div className="text-xs font-bold uppercase tracking-widest">VEHICLE SENSORS</div>
          </div>
          <div className="hidden lg:flex justify-center"><Zap className="text-white/20 w-6 h-6" /></div>
          <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-neon-blue/10 border border-neon-blue/30 text-center">
            <Server className="w-12 h-12 text-neon-blue" />
            <div className="text-sm font-bold uppercase tracking-widest">AI CORE ENGINE</div>
            <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest">RAG + CAG + ML</div>
          </div>
          <div className="hidden lg:flex justify-center"><Zap className="text-white/20 w-6 h-6" /></div>
          <div className="flex flex-col items-center gap-4 p-6 rounded-2xl bg-white/5 border border-white/10 text-center">
            <ShieldCheck className="w-10 h-10 text-neon-green" />
            <div className="text-xs font-bold uppercase tracking-widest">USER INTERFACE</div>
          </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-center gap-8">
        <a 
          href="https://github.com" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-3 px-8 py-4 rounded-2xl glass-panel hover:bg-white/10 transition-all group"
        >
          <Github className="w-6 h-6 text-white group-hover:text-neon-blue transition-colors" />
          <div className="text-left">
            <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest">OPEN SOURCE</div>
            <div className="font-bold">VIEW REPOSITORY</div>
          </div>
          <ExternalLink className="w-4 h-4 text-white/20" />
        </a>
        
        <div className="flex items-center gap-3 px-8 py-4 rounded-2xl glass-panel">
          <div className="w-3 h-3 rounded-full bg-neon-green animate-pulse" />
          <div className="text-left">
            <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest">API STATUS</div>
            <div className="font-bold text-neon-green">ALL SYSTEMS OPERATIONAL</div>
          </div>
        </div>
      </div>
    </div>
  );
}
