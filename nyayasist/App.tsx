
import React, { useState, useEffect } from 'react';
import Landing from './components/Landing';
import Auth from './components/Auth';
import Chat from './components/Chat';
import Layout from './components/Layout';
import { View } from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(View.LANDING);
  const [user, setUser] = useState<any>(null);

  // Check for existing session
  useEffect(() => {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setCurrentView(View.CHAT);
    }
  }, []);

  const handleLogin = (userData: any) => {
    setUser(userData);
    localStorage.setItem('currentUser', JSON.stringify(userData));
    setCurrentView(View.CHAT);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('currentUser');
    setCurrentView(View.LANDING);
  };

  const navigate = (view: View) => {
    setCurrentView(view);
  };

  return (
    <Layout showFooter={currentView !== View.CHAT}>
      <div className="min-h-screen bg-[#0b0d0c] text-[#f5f5f5]">
        {currentView === View.LANDING && (
          <Landing onTryNow={() => navigate(View.AUTH)} />
        )}
        {currentView === View.AUTH && (
          <Auth 
            onSuccess={handleLogin} 
            onBack={() => navigate(View.LANDING)} 
          />
        )}
        {currentView === View.CHAT && (
          <Chat onLogout={handleLogout} />
        )}
      </div>
    </Layout>
  );
};

export default App;
