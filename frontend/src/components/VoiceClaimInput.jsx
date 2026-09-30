import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Square, Loader2, X, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import * as api from '@/services/api';

/**
 * VoiceClaimInput
 *
 * Captures microphone audio using the browser MediaRecorder API,
 * animates live audio volume using the Web Audio API AnalyserNode,
 * and transcribes speech using Groq's high-speed Whisper AI model.
 */
export default function VoiceClaimInput({ onTranscript, disabled = false, token = null }) {
  const [status, setStatus] = useState('idle'); // 'idle' | 'recording' | 'transcribing'
  const [duration, setDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0); // 0 to 1

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const streamRef = useRef(null);

  // Format seconds to mm:ss
  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupAudio();
    };
  }, []);

  const cleanupAudio = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch {
        // ignore
      }
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  };

  // Start recording
  const startRecording = async () => {
    if (status !== 'idle' || disabled) return;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast.error('Voice input is not supported in this browser.', {
        description: 'Please use Chrome, Edge, Safari, or Firefox with microphone permissions.',
      });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // Setup Web Audio API Analyser for live volume meter
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
          const ctx = new AudioContext();
          audioContextRef.current = ctx;
          const source = ctx.createMediaStreamSource(stream);
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 64;
          source.connect(analyser);
          analyserRef.current = analyser;

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const updateLevel = () => {
            if (!analyserRef.current) return;
            analyserRef.current.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            const normalized = Math.min(1, Math.max(0, avg / 128));
            setAudioLevel(normalized);
            animFrameRef.current = requestAnimationFrame(updateLevel);
          };
          updateLevel();
        }
      } catch (audioErr) {
        console.warn('[VoiceClaimInput] Web Audio analyser init note:', audioErr);
      }

      // Determine best audio mime type supported
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          mimeType = 'audio/ogg';
        } else {
          mimeType = '';
        }
      }

      const recorderOptions = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Collect recorded blob
        const chunks = audioChunksRef.current;
        if (chunks.length === 0) {
          cleanupAudio();
          setStatus('idle');
          return;
        }

        const recordedBlob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        cleanupAudio();

        // Process transcription
        await handleTranscription(recordedBlob);
      };

      mediaRecorder.start(250); // Slice data every 250ms
      setStatus('recording');
      setDuration(0);
      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      cleanupAudio();
      setStatus('idle');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        toast.error('Microphone permission denied.', {
          description: 'Please click the microphone icon in your browser address bar to allow mic access.',
        });
      } else {
        toast.error('Could not access microphone.', {
          description: err.message || 'Please check your microphone settings.',
        });
      }
    }
  };

  // Stop recording normally & trigger transcription
  const stopRecording = () => {
    if (status !== 'recording' || !mediaRecorderRef.current) return;
    if (duration < 1) {
      toast.info('Recording was very short. Speak clearly for better results.');
    }
    try {
      mediaRecorderRef.current.stop();
    } catch {
      cleanupAudio();
      setStatus('idle');
    }
  };

  // Cancel recording without transcribing
  const cancelRecording = () => {
    cleanupAudio();
    setStatus('idle');
    setDuration(0);
    setAudioLevel(0);
    toast.info('Voice recording cancelled.');
  };

  // Call backend Groq Whisper transcription API
  const handleTranscription = async (blob) => {
    setStatus('transcribing');
    const filename = blob.type.includes('mp4') ? 'voice_claim.mp4' : 'voice_claim.webm';

    try {
      const res = await api.transcribeAudio(token, blob, filename);
      const text = (res?.text || '').trim();

      if (!text) {
        toast.warning('No speech detected.', {
          description: 'We could not hear any clear speech. Please try speaking closer to your microphone.',
        });
      } else {
        toast.success('Voice recognized!', {
          description: `“${text.length > 50 ? text.slice(0, 50) + '…' : text}”`,
        });
        if (onTranscript) {
          onTranscript(text);
        }
      }
    } catch (err) {
      toast.error('Voice transcription failed', {
        description: err.message || 'Could not convert audio to text. Please try again.',
      });
    } finally {
      setStatus('idle');
      setDuration(0);
      setAudioLevel(0);
    }
  };

  if (status === 'recording') {
    // Dynamic bar heights calculated from real-time audio volume
    const bars = [
      Math.max(0.2, Math.min(1, audioLevel * 1.5 + 0.1)),
      Math.max(0.3, Math.min(1, audioLevel * 2.2 + 0.2)),
      Math.max(0.4, Math.min(1, audioLevel * 2.8 + 0.3)),
      Math.max(0.3, Math.min(1, audioLevel * 2.0 + 0.2)),
      Math.max(0.2, Math.min(1, audioLevel * 1.4 + 0.1)),
    ];

    return (
      <div className="flex items-center gap-2 rounded-full border border-destructive/40 bg-destructive/10 px-3 py-1.5 backdrop-blur-md transition-all animate-in fade-in duration-200">
        {/* Pulsing Red Recording Indicator */}
        <span className="relative flex size-2.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-red-500 opacity-75"></span>
          <span className="relative inline-flex size-2.5 rounded-full bg-red-600"></span>
        </span>

        {/* Live Audio Equalizer Waves */}
        <div className="flex h-4 items-center gap-0.5 px-1" title="Speaking volume">
          {bars.map((heightMultiplier, idx) => (
            <span
              key={idx}
              className="w-1 rounded-full bg-red-500 transition-all duration-75"
              style={{
                height: `${Math.round(heightMultiplier * 16)}px`,
              }}
            />
          ))}
        </div>

        {/* Elapsed Timer */}
        <span className="font-mono text-xs font-semibold tabular-nums text-foreground">
          {formatTime(duration)}
        </span>

        <span className="hidden text-xs text-muted-foreground sm:inline">
          Listening…
        </span>

        {/* Stop / Finish Button */}
        <Button
          type="button"
          size="sm"
          variant="destructive"
          className="h-7 gap-1 rounded-full px-2.5 text-xs shadow-sm hover:brightness-110"
          onClick={stopRecording}
          title="Done speaking — transcribe claim"
        >
          <Square className="size-3 fill-current" />
          <span>Done</span>
        </Button>

        {/* Cancel Button */}
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="size-7 rounded-full p-0 text-muted-foreground hover:bg-destructive/20 hover:text-foreground"
          onClick={cancelRecording}
          title="Cancel recording"
        >
          <X className="size-3.5" />
        </Button>
      </div>
    );
  }

  if (status === 'transcribing') {
    return (
      <div className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1.5 backdrop-blur-md transition-all animate-in fade-in duration-200">
        <Loader2 className="size-3.5 animate-spin text-primary" />
        <span className="text-xs font-medium text-foreground">
          Transcribing with Groq Whisper AI…
        </span>
      </div>
    );
  }

  // Idle state: Clean, sleek microphone button
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      disabled={disabled}
      onClick={startRecording}
      className="h-8 gap-1.5 rounded-full glass-button border-border/60 px-3 text-xs text-muted-foreground transition-all hover:border-primary/50 hover:bg-primary/10 hover:text-primary active:scale-95"
      title="Speak your claim or question using voice input"
    >
      <Mic className="size-3.5 text-primary" />
      <span>Voice Input</span>
      <span className="hidden rounded bg-primary/15 px-1 py-0.2 text-[10px] font-semibold text-primary lg:inline">
        AI Whisper
      </span>
    </Button>
  );
}
