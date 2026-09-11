// client/src/utils/imageResolver.ts
import { ImageSourcePropType } from 'react-native';
import { EXERCISE_IMAGE_MAP } from '../assets/exerciseImages';

export function isValidRemoteUrl(url?: string | null): boolean {
  if (!url) return false;
  return url.startsWith('http://') || url.startsWith('https://');
}

export function getExerciseImageSource(imagePath?: string | null): ImageSourcePropType | null {
  if (!imagePath) return null;

  // 1. Remote CDN / Cloudinary / Supabase URLs
  if (isValidRemoteUrl(imagePath)) {
    return { uri: imagePath };
  }

  // 2. Local Static Dictionary Match
  if (EXERCISE_IMAGE_MAP[imagePath]) {
    return EXERCISE_IMAGE_MAP[imagePath];
  }

  // 3. Normalize fallback (try .webp if requested with .jpg)
  const webpKey = imagePath.replace(/\.jpe?g$/i, '.webp');
  if (EXERCISE_IMAGE_MAP[webpKey]) {
    return EXERCISE_IMAGE_MAP[webpKey];
  }

  // 4. Safe Blueprint Card Fallback
  return null;
}

export function getMuscleBadgeColor(muscle?: string | null): string {
  const m = (muscle || '').toLowerCase();
  if (m.includes('chest') || m.includes('pectoral')) return '#3B82F6';
  if (m.includes('back') || m.includes('lat')) return '#10B981';
  if (m.includes('quad') || m.includes('leg') || m.includes('glute')) return '#F59E0B';
  if (m.includes('hamstring') || m.includes('calf')) return '#EC4899';
  if (m.includes('shoulder') || m.includes('delt')) return '#8B5CF6';
  if (m.includes('arm') || m.includes('bicep') || m.includes('tricep')) return '#06B6D4';
  return '#64748B';
}