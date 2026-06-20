import type { ReactNode } from 'react';

interface PhoneFrameProps {
  children: ReactNode;
}

// The phone-frame chrome (notch, status bar, bezel) is intentionally drawn in
// ink-primary to mimic an iPhone's hardware. We use the ink-primary semantic
// token (`bg-ink-primary` / `border-ink-primary`) so the bezel stays consistent
// when the canvas theme shifts.
export default function PhoneFrame({ children }: PhoneFrameProps) {
  return (
    <div
      className="origin-top"
      style={{ transform: 'scale(0.75)', transformOrigin: 'top center' }}
    >
      <div
        className="relative overflow-hidden rounded-[40px] border-[3px] border-ink-primary bg-ink-primary font-sans"
        style={{ width: 375, height: 812 }}
      >
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 z-20 w-[120px] h-[30px] bg-ink-primary rounded-b-2xl" />

        {/* Status Bar */}
        <div className="relative z-10 flex items-center justify-between px-700 pt-300 pb-100 h-[44px] bg-ink-primary">
          <span className="text-ink-on-photo-light text-body-sm font-semibold">9:41</span>
          <div className="flex items-center gap-100">
            {/* Cellular */}
            <svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor" className="text-ink-on-photo-light">
              <rect x="0" y="8" width="3" height="4" rx="0.5" />
              <rect x="4" y="5" width="3" height="7" rx="0.5" />
              <rect x="8" y="2" width="3" height="10" rx="0.5" />
              <rect x="12" y="0" width="3" height="12" rx="0.5" />
            </svg>
            {/* WiFi */}
            <svg width="14" height="12" viewBox="0 0 14 12" className="ml-100 text-ink-on-photo-light" stroke="currentColor" fill="none">
              <path d="M7 10.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM3.5 8a5 5 0 017 0" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M1 5.5a8 8 0 0112 0" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            {/* Battery */}
            <svg width="24" height="12" viewBox="0 0 24 12" className="ml-100 text-ink-on-photo-light">
              <rect x="0" y="1" width="20" height="10" rx="2" stroke="currentColor" strokeWidth="1" fill="none" />
              <rect x="2" y="3" width="16" height="6" rx="1" fill="currentColor" />
              <rect x="21" y="4" width="2" height="4" rx="0.5" fill="currentColor" />
            </svg>
          </div>
        </div>

        {/* Content area */}
        <div className="overflow-y-auto" style={{ height: 812 - 44 }}>
          {children}
        </div>
      </div>
    </div>
  );
}
