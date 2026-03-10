import React, { useEffect, useRef, useState } from 'react';
import { catalogApi } from '../../../api/catalog';

interface UrlResult {
  url: string;
  status: 'pending' | 'success' | 'no_product' | 'error';
  product_type?: string;
  item_count?: number;
  name?: string;
  error?: string;
}

interface ScrapeTabProps {
  brandId: string;
  onUpload: (data: any[]) => void;
  onBack: () => void;
}

export default function ScrapeTab({ brandId, onUpload, onBack }: ScrapeTabProps) {
  const [urlText, setUrlText] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [urlResults, setUrlResults] = useState<UrlResult[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const parseUrls = () =>
    urlText
      .split('\n')
      .map(u => u.trim())
      .filter(u => u.startsWith('http'));

  const handleScrape = async () => {
    const urls = parseUrls();
    if (!urls.length) return;

    setStatus('loading');
    setError(null);
    setItems([]);
    setUrlResults(urls.map(url => ({ url, status: 'pending' })));

    try {
      const { job_id } = await catalogApi.importScrape(urls, brandId);
      pollRef.current = setInterval(async () => {
        try {
          const job = await catalogApi.getJob(job_id);

          // Update per-URL results as they come in
          if (job.results?.length) {
            setUrlResults(prev => {
              const updated = [...prev];
              for (const r of job.results) {
                const idx = updated.findIndex(u => u.url === r.url);
                if (idx >= 0) updated[idx] = { ...updated[idx], ...r };
              }
              return updated;
            });
          }

          if (job.status === 'completed') {
            clearInterval(pollRef.current!);
            setItems(job.items || []);
            setStatus('done');
          } else if (job.status === 'error') {
            clearInterval(pollRef.current!);
            setError(job.error || 'Scrape failed');
            setStatus('error');
          }
        } catch {
          clearInterval(pollRef.current!);
          setError('Lost connection. Please try again.');
          setStatus('error');
        }
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start scrape');
      setStatus('error');
    }
  };

  const successCount = urlResults.filter(r => r.status === 'success').length;

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Scrape Product Pages</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          Paste product page URLs (one per line). Firecrawl extracts structured data using AI.
          Works on JS-rendered stores, handles bot protection.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Product Page URLs <span className="text-red-500">*</span>
        </label>
        <textarea
          value={urlText}
          onChange={e => setUrlText(e.target.value)}
          disabled={status === 'loading'}
          rows={6}
          placeholder={`https://mystore.com/products/blue-coat\nhttps://mystore.com/products/wool-scarf\nhttps://mystore.com/products/executive-anvil`}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-50"
        />
        <p className="mt-1 text-xs text-gray-400">
          {parseUrls().length} URL{parseUrls().length !== 1 ? 's' : ''} detected · max 50 per batch
        </p>
      </div>

      {/* Per-URL results */}
      {urlResults.length > 0 && (
        <div className="space-y-1.5">
          {urlResults.map((r, i) => (
            <div
              key={i}
              className={`flex items-center gap-3 text-xs px-3 py-2 rounded-md border ${
                r.status === 'success'
                  ? 'bg-green-50 border-green-200 text-green-800'
                  : r.status === 'no_product'
                  ? 'bg-gray-50 border-gray-200 text-gray-500'
                  : r.status === 'error'
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-blue-50 border-blue-200 text-blue-700'
              }`}
            >
              <span className="shrink-0">
                {r.status === 'success' ? '✅' : r.status === 'no_product' ? '⏭️' : r.status === 'error' ? '❌' : '⏳'}
              </span>
              <span className="truncate flex-1">{r.url}</span>
              {r.status === 'success' && (
                <span className="shrink-0 font-medium">
                  {r.product_type} · {r.item_count} item{r.item_count !== 1 ? 's' : ''}
                </span>
              )}
              {r.status === 'no_product' && <span className="shrink-0">Not a product page</span>}
              {r.status === 'error' && <span className="shrink-0 truncate max-w-[160px]">{r.error}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {status === 'error' && error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Done summary */}
      {status === 'done' && (
        <div className="rounded-md bg-green-50 border border-green-200 p-4 text-sm text-green-800">
          ✅ Scraped <strong>{successCount}</strong> of {urlResults.length} URLs · <strong>{items.length}</strong> total products extracted
        </div>
      )}

      <div className="flex justify-between pt-4 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          ← Back to Content Type
        </button>
        {status !== 'done' ? (
          <button
            onClick={handleScrape}
            disabled={!parseUrls().length || status === 'loading'}
            className="px-6 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {status === 'loading' && (
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
            )}
            {status === 'loading' ? 'Scraping…' : 'Start Scraping'}
          </button>
        ) : (
          <button
            onClick={() => onUpload(items)}
            disabled={items.length === 0}
            className="px-6 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Next: Map Fields →
          </button>
        )}
      </div>
    </div>
  );
}
