import React from 'react';
import {
  Image,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Exercise } from '../types';

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
  if (exercise == null) {
    return (
      <Modal visible={isOpen} animationType="slide" onRequestClose={onClose}>
        <View style={styles.emptyModal}>
          <TouchableOpacity accessibilityRole="button" onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeText}>×</Text>
          </TouchableOpacity>
          <Text style={styles.emptyText}>No exercise selected.</Text>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={isOpen} animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalContainer}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Close exercise details" onPress={onClose} style={styles.closeButton}>
          <Text style={styles.closeText}>×</Text>
        </TouchableOpacity>
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.title}>{exercise.name}</Text>
          <View style={styles.equipmentBadge}>
            <Text style={styles.equipmentText}>{exercise.equipment}</Text>
          </View>
          <Text style={styles.sectionTitle}>Primary muscles</Text>
          <Text style={styles.bodyText}>{exercise.primary_muscles.join(', ')}</Text>
          <Text style={styles.sectionTitle}>Instructions</Text>
          {exercise.instructions.map((instruction, index) => (
            <Text key={`${exercise.id}-instruction-${index}`} style={styles.instruction}>
              {index + 1}. {instruction}
            </Text>
          ))}
          <Text style={styles.sectionTitle}>Exercise images</Text>
          {exercise.images.map((image, index) => (
            <Image
              key={`${exercise.id}-image-${index}`}
              source={{ uri: image }}
              accessibilityLabel={`${exercise.name} image ${index + 1}`}
              style={styles.exerciseImage}
              resizeMode="contain"
            />
          ))}
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { padding: 20, paddingTop: 64, paddingBottom: 32 },
  emptyModal: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F8FAFC' },
  emptyText: { color: '#475569', fontSize: 16 },
  closeButton: { position: 'absolute', zIndex: 1, top: 16, right: 16, width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 21, backgroundColor: '#E2E8F0' },
  closeText: { fontSize: 28, lineHeight: 30, color: '#0F172A' },
  title: { marginBottom: 12, fontSize: 26, fontWeight: '700', color: '#0F172A' },
  equipmentBadge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, backgroundColor: '#E0E7FF' },
  equipmentText: { color: '#3730A3', fontWeight: '600' },
  sectionTitle: { marginTop: 22, marginBottom: 8, fontSize: 18, fontWeight: '700', color: '#1E293B' },
  bodyText: { fontSize: 16, lineHeight: 24, color: '#475569' },
  instruction: { marginBottom: 10, fontSize: 16, lineHeight: 24, color: '#334155' },
  exerciseImage: { width: '100%', height: 220, marginBottom: 12, borderRadius: 12, backgroundColor: '#E2E8F0' },
});
