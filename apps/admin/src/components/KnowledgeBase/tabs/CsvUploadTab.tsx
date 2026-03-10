import React, { useRef, useState } from 'react';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';
import { catalogApi } from '../../../api/catalog';

interface CsvUploadTabProps {
  brandId: string;
  onUpload: (data: any[]) => void;
  onBack: () => void;
}

export default function CsvUploadTab({ brandId, onUpload, onBack }: CsvUploadTabProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [items, setItems] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (f: File) => {
    if (!f.name.endsWith('.csv')) {
      setError('Please upload a .csv file.');
      return;
    }
    setFile(f);
    setStatus('loading');
    setError(null);
    try {
      const result = await catalogApi.importCsv(f, brandId);
      setItems(result.items);
      setColumns(result.items.length > 0 ? Object.keys(result.items[0]) : []);
      setStatus('done');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Parse failed');
      setStatus('error');
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Upload CSV</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          Columns are auto-detected. You'll map them to our schema in the next step.
        </p>
      </div>

      {/* Drop zone */}
      <label
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`block w-full border-2 border-dashed rounded-lg px-6 py-10 text-center cursor-pointer transition-colors ${
          dragging ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <DocumentArrowUpIcon className="mx-auto h-10 w-10 text-gray-400 mb-2" />
        {file ? (
          <p className="text-sm text-green-700 font-medium">✓ {file.name}</p>
        ) : (
          <>
            <p className="text-sm font-medium text-primary-600">Upload a CSV file</p>
            <p className="text-xs text-gray-400 mt-1">or drag and drop here</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="sr-only"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />
      </label>

      {/* Loading */}
      {status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          Parsing CSV…
        </div>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Done */}
      {status === 'done' && (
        <div className="rounded-md bg-green-50 border border-green-200 p-4 space-y-2">
          <p className="text-sm text-green-800 font-medium">
            ✅ {items.length} rows parsed
          </p>
          <p className="text-xs text-green-700">
            Columns detected: <span className="font-mono">{columns.join(', ')}</span>
          </p>
          <p className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded px-2 py-1">
            ℹ️ You'll map these columns to our product schema in the next step.
          </p>
        </div>
      )}

      <div className="flex justify-between pt-4 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          ← Back to Content Type
        </button>
        {status === 'done' && (
          <button
            onClick={() => onUpload(items)}
            className="px-6 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md"
          >
            Next: Map Fields →
          </button>
        )}
      </div>
    </div>
  );
}
