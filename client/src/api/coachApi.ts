import { BackendChatResponse } from '../types';

export const API_BASE_URL = 'https://preshow-spiritual-rink.ngrok-free.dev';
export const REQUEST_TIMEOUT_MS = 90_000;

export async function postCoachQuery(queryText: string): Promise<BackendChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'AIGymCoachClient/1.0',
      },
      body: JSON.stringify({ query: queryText }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Server returned HTTP ${response.status}: ${errorBody}`);
    }

    return (await response.json()) as BackendChatResponse;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Inference server timed out. Please try again.');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
