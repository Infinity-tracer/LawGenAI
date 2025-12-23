
import React from 'react';
import { LawIcon, EmblemIcon } from './Icons';

interface LandingProps {
  onTryNow: () => void;
}

const Landing: React.FC<LandingProps> = ({ onTryNow }) => {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Background with Indian Law Theme overlays */}
      <div className="absolute inset-0 z-0 opacity-10 flex items-center justify-center pointer-events-none">
         <EmblemIcon className="w-[80vw] h-[80vw] text-[#3d2b1f]" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl px-6 text-center">
        <div className="flex items-center justify-center mb-10">
          <LawIcon className="w-20 h-20 mr-6 text-[#d4af37]" />
          <h1 className="text-6xl md:text-8xl tracking-tight font-bold text-[#f5f5f5]">
            NYAYASIST
          </h1>
        </div>
        
        <h2 className="text-2xl md:text-4xl font-light mb-8 text-[#d4af37] uppercase tracking-[0.2em] serif">
          AI-Powered Legal Intelligence
        </h2>
        
        <p className="text-lg md:text-xl text-[#f5f5f5] opacity-80 mb-12 leading-relaxed max-w-2xl mx-auto font-light">
          Revolutionizing Indian legal research with precision mapping, comprehensive case analysis, and intelligent summaries designed for the modern advocate.
        </p>

        <div className="flex justify-center items-center">
          <button 
            onClick={onTryNow}
            className="w-full md:w-auto bg-[#3d2b1f] border border-[#d4af37] text-[#f5f5f5] px-16 py-4 text-xl font-medium hover:bg-[#4d3b2f] active:scale-[0.98] transition-colors"
          >
            TRY IT NOW
          </button>
        </div>
        
        <p className="mt-12 text-xs text-[#f5f5f5]/40 tracking-[0.4em] uppercase">
          Quick Case Summary • Law Mapping • Precedent Research
        </p>
      </div>

      {/* Footer Branding */}
      <div className="absolute bottom-10 text-[#d4af37] text-sm tracking-[0.3em] uppercase opacity-50">
        Integrity • Justice • Intelligence
      </div>
    </div>
  );
};

export default Landing;
