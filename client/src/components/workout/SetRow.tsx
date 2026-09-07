import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SetLog } from '../../types';
import { Colors } from '../../theme/colors';

interface SetRowProps {
  set: SetLog;
  onUpdate: (field: 'weight_kg' | 'actual_reps' | 'completed', value: any) => void;
  onDelete?: () => void;
}

export default function SetRow({ set, onUpdate, onDelete }: SetRowProps) {
  const isTimeBased = /(s|sec|hold)/i.test(set.target_reps || '');

  return (
    <View style={[styles.container, set.completed && styles.containerCompleted]}>
      <Text style={[styles.colIndex, set.completed && styles.textCompleted]}>
        {set.set_number}
      </Text>
      <Text style={styles.colTarget} numberOfLines={1}>
        {set.target_reps}
      </Text>
      <TextInput
        style={[styles.input, set.completed && styles.inputCompleted]}
        keyboardType="numeric"
        selectTextOnFocus
        placeholder="kg"
        placeholderTextColor={Colors.textMuted}
        value={set.weight_kg === 0 ? '' : String(set.weight_kg)}
        onChangeText={(v) => onUpdate('weight_kg', v === '' ? 0 : Number(v))}
      />
      <TextInput
        style={[styles.input, set.completed && styles.inputCompleted]}
        keyboardType="numeric"
        selectTextOnFocus
        placeholder={isTimeBased ? 'secs' : 'reps'}
        placeholderTextColor={Colors.textMuted}
        value={set.actual_reps === 0 ? '' : String(set.actual_reps)}
        onChangeText={(v) => onUpdate('actual_reps', v === '' ? 0 : Number(v))}
      />
      <TouchableOpacity
        style={[styles.checkBtn, set.completed && styles.checkBtnActive]}
        onPress={() => onUpdate('completed', !set.completed)}
        activeOpacity={0.7}
      >
        <Ionicons
          name={set.completed ? 'checkmark' : 'remove-outline'}
          size={18}
          color={set.completed ? '#FFFFFF' : Colors.textMuted}
        />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 48,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    paddingHorizontal: 8,
  },
  containerCompleted: {
    backgroundColor: Colors.completedBg,
  },
  colIndex: {
    width: 32,
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  textCompleted: {
    color: Colors.completed,
  },
  colTarget: {
    width: 78,
    color: Colors.textMuted,
    fontSize: 11,
    textAlign: 'center',
    fontWeight: '600',
    paddingHorizontal: 2,
  },
  input: {
    flex: 1,
    height: 34,
    marginHorizontal: 4,
    backgroundColor: Colors.surfaceLight,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    borderRadius: 6,
    color: Colors.textPrimary,
    textAlign: 'center',
    fontSize: 14,
    fontWeight: '700',
  },
  inputCompleted: {
    borderColor: 'rgba(34, 197, 94, 0.4)',
  },
  checkBtn: {
    width: 38,
    height: 34,
    marginLeft: 6,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkBtnActive: {
    backgroundColor: Colors.completed,
    borderColor: Colors.completed,
  },
});
