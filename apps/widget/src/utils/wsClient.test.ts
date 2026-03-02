import { describe, it, expect, beforeEach } from 'vitest';
import { WebSocketClient } from './wsClient';

// MockWebSocket is installed globally in src/test/setup.ts
type MockWS = InstanceType<typeof WebSocket> & {
  url: string;
  readyState: number;
  simulateMessage: (data: object) => void;
  simulateClose: () => void;
};

function lastWS(): MockWS {
  const ws = (globalThis.WebSocket as any).lastInstance as MockWS;
  if (!ws) throw new Error('No MockWebSocket instance created yet');
  return ws;
}

/**
 * Flush two microtask checkpoints so that:
 *   1. queueMicrotask(onopen) fires and resolves connect()'s inner Promise
 *   2. sendMessage's continuation after `await this.connect()` runs (sets onmessage + calls send)
 */
const flushMicrotasks = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

describe('WebSocketClient', () => {
  describe('URL conversion', () => {
    it('converts http:// baseUrl to ws://', async () => {
      const client = new WebSocketClient('http://localhost:8000');
      const p = client.sendMessage({ content: 'hi' }, undefined, undefined, undefined);
      await flushMicrotasks();
      expect(lastWS().url).toBe('ws://localhost:8000/api/v1/messages/ws');
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c1' });
      await p;
    });

    it('converts https:// baseUrl to wss://', async () => {
      const client = new WebSocketClient('https://example.com');
      const p = client.sendMessage({ content: 'hi' }, undefined, undefined, undefined);
      await flushMicrotasks();
      expect(lastWS().url).toBe('wss://example.com/api/v1/messages/ws');
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c1' });
      await p;
    });
  });

  describe('sendMessage()', () => {
    let client: WebSocketClient;

    beforeEach(() => {
      client = new WebSocketClient('http://localhost:8000');
    });

    it('opens a WebSocket connection on first call', async () => {
      const p = client.sendMessage({ content: 'hello' });
      await flushMicrotasks();
      expect(lastWS()).toBeTruthy();
      expect(lastWS().url).toBe('ws://localhost:8000/api/v1/messages/ws');
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c1' });
      await p;
    });

    it('sends correct JSON payload (message, user_id, conversation_id, agent_id, stream: true)', async () => {
      const p = client.sendMessage(
        { content: 'test msg', userId: 'u1' },
        'conv-abc',
        'agent-xyz',
      );
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'conv-abc' });
      await p;

      expect(lastWS().send).toHaveBeenCalledOnce();
      const sent = JSON.parse((lastWS().send as any).mock.calls[0][0]);
      expect(sent).toMatchObject({
        message: 'test msg',
        user_id: 'u1',
        conversation_id: 'conv-abc',
        agent_id: 'agent-xyz',
        stream: true,
      });
    });

    it('calls onStream for each content chunk', async () => {
      const chunks: string[] = [];
      const p = client.sendMessage(
        { content: 'hi' },
        undefined,
        undefined,
        (chunk) => { if (chunk.type === 'content') chunks.push(chunk.content); }
      );
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'content', content: 'Hello', conversation_id: 'c' });
      lastWS().simulateMessage({ type: 'content', content: ' world', conversation_id: 'c' });
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p;

      expect(chunks).toEqual(['Hello', ' world']);
    });

    it('accumulates content and resolves with final Message on metadata chunk', async () => {
      const p = client.sendMessage({ content: 'hi' });
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'content', content: 'Part1', conversation_id: 'c' });
      lastWS().simulateMessage({ type: 'content', content: 'Part2', conversation_id: 'c' });
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });

      const result = await p;
      expect(result.content).toBe('Part1Part2');
      expect(result.role).toBe('assistant');
    });

    it('calls onStream for status chunks', async () => {
      const statusTypes: string[] = [];
      const p = client.sendMessage(
        { content: 'hi' },
        undefined,
        undefined,
        (chunk) => { if (chunk.type === 'status') statusTypes.push(chunk.type); }
      );
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'status', content: 'thinking', conversation_id: 'c' });
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p;

      expect(statusTypes).toEqual(['status']);
    });

    it('captures citations from metadata chunk', async () => {
      const citations = [{ doc_id: 'd1', title: 'Doc', confidence: 0.9 }];
      const p = client.sendMessage({ content: 'hi' });
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c', citations });
      const result = await p;
      expect(result.citations).toEqual(citations);
    });

    it('captures products and dealers from metadata chunk', async () => {
      const products = [{ sku: 'P1', name: 'Widget', price: 9.99 }];
      const dealers = [{ dealer_id: 'D1', name: 'Acme', city: 'NYC' }];
      const p = client.sendMessage({ content: 'hi' });
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'metadata', content: '', conversation_id: 'c', products, dealers });
      const result = await p;
      expect(result.products).toEqual(products);
      expect(result.dealers).toEqual(dealers);
    });

    it('rejects the Promise on an error chunk', async () => {
      const p = client.sendMessage({ content: 'hi' });
      await flushMicrotasks();
      lastWS().simulateMessage({ type: 'error', content: 'Something went wrong', conversation_id: 'c' });
      await expect(p).rejects.toThrow('Something went wrong');
    });
  });

  describe('connection reuse', () => {
    it('reuses the same WebSocket instance for a second sendMessage() call', async () => {
      const client = new WebSocketClient('http://localhost:8000');

      // First call
      const p1 = client.sendMessage({ content: 'first' });
      await flushMicrotasks();
      const ws1 = lastWS();
      ws1.simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p1;

      // Second call — should reuse ws1 (readyState is still OPEN=1)
      const p2 = client.sendMessage({ content: 'second' });
      // No new connect() await needed since ws is OPEN; onmessage set synchronously
      await flushMicrotasks();
      const ws2 = lastWS();
      expect(ws2).toBe(ws1);
      ws1.simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p2;
    });
  });

  describe('reconnection', () => {
    it('opens a new connection if previous was closed before sendMessage()', async () => {
      const client = new WebSocketClient('http://localhost:8000');

      // First call + close
      const p1 = client.sendMessage({ content: 'first' });
      await flushMicrotasks();
      const ws1 = lastWS();
      ws1.simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p1;
      ws1.simulateClose(); // marks readyState = 3 (CLOSED)

      // Second call — must open a fresh connection
      const p2 = client.sendMessage({ content: 'second' });
      await flushMicrotasks();
      const ws2 = lastWS();
      expect(ws2).not.toBe(ws1);
      ws2.simulateMessage({ type: 'metadata', content: '', conversation_id: 'c' });
      await p2;
    });
  });
});
