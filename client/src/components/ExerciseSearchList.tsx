import React, { useMemo, useState } from 'react';
import {
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Exercise } from '../types';

interface ExerciseSearchListProps {
  exercises: Exercise[];
  onSelectExercise: (exerciseId: string) => void;
}

export default function ExerciseSearchList({
  exercises,
  onSelectExercise,
}: ExerciseSearchListProps) {
  const [query, setQuery] = useState('');
  const normalizedQuery = query.trim().toLowerCase();
  const filteredExercises = useMemo(
    () =>
      exercises.filter((exercise) => {
        if (!normalizedQuery) return true;
        return [exercise.name, ...exercise.aliases].some((value) =>
          value.toLowerCase().includes(normalizedQuery),
        );
      }),
    [exercises, normalizedQuery],
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <TextInput
          accessibilityLabel="Search exercises"
          placeholder="Search exercises"
          value={query}
          onChangeText={setQuery}
          style={styles.searchInput}
          autoCapitalize="none"
          returnKeyType="search"
        />
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Clear exercise search"
          onPress={() => setQuery('')}
          style={styles.clearButton}
        >
          <Text style={styles.clearText}>Clear</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={filteredExercises}
        keyExtractor={(exercise) => exercise.id}
        keyboardShouldPersistTaps="handled"
        renderItem={({ item }) => (
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => onSelectExercise(item.id)}
            style={styles.exerciseRow}
          >
            <View style={styles.nameBlock}>
              <Text style={styles.exerciseName}>{item.name}</Text>
              <Text style={styles.primaryMuscle}>
                {item.primary_muscles[0] ?? 'Unspecified muscle'}
              </Text>
            </View>
            <View style={styles.equipmentBadge}>
              <Text style={styles.equipmentText}>{item.equipment}</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>No exercises found.</Text>}
        contentContainerStyle={filteredExercises.length === 0 ? styles.emptyList : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#F8FAFC' },
  searchRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  searchInput: {
    flex: 1,
    minHeight: 44,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
    color: '#0F172A',
  },
  clearButton: { paddingHorizontal: 10, paddingVertical: 12, marginLeft: 6 },
  clearText: { color: '#2563EB', fontWeight: '600' },
  exerciseRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    marginBottom: 8,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  nameBlock: { flex: 1, paddingRight: 10 },
  exerciseName: { fontSize: 16, fontWeight: '700', color: '#0F172A' },
  primaryMuscle: { marginTop: 4, fontSize: 13, color: '#475569' },
  equipmentBadge: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5, backgroundColor: '#E0E7FF' },
  equipmentText: { fontSize: 12, fontWeight: '600', color: '#3730A3' },
  emptyList: { flexGrow: 1, justifyContent: 'center' },
  emptyText: { textAlign: 'center', color: '#64748B' },
});
