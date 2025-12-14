import { useEffect, useState } from 'react';
import { CheckCircle2, Sparkles, Trophy } from 'lucide-react';

interface SuccessToastProps {
  show: boolean;
  onClose: () => void;
}

export default function SuccessToast({ show, onClose }: SuccessToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setTimeout(onClose, 300);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!show && !visible) return null;

  return (
    <div
      className={`fixed top-20 right-4 z-50 transition-all duration-300 ${
        visible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
      }`}
    >
      <div className="glass-panel bg-gradient-to-r from-green-500/90 to-emerald-500/90 backdrop-blur-xl p-6 rounded-2xl shadow-2xl shadow-green-500/50 border-2 border-green-400/50 min-w-[320px]">
        <div className="flex items-start gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-white/20 rounded-full animate-ping" />
            <div className="relative bg-white/20 p-2 rounded-full">
              <CheckCircle2 className="w-8 h-8 text-white" />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Trophy className="w-5 h-5 text-yellow-300" />
              <h3 className="text-lg font-bold text-white">Solution Found!</h3>
              <Sparkles className="w-4 h-4 text-yellow-300 animate-pulse" />
            </div>
            <p className="text-sm text-white/90 font-medium">
              Optimization completed successfully
            </p>
          </div>
        </div>
        
        <div className="mt-4 h-1 bg-white/20 rounded-full overflow-hidden">
          <div className="h-full bg-white/40 rounded-full animate-pulse" />
        </div>
      </div>
    </div>
  );
}
