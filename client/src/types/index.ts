export interface Exercise {
  id: string;
  name: string;
  aliases: string[];
  primary_muscles: string[];
  secondary_muscles: string[];
  equipment: string;
  mechanics?: string | null;
  instructions: string[];
  images: string[];
}

export type RoutingClass =
  | 'CLASS_A_INJURY'
  | 'CLASS_A_OUT_OF_SCOPE'
  | 'CLASS_B_GENERAL'
  | 'CLASS_C_CATALOG'
  | 'DIRECT_COACHING'
  | 'UNKNOWN_TOOL';

export type ExerciseCategory = 'warmup_rehab' | 'compound' | 'accessory';

export interface BackendWorkoutItem {
  name: string;
  existsInCatalog: boolean;
  catalogId: string | null;
  category: ExerciseCategory;
  sets: number;
  reps: string;
  targetRpe?: number | null;
  tempo?: string | null;
  customInstructions?: string[] | null;
  coachingCue?: string | null;
}

export interface BackendWorkoutProposal {
  title: string;
  targetFocus: string;
  estimatedMinutes: number;
  items: BackendWorkoutItem[];
}

export interface BackendChatResponse {
  routing_class: RoutingClass;
  chat_text: string;
  has_workout: boolean;
  workout_proposal: BackendWorkoutProposal | null;
  telemetry?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: number;
  text: string;
  routing_class?: RoutingClass;
  proposal?: BackendWorkoutProposal | null;
  proposalStatus?: 'pending' | 'accepted' | 'declined';
}

export interface SetLog {
  set_number: number;
  target_reps: string;
  actual_reps: number;
  weight_kg: number;
  completed: boolean;
  rpe?: number;
}

export interface RoutineExercise {
  name: string;
  catalogId: string | null;
  existsInCatalog: boolean;
  category: ExerciseCategory;
  targetSets: number;
  targetReps: string;
  targetRpe?: number;
  tempo?: string;
  coachingCue?: string;
  customInstructions?: string[];
}

export interface Routine {
  id: string;
  title: string;
  targetFocus: string;
  estimatedMinutes: number;
  createdAt: number;
  isAiGenerated: boolean;
  routingClass?: RoutingClass;
  exercises: RoutineExercise[];
}

export interface WorkoutExerciseSession {
  name: string;
  catalogId: string | null;
  existsInCatalog: boolean;
  category: ExerciseCategory;
  tempo?: string;
  coachingCue?: string;
  customInstructions?: string[];
  sets: SetLog[];
}

export interface WorkoutHistoryEntry {
  id: string;
  routineId?: string;
  title: string;
  startTime: number;
  endTime: number;
  durationMinutes: number;
  exercises: WorkoutExerciseSession[];
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
    | 'calves'
    | 'abdominals'
    | 'glutes';
  recovery_percentage: number;
}
