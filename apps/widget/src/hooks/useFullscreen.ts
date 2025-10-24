import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for managing fullscreen/expanded state of the widget
 * Handles localStorage persistence and ESC key listener
 */
export const useFullscreen = () => {
  // Load initial state from localStorage
  const [isExpanded, setIsExpanded] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    
    // Check if we're on mobile (auto-expand on mobile)
    const isMobile = window.innerWidth < 640;
    if (isMobile) return true;
    
    // Load saved preference for desktop/tablet
    const saved = localStorage.getItem('agent_widget_expanded');
    return saved === 'true';
  });

  // Toggle expanded state
  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => {
      const newState = !prev;
      localStorage.setItem('agent_widget_expanded', String(newState));
      return newState;
    });
  }, []);

  // Collapse (useful for ESC key)
  const collapse = useCallback(() => {
    setIsExpanded(false);
    localStorage.setItem('agent_widget_expanded', 'false');
  }, []);

  // Expand
  const expand = useCallback(() => {
    setIsExpanded(true);
    localStorage.setItem('agent_widget_expanded', 'true');
  }, []);

  // ESC key listener - only on desktop/tablet
  useEffect(() => {
    const isMobile = window.innerWidth < 640;
    if (isMobile) return; // Don't allow ESC on mobile

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isExpanded) {
        collapse();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isExpanded, collapse]);

  // Handle window resize - auto-expand on mobile
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 640;
      if (isMobile && !isExpanded) {
        setIsExpanded(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isExpanded]);

  return {
    isExpanded,
    toggleExpanded,
    collapse,
    expand,
    isMobile: window.innerWidth < 640,
  };
};
