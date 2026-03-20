import { motion } from 'motion/react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';
import { BarChart3, TrendingUp, Zap, Activity, Calendar } from 'lucide-react';

const batteryPerformanceData = [
  { time: '00:00', efficiency: 85, temp: 32 },
  { time: '04:00', efficiency: 88, temp: 30 },
  { time: '08:00', efficiency: 82, temp: 35 },
  { time: '12:00', efficiency: 75, temp: 42 },
  { time: '16:00', efficiency: 78, temp: 40 },
  { time: '20:00', efficiency: 84, temp: 36 },
  { time: '23:59', efficiency: 86, temp: 33 },
];

const predictionData = [
  { day: 'Mon', actual: 98, predicted: 98 },
  { day: 'Tue', actual: 97.5, predicted: 97.8 },
  { day: 'Wed', actual: 97.2, predicted: 97.5 },
  { day: 'Thu', actual: 96.8, predicted: 97.2 },
  { day: 'Fri', actual: 96.5, predicted: 96.8 },
  { day: 'Sat', actual: null, predicted: 96.5 },
  { day: 'Sun', actual: null, predicted: 96.2 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-panel p-4 border-neon-blue/20 bg-black/80">
        <p className="text-xs font-bold text-white/40 uppercase tracking-widest mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-sm font-bold text-white uppercase tracking-tight">{entry.name}: {entry.value}%</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function Insights() {
  return (
    <div className="pt-24 pb-8 px-6 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel px-8 py-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight neon-glow-blue uppercase">ANALYTICS & INSIGHTS</h1>
          <p className="text-white/40 text-sm font-medium">AI-driven performance trends and predictive modeling</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white/40 text-xs font-bold uppercase tracking-widest">
            <Calendar className="w-4 h-4" />
            LAST 30 DAYS
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-panel p-8 min-h-[400px]"
        >
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <TrendingUp className="text-neon-blue w-5 h-5" />
              <h3 className="font-bold text-lg uppercase tracking-tight">BATTERY EFFICIENCY TRENDS</h3>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
              <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-neon-blue" /> EFFICIENCY</div>
              <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-neon-green" /> TEMPERATURE</div>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={batteryPerformanceData}>
                <defs>
                  <linearGradient id="colorEff" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00aaff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00aaff" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="rgba(255,255,255,0.2)" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontWeight: 'bold' }}
                />
                <YAxis 
                  stroke="rgba(255,255,255,0.2)" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontWeight: 'bold' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="efficiency" 
                  name="Efficiency"
                  stroke="#00aaff" 
                  fillOpacity={1} 
                  fill="url(#colorEff)" 
                  strokeWidth={3}
                />
                <Area 
                  type="monotone" 
                  dataKey="temp" 
                  name="Temperature"
                  stroke="#00ff88" 
                  fillOpacity={1} 
                  fill="url(#colorTemp)" 
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-panel p-8 min-h-[400px]"
        >
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <Zap className="text-neon-blue w-5 h-5" />
              <h3 className="font-bold text-lg uppercase tracking-tight">AI PREDICTIVE HEALTH</h3>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
              <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-white/40" /> ACTUAL</div>
              <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-neon-blue" /> PREDICTED</div>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={predictionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="day" 
                  stroke="rgba(255,255,255,0.2)" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontWeight: 'bold' }}
                />
                <YAxis 
                  stroke="rgba(255,255,255,0.2)" 
                  fontSize={10} 
                  tickLine={false} 
                  axisLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontWeight: 'bold' }}
                  domain={[95, 100]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line 
                  type="monotone" 
                  dataKey="actual" 
                  name="Actual Health"
                  stroke="rgba(255,255,255,0.4)" 
                  strokeWidth={3}
                  dot={{ r: 4, fill: 'white', strokeWidth: 0 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="predicted" 
                  name="Predicted Health"
                  stroke="#00aaff" 
                  strokeWidth={3}
                  strokeDasharray="5 5"
                  dot={{ r: 4, fill: '#00aaff', strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="glass-panel p-8 lg:col-span-1">
          <h3 className="font-bold text-lg uppercase tracking-tight mb-6">PERFORMANCE SUMMARY</h3>
          <div className="space-y-6">
            {[
              { label: 'Avg. Efficiency', value: '82.4%', change: '+2.1%', up: true },
              { label: 'Energy Recovery', value: '14.2 kWh', change: '+0.8 kWh', up: true },
              { label: 'Idle Drain', value: '0.4%', change: '-0.1%', up: true },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                <div>
                  <div className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-1">{item.label}</div>
                  <div className="text-xl font-black text-white">{item.value}</div>
                </div>
                <div className={`text-xs font-bold px-2 py-1 rounded-lg ${item.up ? 'bg-neon-green/10 text-neon-green' : 'bg-red-500/10 text-red-500'}`}>
                  {item.change}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel p-8 lg:col-span-2">
          <div className="flex items-center gap-2 mb-8">
            <Activity className="text-neon-blue w-5 h-5" />
            <h3 className="font-bold text-lg uppercase tracking-tight">AI PREDICTIONS & ANOMALIES</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-neon-blue/5 border border-neon-blue/20">
              <h4 className="font-bold text-neon-blue text-sm uppercase tracking-widest mb-2">MAINTENANCE PREDICTION</h4>
              <p className="text-sm text-white/60 leading-relaxed">
                Based on current degradation patterns, cell #48 is predicted to reach 80% capacity in approximately 14,200 KM. No immediate action required.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-neon-green/5 border border-neon-green/20">
              <h4 className="font-bold text-neon-green text-sm uppercase tracking-widest mb-2">EFFICIENCY OPTIMIZATION</h4>
              <p className="text-sm text-white/60 leading-relaxed">
                Regenerative braking efficiency has increased by 12% since the last software update. AI recommends maintaining current driving profile.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
