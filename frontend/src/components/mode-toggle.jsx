import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/theme-provider';

export function ModeToggle() {
  const { theme, setTheme } = useTheme();

  const isDark =
    theme === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : theme === 'dark';

  return (
    <Button
      variant="outline"
      size="icon"
      className="relative shrink-0"
      aria-label="Toggle theme"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      <Sun className="scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
      <Moon className="absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
    </Button>
  );
}
