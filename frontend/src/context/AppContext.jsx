// File: frontend/src/context/AppContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

// Default theme based on system preference
const getDefaultTheme = () => {
    if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }
    return 'light';
};

// Get saved preferences from localStorage
const getSavedPreferences = () => {
    if (typeof window !== 'undefined') {
        return {
            theme: localStorage.getItem('theme') || 'light',
            language: localStorage.getItem('language') || 'en',
            fontSize: localStorage.getItem('fontSize') || 'medium',
            notifications: localStorage.getItem('notifications') === 'true'
        };
    }
    return {
        theme: 'light',
        language: 'en',
        fontSize: 'medium',
        notifications: true
    };
};

export const AppContextProvider = ({ children }) => {
    // State for user preferences
    const [theme, setTheme] = useState(getSavedPreferences().theme);
    const [language, setLanguage] = useState(getSavedPreferences().language);
    const [fontSize, setFontSize] = useState(getSavedPreferences().fontSize);
    const [notifications, setNotifications] = useState(getSavedPreferences().notifications);
    
    // State for app status
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Save preferences to localStorage when they change
    useEffect(() => {
        localStorage.setItem('theme', theme);
        localStorage.setItem('language', language);
        localStorage.setItem('fontSize', fontSize);
        localStorage.setItem('notifications', notifications);
        
        // Apply theme to body element
        document.body.classList.remove('light', 'dark');
        document.body.classList.add(theme);
        
        // Apply font size to body element
        document.body.style.fontSize = {
            small: '14px',
            medium: '16px',
            large: '18px'
        }[fontSize];
    }, [theme, language, fontSize, notifications]);
    
    // Listen for system theme changes
    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = () => {
            if (!localStorage.getItem('theme')) {
                setTheme(mediaQuery.matches ? 'dark' : 'light');
            }
        };
        
        mediaQuery.addListener(handleChange);
        return () => mediaQuery.removeListener(handleChange);
    }, []);
    
    const updateError = (error) => {
        setError(error);
        if (error && notifications) {
            // Show error notification
            console.error(error);
        }
    };

    const value = {
        // Theme
        theme,
        setTheme,
        // Language
        language,
        setLanguage,
        // Font Size
        fontSize,
        setFontSize,
        // Notifications
        notifications,
        setNotifications,
        // App Status
        isLoading,
        setIsLoading,
        error,
        setError: updateError,
        // Utility functions
        clearError: () => setError(null),
        resetPreferences: () => {
            setTheme(getDefaultTheme());
            setLanguage('en');
            setFontSize('medium');
            setNotifications(true);
        }
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within AppContextProvider');
    }
    return context;
};

// Custom hooks for specific context values
export const useTheme = () => {
    const { theme, setTheme } = useAppContext();
    return { theme, setTheme };
};

export const useLanguage = () => {
    const { language, setLanguage } = useAppContext();
    return { language, setLanguage };
};

export const useFontSize = () => {
    const { fontSize, setFontSize } = useAppContext();
    return { fontSize, setFontSize };
};

export const useAppStatus = () => {
    const { isLoading, error, setIsLoading, setError, clearError } = useAppContext();
    return { isLoading, error, setIsLoading, setError, clearError };
};