import { apiClient } from './client';

export const catalogApi = {
  importShopify: async (storeUrl: string, brandId: string, accessToken?: string) => {
    const response = await apiClient.post('/api/v1/catalog/import/shopify', {
      store_url: storeUrl,
      brand_id: brandId,
      access_token: accessToken || null,
    });
    return response.data as { job_id: string; status: string };
  },

  importJsonFeed: async (url: string, brandId: string) => {
    const response = await apiClient.post('/api/v1/catalog/import/json-feed', {
      url,
      brand_id: brandId,
    });
    return response.data as { items: any[]; detected_format: string; raw_count: number };
  },

  importCsv: async (file: File, brandId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('brand_id', brandId);
    const response = await apiClient.post('/api/v1/catalog/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data as { items: any[]; detected_format: string; raw_count: number };
  },

  importScrape: async (urls: string[], brandId: string) => {
    const response = await apiClient.post('/api/v1/catalog/import/scrape', {
      urls,
      brand_id: brandId,
    });
    return response.data as { job_id: string; status: string };
  },

  getJob: async (jobId: string) => {
    const response = await apiClient.get(`/api/v1/catalog/jobs/${jobId}`);
    return response.data;
  },

  getSyncConfig: async (brandId: string) => {
    const response = await apiClient.get(`/api/v1/catalog/sync-config/${brandId}`);
    return response.data;
  },

  updateSyncConfig: async (
    brandId: string,
    config: {
      source_type: string;
      source_url: string;
      access_token?: string;
      auto_sync: boolean;
      sync_frequency: string;
    }
  ) => {
    const response = await apiClient.put(`/api/v1/catalog/sync-config/${brandId}`, config);
    return response.data;
  },

  manualSync: async (brandId: string) => {
    const response = await apiClient.post(`/api/v1/catalog/sync/${brandId}`);
    return response.data;
  },
};
