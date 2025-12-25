
import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
  showFooter?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, showFooter = true }) => {
  return (
    <div className="min-h-screen flex flex-col relative">
      {/* Main Content */}
      <div className="flex-1">
        {children}
      </div>

      {/* Footer */}
      {showFooter && (
        <footer className="w-full py-4 bg-[#0b0d0c] border-t border-[#3d2b1f] text-center z-40">
          <p className="text-[#d4af37] text-sm tracking-wide">
            © {new Date().getFullYear()} All Rights Reserved
          </p>
          <p className="text-[#f5f5f5]/60 text-xs mt-1 tracking-widest uppercase">
            Developed by <span className="text-[#d4af37]">NAVYASRI P</span> & <span className="text-[#d4af37]">NITYA SHARMA</span>
          </p>
        </footer>
      )}
    </div>
  );
};

export default Layout;
