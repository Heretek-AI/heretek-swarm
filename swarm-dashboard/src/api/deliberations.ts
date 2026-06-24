// REST client for /api/deliberations.
import axios from 'axios';
import type { DeliberationDetail, DeliberationSummary } from '../types/deliberation';

const client = axios.create({ baseURL: '/api' });

export async function createDeliberation(problem: string): Promise<string> {
  const r = await client.post<{ id: string; status: string }>('/deliberations', { problem });
  return r.data.id;
}

export async function getDeliberation(id: string): Promise<DeliberationDetail> {
  const r = await client.get<DeliberationDetail>(`/deliberations/${id}`);
  return r.data;
}

export async function listDeliberations(limit = 20): Promise<DeliberationSummary[]> {
  const r = await client.get<{ items: DeliberationSummary[] }>(`/deliberations?limit=${limit}`);
  return r.data.items;
}

export async function interject(id: string, text: string): Promise<void> {
  await client.post(`/deliberations/${id}/interject`, { text });
}
