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
      className="relative shrink-0 size-8.5 rounded-xl border border-slate-300/80 bg-white/80 text-slate-800 shadow-xs hover:border-slate-400 hover:bg-white hover:text-black dark:border-white/10 dark:bg-transparent dark:text-muted-foreground [&_svg]:size-4 [&_svg]:stroke-[2.2]"
      aria-label="Toggle theme"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      <Sun className="scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90 text-amber-600 dark:text-inherit" />
      <Moon className="absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
    </Button>
  );
}
