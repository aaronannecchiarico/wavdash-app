export const checkMediaBunnySupport = (): {
  supported: boolean;
  missingFeatures: string[];
} => {
  const missingFeatures: string[] = [];
  
  if (!('VideoDecoder' in window)) {
    missingFeatures.push('VideoDecoder');
  }
  
  if (!('VideoEncoder' in window)) {
    missingFeatures.push('VideoEncoder');
  }
  
  if (!('AudioDecoder' in window)) {
    missingFeatures.push('AudioDecoder');
  }
  
  if (!('AudioEncoder' in window)) {
    missingFeatures.push('AudioEncoder');
  }
  
  return {
    supported: missingFeatures.length === 0,
    missingFeatures,
  };
};