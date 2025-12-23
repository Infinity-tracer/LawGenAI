
import React from 'react';

export const LawIcon: React.FC<{ className?: string }> = ({ className = "w-8 h-8" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    {/* Central Pillar */}
    <path d="M12 3v18" />
    <path d="M9 21h6" />
    {/* Beam */}
    <path d="M6 7l6-1 6 1" />
    {/* Left Scale */}
    <path d="M6 7v2" />
    <path d="M3 13c0 2 1.5 3 3 3s3-1 3-3" />
    <path d="M6 9l-3 4" />
    <path d="M6 9l3 4" />
    {/* Right Scale */}
    <path d="M18 7v2" />
    <path d="M15 13c0 2 1.5 3 3 3s3-1 3-3" />
    <path d="M18 9l-3 4" />
    <path d="M18 9l3 4" />
  </svg>
);

export const EmblemIcon: React.FC<{ className?: string }> = ({ className = "w-12 h-12" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" />
    <path d="M12 22V12" />
    <path d="M12 12l8.5-4.7" />
    <path d="M12 12L3.5 7.3" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

export const PlusIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);

export const FolderIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

export const SendIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

export const PaperclipIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.51a2 2 0 0 1-2.83-2.83l8.49-8.48" />
  </svg>
);
