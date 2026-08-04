import type { LLMModel } from '../types';

export const LLM_MODELS: LLMModel[] = [
  {
    id: 'openai',
    name: 'ChatGPT',
    version: 'GPT-4o',
    logo: '🤖',
    color: '#10a37f',
    bgColor: 'rgba(16, 163, 127, 0.1)',
    description: 'OpenAI\'s most capable multimodal model',
  },
  {
    id: 'google',
    name: 'Gemini',
    version: 'Gemini 1.5 Pro',
    logo: '✨',
    color: '#4285f4',
    bgColor: 'rgba(66, 133, 244, 0.1)',
    description: 'Google\'s advanced multimodal AI model',
  },
  {
    id: 'anthropic',
    name: 'Claude',
    version: 'Claude 3.5 Sonnet',
    logo: '🧠',
    color: '#d97757',
    bgColor: 'rgba(217, 119, 87, 0.1)',
    description: 'Anthropic\'s safety-focused AI assistant',
  },
  {
    id: 'meta',
    name: 'Llama',
    version: 'Llama 3.1 405B',
    logo: '🦙',
    color: '#0467df',
    bgColor: 'rgba(4, 103, 223, 0.1)',
    description: 'Meta\'s open-source frontier model',
  },
  {
    id: 'mistral',
    name: 'Mistral',
    version: 'Mistral Large 2',
    logo: '🌪️',
    color: '#ff7000',
    bgColor: 'rgba(255, 112, 0, 0.1)',
    description: 'Mistral AI\'s most powerful model',
  },
];

export const getModelById = (id: string): LLMModel | undefined =>
  LLM_MODELS.find((m) => m.id === id);
