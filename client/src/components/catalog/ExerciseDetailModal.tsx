// client/src/components/catalog/ExerciseDetailModal.tsx
import React from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Image,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Exercise } from '../../types';
import { Colors } from '../../theme/colors';
import { getExerciseImageSource, getMuscleBadgeColor } from '../../utils/imageResolver';

interface ExerciseDetailModalProps {
  exercise: Exercise | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ExerciseDetailModal({
  exercise,
  isOpen,
  onClose,
}: ExerciseDetailModalProps) {
  if (!exercise) return null;

  const images = exercise.images || [];
  const imageSource = images.length > 0 ? getExerciseImageSource(images[0]) : null;
  const primaryMuscles = exercise.primary_muscles || (exercise as any).primaryMuscles || [];
  const secondaryMuscles = exercise.secondary_muscles || (exercise as any).secondaryMuscles || [];
  const instructions = exercise.instructions || [];
  const mechanics = exercise.mechanics || (exercise as any).mechanic;
  const equipment = exercise.equipment || 'body only';

  return (
    <Modal
      visible={isOpen}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.topBar}>
          <View style={styles.titleBlock}>
            <Text style={styles.title} numberOfLines={2}>{exercise.name}</Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Close modal"
            onPress={onClose}
            style={styles.closeBtn}
          >
            <Ionicons name="close" size={24} color={Colors.textPrimary} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.badgeRow}>
            <View style={styles.equipmentBadge}>
              <Ionicons name="fitness-outline" size={14} color={Colors.accent} style={{ marginRight: 4 }} />
              <Text style={styles.equipmentText}>{equipment.toUpperCase()}</Text>
            </View>
            {mechanics ? (
              <View style={styles.mechanicsBadge}>
                <Text style={styles.mechanicsText}>{String(mechanics).toUpperCase()}</Text>
              </View>
            ) : null}
          </View>

          <View style={styles.visualContainer}>
            {imageSource ? (
              <Image source={imageSource} style={styles.heroImage} resizeMode="contain" />
            ) : (
              <View style={styles.blueprintCard}>
                <View style={styles.blueprintIconCircle}>
                  <Ionicons name="barbell-outline" size={36} color={Colors.accent} />
                </View>
                <Text style={styles.blueprintTitle}>Movement Blueprint</Text>
                <Text style={styles.blueprintSubtitle}>Form & execution specification</Text>
              </View>
            )}
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Target Muscles</Text>
            <View style={styles.pillContainer}>
              {primaryMuscles.map((muscle: string) => (
                <View
                  key={`primary-${muscle}`}
                  style={[styles.musclePill, { borderColor: getMuscleBadgeColor(muscle) }]}
                >
                  <Text style={[styles.musclePillText, { color: getMuscleBadgeColor(muscle) }]}>
                    • {muscle.toUpperCase()} (PRIMARY)
                  </Text>
                </View>
              ))}
              {secondaryMuscles.map((muscle: string) => (
                <View key={`secondary-${muscle}`} style={styles.secondaryPill}>
                  <Text style={styles.secondaryPillText}>{muscle.toUpperCase()}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Execution Guide</Text>
            {instructions.length > 0 ? (
              instructions.map((instruction: string, index: number) => (
                <View key={`step-${index}`} style={styles.stepCard}>
                  <View style={styles.stepNumberBadge}>
                    <Text style={styles.stepNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.stepText}>{instruction}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.emptyText}>No written instructions available for this movement.</Text>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: { flex: 1, backgroundColor: Colors.background },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.surfaceBorder,
    backgroundColor: Colors.surface,
  },
  titleBlock: { flex: 1, paddingRight: 12 },
  title: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: { padding: 20, paddingBottom: 48 },
  badgeRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  equipmentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accentGlow,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  equipmentText: { color: Colors.accent, fontWeight: '700', fontSize: 11, letterSpacing: 0.5 },
  mechanicsBadge: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
  },
  mechanicsText: { color: Colors.textSecondary, fontWeight: '700', fontSize: 11, letterSpacing: 0.5 },
  visualContainer: { marginBottom: 20 },
  heroImage: { width: '100%', height: 220, borderRadius: 12, backgroundColor: Colors.surface },
  blueprintCard: {
    height: 160,
    borderRadius: 12,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  blueprintIconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.accentGlow,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  blueprintTitle: { color: Colors.textPrimary, fontSize: 16, fontWeight: '700' },
  blueprintSubtitle: { color: Colors.textMuted, fontSize: 12, marginTop: 2 },
  section: { marginBottom: 24 },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  pillContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  musclePill: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  musclePillText: { fontSize: 11, fontWeight: '700' },
  secondaryPill: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  secondaryPillText: { color: Colors.textMuted, fontSize: 11, fontWeight: '600' },
  stepCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
  },
  stepNumberBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: Colors.accentGlow,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  stepNumberText: { color: Colors.accent, fontSize: 12, fontWeight: '700' },
  stepText: { flex: 1, color: Colors.textPrimary, fontSize: 14, lineHeight: 21 },
  emptyText: { color: Colors.textMuted, fontSize: 13 },
});