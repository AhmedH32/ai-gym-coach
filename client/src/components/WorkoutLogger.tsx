import React from 'react';
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SetEntry } from '../types';

interface WorkoutLoggerProps {
  exerciseName: string;
  sets: SetEntry[];
  onUpdateSet: (
    setNumber: number,
    field: 'reps' | 'weight_kg' | 'completed',
    value: any,
  ) => void;
  onAddSet: () => void;
}

export default function WorkoutLogger({
  exerciseName,
  sets,
  onUpdateSet,
  onAddSet,
}: WorkoutLoggerProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{exerciseName}</Text>
      <View style={styles.headerRow}>
        <Text style={[styles.headerText, styles.setColumn]}>Set #</Text>
        <Text style={[styles.headerText, styles.inputColumn]}>Weight (kg)</Text>
        <Text style={[styles.headerText, styles.inputColumn]}>Reps</Text>
        <Text style={[styles.headerText, styles.completedColumn]}>Completed</Text>
      </View>
      {sets.map((set) => (
        <View
          key={set.set_number}
          style={[styles.setRow, set.completed && styles.completedRow]}
        >
          <Text style={styles.setColumn}>{set.set_number}</Text>
          <TextInput
            style={styles.numberInput}
            keyboardType="numeric"
            value={String(set.weight_kg)}
            onChangeText={(value) =>
              onUpdateSet(set.set_number, 'weight_kg', value === '' ? 0 : Number(value))
            }
          />
          <TextInput
            style={styles.numberInput}
            keyboardType="numeric"
            value={String(set.reps)}
            onChangeText={(value) =>
              onUpdateSet(set.set_number, 'reps', value === '' ? 0 : Number(value))
            }
          />
          <TouchableOpacity
            accessibilityRole="checkbox"
            accessibilityState={{ checked: set.completed }}
            onPress={() => onUpdateSet(set.set_number, 'completed', !set.completed)}
            style={[styles.completedButton, set.completed && styles.completedButtonActive]}
          >
            <Text style={styles.completedText}>{set.completed ? '✓' : '○'}</Text>
          </TouchableOpacity>
        </View>
      ))}
      <TouchableOpacity accessibilityRole="button" onPress={onAddSet} style={styles.addButton}>
        <Text style={styles.addButtonText}>+ Add Set</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#F8FAFC' },
  title: { marginBottom: 16, fontSize: 20, fontWeight: '700', color: '#0F172A' },
  headerRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  headerText: { fontSize: 12, fontWeight: '700', color: '#64748B' },
  setColumn: { width: 48 },
  inputColumn: { flex: 1, textAlign: 'center' },
  completedColumn: { width: 76, textAlign: 'center' },
  setRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 58,
    marginBottom: 8,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  completedRow: { backgroundColor: '#DCFCE7' },
  numberInput: {
    flex: 1,
    height: 40,
    marginHorizontal: 5,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 8,
    textAlign: 'center',
    backgroundColor: '#FFFFFF',
    color: '#0F172A',
  },
  completedButton: {
    width: 42,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#94A3B8',
  },
  completedButtonActive: { backgroundColor: '#16A34A', borderColor: '#16A34A' },
  completedText: { fontSize: 20, color: '#FFFFFF', fontWeight: '700' },
  addButton: { alignItems: 'center', paddingVertical: 13, marginTop: 8, borderRadius: 10, backgroundColor: '#2563EB' },
  addButtonText: { color: '#FFFFFF', fontWeight: '700' },
});
