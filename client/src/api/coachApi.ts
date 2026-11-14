// client/src/api/coachApi.ts
import { BackendChatResponse } from '../types';

export const API_BASE_URL =
  'https://ahmed-h-moustafa2003--ai-gym-coach-v2-gymcoachservice-api.us-east.modal.run';

const REQUEST_TIMEOUT_MS = 240000;
const WARMUP_COOLDOWN_MS = 120000; // Matches Modal container scaledown window

let lastWarmupTimestamp = 0;
let warmupInFlight: Promise<boolean> | null = null;

/**
 * Speculative Pre-Warming (Wake-on-Mount):
 * Fires a silent, non-blocking GET /health ping when the user opens the app or
 * enters the Coach screen so Modal boots the GPU container while the user is typing.
 */
export function warmupCoachServer(): Promise<boolean> {
  const now = Date.now();
  if (now - lastWarmupTimestamp < WARMUP_COOLDOWN_MS) {
    return Promise.resolve(true);
  }
  if (warmupInFlight) {
    return warmupInFlight;
  }

  warmupInFlight = fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'User-Agent': 'AIGymCoachClient/2.5',
    },
  })
    .then((res) => {
      if (res.ok) {
        lastWarmupTimestamp = Date.now();
        return true;
      }
      return false;
    })
    .catch(() => false)
    .finally(() => {
      warmupInFlight = null;
    });

  return warmupInFlight;
}

export async function postCoachQuery(
  queryText: string,
  sessionUserProfile?: string,
): Promise<BackendChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const payload: Record<string, string> = { query: queryText };
    if (sessionUserProfile) {
      payload.session_user_profile = sessionUserProfile;
    }

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'User-Agent': 'AIGymCoachClient/2.5',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Server returned HTTP ${response.status}: ${errorBody}`);
    }

    lastWarmupTimestamp = Date.now();
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