import React from 'react';
import {
  Image,
  Modal,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Exercise } from '../../types';
import { Colors } from '../../theme/colors';
import { getExerciseImageSource, getMuscleBadgeColor } from '../../utils/imageResolver';

export interface ExerciseDetailModalProps {
  exercise: Exercise | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ExerciseDetailModal({ exercise, isOpen, onClose }: ExerciseDetailModalProps) {
  if (!exercise) return null;

  const imageSource = getExerciseImageSource(exercise.images?.[0]);
  const primaryMuscles = exercise.primary_muscles ?? [];
  const secondaryMuscles = exercise.secondary_muscles ?? [];

  return (
    <Modal visible={isOpen} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.topBar}>
          <Text style={styles.title} numberOfLines={2}>{exercise.name}</Text>
          <TouchableOpacity accessibilityRole="button" accessibilityLabel="Close modal" onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={Colors.textPrimary} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.badgeRow}>
            <View style={styles.accentBadge}>
              <Ionicons name="fitness-outline" size={14} color={Colors.accent} />
              <Text style={styles.accentBadgeText}>{exercise.equipment.toUpperCase()}</Text>
            </View>
            <View style={styles.surfaceBadge}>
              <Text style={styles.surfaceBadgeText}>{(exercise.mechanics ?? 'GENERAL').toUpperCase()}</Text>
            </View>
          </View>

          {imageSource ? (
            <Image source={imageSource} style={styles.heroImage} resizeMode="cover" />
          ) : (
            <View style={styles.blueprintCard}>
              <Ionicons name="barbell-outline" size={52} color={Colors.accent} />
              <Text style={styles.blueprintTitle}>Movement Blueprint</Text>
              <Text style={styles.blueprintSubtitle}>Visual reference available offline</Text>
            </View>
          )}

          <Text style={styles.sectionTitle}>Target Muscles</Text>
          <View style={styles.pillRow}>
            {primaryMuscles.map((muscle) => (
              <View key={`primary-${muscle}`} style={[styles.musclePill, { borderColor: getMuscleBadgeColor(muscle) }]}>
                <Text style={styles.musclePillText}>{muscle}</Text>
              </View>
            ))}
            {secondaryMuscles.map((muscle) => (
              <View key={`secondary-${muscle}`} style={styles.secondaryPill}>
                <Text style={styles.secondaryPillText}>{muscle}</Text>
              </View>
            ))}
          </View>

          <Text style={styles.sectionTitle}>Execution Guide</Text>
          {exercise.instructions.map((instruction, index) => (
            <View key={`${exercise.id}-step-${index}`} style={styles.instructionCard}>
              <View style={styles.stepBadge}><Text style={styles.stepNumber}>{index + 1}</Text></View>
              <Text style={styles.instructionText}>{instruction}</Text>
            </View>
          ))}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: { flex: 1, backgroundColor: Colors.background },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: Colors.surfaceBorder },
  title: { flex: 1, color: Colors.textPrimary, fontSize: 20, fontWeight: '700', marginRight: 12 },
  closeButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.surfaceLight, alignItems: 'center', justifyContent: 'center' },
  scrollContent: { padding: 16, paddingBottom: 32 },
  badgeRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  accentBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: Colors.accentGlow, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  accentBadgeText: { color: Colors.accent, fontSize: 11, fontWeight: '700' },
  surfaceBadge: { backgroundColor: Colors.surfaceLight, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  surfaceBadgeText: { color: Colors.textSecondary, fontSize: 11, fontWeight: '700' },
  heroImage: { width: '100%', height: 190, borderRadius: 14, backgroundColor: Colors.surface, marginBottom: 20 },
  blueprintCard: { height: 190, borderRadius: 14, backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder, alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  blueprintTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', marginTop: 10 },
  blueprintSubtitle: { color: Colors.textSecondary, fontSize: 13, marginTop: 5 },
  sectionTitle: { color: Colors.textPrimary, fontSize: 17, fontWeight: '700', marginBottom: 10, marginTop: 4 },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  musclePill: { borderWidth: 1, backgroundColor: Colors.surface, borderRadius: 16, paddingHorizontal: 10, paddingVertical: 6 },
  musclePillText: { color: Colors.textPrimary, fontSize: 12, textTransform: 'capitalize' },
  secondaryPill: { borderRadius: 16, backgroundColor: Colors.surfaceLight, paddingHorizontal: 10, paddingVertical: 6 },
  secondaryPillText: { color: Colors.textSecondary, fontSize: 12, textTransform: 'capitalize' },
  instructionCard: { flexDirection: 'row', alignItems: 'flex-start', backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder, borderRadius: 10, padding: 12, marginBottom: 8 },
  stepBadge: { width: 26, height: 26, borderRadius: 13, backgroundColor: Colors.accent, alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  stepNumber: { color: '#FFFFFF', fontWeight: '700' },
  instructionText: { flex: 1, color: Colors.textPrimary, fontSize: 14, lineHeight: 20 },
});
