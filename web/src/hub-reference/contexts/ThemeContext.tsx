// @ts-nocheck
import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Check for saved theme preference or default to dark
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'dark';
    
    try {
      const saved = localStorage.getItem('theme') as Theme;
      const initialTheme = saved || 'dark';
      
      console.log('🎨 Theme initialized:', initialTheme, saved ? '(from localStorage)' : '(default)');
      
      // Immediately add the class to prevent flash
      if (typeof document !== 'undefined') {
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(initialTheme);
      }
      
      return initialTheme;
    } catch (e) {
      console.error('Error initializing theme:', e);
      return 'dark';
    }
  });

  // Update document class and localStorage when theme changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    try {
      const root = document.documentElement;
      
      // Remove both classes first
      root.classList.remove('light', 'dark');
      
      // Add the current theme class
      root.classList.add(theme);
      
      // Save to localStorage
      localStorage.setItem('theme', theme);
      
      console.log('🎨 Theme applied:', theme, 'HTML classList:', root.classList.toString());
    } catch (e) {
      console.error('Error applying theme:', e);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => {
      const newTheme = prev === 'dark' ? 'light' : 'dark';
      console.log('🎨 Theme toggled:', prev, '→', newTheme);
      return newTheme;
    });
  };

  const isDark = theme === 'dark';

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}