import { motion } from 'motion/react';
import { Battery, Zap, Thermometer, Activity, AlertTriangle, CheckCircle2, Gauge, ShieldCheck } from 'lucide-react';
import { useStore } from '../store/useStore';

const metrics = [
  { label: 'Battery Voltage', value: '398.4V', icon: Zap, color: 'text-neon-blue' },
  { label: 'Current Draw', value: '12.5A', icon: Activity, color: 'text-neon-green' },
  { label: 'System Temp', value: '34.2°C', icon: Thermometer, color: 'text-neon-blue' },
  { label: 'Health Index', value: '98.2%', icon: ShieldCheck, color: 'text-neon-green' },
];

const alerts = [
  { id: 1, type: 'warning', message: 'Coolant flow rate below optimal threshold', time: '2m ago' },
  { id: 2, type: 'critical', message: 'Cell #48 voltage imbalance detected', time: '15m ago' },
  { id: 3, type: 'info', message: 'System optimization complete', time: '1h ago' },
];

export function Dashboard() {
  return (
    <div className="pt-24 pb-8 px-6 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel px-8 py-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight neon-glow-blue uppercase">VEHICLE DIAGNOSTICS</h1>
          <p className="text-white/40 text-sm font-medium">Real-time monitoring and fault detection system</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-neon-green/10 border border-neon-green/20 text-neon-green text-xs font-bold uppercase tracking-widest">
            <CheckCircle2 className="w-4 h-4" />
            SYSTEMS OPTIMAL
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/40 text-xs font-bold uppercase tracking-widest">
            <Activity className="w-4 h-4" />
            LIVE TELEMETRY
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-panel p-6 hover:bg-white/10 transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform ${metric.color}`}>
                <metric.icon className="w-6 h-6" />
              </div>
              <div className="text-xs font-bold text-white/20 uppercase tracking-widest">REAL-TIME</div>
            </div>
            <div className="text-sm font-bold text-white/40 uppercase tracking-widest mb-1">{metric.label}</div>
            <div className={`text-3xl font-black ${metric.color}`}>{metric.value}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="glass-panel p-8 min-h-[400px] flex flex-col items-center justify-center relative overflow-hidden">
            <div className="absolute top-6 left-8 flex items-center gap-2">
              <Battery className="text-neon-blue w-5 h-5" />
              <h3 className="font-bold text-lg uppercase tracking-tight">BATTERY HEALTH GAUGE</h3>
            </div>
            
            <div className="relative w-64 h-64 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90">
                <circle
                  cx="128"
                  cy="128"
                  r="110"
                  fill="none"
                  stroke="rgba(255,255,255,0.05)"
                  strokeWidth="20"
                />
                <circle
                  cx="128"
                  cy="128"
                  r="110"
                  fill="none"
                  stroke="#00aaff"
                  strokeWidth="20"
                  strokeDasharray="691"
                  strokeDashoffset="69"
                  className="transition-all duration-1000 ease-out"
                  style={{ filter: 'drop-shadow(0 0 10px #00aaff)' }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-6xl font-black neon-glow-blue">90%</span>
                <span className="text-xs font-bold text-white/40 uppercase tracking-widest">CAPACITY</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-12 mt-12 w-full max-w-md">
              <div className="text-center">
                <div className="text-xs font-bold text-white/40 uppercase tracking-widest mb-2">CYCLE COUNT</div>
                <div className="text-2xl font-black text-white">482</div>
              </div>
              <div className="text-center">
                <div className="text-xs font-bold text-white/40 uppercase tracking-widest mb-2">EST. RANGE</div>
                <div className="text-2xl font-black text-neon-green">342 KM</div>
              </div>
            </div>
          </div>

          <div className="glass-panel p-8">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <AlertTriangle className="text-neon-blue w-5 h-5" />
                <h3 className="font-bold text-lg uppercase tracking-tight">SYSTEM FAULTS & ALERTS</h3>
              </div>
              <button className="text-xs font-bold text-neon-blue hover:underline uppercase tracking-widest">CLEAR ALL</button>
            </div>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      alert.type === 'critical' ? 'bg-red-500/20 text-red-500' : 
                      alert.type === 'warning' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-neon-blue/20 text-neon-blue'
                    }`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white group-hover:text-neon-blue transition-colors">{alert.message}</div>
                      <div className="text-[10px] font-bold text-white/20 uppercase tracking-widest">{alert.time}</div>
                    </div>
                  </div>
                  <button className="px-3 py-1 rounded-lg bg-white/5 text-[10px] font-bold text-white/40 hover:bg-white/10 uppercase tracking-widest">DETAILS</button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div className="glass-panel p-8">
            <div className="flex items-center gap-2 mb-8">
              <Gauge className="text-neon-blue w-5 h-5" />
              <h3 className="font-bold text-lg uppercase tracking-tight">MOTOR STATUS</h3>
            </div>
            <div className="space-y-8">
              {['Front Motor', 'Rear Motor'].map((motor, i) => (
                <div key={i} className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white/60 uppercase tracking-widest">{motor}</span>
                    <span className="text-xs font-bold text-neon-green uppercase tracking-widest">OPTIMAL</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: i === 0 ? '85%' : '72%' }}
                      className="h-full bg-neon-blue shadow-[0_0_10px_#00aaff]"
                    />
                  </div>
                  <div className="flex justify-between text-[10px] font-bold text-white/20 uppercase tracking-widest">
                    <span>LOAD: {i === 0 ? '85%' : '72%'}</span>
                    <span>TEMP: {i === 0 ? '42°C' : '38°C'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel p-8 bg-neon-blue/5 border-neon-blue/20">
            <h3 className="font-bold text-lg uppercase tracking-tight mb-4">AI RECOMMENDATION</h3>
            <p className="text-sm text-white/60 leading-relaxed mb-6">
              "Based on current cell imbalance in the rear battery pack, I recommend performing a full balance charge cycle (0-100%) at a level 2 charger to recalibrate the BMS."
            </p>
            <button className="w-full py-3 rounded-xl bg-neon-blue text-black font-bold text-sm hover:neon-border-blue transition-all">
              SCHEDULE MAINTENANCE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
