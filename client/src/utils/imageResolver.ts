import { Exercise } from '../types';

export function isValidRemoteUrl(url?: string | null): boolean {
  return Boolean(url && (url.startsWith('http://') || url.startsWith('https://')));
}

export function getExerciseImageSource(imagePath?: string | null): { uri: string } | null {
  return isValidRemoteUrl(imagePath) ? { uri: imagePath as string } : null;
}

export function getMuscleBadgeColor(muscle: string): string {
  const value = muscle.toLowerCase();
  if (['chest', 'quadriceps', 'quads', 'back', 'lats', 'hamstrings'].some((group) => value.includes(group))) {
    return '#3B82F6';
  }
  if (['abdominals', 'abs', 'core', 'glutes', 'calves', 'forearms'].some((group) => value.includes(group))) {
    return '#10B981';
  }
  if (['shoulders', 'biceps', 'triceps', 'traps'].some((group) => value.includes(group))) {
    return '#8B5CF6';
  }
  return '#64748B';
}

export type ExerciseImageSource = ReturnType<typeof getExerciseImageSource>;
export type ExerciseRecord = Exercise;
