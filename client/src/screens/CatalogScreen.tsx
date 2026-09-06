import React, { useMemo, useState } from 'react';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Exercise } from '../types';
import { Colors } from '../theme/colors';
import ExerciseSearchList from '../components/catalog/ExerciseSearchList';
import ExerciseDetailModal from '../components/catalog/ExerciseDetailModal';
import rawExercises from '../assets/data/exercises.json';

type RawExercise = {
  id: string;
  name: string;
  aliases?: string[];
  equipment: string;
  mechanic?: string | null;
  mechanics?: string | null;
  primaryMuscles?: string[];
  secondaryMuscles?: string[];
  primary_muscles?: string[];
  secondary_muscles?: string[];
  instructions?: string[];
  images?: string[];
};

export default function CatalogScreen() {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | null>(null);

  const exercises = useMemo<Exercise[]>(() => {
    const source = rawExercises as RawExercise[] | { exercises: RawExercise[] };
    const records = Array.isArray(source) ? source : source.exercises;
    return records.map((exercise) => ({
      id: exercise.id,
      name: exercise.name,
      aliases: exercise.aliases ?? [],
      equipment: exercise.equipment,
      mechanics: exercise.mechanics ?? exercise.mechanic ?? null,
      primary_muscles: exercise.primary_muscles ?? exercise.primaryMuscles ?? [],
      secondary_muscles: exercise.secondary_muscles ?? exercise.secondaryMuscles ?? [],
      instructions: exercise.instructions ?? [],
      images: exercise.images ?? [],
    }));
  }, []);

  const selectedExercise = useMemo(
    () => exercises.find((exercise) => exercise.id === selectedExerciseId) ?? null,
    [exercises, selectedExerciseId],
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.countText}>{exercises.length} Movements Indexed</Text>
      </View>
      <ExerciseSearchList exercises={exercises} onSelectExercise={setSelectedExerciseId} />
      <ExerciseDetailModal exercise={selectedExercise} isOpen={selectedExercise !== null} onClose={() => setSelectedExerciseId(null)} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.background },
  header: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  countText: { color: Colors.textMuted, fontSize: 12, fontWeight: '600' },
});
