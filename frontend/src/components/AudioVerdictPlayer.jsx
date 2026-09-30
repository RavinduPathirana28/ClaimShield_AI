import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Pause, Play, Square, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

/**
 * AudioVerdictPlayer
 *
 * Uses the Web Speech API (SpeechSynthesis) to read aloud the verification
 * verdict, straight answer, and evidence summary in natural spoken audio.
 */
export default function AudioVerdictPlayer({ verdict, straight, summary, className = '' }) {
  const [isSupported, setIsSupported] = useState(false);
  const [playbackState, setPlaybackState] = useState('idle'); // 'idle' | 'playing' | 'paused'
  const [voices, setVoices] = useState([]);
  const utteranceRef = useRef(null);

  // Check Web Speech API support and load available voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);

      const updateVoices = () => {
        const available = window.speechSynthesis.getVoices() || [];
        setVoices(available);
      };

      updateVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = updateVoices;
      }
    }

    // Stop speaking when unmounted
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Cancel playback if verdict or text changes
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setPlaybackState('idle');
    }
  }, [verdict, straight, summary]);

  // Select the highest quality natural English voice available
  const selectVoice = () => {
    if (!voices || voices.length === 0) return null;

    // 1. Prefer modern Neural/Natural voices (Edge/Chrome/Safari)
    const naturalVoice = voices.find(
      (v) =>
        v.lang.startsWith('en') &&
        (v.name.includes('Natural') || v.name.includes('Neural') || v.name.includes('Google') || v.name.includes('Samantha'))
    );
    if (naturalVoice) return naturalVoice;

    // 2. Prefer any standard en-US or en-GB voice
    const englishVoice = voices.find((v) => v.lang === 'en-US' || v.lang === 'en-GB' || v.lang.startsWith('en'));
    if (englishVoice) return englishVoice;

    // 3. Fallback to default system voice
    return voices[0] || null;
  };

  const cleanText = (str) => (str || '').replace(/[#*_`]/g, '').trim();

  const buildSpeechScript = () => {
    const parts = [];
    if (verdict) parts.push(`Verdict: ${verdict}.`);
    if (straight) parts.push(cleanText(straight));
    if (summary) parts.push(`Summary: ${cleanText(summary)}`);
    return parts.join(' ');
  };

  const handlePlay = () => {
    if (!isSupported) {
      toast.error('Voice output is not supported in this browser.');
      return;
    }

    const synth = window.speechSynthesis;

    // If currently paused, resume
    if (playbackState === 'paused') {
      synth.resume();
      setPlaybackState('playing');
      return;
    }

    // Cancel any ongoing speech
    synth.cancel();

    const script = buildSpeechScript();
    if (!script) {
      toast.warning('No verdict text available to read aloud.');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(script);
    const chosenVoice = selectVoice();
    if (chosenVoice) {
      utterance.voice = chosenVoice;
    }
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setPlaybackState('playing');
    };

    utterance.onpause = () => {
      setPlaybackState('paused');
    };

    utterance.onresume = () => {
      setPlaybackState('playing');
    };

    utterance.onend = () => {
      setPlaybackState('idle');
    };

    utterance.onerror = (event) => {
      // 'canceled' or 'interrupted' is normal when user clicks stop
      if (event.error !== 'canceled' && event.error !== 'interrupted') {
        toast.error('Voice playback error', {
          description: event.error || 'Could not complete speech playback.',
        });
      }
      setPlaybackState('idle');
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);
  };

  const handlePause = () => {
    if (!isSupported) return;
    window.speechSynthesis.pause();
    setPlaybackState('paused');
  };

  const handleStop = () => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setPlaybackState('idle');
  };

  if (!isSupported) return null;

  if (playbackState === 'playing') {
    return (
      <div className={`inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-2 py-1 text-xs backdrop-blur-md ${className}`}>
        {/* Animated wave bars */}
        <div className="flex h-3.5 items-center gap-0.5 px-1" title="Reading verdict aloud">
          <span className="w-0.5 h-3 animate-pulse rounded-full bg-primary" />
          <span className="w-0.5 h-2 animate-pulse delay-75 rounded-full bg-primary" />
          <span className="w-0.5 h-3.5 animate-pulse delay-150 rounded-full bg-primary" />
          <span className="w-0.5 h-1.5 animate-pulse delay-100 rounded-full bg-primary" />
        </div>

        <span className="text-[11px] font-medium text-primary hidden sm:inline">
          Reading Verdict…
        </span>

        {/* Pause Button */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="size-6 rounded-full p-0 text-primary hover:bg-primary/20"
          onClick={handlePause}
          title="Pause speech"
        >
          <Pause className="size-3 fill-current" />
        </Button>

        {/* Stop Button */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="size-6 rounded-full p-0 text-muted-foreground hover:bg-primary/20 hover:text-foreground"
          onClick={handleStop}
          title="Stop speech"
        >
          <Square className="size-3 fill-current" />
        </Button>
      </div>
    );
  }

  if (playbackState === 'paused') {
    return (
      <div className={`inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs backdrop-blur-md ${className}`}>
        <span className="text-[11px] font-medium text-amber-600 dark:text-amber-400">
          Paused
        </span>

        {/* Resume Button */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="size-6 rounded-full p-0 text-amber-600 hover:bg-amber-500/20 dark:text-amber-400"
          onClick={handlePlay}
          title="Resume speech"
        >
          <Play className="size-3 fill-current" />
        </Button>

        {/* Stop Button */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="size-6 rounded-full p-0 text-muted-foreground hover:bg-amber-500/20 hover:text-foreground"
          onClick={handleStop}
          title="Stop speech"
        >
          <Square className="size-3 fill-current" />
        </Button>
      </div>
    );
  }

  // Idle state: "Listen to Verdict" button
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handlePlay}
      className={`h-8 gap-1.5 rounded-full glass-button border-border/60 px-3 text-xs transition-all hover:border-primary/50 hover:bg-primary/10 hover:text-primary active:scale-95 ${className}`}
      title="Listen to this verdict and explanation read aloud"
    >
      <Volume2 className="size-3.5 text-primary" />
      <span>Listen to Verdict</span>
    </Button>
  );
}
