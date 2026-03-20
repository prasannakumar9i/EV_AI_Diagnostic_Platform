import { Link, useLocation } from 'react-router-dom';
import { motion } from 'motion/react';
import { Battery, MessageSquare, LayoutDashboard, BarChart3, Info, Zap } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Home', icon: Zap },
  { path: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  { path: '/dashboard', label: 'Diagnostics', icon: LayoutDashboard },
  { path: '/insights', label: 'Insights', icon: BarChart3 },
  { path: '/about', label: 'About', icon: Info },
];

export function Navbar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between glass-panel px-6 py-3">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-neon-blue/20 flex items-center justify-center group-hover:neon-border-blue transition-all">
            <Battery className="text-neon-blue w-6 h-6" />
          </div>
          <span className="font-bold text-xl tracking-tight neon-glow-blue">EV AI <span className="text-neon-green">DIAGNOSTIC</span></span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-2 text-sm font-medium transition-colors hover:text-neon-blue ${
                  isActive ? 'text-neon-blue' : 'text-white/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
                {isActive && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute -bottom-1 left-0 right-0 h-0.5 bg-neon-blue shadow-[0_0_10px_#00aaff]"
                  />
                )}
              </Link>
            );
          })}
        </div>

        <button className="px-4 py-2 rounded-xl bg-neon-blue text-black font-bold text-sm hover:scale-105 transition-transform hover:neon-border-blue">
          CONNECT VEHICLE
        </button>
      </div>
    </nav>
  );
}
