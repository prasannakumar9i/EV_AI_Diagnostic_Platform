import { motion } from 'motion/react';
import { Scene } from '../components/3d/Scene';
import { Zap, ShieldCheck, Activity, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const stats = [
  { label: 'Diagnostic Accuracy', value: '99.8%', icon: ShieldCheck, color: 'text-neon-blue' },
  { label: 'Processing Speed', value: '12ms', icon: Zap, color: 'text-neon-green' },
  { label: 'Real-time Insights', value: '24/7', icon: Activity, color: 'text-neon-blue' },
];

export function Home() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center pt-20 px-6 overflow-hidden">
      <Scene />

      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center z-10">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="flex flex-col gap-6"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neon-blue/10 border border-neon-blue/20 text-neon-blue text-xs font-bold tracking-widest uppercase">
            <Zap className="w-4 h-4" />
            Next-Gen EV Intelligence
          </div>
          
          <h1 className="text-6xl lg:text-8xl font-black tracking-tighter leading-none">
            EV AI <br />
            <span className="neon-glow-blue">DIAGNOSTIC</span> <br />
            <span className="text-neon-green">PLATFORM</span>
          </h1>

          <p className="text-lg text-white/60 max-w-lg leading-relaxed">
            Harness the power of RAG, CAG, and advanced ML models to monitor, diagnose, and optimize your electric vehicle's performance in real-time.
          </p>

          <div className="flex flex-wrap gap-4 mt-4">
            <Link
              to="/assistant"
              className="px-8 py-4 rounded-2xl bg-neon-blue text-black font-bold flex items-center gap-2 hover:scale-105 transition-all hover:neon-border-blue"
            >
              LAUNCH AI ASSISTANT
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/dashboard"
              className="px-8 py-4 rounded-2xl glass-panel text-white font-bold hover:bg-white/10 transition-all"
            >
              VIEW DASHBOARD
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-1 gap-6"
        >
          {stats.map((stat, index) => (
            <div key={index} className="glass-panel p-6 flex items-center gap-6 hover:bg-white/10 transition-all group cursor-default">
              <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform ${stat.color}`}>
                <stat.icon className="w-8 h-8" />
              </div>
              <div>
                <div className="text-xs font-bold text-white/40 uppercase tracking-widest">{stat.label}</div>
                <div className={`text-3xl font-black ${stat.color}`}>{stat.value}</div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Decorative elements */}
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-neon-blue/10 to-transparent pointer-events-none" />
    </div>
  );
}
