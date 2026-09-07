import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BackendWorkoutProposal } from '../../types';
import { Colors } from '../../theme/colors';

export interface WorkoutProposalCardProps {
  proposal: BackendWorkoutProposal;
  status: 'pending' | 'accepted' | 'declined';
  onAccept: () => void;
  onDecline: () => void;
}

export default function WorkoutProposalCard({ proposal, status, onAccept, onDecline }: WorkoutProposalCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.badge}><Text style={styles.badgeText}>AI PROPOSED ROUTINE</Text></View>
        <View style={styles.durationRow}><Ionicons name="time-outline" size={13} color={Colors.textSecondary} /><Text style={styles.durationText}>{proposal.estimatedMinutes} min</Text></View>
      </View>
      <Text style={styles.title}>{proposal.title}</Text>
      <Text style={styles.targetFocus}>Focus: {proposal.targetFocus}</Text>

      <View style={styles.itemList}>
        {proposal.items.map((item, index) => (
          <View key={`${item.name}-${index}`} style={styles.itemRow}>
            <View style={styles.itemMeta}>
              <Text style={styles.itemName}>{index + 1}. {item.name}</Text>
              <Text style={styles.itemVolume}>
                {item.sets} sets × {item.reps}
                {item.targetRpe ? ` · RPE ${item.targetRpe}` : ''}
                {item.tempo ? ` · Tempo: ${item.tempo}` : ''}
              </Text>
              {item.coachingCue ? <View style={styles.cueRow}><Ionicons name="medkit-outline" size={11} color={Colors.rehab} /><Text style={styles.itemCue}>{item.coachingCue}</Text></View> : null}
            </View>
            <View style={[styles.typeBadge, item.existsInCatalog ? styles.catalogBadge : styles.rehabBadge]}>
              <Text style={[styles.typeBadgeText, item.existsInCatalog ? styles.catalogText : styles.rehabText]}>{item.existsInCatalog ? 'CATALOG' : 'CUSTOM REHAB'}</Text>
            </View>
          </View>
        ))}
      </View>

      {status === 'pending' ? (
        <View style={styles.actionRow}>
          <TouchableOpacity style={[styles.button, styles.declineButton]} onPress={onDecline}><Text style={styles.declineText}>Dismiss</Text></TouchableOpacity>
          <TouchableOpacity style={[styles.button, styles.acceptButton]} onPress={onAccept}><Ionicons name="add-circle-outline" size={18} color="#FFFFFF" /><Text style={styles.acceptText}>Save to Routines</Text></TouchableOpacity>
        </View>
      ) : (
        <View style={styles.finalizedBar}>
          {status === 'accepted' ? <Ionicons name="checkmark-circle" size={16} color={Colors.completed} /> : null}
          <Text style={status === 'accepted' ? styles.acceptedNotice : styles.declinedNotice}>{status === 'accepted' ? 'Routine saved to library' : 'Proposal dismissed'}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: Colors.surfaceLight, borderRadius: 14, borderWidth: 1, borderColor: Colors.surfaceBorder, padding: 16, marginVertical: 10 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  badge: { backgroundColor: Colors.accentGlow, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  badgeText: { color: Colors.accent, fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  durationRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  durationText: { color: Colors.textSecondary, fontSize: 12, fontWeight: '600' },
  title: { color: Colors.textPrimary, fontSize: 18, fontWeight: '800', marginTop: 10 },
  targetFocus: { color: Colors.textMuted, fontSize: 13, marginBottom: 12 },
  itemList: { borderTopWidth: 1, borderTopColor: Colors.surfaceBorder, paddingTop: 12 },
  itemRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
  itemMeta: { flex: 1, paddingRight: 10 },
  itemName: { color: Colors.textPrimary, fontSize: 14, fontWeight: '700' },
  itemVolume: { color: Colors.textSecondary, fontSize: 12, marginTop: 2 },
  cueRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 4, marginTop: 3 },
  itemCue: { flex: 1, color: Colors.rehab, fontSize: 11, fontStyle: 'italic', lineHeight: 15 },
  typeBadge: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 5 },
  catalogBadge: { backgroundColor: Colors.surfaceBorder },
  rehabBadge: { backgroundColor: Colors.rehabGlow },
  typeBadgeText: { fontSize: 9, fontWeight: '800' },
  catalogText: { color: Colors.textSecondary },
  rehabText: { color: Colors.rehab },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  button: { flex: 1, height: 42, borderRadius: 8, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6 },
  declineButton: { backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder },
  acceptButton: { backgroundColor: Colors.accent },
  declineText: { color: Colors.textSecondary, fontWeight: '600', fontSize: 13 },
  acceptText: { color: '#FFFFFF', fontWeight: '700', fontSize: 13 },
  finalizedBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 8, paddingVertical: 6, backgroundColor: Colors.surface, borderRadius: 6 },
  acceptedNotice: { color: Colors.completed, fontSize: 12, fontWeight: '700' },
  declinedNotice: { color: Colors.textMuted, fontSize: 12, fontWeight: '600' },
});
