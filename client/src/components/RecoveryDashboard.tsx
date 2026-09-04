import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { MuscleRecoveryState } from '../types';

interface RecoveryDashboardProps {
  recoveryData: MuscleRecoveryState[];
}

function getRecoveryStatus(percentage: number) {
  if (percentage < 40) {
    return { label: 'Fatigued / Rest Required', color: '#EF4444' };
  }
  if (percentage <= 75) {
    return { label: 'Recovering', color: '#F59E0B' };
  }
  return { label: 'Ready to Train', color: '#22C55E' };
}

export default function RecoveryDashboard({ recoveryData }: RecoveryDashboardProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Muscle Recovery</Text>
      <View style={styles.grid}>
        {recoveryData.map((muscle) => {
          const percentage = Math.max(0, Math.min(100, muscle.recovery_percentage));
          const status = getRecoveryStatus(muscle.recovery_percentage);
          return (
            <View key={muscle.muscle_group} style={[styles.card, { borderColor: status.color }]}>
              <Text style={styles.muscleName}>{muscle.muscle_group}</Text>
              <Text style={styles.percentage}>{muscle.recovery_percentage}%</Text>
              <View style={styles.progressTrack}>
                <View style={[styles.progressBar, { width: `${percentage}%`, backgroundColor: status.color }]} />
              </View>
              <Text style={[styles.status, { color: status.color }]}>{status.label}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#F8FAFC' },
  title: { marginBottom: 14, fontSize: 22, fontWeight: '700', color: '#0F172A' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  card: { width: '48%', minHeight: 142, marginBottom: 12, padding: 14, borderWidth: 2, borderRadius: 12, backgroundColor: '#FFFFFF' },
  muscleName: { textTransform: 'capitalize', fontSize: 16, fontWeight: '700', color: '#1E293B' },
  percentage: { marginTop: 8, fontSize: 24, fontWeight: '700', color: '#0F172A' },
  progressTrack: { height: 8, marginTop: 10, overflow: 'hidden', borderRadius: 4, backgroundColor: '#E2E8F0' },
  progressBar: { height: '100%', borderRadius: 4 },
  status: { marginTop: 8, fontSize: 12, fontWeight: '600' },
});
