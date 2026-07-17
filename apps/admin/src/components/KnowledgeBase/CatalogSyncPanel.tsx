import React, { useCallback, useEffect, useState } from 'react';
import { ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon, KeyIcon, WrenchScrewdriverIcon } from '@heroicons/react/24/outline';
import { catalogApi } from '../../api/catalog';
import type { CatalogSyncConfig } from '../../api/catalog';
import SyncSettingsModal from './SyncSettingsModal';

interface CatalogSyncPanelProps {
  brandId: string;
  brandName?: string;
}

function statusClasses(status?: string): string {
  if (status === 'completed') return 'bg-emerald-50 text-emerald-700';
  if (status === 'error') return 'bg-red-50 text-red-700';
  if (status === 'processing') return 'bg-amber-50 text-amber-700';
  return 'bg-gray-100 text-gray-600';
}

export default function CatalogSyncPanel({ brandId, brandName }: CatalogSyncPanelProps) {
  const [config, setConfig] = useState<CatalogSyncConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setConfig(await catalogApi.getSyncConfig(brandId));
    } catch (loadError: any) {
      setError(loadError?.response?.data?.detail || loadError?.message || 'Catalog sync settings are unavailable.');
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { loadConfig(); }, [loadConfig]);

  const status = config?.last_sync_status || 'not configured';
  const counts = config?.last_sync_counts;

  return (
    <section className="border-y border-gray-200 bg-white py-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span className="inline-flex h-9 w-9 flex-none items-center justify-center rounded-md bg-gray-950 text-white">
            <WrenchScrewdriverIcon className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-sm font-semibold text-gray-950">Catalog Sync</h2>
              <span className={`rounded px-2 py-1 text-xs font-medium capitalize ${statusClasses(config?.last_sync_status)}`}>{status}</span>
              {config?.access_token_configured && <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600"><KeyIcon className="h-3.5 w-3.5" /> Admin token saved</span>}
            </div>
            <p className="mt-1 max-w-2xl text-sm leading-5 text-gray-500">
              {config?.source_url ? `Shopify products for ${brandName || brandId} sync into the brand catalog.` : 'Connect a Shopify store to populate this brand’s product catalog.'}
            </p>
            {config?.source_url && <p className="mt-2 truncate font-mono text-xs text-gray-500">{config.source_url}</p>}
            {config?.last_sync_error && <p className="mt-2 flex items-start gap-1.5 text-xs leading-5 text-red-700"><ExclamationTriangleIcon className="mt-0.5 h-4 w-4 flex-none" />{config.last_sync_error}</p>}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 lg:justify-end">
          <button type="button" onClick={() => setOpen(true)} className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-800 hover:bg-gray-50 active:translate-y-px">
            <KeyIcon className="h-4 w-4" />
            {config?.source_url ? 'Manage sync' : 'Configure Shopify'}
          </button>
          <button type="button" onClick={loadConfig} disabled={loading} className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50" aria-label="Refresh catalog sync status">
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {counts && (
        <div className="mt-4 grid gap-3 border-t border-gray-100 pt-3 sm:grid-cols-4">
          <div><p className="font-mono text-xl font-semibold text-gray-950">{counts.products_seen}</p><p className="text-xs text-gray-500">Products seen</p></div>
          <div><p className="font-mono text-xl font-semibold text-gray-950">{counts.products_upserted}</p><p className="text-xs text-gray-500">Products updated</p></div>
          <div><p className="font-mono text-xl font-semibold text-gray-950">{counts.products_marked_inactive}</p><p className="text-xs text-gray-500">Inactive source rows</p></div>
          <div><p className="font-mono text-xl font-semibold text-gray-950">{counts.error_count}</p><p className="text-xs text-gray-500">Errors</p></div>
        </div>
      )}
      {config?.last_synced_at && <p className="mt-3 flex items-center gap-1.5 text-xs text-gray-500"><CheckCircleIcon className="h-4 w-4 text-emerald-600" />Last successful sync {new Date(config.last_synced_at).toLocaleString()}</p>}
      {error && <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {open && <SyncSettingsModal brandId={brandId} onClose={() => { setOpen(false); loadConfig(); }} onChanged={setConfig} />}
    </section>
  );
}
