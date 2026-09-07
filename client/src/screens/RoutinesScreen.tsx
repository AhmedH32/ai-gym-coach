// src/screens/RoutinesScreen.tsx
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { Routine, WorkoutExerciseSession } from '../types';
import { StorageService, ActiveSessionState } from '../storage/storageService';
import { Colors } from '../theme/colors';
import RoutineBuilderModal from '../components/workout/RoutineBuilderModal';
import WorkoutHistoryModal from '../components/workout/WorkoutHistoryModal';

export default function RoutinesScreen() {
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const navigation = useNavigation<any>();

  useFocusEffect(
    useCallback(() => {
      StorageService.getRoutines().then(setRoutines);
    }, [])
  );

  const handleStartWorkout = async (routine: Routine) => {
    const activeExercises: WorkoutExerciseSession[] = routine.exercises.map((ex) => {
      const sets = Array.from({ length: ex.targetSets }, (_, i) => ({
        set_number: i + 1,
        target_reps: ex.targetReps,
        actual_reps: 0,
        weight_kg: 0,
        completed: false,
      }));
      return {
        name: ex.name,
        catalogId: ex.catalogId,
        existsInCatalog: ex.existsInCatalog,
        category: ex.category,
        tempo: ex.tempo,
        coachingCue: ex.coachingCue,
        customInstructions: ex.customInstructions,
        sets,
      };
    });
    const sessionState: ActiveSessionState = {
      routineTitle: routine.title,
      routineId: routine.id,
      startTime: Date.now(),
      exercises: activeExercises,
    };
    await StorageService.saveActiveSession(sessionState);
    navigation.navigate('Workout');
  };

  const handleSaveNewRoutine = async (newRoutine: Routine) => {
    await StorageService.saveRoutine(newRoutine);
    setRoutines((prev) => [newRoutine, ...prev]);
    Alert.alert('Routine Created!', `"${newRoutine.title}" has been saved to your library.`);
  };

  const handleDeleteRoutine = (routineId: string) => {
    Alert.alert('Delete Routine', 'Are you sure you want to remove this routine from your library?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await StorageService.deleteRoutine(routineId);
          setRoutines((prev) => prev.filter((r) => r.id !== routineId));
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.pageHeader}>
        <View>
          <Text style={styles.eyebrow}>YOUR TRAINING PLAN</Text>
          <Text style={styles.pageTitle}>Routines</Text>
        </View>
        <View style={styles.countBadge}>
          <Text style={styles.countBadgeText}>{routines.length}</Text>
        </View>
      </View>
      <View style={styles.headerBar}>
        <Text style={styles.headerSubtitle}>
          {routines.length} Saved {routines.length === 1 ? 'Routine' : 'Routines'}
        </Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.historyBtn}
            onPress={() => setIsHistoryOpen(true)}
          >
            <Ionicons name="time-outline" size={16} color={Colors.textSecondary} style={{ marginRight: 4 }} />
            <Text style={styles.historyBtnText}>History</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.newRoutineBtn}
            onPress={() => setIsBuilderOpen(true)}
          >
            <Ionicons name="add" size={16} color="#FFFFFF" style={{ marginRight: 2 }} />
            <Text style={styles.newRoutineBtnText}>New Routine</Text>
          </TouchableOpacity>
        </View>
      </View>
      <FlatList
        data={routines}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.titleBlock}>
                <Text style={styles.routineTitle}>{item.title}</Text>
                {item.isAiGenerated ? (
                  <View style={styles.aiBadge}>
                    <Text style={styles.aiBadgeText}>AI PRESCRIBED</Text>
                  </View>
                ) : null}
              </View>
              <TouchableOpacity onPress={() => handleDeleteRoutine(item.id)} style={styles.deleteBtn}>
                <Ionicons name="trash-outline" size={18} color={Colors.textMuted} />
              </TouchableOpacity>
            </View>
            <View style={styles.metaRow}>
              <Text style={styles.metaText}>
                {item.targetFocus} • {item.estimatedMinutes} min
              </Text>
            </View>
            <View style={styles.exerciseSummary}>
              {item.exercises.map((ex, idx) => (
                <View key={`${ex.name}-${idx}`} style={styles.exSummaryRow}>
                  <Text style={styles.exSummaryName} numberOfLines={1}>
                    • {ex.name}
                  </Text>
                  <Text style={styles.exSummaryVolume}>
                    {ex.targetSets} x {ex.targetReps}
                  </Text>
                </View>
              ))}
            </View>
            <TouchableOpacity style={styles.startBtn} onPress={() => handleStartWorkout(item)}>
              <Ionicons name="play" size={16} color="#FFFFFF" style={{ marginRight: 6 }} />
              <Text style={styles.startBtnText}>Start Workout</Text>
            </TouchableOpacity>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="clipboard-outline" size={48} color={Colors.textMuted} />
            <Text style={styles.emptyTitle}>No Saved Routines</Text>
            <Text style={styles.emptySubtitle}>
              Tap &quot;+ New Routine&quot; above or ask the AI Coach to prescribe customized workouts.
            </Text>
          </View>
        }
      />
      <RoutineBuilderModal
        isOpen={isBuilderOpen}
        onClose={() => setIsBuilderOpen(false)}
        onSaveRoutine={handleSaveNewRoutine}
      />
      <WorkoutHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    backgroundColor: Colors.surface,
  },
  pageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 14,
    backgroundColor: Colors.background,
  },
  eyebrow: {
    color: Colors.accent,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  pageTitle: {
    color: Colors.textPrimary,
    fontSize: 28,
    fontWeight: '900',
    marginTop: 3,
  },
  countBadge: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accentGlow,
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  countBadgeText: {
    color: Colors.accent,
    fontSize: 16,
    fontWeight: '800',
  },
  headerSubtitle: {
    color: Colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  historyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceLight,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  historyBtnText: {
    color: Colors.textSecondary,
    fontSize: 12,
    fontWeight: '700',
  },
  newRoutineBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  newRoutineBtnText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  listContent: {
    padding: 16,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    padding: 16,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  titleBlock: {
    flex: 1,
    paddingRight: 8,
  },
  routineTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
  },
  aiBadge: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.accentGlow,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginTop: 6,
  },
  aiBadgeText: {
    color: Colors.accent,
    fontSize: 10,
    fontWeight: '800',
  },
  deleteBtn: {
    padding: 4,
  },
  metaRow: {
    marginTop: 6,
    marginBottom: 12,
  },
  metaText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  exerciseSummary: {
    borderTopWidth: 1,
    borderTopColor: Colors.surfaceBorder,
    paddingTop: 10,
    marginBottom: 14,
  },
  exSummaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  exSummaryName: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 13,
  },
  exSummaryVolume: {
    color: Colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  startBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    borderRadius: 8,
    paddingVertical: 12,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
    paddingHorizontal: 24,
  },
  emptyTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    marginTop: 14,
  },
  emptySubtitle: {
    color: Colors.textMuted,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
});
