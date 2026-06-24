import { describe, it, expect } from 'vitest';
import { useDeliberationStore } from '../../src/stores/deliberation-store';
import type { DeliberationEvent } from '../../src/types/deliberation';

describe('deliberationStore', () => {
  it('reset initializes empty state', () => {
    useDeliberationStore.getState().reset('xyz', 'test problem');
    const s = useDeliberationStore.getState();
    expect(s.id).toBe('xyz');
    expect(s.problem).toBe('test problem');
    expect(s.status).toBe('running');
    expect(s.events).toEqual([]);
  });

  it('applyEvent appends and updates reasoning for token events', () => {
    useDeliberationStore.getState().reset('xyz', 'x');
    const e: DeliberationEvent = {
      seq: 0,
      ts: 1.0,
      kind: 'token',
      payload: { agent: 'alpha', token: 'hello ', seq: 0 },
    };
    useDeliberationStore.getState().applyEvent(e);
    expect(useDeliberationStore.getState().reasoningByAgent.alpha).toBe('hello ');
  });

  it('applyEvent sets activeAgent on alpha_thinking', () => {
    useDeliberationStore.getState().reset('xyz', 'x');
    useDeliberationStore.getState().applyEvent({
      seq: 1,
      ts: 1.0,
      kind: 'alpha_thinking',
      payload: {},
    });
    expect(useDeliberationStore.getState().activeAgent).toBe('alpha');
  });

  it('applyEvent sets status to completed on completed event', () => {
    useDeliberationStore.getState().reset('xyz', 'x');
    useDeliberationStore.getState().applyEvent({
      seq: 5,
      ts: 5.0,
      kind: 'completed',
      payload: {
        decision: 'approved',
        summary: 'ok',
        votes: {},
        rounds: 0,
      },
    });
    expect(useDeliberationStore.getState().status).toBe('completed');
  });
});
