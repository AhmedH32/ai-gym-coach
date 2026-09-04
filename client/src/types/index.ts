export interface Exercise {
  id: string;
  name: string;
  aliases: string[];
  primary_muscles: string[];
  secondary_muscles: string[];
  equipment: string;
  mechanics?: string;
  instructions: string[];
  images: string[];
}

export interface SetEntry {
  set_number: number;
  reps: number;
  weight_kg: number;
  completed: boolean;
}

export interface MuscleRecoveryState {
  muscle_group:
    | 'chest'
    | 'back'
    | 'quads'
    | 'hamstrings'
    | 'shoulders'
    | 'triceps'
    | 'biceps'
    | 'calves';
  recovery_percentage: number;
}
