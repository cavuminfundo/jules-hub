import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import type { ToastMessage } from '../types';

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => {
        let borderStyle = 'border-zinc-700 bg-zinc-900';
        let icon = <Info className="w-4 h-4 text-zinc-400" />;

        if (toast.type === 'error') {
          borderStyle = 'border-rose-700/80 bg-zinc-900 text-rose-200';
          icon = <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />;
        } else if (toast.type === 'success') {
          borderStyle = 'border-emerald-700/80 bg-zinc-900 text-emerald-200';
          icon = <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />;
        } else if (toast.type === 'warning') {
          borderStyle = 'border-amber-700/80 bg-zinc-900 text-amber-200';
          icon = <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />;
        }

        return (
          <div
            key={toast.id}
            role="alert"
            className={`pointer-events-auto p-3.5 rounded-lg border shadow-xl flex items-start gap-3 transition-all animate-in fade-in slide-in-from-bottom-2 ${borderStyle}`}
          >
            {icon}
            <div className="flex-1 min-w-0">
              <h5 className="text-xs font-semibold text-zinc-100">{toast.title}</h5>
              <p className="text-xs text-zinc-300 mt-0.5 leading-relaxed break-words">
                {toast.message}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="text-zinc-400 hover:text-zinc-100 p-0.5 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
