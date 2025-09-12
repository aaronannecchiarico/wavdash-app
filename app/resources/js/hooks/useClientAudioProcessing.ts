import { useState, useCallback } from 'react';
import { 
  Input, 
  Output, 
  Conversion, 
  OggOutputFormat, 
  BlobSource, 
  BufferTarget, 
  ALL_FORMATS,
  canEncodeAudio 
} from 'mediabunny';

interface ProcessedAudioData {
  processedFile: File;
  duration: number;
  originalSize: number;
  processedSize: number;
}

interface UseClientAudioProcessingReturn {
  processAudioFile: (file: File) => Promise<ProcessedAudioData>;
  progress: number;
  error: string | null;
  isProcessing: boolean;
  isSupported: boolean;
}

export function useClientAudioProcessing(): UseClientAudioProcessingReturn {
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Check browser compatibility
  const isSupported = 'VideoDecoder' in window && 'VideoEncoder' in window && 'AudioDecoder' in window && 'AudioEncoder' in window;

  const processAudioFile = useCallback(async (file: File): Promise<ProcessedAudioData> => {
    if (!isSupported) {
      throw new Error('Browser does not support WebCodecs API');
    }

    // Check if Opus encoding is supported (Opus works better in Chrome than Vorbis)
    const canEncodeOpus = await canEncodeAudio('opus', {
      numberOfChannels: 2,
      sampleRate: 44100,
      bitrate: 128000,
    });
    
    if (!canEncodeOpus) {
      throw new Error('Browser does not support Opus encoding');
    }

    setIsProcessing(true);
    setError(null);
    setProgress(0);

    try {
      const input = new Input({
        source: new BlobSource(file),
        formats: ALL_FORMATS,
      });
      
      const output = new Output({
        format: new OggOutputFormat(),
        target: new BufferTarget(),
      });
      
      // Start the output stream
      output.start();
      
      const conversion = await Conversion.init({
        input,
        output,
        audio: {
          codec: 'opus',
          bitrate: 128000, // 128kbps to match server processing
          numberOfChannels: 2, // stereo
          sampleRate: 44100, // Standard sample rate
          forceTranscode: true, // Ensure transcoding happens
        },
      });

      // Track conversion progress
      conversion.onProgress = (progress: number) => {
        setProgress(Math.round(progress * 100));
      };

      await conversion.execute();
      
      // Finalize the output to ensure all data is written
      await output.finalize();
      
      const processedBuffer = output.target.buffer;
      
      if (!processedBuffer) {
        throw new Error('Conversion failed: No output buffer generated');
      }
      
      const processedFile = new File(
        [processedBuffer], 
        file.name.replace(/\.[^/.]+$/, '.ogg'),
        { type: 'audio/ogg' }
      );

      // Extract duration from original input
      const duration = await input.computeDuration();
      
      setProgress(100);
      
      return {
        processedFile,
        duration,
        originalSize: file.size,
        processedSize: processedBuffer.byteLength,
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown processing error';
      setError(errorMessage);
      throw new Error(`Audio processing failed: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
    }
  }, [isSupported]);

  return {
    processAudioFile,
    progress,
    error,
    isProcessing,
    isSupported,
  };
}