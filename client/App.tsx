import React, { useMemo, useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import ExerciseDetailModal from './src/components/ExerciseDetailModal';
import ExerciseSearchList from './src/components/ExerciseSearchList';
import RecoveryDashboard from './src/components/RecoveryDashboard';
import WorkoutLogger from './src/components/WorkoutLogger';
import { Exercise, MuscleRecoveryState, SetEntry } from './src/types';

const previewImage =
  'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=900&q=80';

const exercises: Exercise[] = [
  {
    id: 'barbell-squat',
    name: 'Barbell Squat',
    aliases: ['Back Squat', 'BB Squat'],
    primary_muscles: ['quads', 'glutes'],
    secondary_muscles: ['hamstrings', 'core'],
    equipment: 'Barbell',
    mechanics: 'Compound',
    instructions: [
      'Place the bar comfortably across your upper back and stand with feet shoulder-width apart.',
      'Brace your core, bend your knees, and lower your hips under control.',
      'Drive through your feet to return to a tall standing position.',
    ],
    images: [previewImage],
  },
  {
    id: 'bench-press',
    name: 'Bench Press',
    aliases: ['Chest Press', 'BB Bench'],
    primary_muscles: ['chest'],
    secondary_muscles: ['triceps', 'shoulders'],
    equipment: 'Barbell',
    mechanics: 'Compound',
    instructions: [
      'Lie flat on the bench with your eyes below the bar.',
      'Lower the bar toward the middle of your chest with your elbows controlled.',
      'Press the bar upward until your arms are extended without locking aggressively.',
    ],
    images: [previewImage],
  },
  {
    id: 'lat-pulldown',
    name: 'Lat Pulldown',
    aliases: ['Pulldown', 'Wide Grip Pulldown'],
    primary_muscles: ['back'],
    secondary_muscles: ['biceps'],
    equipment: 'Cable',
    mechanics: 'Compound',
    instructions: [
      'Sit tall and grip the bar slightly wider than shoulder width.',
      'Pull the bar toward your upper chest while keeping your torso stable.',
      'Return the bar slowly until your elbows are extended.',
    ],
    images: [previewImage],
  },
];

const initialSets: SetEntry[] = [
  { set_number: 1, weight_kg: 60, reps: 10, completed: true },
  { set_number: 2, weight_kg: 65, reps: 8, completed: false },
  { set_number: 3, weight_kg: 65, reps: 8, completed: false },
];

const recoveryData: MuscleRecoveryState[] = [
  { muscle_group: 'chest', recovery_percentage: 25 },
  { muscle_group: 'back', recovery_percentage: 60 },
  { muscle_group: 'quads', recovery_percentage: 90 },
  { muscle_group: 'shoulders', recovery_percentage: 75 },
  { muscle_group: 'hamstrings', recovery_percentage: 40 },
  { muscle_group: 'triceps', recovery_percentage: 15 },
];

export default function App() {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | null>(null);
  const [sets, setSets] = useState<SetEntry[]>(initialSets);
  const [lastSelected, setLastSelected] = useState('None yet');
  const selectedExercise = useMemo(
    () => exercises.find((exercise) => exercise.id === selectedExerciseId) ?? null,
    [selectedExerciseId],
  );

  const updateSet = (setNumber: number, field: 'reps' | 'weight_kg' | 'completed', value: any) => {
    setSets((currentSets) =>
      currentSets.map((set) =>
        set.set_number === setNumber ? { ...set, [field]: value } : set,
      ),
    );
  };

  const addSet = () => {
    setSets((currentSets) => [
      ...currentSets,
      { set_number: currentSets.length + 1, weight_kg: 0, reps: 0, completed: false },
    ]);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
        <Text style={styles.appTitle}>AI Gym Coach</Text>
        <Text style={styles.subtitle}>Phase 3 Runtime Preview</Text>
        <Text style={styles.helperText}>Interact with each component below to verify its runtime behavior.</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>ExerciseSearchList</Text>
          <Text style={styles.sectionHint}>Try “Back Squat” or “Pulldown” to test aliases.</Text>
          <View style={styles.searchPanel}>
            <ExerciseSearchList
              exercises={exercises}
              onSelectExercise={(exerciseId) => {
                setSelectedExerciseId(exerciseId);
                setLastSelected(exercises.find((exercise) => exercise.id === exerciseId)?.name ?? exerciseId);
              }}
            />
          </View>
          <Text style={styles.eventText}>Selected exercise: {lastSelected}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>WorkoutLogger</Text>
          <Text style={styles.sectionHint}>Edit weight/reps, toggle completion, and add a set.</Text>
          <WorkoutLogger
            exerciseName="Barbell Squat"
            sets={sets}
            onUpdateSet={updateSet}
            onAddSet={addSet}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>RecoveryDashboard</Text>
          <Text style={styles.sectionHint}>Sample values cover fatigued, recovering, and ready states.</Text>
          <RecoveryDashboard recoveryData={recoveryData} />
        </View>
      </ScrollView>
      <ExerciseDetailModal
        exercise={selectedExercise}
        isOpen={selectedExercise !== null}
        onClose={() => setSelectedExerciseId(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#E2E8F0' },
  screen: { padding: 16, paddingBottom: 36 },
  appTitle: { fontSize: 28, fontWeight: '800', color: '#0F172A' },
  subtitle: { marginTop: 4, fontSize: 18, fontWeight: '700', color: '#2563EB' },
  helperText: { marginTop: 8, marginBottom: 16, color: '#475569', lineHeight: 20 },
  section: { marginBottom: 18, overflow: 'hidden', borderRadius: 16, backgroundColor: '#FFFFFF' },
  sectionTitle: { paddingHorizontal: 16, paddingTop: 16, fontSize: 20, fontWeight: '800', color: '#0F172A' },
  sectionHint: { paddingHorizontal: 16, paddingTop: 5, color: '#64748B' },
  searchPanel: { height: 370, marginTop: 8 },
  eventText: { paddingHorizontal: 16, paddingBottom: 16, color: '#166534', fontWeight: '600' },
});
