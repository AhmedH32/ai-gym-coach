import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  FlatList,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { WorkoutExerciseSession, WorkoutHistoryEntry, SetLog, Exercise } from '../types';
import { StorageService, ActiveSessionState } from '../storage/storageService';
import { Colors } from '../theme/colors';
import ExerciseLoggerCard from '../components/workout/ExerciseLoggerCard';
import ExercisePickerModal from '../components/common/ExercisePickerModal';

export default function WorkoutScreen() {
  const [session, setSession] = useState<ActiveSessionState | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const navigation = useNavigation<any>();

  useFocusEffect(
    useCallback(() => {
      StorageService.getActiveSession().then((active) => {
        setSession(active);
        if (active) {
          setElapsedSeconds(Math.floor((Date.now() - active.startTime) / 1000));
        }
      });
    }, [])
  );

  useEffect(() => {
    if (!session) return;
    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - session.startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [session]);

  const formatTimer = (totalSeconds: number): string => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    if (mins >= 60) {
      const hrs = Math.floor(mins / 60);
      const remMins = mins % 60;
      return `${hrs}:${remMins < 10 ? '0' : ''}${remMins}:${secs < 10 ? '0' : ''}${secs}`;
    }
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleUpdateSet = async (
    exIdx: number,
    setIdx: number,
    field: 'weight_kg' | 'actual_reps' | 'completed',
    value: any
  ) => {
    if (!session) return;
    const updatedExercises = [...session.exercises];
    const targetSets = [...updatedExercises[exIdx].sets];
    targetSets[setIdx] = { ...targetSets[setIdx], [field]: value };
    updatedExercises[exIdx] = { ...updatedExercises[exIdx], sets: targetSets };
    const updatedSession = { ...session, exercises: updatedExercises };
    setSession(updatedSession);
    await StorageService.saveActiveSession(updatedSession);
  };

  const handleAddSet = async (exIdx: number) => {
    if (!session) return;
    const updatedExercises = [...session.exercises];
    const sets = updatedExercises[exIdx].sets;
    const lastSet = sets[sets.length - 1];
    const newSet: SetLog = {
      set_number: sets.length + 1,
      target_reps: lastSet ? lastSet.target_reps : '10',
      actual_reps: 0,
      weight_kg: lastSet ? lastSet.weight_kg : 0,
      completed: false,
    };
    updatedExercises[exIdx] = { ...updatedExercises[exIdx], sets: [...sets, newSet] };
    const updatedSession = { ...session, exercises: updatedExercises };
    setSession(updatedSession);
    await StorageService.saveActiveSession(updatedSession);
  };

  const handleDeleteSet = async (exIdx: number, setIdx: number) => {
    if (!session) return;
    const updatedExercises = [...session.exercises];
    const filtered = updatedExercises[exIdx].sets
      .filter((_, idx) => idx !== setIdx)
      .map((s, idx) => ({ ...s, set_number: idx + 1 }));
    updatedExercises[exIdx] = { ...updatedExercises[exIdx], sets: filtered };
    const updatedSession = { ...session, exercises: updatedExercises };
    setSession(updatedSession);
    await StorageService.saveActiveSession(updatedSession);
  };

  const handleRemoveExercise = async (exIdx: number) => {
    if (!session) return;
    Alert.alert('Remove Exercise', 'Are you sure you want to remove this exercise from your workout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          const updatedExercises = session.exercises.filter((_, idx) => idx !== exIdx);
          const updatedSession = { ...session, exercises: updatedExercises };
          setSession(updatedSession);
          await StorageService.saveActiveSession(updatedSession);
        },
      },
    ]);
  };

  const handlePickExercise = async (exercise: Exercise) => {
    if (!session) return;
    const newExerciseSession: WorkoutExerciseSession = {
      name: exercise.name,
      catalogId: exercise.id,
      existsInCatalog: true,
      category: exercise.mechanics === 'compound' ? 'compound' : 'accessory',
      sets: [
        { set_number: 1, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
        { set_number: 2, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
        { set_number: 3, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
      ],
    };
    const updatedSession = {
      ...session,
      exercises: [...session.exercises, newExerciseSession],
    };
    setSession(updatedSession);
    await StorageService.saveActiveSession(updatedSession);
  };

  const handleFinishWorkout = () => {
    if (!session) return;
    const hasCompletedSets = session.exercises.some((ex) => ex.sets.some((s) => s.completed));
    if (!hasCompletedSets) {
      Alert.alert(
        'Finish Workout?',
        'You have not marked any sets as completed. Do you still want to log this workout?',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Log Anyway', onPress: () => commitWorkout() },
        ]
      );
      return;
    }
    commitWorkout();
  };

  const commitWorkout = async () => {
    if (!session) return;
    const durationMinutes = Math.max(1, Math.round(elapsedSeconds / 60));
    const historyEntry: WorkoutHistoryEntry = {
      id: Date.now().toString(),
      routineId: session.routineId,
      title: session.routineTitle,
      startTime: session.startTime,
      endTime: Date.now(),
      durationMinutes,
      exercises: session.exercises,
    };
    await StorageService.logCompletedWorkout(historyEntry);
    setSession(null);
    Alert.alert('Workout Logged!', `Great job! Recorded a ${durationMinutes} min session.`);
  };

  const handleDiscardWorkout = () => {
    Alert.alert('Discard Workout?', 'Are you sure you want to discard this session? All logged sets will be lost.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Discard',
        style: 'destructive',
        onPress: async () => {
          await StorageService.saveActiveSession(null);
          setSession(null);
        },
      },
    ]);
  };

  const handleStartQuickWorkout = async () => {
    const quickSession: ActiveSessionState = {
      routineTitle: 'Quick Workout',
      startTime: Date.now(),
      exercises: [
        {
          name: 'General Movement',
          catalogId: null,
          existsInCatalog: false,
          category: 'compound',
          sets: [
            { set_number: 1, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
            { set_number: 2, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
            { set_number: 3, target_reps: '10', actual_reps: 0, weight_kg: 0, completed: false },
          ],
        },
      ],
    };
    await StorageService.saveActiveSession(quickSession);
    setSession(quickSession);
  };

  if (!session) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.emptyContainer}>
          <View style={styles.emptyIconCircle}>
            <Ionicons name="barbell-outline" size={48} color={Colors.accent} />
          </View>
          <Text style={styles.emptyTitle}>No Active Workout</Text>
          <Text style={styles.emptySubtitle}>
            Launch a saved routine or start an empty training session.
          </Text>
          <TouchableOpacity style={styles.actionBtnPrimary} onPress={() => navigation.navigate('Routines')}>
            <Ionicons name="clipboard-outline" size={18} color="#FFFFFF" style={{ marginRight: 6 }} />
            <Text style={styles.actionBtnText}>Browse Routines</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtnSecondary} onPress={handleStartQuickWorkout}>
            <Ionicons name="flash-outline" size={18} color={Colors.textPrimary} style={{ marginRight: 6 }} />
            <Text style={[styles.actionBtnText, { color: Colors.textPrimary }]}>Start Quick Session</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.stickyHeader}>
        <View style={styles.headerInfo}>
          <Text style={styles.routineTitle} numberOfLines={1}>
            {session.routineTitle}
          </Text>
          <View style={styles.timerRow}>
            <Ionicons name="stopwatch-outline" size={14} color={Colors.accent} style={{ marginRight: 4 }} />
            <Text style={styles.timerText}>{formatTimer(elapsedSeconds)}</Text>
          </View>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.discardBtn} onPress={handleDiscardWorkout}>
            <Ionicons name="close" size={18} color={Colors.danger} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.finishBtn} onPress={handleFinishWorkout}>
            <Text style={styles.finishBtnText}>Finish</Text>
          </TouchableOpacity>
        </View>
      </View>

      <FlatList
        data={session.exercises}
        keyExtractor={(_, idx) => `ex-${idx}`}
        contentContainerStyle={styles.scrollList}
        renderItem={({ item, index }) => (
          <ExerciseLoggerCard
            exercise={item}
            exerciseIndex={index}
            onUpdateSet={(sIdx, field, val) => handleUpdateSet(index, sIdx, field, val)}
            onAddSet={() => handleAddSet(index)}
            onDeleteSet={(sIdx) => handleDeleteSet(index, sIdx)}
            onRemoveExercise={() => handleRemoveExercise(index)}
          />
        )}
        ListFooterComponent={
          <TouchableOpacity style={styles.addExerciseBtn} onPress={() => setIsPickerOpen(true)}>
            <Ionicons name="add-circle-outline" size={20} color={Colors.accent} style={{ marginRight: 6 }} />
            <Text style={styles.addExerciseBtnText}>Add Exercise</Text>
          </TouchableOpacity>
        }
      />

      <ExercisePickerModal
        isOpen={isPickerOpen}
        onClose={() => setIsPickerOpen(false)}
        onSelectExercise={handlePickExercise}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  stickyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
  },
  headerInfo: {
    flex: 1,
    paddingRight: 10,
  },
  routineTitle: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '800',
  },
  timerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  timerText: {
    color: Colors.accent,
    fontSize: 13,
    fontWeight: '700',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  discardBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
  },
  finishBtn: {
    backgroundColor: Colors.completed,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  finishBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  scrollList: {
    padding: 16,
    paddingBottom: 40,
  },
  addExerciseBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: Colors.accent,
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 4,
    marginBottom: 20,
  },
  addExerciseBtnText: {
    color: Colors.accent,
    fontSize: 14,
    fontWeight: '700',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyIconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.accentGlow,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    color: Colors.textPrimary,
    fontSize: 20,
    fontWeight: '800',
  },
  emptySubtitle: {
    color: Colors.textMuted,
    fontSize: 14,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 20,
    marginBottom: 24,
  },
  actionBtnPrimary: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    borderRadius: 10,
    width: '100%',
    paddingVertical: 14,
    marginBottom: 10,
  },
  actionBtnSecondary: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    borderRadius: 10,
    width: '100%',
    paddingVertical: 14,
  },
  actionBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
});
