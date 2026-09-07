// src/components/workout/WorkoutHistoryModal.tsx
import React, { useState, useEffect } from 'react';
import {
  Modal,
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { WorkoutHistoryEntry } from '../../types';
import { StorageService } from '../../storage/storageService';
import { Colors } from '../../theme/colors';

interface WorkoutHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function WorkoutHistoryModal({
  isOpen,
  onClose,
}: WorkoutHistoryModalProps) {
  const [history, setHistory] = useState<WorkoutHistoryEntry[]>([]);

  useEffect(() => {
    if (isOpen) {
      StorageService.getHistory().then((data) => {
        const sorted = [...data].sort((a, b) => b.startTime - a.startTime);
        setHistory(sorted);
      });
    }
  }, [isOpen]);

  const formatDate = (timestamp: number): string => {
    const d = new Date(timestamp);
    return d.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const calculateTotalVolume = (entry: WorkoutHistoryEntry): number => {
    let total = 0;
    entry.exercises.forEach((ex) => {
      ex.sets.forEach((s) => {
        if (s.completed && s.weight_kg > 0 && s.actual_reps > 0) {
          total += s.weight_kg * s.actual_reps;
        }
      });
    });
    return total;
  };

  return (
    <Modal
      visible={isOpen}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <View style={styles.titleBlock}>
            <Text style={styles.headerTitle}>Workout History</Text>
            <Text style={styles.headerSubtitle}>
              {history.length} Completed {history.length === 1 ? 'Session' : 'Sessions'}
            </Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Ionicons name="close" size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
        </View>
        <FlatList
          data={history}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => {
            const volume = calculateTotalVolume(item);
            return (
              <View style={styles.card}>
                <View style={styles.cardTopRow}>
                  <Text style={styles.sessionTitle} numberOfLines={1}>
                    {item.title}
                  </Text>
                  <View style={styles.durationChip}>
                    <Ionicons name="stopwatch-outline" size={13} color={Colors.accent} style={{ marginRight: 4 }} />
                    <Text style={styles.durationText}>{item.durationMinutes} min</Text>
                  </View>
                </View>
                <View style={styles.metaRow}>
                  <Text style={styles.dateText}>{formatDate(item.startTime)}</Text>
                  {volume > 0 ? (
                    <Text style={styles.volumeText}>{volume.toLocaleString()} kg Volume</Text>
                  ) : null}
                </View>
                <View style={styles.exercisesList}>
                  {item.exercises.map((ex, exIdx) => {
                    const completedSets = ex.sets.filter((s) => s.completed);
                    return (
                      <View key={`hist-ex-${exIdx}`} style={styles.exerciseRow}>
                        <Text style={styles.exerciseName}>{ex.name}</Text>
                        <View style={styles.setsChipsRow}>
                          {completedSets.length > 0 ? (
                            completedSets.map((s, sIdx) => (
                              <View key={`set-chip-${sIdx}`} style={styles.setChip}>
                                <Text style={styles.setChipText}>
                                  {s.weight_kg > 0 ? `${s.weight_kg}kg x ` : ''}
                                  {s.actual_reps > 0 ? `${s.actual_reps}` : s.target_reps}
                                </Text>
                              </View>
                            ))
                          ) : (
                            <Text style={styles.noSetsText}>No completed sets</Text>
                          )}
                        </View>
                      </View>
                    );
                  })}
                </View>
              </View>
            );
          }}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="time-outline" size={48} color={Colors.textMuted} />
              <Text style={styles.emptyTitle}>No Workouts Logged</Text>
              <Text style={styles.emptySubtitle}>
                Completed workout sessions will automatically appear here for progress tracking.
              </Text>
            </View>
          }
        />
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    backgroundColor: Colors.surface,
  },
  titleBlock: {
    flex: 1,
    paddingRight: 10,
  },
  headerTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
  },
  headerSubtitle: {
    color: Colors.textMuted,
    fontSize: 12,
    marginTop: 2,
  },
  closeBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    padding: 16,
    marginBottom: 14,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionTitle: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '800',
    paddingRight: 8,
  },
  durationChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accentGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  durationText: {
    color: Colors.accent,
    fontSize: 11,
    fontWeight: '700',
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
    marginBottom: 12,
  },
  dateText: {
    color: Colors.textMuted,
    fontSize: 12,
  },
  volumeText: {
    color: Colors.completed,
    fontSize: 12,
    fontWeight: '700',
  },
  exercisesList: {
    borderTopWidth: 1,
    borderTopColor: Colors.surfaceBorder,
    paddingTop: 10,
  },
  exerciseRow: {
    marginBottom: 8,
  },
  exerciseName: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  setsChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  setChip: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  setChipText: {
    color: Colors.textPrimary,
    fontSize: 11,
    fontWeight: '600',
  },
  noSetsText: {
    color: Colors.textMuted,
    fontSize: 11,
    fontStyle: 'italic',
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
