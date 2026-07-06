import { afterEach, describe, expect, it, vi } from 'vitest';
import { APIClient } from './apiClient';

const createJsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  statusText: 'OK',
  json: async () => data,
});

const createStreamResponse = (frames: object[]) => {
  const encoder = new TextEncoder();
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    body: new ReadableStream<Uint8Array>({
      start(controller) {
        frames.forEach((frame) => {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(frame)}\n\n`));
        });
        controller.close();
      },
    }),
  };
};

describe('APIClient product metadata', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('preserves products from direct message responses', async () => {
    const products = [
      {
        sku: 'HD-001',
        name: 'Heart Drop Earrings',
        price: 44900,
        currency: 'USD',
      },
    ];
    const fetchMock = vi.fn().mockResolvedValue(createJsonResponse({
      id: 'm1',
      content: 'These match your search.',
      products,
    }));
    vi.stubGlobal('fetch', fetchMock);

    const client = new APIClient('https://api.example.test');
    const result = await client.sendMessage({ content: 'show earrings', userId: 'u1' }, 'c1', 'a1');

    expect(result).toMatchObject({
      id: 'm1',
      content: 'These match your search.',
      role: 'assistant',
      products,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/messages/',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });

  it('preserves products from streaming message metadata', async () => {
    const products = [
      {
        sku: 'HD-001',
        name: 'Heart Drop Earrings',
        price: 44900,
        currency: 'USD',
      },
    ];
    const fetchMock = vi.fn().mockResolvedValue(createStreamResponse([
      { type: 'content', content: 'Found ', conversation_id: 'c1' },
      { type: 'content', content: 'one match.', conversation_id: 'c1' },
      { type: 'metadata', content: '', conversation_id: 'c1', products },
    ]));
    vi.stubGlobal('fetch', fetchMock);

    const onStream = vi.fn();
    const client = new APIClient('https://api.example.test');
    const result = await client.sendMessage({ content: 'show earrings', userId: 'u1' }, 'c1', 'a1', onStream);

    expect(result.content).toBe('Found one match.');
    expect(result.products).toEqual(products);
    expect(onStream).toHaveBeenCalledWith(expect.objectContaining({ type: 'metadata', products }));
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/messages/stream',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        }),
      }),
    );
  });
});
