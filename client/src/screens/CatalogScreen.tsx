// client/src/screens/CatalogScreen.tsx
import React, { useState, useMemo } from 'react';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Exercise } from '../types';
import { Colors } from '../theme/colors';
import ExerciseSearchList from '../components/catalog/ExerciseSearchList';
import ExerciseDetailModal from '../components/catalog/ExerciseDetailModal';
import rawExercises from '../assets/data/exercises.json';

export default function CatalogScreen() {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | null>(null);

  const exercises: Exercise[] = useMemo(() => {
    const raw = Array.isArray(rawExercises)
      ? rawExercises
      : (rawExercises as any).exercises || [];

    return raw.map((ex: any) => ({
      id: ex.id || String(ex.name).replace(/\s+/g, '_'),
      name: ex.name,
      aliases: ex.aliases || [],
      primary_muscles: ex.primary_muscles || ex.primaryMuscles || [],
      secondary_muscles: ex.secondary_muscles || ex.secondaryMuscles || [],
      equipment: ex.equipment || 'body only',
      mechanics: ex.mechanics || ex.mechanic || null,
      instructions: ex.instructions || [],
      images: ex.images || [],
    }));
  }, []);

  const selectedExercise = useMemo(() => {
    if (!selectedExerciseId) return null;
    return exercises.find((ex) => ex.id === selectedExerciseId) || null;
  }, [exercises, selectedExerciseId]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.countText}>
          {exercises.length} Movements Indexed
        </Text>
      </View>
      <ExerciseSearchList
        exercises={exercises}
        onSelectExercise={(id) => setSelectedExerciseId(id)}
      />
      <ExerciseDetailModal
        exercise={selectedExercise}
        isOpen={selectedExercise !== null}
        onClose={() => setSelectedExerciseId(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  countText: {
    color: Colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
});