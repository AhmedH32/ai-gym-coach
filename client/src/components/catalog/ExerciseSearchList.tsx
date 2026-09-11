// client/src/components/catalog/ExerciseSearchList.tsx
import React, { useMemo, useState } from 'react';
import { FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Exercise } from '../../types';
import { Colors } from '../../theme/colors';

export interface ExerciseSearchListProps {
  exercises: Exercise[];
  onSelectExercise: (exerciseId: string) => void;
}

const CATEGORIES = ['All', 'Chest', 'Back', 'Quads', 'Hamstrings', 'Shoulders', 'Arms', 'Core'] as const;
type MuscleCategory = (typeof CATEGORIES)[number];

function matchesCategory(exercise: any, category: MuscleCategory): boolean {
  if (category === 'All') return true;
  const primary = exercise.primary_muscles ?? exercise.primaryMuscles ?? [];
  const secondary = exercise.secondary_muscles ?? exercise.secondaryMuscles ?? [];
  const muscles = [...primary, ...secondary].map((muscle: string) => String(muscle).toLowerCase());

  const terms: Record<Exclude<MuscleCategory, 'All'>, string[]> = {
    Chest: ['chest'],
    Back: ['back', 'lat'],
    Quads: ['quad'],
    Hamstrings: ['hamstring', 'glute'],
    Shoulders: ['shoulder'],
    Arms: ['bicep', 'tricep', 'forearm'],
    Core: ['abdominal', 'waist'],
  };
  return terms[category].some((term) => muscles.some((muscle) => muscle.includes(term)));
}

export default function ExerciseSearchList({ exercises, onSelectExercise }: ExerciseSearchListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<MuscleCategory>('All');

  const filteredExercises = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return exercises.filter((exercise: any) => {
      const aliases: string[] = exercise.aliases ?? [];
      const matchesText =
        !query ||
        exercise.name?.toLowerCase().includes(query) ||
        aliases.some((alias) => alias.toLowerCase().includes(query));

      return matchesText && matchesCategory(exercise, selectedCategory);
    });
  }, [exercises, searchQuery, selectedCategory]);

  return (
    <View style={styles.container}>
      <View style={styles.searchBar}>
        <Ionicons name="search" size={18} color={Colors.textMuted} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search exercises or aliases..."
          placeholderTextColor={Colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')} style={styles.clearButton} accessibilityLabel="Clear search">
            <Ionicons name="close-circle" size={18} color={Colors.textMuted} />
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.filterHeader}>
        <Text style={styles.filterLabel}>FILTER BY MUSCLE</Text>
        <Text style={styles.resultCount}>{filteredExercises.length} results</Text>
      </View>

      <View style={styles.categoryGrid}>
        {CATEGORIES.map((category) => {
          const active = selectedCategory === category;
          return (
            <TouchableOpacity
              key={category}
              onPress={() => setSelectedCategory(category)}
              style={[styles.categoryPill, active && styles.categoryPillActive]}
            >
              <Text style={[styles.categoryText, active && styles.categoryTextActive]}>{category}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <FlatList
        data={filteredExercises}
        keyExtractor={(item, index) => item?.id ?? `ex-${index}`}
        initialNumToRender={15}
        maxToRenderPerBatch={20}
        windowSize={10}
        removeClippedSubviews
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.listContent}
        renderItem={({ item }: { item: any }) => {
          const primaryList = item.primary_muscles ?? item.primaryMuscles ?? [];
          const primaryMuscle = primaryList.length > 0 ? String(primaryList[0]).toUpperCase() : 'GENERAL';

          return (
            <TouchableOpacity style={styles.rowItem} onPress={() => onSelectExercise(item.id)} activeOpacity={0.7}>
              <View style={styles.itemMain}>
                <Text style={styles.itemName} numberOfLines={2}>{item.name}</Text>
                <Text style={styles.itemMuscle}>{primaryMuscle}</Text>
              </View>
              <View style={styles.itemMeta}>
                <View style={styles.equipmentTag}>
                  <Text style={styles.equipmentTagText}>{item.equipment || 'General'}</Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
              </View>
            </TouchableOpacity>
          );
        }}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="search-outline" size={40} color={Colors.textMuted} />
            <Text style={styles.emptyTitle}>No Exercises Found</Text>
            <Text style={styles.emptySubtitle}>Try adjusting your search terms or filter selection.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  searchBar: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder, borderRadius: 12, marginHorizontal: 16, marginTop: 6, marginBottom: 14, paddingHorizontal: 13, height: 48 },
  searchInput: { flex: 1, color: Colors.textPrimary, fontSize: 14, marginLeft: 8 },
  clearButton: { padding: 4 },
  filterHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, marginBottom: 7 },
  filterLabel: { color: Colors.textMuted, fontSize: 10, fontWeight: '800', letterSpacing: 1.1 },
  resultCount: { color: Colors.textSecondary, fontSize: 11, fontWeight: '600' },
  categoryGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, paddingBottom: 6 },
  categoryPill: { backgroundColor: Colors.surface, paddingHorizontal: 13, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: Colors.surfaceBorder, marginRight: 7, marginBottom: 7 },
  categoryPillActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  categoryText: { color: Colors.textSecondary, fontSize: 12, fontWeight: '600' },
  categoryTextActive: { color: '#FFFFFF', fontWeight: '700' },
  listContent: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 24 },
  rowItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder, borderRadius: 12, minHeight: 68, paddingVertical: 11, paddingHorizontal: 13, marginBottom: 8 },
  itemMain: { flex: 1, paddingRight: 12 },
  itemName: { color: Colors.textPrimary, fontSize: 14, lineHeight: 19, fontWeight: '700' },
  itemMuscle: { color: Colors.accent, fontSize: 11, fontWeight: '600', marginTop: 2 },
  itemMeta: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  equipmentTag: { backgroundColor: Colors.surfaceLight, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  equipmentTagText: { color: Colors.textMuted, fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  emptyContainer: { alignItems: 'center', justifyContent: 'center', paddingVertical: 64 },
  emptyTitle: { color: Colors.textPrimary, fontSize: 16, fontWeight: '700', marginTop: 12 },
  emptySubtitle: { color: Colors.textMuted, fontSize: 13, textAlign: 'center', marginTop: 4 },
});