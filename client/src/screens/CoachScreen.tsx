import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, KeyboardAvoidingView, Platform, SafeAreaView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ChatMessage, Routine } from '../types';
import { StorageService } from '../storage/storageService';
import { postCoachQuery } from '../api/coachApi';
import { Colors } from '../theme/colors';
import ChatBubble from '../components/coach/ChatBubble';

export default function CoachScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef<FlatList<ChatMessage>>(null);

  useEffect(() => {
    let mounted = true;
    StorageService.getChatHistory().then((history) => {
      if (!mounted) return;
      setMessages(history.length > 0 ? history : [{ id: 'welcome', sender: 'assistant', timestamp: Date.now(), text: "Welcome to your AI Strength & Clinical Coach. Ask about lifting mechanics, fatigue management, or report an injury or symptom and I'll prescribe a pain-sparing session." }]);
    });
    return () => { mounted = false; };
  }, []);

  const handleSend = async () => {
    const query = inputText.trim();
    if (!query || loading) return;
    const userMessage: ChatMessage = { id: `${Date.now()}`, sender: 'user', timestamp: Date.now(), text: query };
    setMessages((previous) => [...previous, userMessage]);
    setInputText('');
    setLoading(true);
    await StorageService.saveChatMessage(userMessage);

    try {
      const response = await postCoachQuery(query);
      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-assistant`,
        sender: 'assistant',
        timestamp: Date.now(),
        text: response.chat_text,
        routing_class: response.routing_class,
        proposal: response.workout_proposal,
        proposalStatus: response.workout_proposal ? 'pending' : undefined,
      };
      setMessages((previous) => [...previous, assistantMessage]);
      await StorageService.saveChatMessage(assistantMessage);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to contact inference gateway.';
      const errorMessage: ChatMessage = { id: `${Date.now()}-error`, sender: 'assistant', timestamp: Date.now(), text: `Error: ${message}\n\nPlease verify that your backend ngrok tunnel is live and reachable.` };
      setMessages((previous) => [...previous, errorMessage]);
      await StorageService.saveChatMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptProposal = async (messageId: string) => {
    const targetMessage = messages.find((message) => message.id === messageId);
    if (!targetMessage?.proposal) return;
    const newRoutine: Routine = {
      id: `ai_${Date.now()}`,
      title: targetMessage.proposal.title,
      targetFocus: targetMessage.proposal.targetFocus,
      estimatedMinutes: targetMessage.proposal.estimatedMinutes,
      createdAt: Date.now(),
      isAiGenerated: true,
      routingClass: targetMessage.routing_class,
      exercises: targetMessage.proposal.items.map((item) => ({
        name: item.name,
        catalogId: item.catalogId ?? null,
        existsInCatalog: item.existsInCatalog,
        category: item.category,
        targetSets: item.sets,
        targetReps: item.reps,
        targetRpe: item.targetRpe ?? undefined,
        tempo: item.tempo ?? undefined,
        coachingCue: item.coachingCue ?? undefined,
        customInstructions: item.customInstructions ?? undefined,
      })),
    };
    await StorageService.saveRoutine(newRoutine);
    await StorageService.updateProposalStatus(messageId, 'accepted');
    setMessages((previous) => previous.map((message) => message.id === messageId ? { ...message, proposalStatus: 'accepted' } : message));
  };

  const handleDeclineProposal = async (messageId: string) => {
    await StorageService.updateProposalStatus(messageId, 'declined');
    setMessages((previous) => previous.map((message) => message.id === messageId ? { ...message, proposalStatus: 'declined' } : message));
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => <ChatBubble message={item} onAcceptProposal={handleAcceptProposal} onDeclineProposal={handleDeclineProposal} />}
        />
        {loading ? <View style={styles.loadingBar}><ActivityIndicator size="small" color={Colors.accent} /><Text style={styles.loadingText}>Synthesizing biomechanical & clinical guidance...</Text></View> : null}
        <View style={styles.inputBar}>
          <TextInput style={styles.textInput} placeholder="Ask coach or describe injury..." placeholderTextColor={Colors.textMuted} value={inputText} onChangeText={setInputText} multiline maxLength={500} />
          <TouchableOpacity style={[styles.sendButton, (!inputText.trim() || loading) && styles.sendButtonDisabled]} onPress={handleSend} disabled={!inputText.trim() || loading} accessibilityLabel="Send message">
            <Ionicons name="arrow-up" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.background },
  container: { flex: 1 },
  listContent: { padding: 16, paddingBottom: 20 },
  loadingBar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 8, backgroundColor: Colors.surface, borderTopWidth: 1, borderTopColor: Colors.surfaceBorder },
  loadingText: { color: Colors.textSecondary, fontSize: 12, fontWeight: '600', marginLeft: 8 },
  inputBar: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 12, paddingVertical: 10, backgroundColor: Colors.surface, borderTopWidth: 1, borderTopColor: Colors.surfaceBorder, gap: 8 },
  textInput: { flex: 1, minHeight: 40, maxHeight: 100, backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.surfaceBorder, borderRadius: 20, color: Colors.textPrimary, paddingHorizontal: 16, paddingTop: 10, paddingBottom: 10, fontSize: 14 },
  sendButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.accent, justifyContent: 'center', alignItems: 'center' },
  sendButtonDisabled: { backgroundColor: Colors.surfaceBorder, opacity: 0.6 },
});
