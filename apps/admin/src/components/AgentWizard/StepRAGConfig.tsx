import React, { useState } from 'react';
import { api } from '../../api/client';

interface StepRAGConfigProps {
  data: {
    data_source: 'rag' | 'shopify' | 'none';
    shopify_shop_url: string;
    shopify_access_token: string;
    embedding_provider: string;
    embedding_model: string;
    top_k: number;
    similarity_threshold: number;
    rerank_enabled: boolean;
    rerank_top_k: number;
    context_window: number;
  };
  brandId?: string;
  onChange: (field: string, value: string | number | boolean) => void;
}

const embeddingProviders = [
  {
    id: 'voyage',
    name: 'Voyage AI',
    models: [
      { id: 'voyage-large-2', name: 'Voyage Large 2', description: 'Best performance' },
      { id: 'voyage-code-2', name: 'Voyage Code 2', description: 'Optimized for code' },
      { id: 'voyage-2', name: 'Voyage 2', description: 'Balanced performance' },
    ]
  },
  {
    id: 'openai',
    name: 'OpenAI',
    models: [
      { id: 'text-embedding-3-large', name: 'Text Embedding 3 Large', description: 'Highest quality' },
      { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small', description: 'Good performance, lower cost' },
      { id: 'text-embedding-ada-002', name: 'Ada 002', description: 'Legacy model' },
    ]
  },
  {
    id: 'cohere',
    name: 'Cohere',
    models: [
      { id: 'embed-english-v3.0', name: 'Embed English v3.0', description: 'Latest English model' },
      { id: 'embed-multilingual-v3.0', name: 'Embed Multilingual v3.0', description: 'Supports multiple languages' },
    ]
  }
];

export default function StepRAGConfig({ data, brandId, onChange }: StepRAGConfigProps) {
  const selectedProvider = embeddingProviders.find(p => p.id === data.embedding_provider);
  const availableModels = selectedProvider?.models || [];
  
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const handleShopifySync = async () => {
    if (!brandId) {
       alert("Please complete the basic information step and save the agent first, to link it to a brand.");
       return;
    }
    if (!data.shopify_shop_url) {
      alert("Please enter a Shop URL.");
      return;
    }
    setIsSyncing(true);
    setSyncStatus('Starting catalog sync...');
    try {
      const resp = await api.syncShopify({
        brand_id: brandId,
        store_url: data.shopify_shop_url,
        access_token: data.shopify_access_token || undefined,
      });
      setSyncStatus(`Sync initiated. Job ID: ${resp.job_id}`);
    } catch (e: any) {
      console.error(e);
      setSyncStatus(`Sync failed: ${e.message || 'Unknown error'}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Data Source Configuration</h3>
        <p className="mt-1 text-sm text-gray-600">
          Configure how your agent retrieves and uses knowledge to answer your users.
        </p>
      </div>

      {/* Data Source Selection */}
      <fieldset>
        <legend className="sr-only">Data Source</legend>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              id="source_none"
              name="data_source"
              type="radio"
              checked={data.data_source === 'none' || !data.data_source}
              onChange={() => onChange('data_source', 'none')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
            />
            <label htmlFor="source_none" className="ml-3 block text-sm font-medium text-gray-700">
              None
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="source_rag"
              name="data_source"
              type="radio"
              checked={data.data_source === 'rag'}
              onChange={() => onChange('data_source', 'rag')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
            />
            <label htmlFor="source_rag" className="ml-3 block text-sm font-medium text-gray-700">
              Retrieval-Augmented Generation (Upload Custom Documents)
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="source_shopify"
              name="data_source"
              type="radio"
              checked={data.data_source === 'shopify'}
              onChange={() => onChange('data_source', 'shopify')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
            />
            <label htmlFor="source_shopify" className="ml-3 block text-sm font-medium text-gray-700">
              Shopify Store Integration
            </label>
          </div>
        </div>
      </fieldset>

      {/* Shopify Configuration */}
      {data.data_source === 'shopify' && (
        <div className="space-y-6 border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900">Shopify Connection</h4>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="shopify_shop_url" className="block text-sm font-medium text-gray-700">
                Shopify Store URL *
              </label>
              <input
                type="url"
                id="shopify_shop_url"
                placeholder="https://your-store.myshopify.com"
                value={data.shopify_shop_url}
                onChange={(e) => onChange('shopify_shop_url', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                required
              />
            </div>
            <div>
              <label htmlFor="shopify_access_token" className="block text-sm font-medium text-gray-700">
                Access Token (Optional)
              </label>
              <input
                type="password"
                id="shopify_access_token"
                placeholder="shpat_..."
                value={data.shopify_access_token}
                onChange={(e) => onChange('shopify_access_token', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Required only if your store catalog is private or password-protected.
              </p>
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-md">
            <div className="flex items-center justify-between">
              <div>
                <h5 className="text-sm font-medium text-gray-900">Sync Product Catalog</h5>
                <p className="text-sm text-gray-500 mt-1">Import products into AgentBuilder for this brand.</p>
                {syncStatus && <p className="text-sm font-semibold mt-2 text-primary-600">{syncStatus}</p>}
              </div>
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                onClick={handleShopifySync}
                disabled={isSyncing || !data.shopify_shop_url}
              >
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RAG Configuration */}
      {data.data_source === 'rag' && (
        <div className="space-y-6 border-t border-gray-200 pt-6">
          <h4 className="text-md font-medium text-gray-900">Embedding Settings</h4>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="embedding_provider" className="block text-sm font-medium text-gray-700">
                Embedding Provider *
              </label>
              <select
                id="embedding_provider"
                value={data.embedding_provider}
                onChange={(e) => {
                  onChange('embedding_provider', e.target.value);
                  onChange('embedding_model', ''); // Reset model when provider changes
                }}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                required
              >
                <option value="">Select provider</option>
                {embeddingProviders.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="embedding_model" className="block text-sm font-medium text-gray-700">
                Embedding Model *
              </label>
              <select
                id="embedding_model"
                value={data.embedding_model}
                onChange={(e) => onChange('embedding_model', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                disabled={!data.embedding_provider}
                required
              >
                <option value="">Select model</option>
                {availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} - {model.description}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <h4 className="text-md font-medium text-gray-900">Retrieval Parameters</h4>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label htmlFor="top_k" className="block text-sm font-medium text-gray-700">
                Top K Results
              </label>
              <input
                type="number"
                id="top_k"
                min="1"
                max="20"
                value={data.top_k}
                onChange={(e) => onChange('top_k', parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Number of relevant chunks to retrieve (1-20)
              </p>
            </div>

            <div>
              <label htmlFor="similarity_threshold" className="block text-sm font-medium text-gray-700">
                Similarity Threshold
              </label>
              <div className="mt-1">
                <input
                  type="range"
                  id="similarity_threshold"
                  min="0"
                  max="1"
                  step="0.05"
                  value={data.similarity_threshold}
                  onChange={(e) => onChange('similarity_threshold', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Loose (0)</span>
                  <span className="font-medium">{data.similarity_threshold}</span>
                  <span>Strict (1)</span>
                </div>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Minimum similarity score
              </p>
            </div>

            <div>
              <label htmlFor="context_window" className="block text-sm font-medium text-gray-700">
                Context Window
              </label>
              <input
                type="number"
                id="context_window"
                min="500"
                max="4000"
                step="100"
                value={data.context_window}
                onChange={(e) => onChange('context_window', parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Max tokens for retrieved context
              </p>
            </div>
          </div>

          <h4 className="text-md font-medium text-gray-900">Reranking</h4>
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="rerank_enabled"
                type="checkbox"
                checked={data.rerank_enabled}
                onChange={(e) => onChange('rerank_enabled', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="rerank_enabled" className="ml-2 block text-sm text-gray-900">
                Enable result reranking for better relevance
              </label>
            </div>

            {data.rerank_enabled && (
              <div className="ml-6">
                <label htmlFor="rerank_top_k" className="block text-sm font-medium text-gray-700">
                  Rerank Top K
                </label>
                <input
                  type="number"
                  id="rerank_top_k"
                  min="1"
                  max={Math.min(data.top_k, 10)}
                  value={data.rerank_top_k}
                  onChange={(e) => onChange('rerank_top_k', parseInt(e.target.value))}
                  className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Must be ≤ Top K (max {Math.min(data.top_k, 10)})
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {data.data_source === 'none' && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-gray-800">
                Static Knowledge Only
              </h3>
              <div className="mt-2 text-sm text-gray-700">
                <p>
                  Your agent will rely only on its training data and system prompt. 
                  Choose RAG or Shopify to give your agent access to additional external knowledge.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
