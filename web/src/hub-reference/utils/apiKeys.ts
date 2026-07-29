// @ts-nocheck
/**
 * API Key Manager
 *
 * Keys are stored in browser localStorage via the in-app Settings UI.
 */

const GEMINI_STORAGE_KEY = 'iidatech.geminiKey';
const CLAUDE_STORAGE_KEY = 'iidatech.claudeKey';
const ZO_STORAGE_KEY = 'iidatech.zoKey';

function readEnv(key: 'VITE_GEMINI_API_KEY' | 'VITE_CLAUDE_API_KEY' | 'VITE_ZO_API_KEY'): string {
  const nextPublic = key.replace('VITE_', 'NEXT_PUBLIC_');
  try {
    if (typeof process !== 'undefined' && process.env?.[nextPublic]) {
      return String(process.env[nextPublic]);
    }
  } catch {
    // ignore
  }
  try {
    const env = (import.meta as { env?: Record<string, string> })?.env;
    const value = env?.[key];
    return typeof value === 'string' ? value : '';
  } catch {
    return '';
  }
}

function readLocalStorage(key: string): string {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return '';
    return window.localStorage.getItem(key) || '';
  } catch {
    return '';
  }
}

function writeLocalStorage(key: string, value: string): void {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return;
    window.localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

// ─── Public accessors (used throughout the app) ────────────────────────────────

export function getGeminiKey(): string {
  return readLocalStorage(GEMINI_STORAGE_KEY) || readEnv('VITE_GEMINI_API_KEY');
}

export function getClaudeKey(): string {
  return readLocalStorage(CLAUDE_STORAGE_KEY) || readEnv('VITE_CLAUDE_API_KEY');
}

export function getZoKey(): string {
  return readLocalStorage(ZO_STORAGE_KEY) || readEnv('VITE_ZO_API_KEY');
}

export function setGeminiKey(key: string): void {
  writeLocalStorage(GEMINI_STORAGE_KEY, key.trim());
}

export function setClaudeKey(key: string): void {
  writeLocalStorage(CLAUDE_STORAGE_KEY, key.trim());
}

export function setZoKey(key: string): void {
  writeLocalStorage(ZO_STORAGE_KEY, key.trim());
}

export function hasGeminiKey(): boolean {
  return getGeminiKey().length > 0;
}

export function hasClaudeKey(): boolean {
  return getClaudeKey().length > 0;
}

export function hasZoKey(): boolean {
  if (getZoKey().length > 0) return true;
  try {
    const isDev = process.env.NODE_ENV === 'development';
    if (isDev) return true;
  } catch {
    // ignore
  }
  // Zo calls are proxied at /api/zo/ask; server may hold ZO_API_KEY without exposing it to the browser.
  return true;
}

export function hasAnyKey(): boolean {
  return hasZoKey() || hasGeminiKey() || hasClaudeKey();
}
