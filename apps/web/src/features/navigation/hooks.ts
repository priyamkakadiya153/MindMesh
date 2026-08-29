import { useEffect } from 'react';
import { useNavigationStore } from './store';

export function useKeyboardShortcuts(onUploadDoc?: () => void) {
  const { 
    setCommandPaletteOpen, 
    commandPaletteOpen,
    setActiveTab 
  } = useNavigationStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle Command Palette: Ctrl+K / Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }

      // Global Search focus: Ctrl+/
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="search"]') as HTMLInputElement;
        if (searchInput) searchInput.focus();
      }

      // Quick Nav Projects: Ctrl+P
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        setActiveTab('projects');
      }

      // Quick Nav Dashboard: Ctrl+D
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        setActiveTab('dashboard');
      }

      // Upload Document: Ctrl+Shift+U
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'u') {
        e.preventDefault();
        if (onUploadDoc) onUploadDoc();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen, setActiveTab, onUploadDoc]);
}
export default useKeyboardShortcuts;
