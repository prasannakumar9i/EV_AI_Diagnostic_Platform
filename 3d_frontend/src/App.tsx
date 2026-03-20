import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/common/Navbar';
import { Home } from './pages/Home';
import { Assistant } from './pages/Assistant';
import { Dashboard } from './pages/Dashboard';
import { Insights } from './pages/Insights';
import { About } from './pages/About';
import { AnimatePresence } from 'motion/react';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-bg text-white selection:bg-neon-blue selection:text-black">
        <Navbar />
        <main className="relative z-10">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/insights" element={<Insights />} />
              <Route path="/about" element={<About />} />
            </Routes>
          </AnimatePresence>
        </main>
        
        {/* Global Background Effects */}
        <div className="fixed inset-0 pointer-events-none -z-20">
          <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,_rgba(0,170,255,0.05)_0%,_transparent_50%)]" />
          <div className="absolute bottom-0 right-0 w-full h-full bg-[radial-gradient(circle_at_80%_80%,_rgba(0,255,136,0.05)_0%,_transparent_50%)]" />
        </div>
      </div>
    </Router>
  );
}
