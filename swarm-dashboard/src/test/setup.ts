/**
 * Vitest global setup — extends Jest globals for @testing-library/react compatibility
 * and provides jest global aliases for legacy Jest-style test files.
 */
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Bridge Jest globals → vitest for pre-existing test files written in Jest style
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).jest = vi;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).beforeEach = vi.beforeEach;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).afterEach = vi.afterEach;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).describe = vi.describe;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).it = vi.it;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).test = vi.test;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).expect = vi.expect;
