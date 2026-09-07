// src/components/workout/RoutineBuilderModal.tsx
import React, { useState } from 'react';
import {
  Modal,
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Routine, RoutineExercise, Exercise } from '../../types';
import { Colors } from '../../theme/colors';
import ExercisePickerModal from '../common/ExercisePickerModal';

interface RoutineBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveRoutine: (routine: Routine) => void;
}

export default function RoutineBuilderModal({
  isOpen,
  onClose,
  onSaveRoutine,
}: RoutineBuilderModalProps) {
  const [title, setTitle] = useState('');
  const [targetFocus, setTargetFocus] = useState('');
  const [estimatedMinutes, setEstimatedMinutes] = useState('45');
  const [exercises, setExercises] = useState<RoutineExercise[]>([]);
  const [isPickerOpen, setIsPickerOpen] = useState(false);

  const handleSelectExercise = (exercise: Exercise) => {
    const newEx: RoutineExercise = {
      name: exercise.name,
      catalogId: exercise.id,
      existsInCatalog: true,
      category: exercise.mechanics === 'compound' ? 'compound' : 'accessory',
      targetSets: 3,
      targetReps: '10',
    };
    setExercises((prev) => [...prev, newEx]);
  };

  const handleUpdateExercise = (
    index: number,
    field: 'targetSets' | 'targetReps',
    value: any
  ) => {
    setExercises((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleDeleteExercise = (index: number) => {
    setExercises((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSave = () => {
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      Alert.alert('Missing Title', 'Please enter a title for your routine.');
      return;
    }
    if (exercises.length === 0) {
      Alert.alert('Empty Routine', 'Please add at least one exercise to your routine.');
      return;
    }
    const newRoutine: Routine = {
      id: `custom_${Date.now()}`,
      title: cleanTitle,
      targetFocus: targetFocus.trim() || 'General Fitness',
      estimatedMinutes: Number(estimatedMinutes) || 45,
      createdAt: Date.now(),
      isAiGenerated: false,
      exercises,
    };
    onSaveRoutine(newRoutine);
    resetForm();
    onClose();
  };

  const resetForm = () => {
    setTitle('');
    setTargetFocus('');
    setEstimatedMinutes('45');
    setExercises([]);
  };

  return (
    <Modal
      visible={isOpen}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.container}
        >
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.headerBtn}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>New Routine</Text>
            <TouchableOpacity
              onPress={handleSave}
              style={[styles.headerBtn, (!title.trim() || exercises.length === 0) && styles.saveBtnDisabled]}
              disabled={!title.trim() || exercises.length === 0}
            >
              <Text style={styles.saveText}>Save</Text>
            </TouchableOpacity>
          </View>
          <FlatList
            data={exercises}
            keyExtractor={(_, idx) => `routine-ex-${idx}`}
            contentContainerStyle={styles.scrollList}
            ListHeaderComponent={
              <View style={styles.metadataSection}>
                <Text style={styles.fieldLabel}>ROUTINE NAME *</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="e.g., Push Day (Chest & Triceps)"
                  placeholderTextColor={Colors.textMuted}
                  value={title}
                  onChangeText={setTitle}
                />
                <View style={styles.rowFields}>
                  <View style={{ flex: 2, marginRight: 10 }}>
                    <Text style={styles.fieldLabel}>TARGET FOCUS</Text>
                    <TextInput
                      style={styles.textInput}
                      placeholder="e.g., Hypertrophy"
                      placeholderTextColor={Colors.textMuted}
                      value={targetFocus}
                      onChangeText={setTargetFocus}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.fieldLabel}>EST. MIN</Text>
                    <TextInput
                      style={styles.textInput}
                      placeholder="45"
                      placeholderTextColor={Colors.textMuted}
                      keyboardType="numeric"
                      value={estimatedMinutes}
                      onChangeText={setEstimatedMinutes}
                    />
                  </View>
                </View>
                <Text style={[styles.fieldLabel, { marginTop: 16, marginBottom: 8 }]}>
                  EXERCISES ({exercises.length})
                </Text>
              </View>
            }
            renderItem={({ item, index }) => (
              <View style={styles.exerciseCard}>
                <View style={styles.cardTopRow}>
                  <Text style={styles.cardExerciseName} numberOfLines={1}>
                    {index + 1}. {item.name}
                  </Text>
                  <TouchableOpacity onPress={() => handleDeleteExercise(index)}>
                    <Ionicons name="trash-outline" size={16} color={Colors.textMuted} />
                  </TouchableOpacity>
                </View>
                <View style={styles.configRow}>
                  <View style={styles.stepperContainer}>
                    <Text style={styles.configLabel}>Sets:</Text>
                    <TouchableOpacity
                      style={styles.stepBtn}
                      onPress={() => handleUpdateExercise(index, 'targetSets', Math.max(1, item.targetSets - 1))}
                    >
                      <Ionicons name="remove" size={14} color={Colors.textPrimary} />
                    </TouchableOpacity>
                    <Text style={styles.stepperValue}>{item.targetSets}</Text>
                    <TouchableOpacity
                      style={styles.stepBtn}
                      onPress={() => handleUpdateExercise(index, 'targetSets', item.targetSets + 1)}
                    >
                      <Ionicons name="add" size={14} color={Colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                  <View style={styles.repsInputContainer}>
                    <Text style={styles.configLabel}>Reps:</Text>
                    <TextInput
                      style={styles.repsInput}
                      placeholder="e.g. 10 or 45s hold"
                      placeholderTextColor={Colors.textMuted}
                      value={item.targetReps}
                      onChangeText={(v) => handleUpdateExercise(index, 'targetReps', v)}
                    />
                  </View>
                </View>
              </View>
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
            onSelectExercise={handleSelectExercise}
          />
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    backgroundColor: Colors.surface,
  },
  headerTitle: {
    color: Colors.textPrimary,
    fontSize: 17,
    fontWeight: '800',
  },
  headerBtn: {
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  cancelText: {
    color: Colors.textSecondary,
    fontSize: 15,
  },
  saveText: {
    color: Colors.accent,
    fontSize: 15,
    fontWeight: '800',
  },
  saveBtnDisabled: {
    opacity: 0.35,
  },
  scrollList: {
    padding: 16,
    paddingBottom: 40,
  },
  metadataSection: {
    marginBottom: 8,
  },
  fieldLabel: {
    color: Colors.textMuted,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  textInput: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    borderRadius: 8,
    color: Colors.textPrimary,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    marginBottom: 12,
  },
  rowFields: {
    flexDirection: 'row',
  },
  exerciseCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    padding: 12,
    marginBottom: 10,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardExerciseName: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    paddingRight: 8,
  },
  configRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.surfaceLight,
    padding: 8,
    borderRadius: 8,
  },
  stepperContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  configLabel: {
    color: Colors.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    marginRight: 6,
  },
  stepBtn: {
    width: 26,
    height: 26,
    borderRadius: 4,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
  },
  stepperValue: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '800',
    paddingHorizontal: 8,
  },
  repsInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginLeft: 16,
  },
  repsInput: {
    flex: 1,
    height: 30,
    backgroundColor: Colors.surface,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    color: Colors.textPrimary,
    paddingHorizontal: 8,
    fontSize: 12,
  },
  addExerciseBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: Colors.accent,
    borderRadius: 10,
    paddingVertical: 14,
    marginTop: 6,
  },
  addExerciseBtnText: {
    color: Colors.accent,
    fontSize: 14,
    fontWeight: '700',
  },
});
