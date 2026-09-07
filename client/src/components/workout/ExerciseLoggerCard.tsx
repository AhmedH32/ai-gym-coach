import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { WorkoutExerciseSession } from '../../types';
import { Colors } from '../../theme/colors';
import SetRow from './SetRow';

interface ExerciseLoggerCardProps {
  exercise: WorkoutExerciseSession;
  exerciseIndex: number;
  onUpdateSet: (setIndex: number, field: 'weight_kg' | 'actual_reps' | 'completed', value: any) => void;
  onAddSet: () => void;
  onDeleteSet: (setIndex: number) => void;
  onRemoveExercise: () => void;
}

export default function ExerciseLoggerCard({
  exercise,
  exerciseIndex,
  onUpdateSet,
  onAddSet,
  onDeleteSet,
  onRemoveExercise,
}: ExerciseLoggerCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.titleBlock}>
          <Text style={styles.exerciseTitle}>
            {exerciseIndex + 1}. {exercise.name}
          </Text>
          <View style={[styles.badge, exercise.existsInCatalog ? styles.catalogBadge : styles.rehabBadge]}>
            <Text style={[styles.badgeText, exercise.existsInCatalog ? styles.catalogText : styles.rehabText]}>
              {exercise.existsInCatalog ? 'CATALOG' : 'REHAB PROTOCOL'}
            </Text>
          </View>
        </View>
        <TouchableOpacity onPress={onRemoveExercise} style={styles.deleteBtn}>
          <Ionicons name="trash-outline" size={16} color={Colors.textMuted} />
        </TouchableOpacity>
      </View>

      {exercise.coachingCue ? (
        <View style={styles.cueRow}>
          <Ionicons name="medical" size={12} color={Colors.rehab} style={{ marginRight: 4, marginTop: 1 }} />
          <Text style={styles.cueText}>{exercise.coachingCue}</Text>
        </View>
      ) : null}

      {exercise.tempo ? (
        <View style={styles.tempoRow}>
          <Text style={styles.tempoText}>Tempo: {exercise.tempo}</Text>
        </View>
      ) : null}

      <View style={styles.columnHeader}>
        <Text style={[styles.columnLabel, { width: 32 }]}>SET</Text>
        <Text style={[styles.columnLabel, { width: 78 }]}>TARGET</Text>
        <Text style={[styles.columnLabel, { flex: 1 }]}>KG</Text>
        <Text style={[styles.columnLabel, { flex: 1 }]}>ACTUAL</Text>
        <Text style={[styles.columnLabel, { width: 38 }]}>DONE</Text>
      </View>

      {exercise.sets.map((set, sIdx) => (
        <SetRow
          key={`set-${sIdx}`}
          set={set}
          onUpdate={(field, val) => onUpdateSet(sIdx, field, val)}
          onDelete={() => onDeleteSet(sIdx)}
        />
      ))}

      <TouchableOpacity style={styles.addSetBtn} onPress={onAddSet}>
        <Ionicons name="add" size={16} color={Colors.accent} style={{ marginRight: 4 }} />
        <Text style={styles.addSetText}>Add Set</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    padding: 14,
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  titleBlock: {
    flex: 1,
    paddingRight: 8,
  },
  exerciseTitle: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '700',
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 4,
  },
  catalogBadge: {
    backgroundColor: Colors.surfaceLight,
  },
  rehabBadge: {
    backgroundColor: Colors.rehabGlow,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '800',
  },
  catalogText: {
    color: Colors.textSecondary,
  },
  rehabText: {
    color: Colors.rehab,
  },
  deleteBtn: {
    padding: 4,
  },
  cueRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.surfaceLight,
    padding: 8,
    borderRadius: 6,
    marginVertical: 6,
  },
  cueText: {
    flex: 1,
    color: Colors.rehab,
    fontSize: 12,
    fontStyle: 'italic',
    lineHeight: 16,
  },
  tempoRow: {
    marginBottom: 6,
  },
  tempoText: {
    color: Colors.textMuted,
    fontSize: 11,
    fontWeight: '600',
  },
  columnHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    marginTop: 4,
  },
  columnLabel: {
    color: Colors.textMuted,
    fontSize: 10,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  addSetBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surfaceLight,
    borderRadius: 8,
    paddingVertical: 10,
    marginTop: 10,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
  },
  addSetText: {
    color: Colors.accent,
    fontSize: 13,
    fontWeight: '700',
  },
});
