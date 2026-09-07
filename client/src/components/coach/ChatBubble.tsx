import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import { ChatMessage } from '../../types';
import { Colors } from '../../theme/colors';
import WorkoutProposalCard from './WorkoutProposalCard';

export interface ChatBubbleProps {
  message: ChatMessage;
  onAcceptProposal: (messageId: string) => void;
  onDeclineProposal: (messageId: string) => void;
}

export default function ChatBubble({ message, onAcceptProposal, onDeclineProposal }: ChatBubbleProps) {
  const isUser = message.sender === 'user';
  const cleanText = message.text.replace(/<!-- WORKOUT_PAYLOAD_START -->[\s\S]*?<!-- WORKOUT_PAYLOAD_END -->/g, '').trim();

  return (
    <View style={[styles.row, isUser ? styles.rowUser : styles.rowAssistant]}>
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant]}>
        {message.routing_class === 'CLASS_A_INJURY' ? <View style={styles.clinicalTag}><Text style={styles.clinicalTagText}>CLINICAL TRIAGE GUIDANCE</Text></View> : null}
        {isUser ? <Text style={styles.userText}>{message.text}</Text> : <Markdown style={markdownStyles}>{cleanText}</Markdown>}
        {message.proposal ? <WorkoutProposalCard proposal={message.proposal} status={message.proposalStatus ?? 'pending'} onAccept={() => onAcceptProposal(message.id)} onDecline={() => onDeclineProposal(message.id)} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { marginVertical: 6, flexDirection: 'row' },
  rowUser: { justifyContent: 'flex-end' },
  rowAssistant: { justifyContent: 'flex-start' },
  bubble: { maxWidth: '90%', padding: 14, borderRadius: 16 },
  bubbleUser: { backgroundColor: Colors.accent, borderBottomRightRadius: 2 },
  bubbleAssistant: { backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.surfaceBorder, borderBottomLeftRadius: 2 },
  userText: { color: '#FFFFFF', fontSize: 15, lineHeight: 21 },
  clinicalTag: { backgroundColor: Colors.rehabGlow, alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4, marginBottom: 8 },
  clinicalTagText: { color: Colors.rehab, fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },
});

const markdownStyles = {
  body: { color: Colors.textPrimary, fontSize: 15, lineHeight: 22 },
  heading1: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700' as const, marginVertical: 6 },
  heading2: { color: Colors.textPrimary, fontSize: 16, fontWeight: '700' as const, marginVertical: 4 },
  strong: { color: '#FFFFFF', fontWeight: '700' as const },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { color: Colors.textPrimary, marginVertical: 2 },
  paragraph: { marginTop: 0, marginBottom: 8 },
};
