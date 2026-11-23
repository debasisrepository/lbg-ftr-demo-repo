import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { apiClient, ApiError } from '../lib/api-client';

describe('apiClient', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear();
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('request', () => {
    it('should make a GET request with auth token', async () => {
      // Set up auth token
      sessionStorage.setItem('auth_token', 'test-token');

      // Mock successful response
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      const result = await apiClient.get('/v1/test');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.any(Headers),
        })
      );
      expect(result).toEqual({ data: 'test' });
    });

    it('should make a POST request with body', async () => {
      sessionStorage.setItem('auth_token', 'test-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ id: 1, name: 'test' }),
      });

      const body = { name: 'test' };
      const result = await apiClient.post('/v1/items', body);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/items',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(body),
        })
      );
      expect(result).toEqual({ id: 1, name: 'test' });
    });

    it('should throw ApiError on HTTP error', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
        json: async () => ({ detail: 'Resource not found' }),
      });

      try {
        await apiClient.get('/v1/missing');
        // Should not reach here
        expect.fail('Expected ApiError to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).status).toBe(404);
        expect((error as ApiError).detail).toBe('Resource not found');
      }
    });

    it('should handle 204 No Content responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers({ 'content-length': '0' }),
      });

      const result = await apiClient.delete('/v1/items/1');

      expect(result).toBeNull();
    });
  });
});
