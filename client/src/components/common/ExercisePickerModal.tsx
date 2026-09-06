import React, { useMemo } from 'react';
import {
  Modal,
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Exercise } from '../../types';
import { Colors } from '../../theme/colors';
import ExerciseSearchList from '../catalog/ExerciseSearchList';
import rawExercises from '../../assets/data/exercises.json';

interface ExercisePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectExercise: (exercise: Exercise) => void;
}

export default function ExercisePickerModal({
  isOpen,
  onClose,
  onSelectExercise,
}: ExercisePickerModalProps) {
  const exercises: Exercise[] = useMemo(() => {
    return Array.isArray(rawExercises)
      ? (rawExercises as unknown as Exercise[])
      : (rawExercises as any).exercises || [];
  }, []);

  const handleSelect = (exerciseId: string) => {
    const selected = exercises.find((ex) => ex.id === exerciseId);
    if (selected) {
      onSelectExercise(selected);
      onClose();
    }
  };

  return (
    <Modal
      visible={isOpen}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <View style={styles.titleBlock}>
            <Text style={styles.title}>Select Exercise</Text>
            <Text style={styles.subtitle}>Choose a movement to add to your workout</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Ionicons name="close" size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
        </View>
        <View style={styles.searchContainer}>
          <ExerciseSearchList
            exercises={exercises}
            onSelectExercise={handleSelect}
          />
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
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
  title: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
  },
  subtitle: {
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
  searchContainer: {
    flex: 1,
  },
});
