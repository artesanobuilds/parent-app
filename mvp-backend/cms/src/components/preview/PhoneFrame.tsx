import type { ReactNode } from 'react';

interface PhoneFrameProps {
  children: ReactNode;
}

export default function PhoneFrame({ children }: PhoneFrameProps) {
  return (
    <div
      className="origin-top"
      style={{ transform: 'scale(0.75)', transformOrigin: 'top center' }}
    >
      <div
        className="relative overflow-hidden rounded-[40px] border-[3px] border-[#1C1C1E]"
        style={{
          width: 375,
          height: 812,
          backgroundColor: '#1C1C1E',
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
        }}
      >
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 z-20 w-[120px] h-[30px] bg-[#1C1C1E] rounded-b-2xl" />

        {/* Status Bar */}
        <div className="relative z-10 flex items-center justify-between px-6 pt-3 pb-1 h-[44px] bg-[#1C1C1E]">
          <span className="text-white text-[14px] font-semibold">9:41</span>
          <div className="flex items-center gap-1">
            {/* Cellular */}
            <svg width="16" height="12" viewBox="0 0 16 12" fill="white">
              <rect x="0" y="8" width="3" height="4" rx="0.5" />
              <rect x="4" y="5" width="3" height="7" rx="0.5" />
              <rect x="8" y="2" width="3" height="10" rx="0.5" />
              <rect x="12" y="0" width="3" height="12" rx="0.5" />
            </svg>
            {/* WiFi */}
            <svg width="14" height="12" viewBox="0 0 14 12" fill="white" className="ml-1">
              <path d="M7 10.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM3.5 8a5 5 0 017 0" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" />
              <path d="M1 5.5a8 8 0 0112 0" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            </svg>
            {/* Battery */}
            <svg width="24" height="12" viewBox="0 0 24 12" className="ml-1">
              <rect x="0" y="1" width="20" height="10" rx="2" stroke="white" strokeWidth="1" fill="none" />
              <rect x="2" y="3" width="16" height="6" rx="1" fill="white" />
              <rect x="21" y="4" width="2" height="4" rx="0.5" fill="white" />
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
