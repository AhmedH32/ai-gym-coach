import AsyncStorage from '@react-native-async-storage/async-storage';

import type {
  ChatMessage,
  Routine,
  WorkoutExerciseSession,
  WorkoutHistoryEntry,
} from '../types';

const STORAGE_KEYS = {
  ROUTINES: '@ai_gym_routines',
  HISTORY: '@ai_gym_history',
  ACTIVE_SESSION: '@ai_gym_active_session',
  CHAT_HISTORY: '@ai_gym_chat_history',
} as const;

export interface ActiveSessionState {
  routineTitle: string;
  routineId?: string;
  startTime: number;
  exercises: WorkoutExerciseSession[];
}

export const StorageService = {
  async getRoutines(): Promise<Routine[]> {
    try {
      const storedRoutines = await AsyncStorage.getItem(STORAGE_KEYS.ROUTINES);

      if (!storedRoutines) {
        return [];
      }

      const routines = JSON.parse(storedRoutines);
      return Array.isArray(routines) ? routines : [];
    } catch (error) {
      console.error('Failed to get routines from storage:', error);
      return [];
    }
  },

  async saveRoutine(routine: Routine): Promise<void> {
    try {
      const routines = await StorageService.getRoutines();
      const existingRoutineIndex = routines.findIndex(
        (existingRoutine) => existingRoutine.id === routine.id,
      );

      if (existingRoutineIndex >= 0) {
        routines[existingRoutineIndex] = routine;
      } else {
        routines.unshift(routine);
      }

      await AsyncStorage.setItem(STORAGE_KEYS.ROUTINES, JSON.stringify(routines));
    } catch (error) {
      console.error('Failed to save routine to storage:', error);
    }
  },

  async deleteRoutine(routineId: string): Promise<void> {
    try {
      const routines = await StorageService.getRoutines();
      const remainingRoutines = routines.filter((routine) => routine.id !== routineId);
      await AsyncStorage.setItem(
        STORAGE_KEYS.ROUTINES,
        JSON.stringify(remainingRoutines),
      );
    } catch (error) {
      console.error('Failed to delete routine from storage:', error);
    }
  },

  async getActiveSession(): Promise<ActiveSessionState | null> {
    try {
      const storedSession = await AsyncStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);

      if (!storedSession) {
        return null;
      }

      return JSON.parse(storedSession) as ActiveSessionState;
    } catch (error) {
      console.error('Failed to get active session from storage:', error);
      return null;
    }
  },

  async saveActiveSession(session: ActiveSessionState | null): Promise<void> {
    try {
      if (session === null) {
        await AsyncStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
        return;
      }

      await AsyncStorage.setItem(
        STORAGE_KEYS.ACTIVE_SESSION,
        JSON.stringify(session),
      );
    } catch (error) {
      console.error('Failed to save active session to storage:', error);
    }
  },

  async getHistory(): Promise<WorkoutHistoryEntry[]> {
    try {
      const storedHistory = await AsyncStorage.getItem(STORAGE_KEYS.HISTORY);

      if (!storedHistory) {
        return [];
      }

      const history = JSON.parse(storedHistory);
      return Array.isArray(history) ? history : [];
    } catch (error) {
      console.error('Failed to get workout history from storage:', error);
      return [];
    }
  },

  async logCompletedWorkout(entry: WorkoutHistoryEntry): Promise<void> {
    try {
      const history = await StorageService.getHistory();
      history.unshift(entry);
      await AsyncStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(history));
      await AsyncStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
    } catch (error) {
      console.error('Failed to log completed workout to storage:', error);
    }
  },

  async getChatHistory(): Promise<ChatMessage[]> {
    try {
      const storedChatHistory = await AsyncStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);

      if (!storedChatHistory) {
        return [];
      }

      const chatHistory = JSON.parse(storedChatHistory);
      return Array.isArray(chatHistory) ? chatHistory : [];
    } catch (error) {
      console.error('Failed to get chat history from storage:', error);
      return [];
    }
  },

  async saveChatMessage(message: ChatMessage): Promise<void> {
    try {
      const chatHistory = await StorageService.getChatHistory();
      chatHistory.push(message);
      await AsyncStorage.setItem(
        STORAGE_KEYS.CHAT_HISTORY,
        JSON.stringify(chatHistory),
      );
    } catch (error) {
      console.error('Failed to save chat message to storage:', error);
    }
  },

  async updateProposalStatus(
    messageId: string,
    status: 'accepted' | 'declined',
  ): Promise<void> {
    try {
      const chatHistory = await StorageService.getChatHistory();
      const message = chatHistory.find((chatMessage) => chatMessage.id === messageId);

      if (message) {
        message.proposalStatus = status;
      }

      await AsyncStorage.setItem(
        STORAGE_KEYS.CHAT_HISTORY,
        JSON.stringify(chatHistory),
      );
    } catch (error) {
      console.error('Failed to update proposal status in storage:', error);
    }
  },

  async clearChatHistory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    } catch (error) {
      console.error('Failed to clear chat history from storage:', error);
    }
  },
};
