import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, PlusIcon } from '@heroicons/react/24/outline';
import DocumentUploadWizard from '../KnowledgeBase/DocumentUploadWizard';
import DocumentsList from '../KnowledgeBase/DocumentsList';
import { knowledgeApi } from '../../api/knowledge';
import type { DocumentSummary, UploadDocumentResponse, UploadJobStatus } from '../../types/knowledge';

const isDev = process.env.NODE_ENV !== 'production';

interface StepKnowledgeBaseProps {
  data: {
    documents: Array<{
      id: string;
      filename: string;
      size: number;
      type: string;
      status: 'uploading' | 'processing' | 'ready' | 'error';
      file?: File;
    }>;
    chunking_strategy: string;
    chunk_size: number;
    chunk_overlap: number;
  };
  onChange: (field: string, value: any) => void;
  agentId?: string;
  brandId?: string;
}

export default function StepKnowledgeBase({ data, onChange, agentId, brandId }: StepKnowledgeBaseProps) {
  const [showWizard, setShowWizard] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [resolvedBrandId, setResolvedBrandId] = useState<string | null>(null);
  const [brandAliases, setBrandAliases] = useState<string[]>([]);
  const [uploadJob, setUploadJob] = useState<UploadJobStatus | null>(null);

  const mergeDocuments = (documents: DocumentSummary[]) => {
    const byId = new Map<string, DocumentSummary>();
    documents.forEach((doc) => {
      const existing = byId.get(doc.doc_id);
      if (!existing || (doc.chunks_count || 0) > (existing.chunks_count || 0)) {
        byId.set(doc.doc_id, doc);
      }
    });

    return Array.from(byId.values()).sort((a, b) =>
      String(b.created_at || '').localeCompare(String(a.created_at || ''))
    );
  };

  const mapDocumentsForWizard = (docs: DocumentSummary[]) => docs.map(doc => ({
    id: doc.doc_id,
    filename: doc.title || doc.doc_id,
    size: doc.chunks_count || 0,
    type: doc.content_type,
    status: 'ready' as const
  }));

  // Resolve brand slug from agent ID if needed
  useEffect(() => {
    const resolveBrand = async () => {
      // If we have an agentId, ALWAYS resolve through API (don't trust brandId prop)
      if (agentId) {
        try {
          const clientModule = await import('../../api/client');
          const resp = await clientModule.agentApi.get(agentId);
          const agent = resp.data as any;
          const aliases = [agent?.brand_slug, agent?.brand_id, brandId].filter(Boolean) as string[];
          let primaryBrand = agent?.brand_slug || agent?.brand_id || brandId || null;

          if (agent?.brand_id) {
            try {
              const brandResp = await clientModule.brandApi.get(agent.brand_id);
              if (brandResp.data?.slug) {
                primaryBrand = brandResp.data.slug;
                aliases.unshift(brandResp.data.slug);
              }
              if (brandResp.data?.id) {
                aliases.push(brandResp.data.id);
              }
            } catch (brandErr) {
              isDev && console.warn('[StepKnowledgeBase] Brand lookup fallback:', brandErr);
            }
          }

          const uniqueAliases = Array.from(new Set(aliases));
          isDev && console.log('[StepKnowledgeBase] Resolved agent to brand:', { agentId, primaryBrand, aliases: uniqueAliases });
          setResolvedBrandId(primaryBrand);
          setBrandAliases(uniqueAliases);
        } catch (err) {
          console.warn('[StepKnowledgeBase] Failed to resolve agent -> brand', err);
          setResolvedBrandId(brandId || null); // fallback to brandId
          setBrandAliases(brandId ? [brandId] : []);
        }
      } else if (brandId) {
        try {
          const clientModule = await import('../../api/client');
          const brandResp = await clientModule.brandApi.get(brandId);
          const primaryBrand = brandResp.data?.slug || brandId;
          const uniqueAliases = Array.from(new Set([primaryBrand, brandResp.data?.id, brandId].filter(Boolean) as string[]));
          isDev && console.log('[StepKnowledgeBase] Resolved brand directly:', { primaryBrand, aliases: uniqueAliases });
          setResolvedBrandId(primaryBrand);
          setBrandAliases(uniqueAliases);
        } catch {
          isDev && console.log('[StepKnowledgeBase] Using brandId directly:', brandId);
          setResolvedBrandId(brandId);
          setBrandAliases([brandId]);
        }
      }
    };

    resolveBrand();
  }, [brandId, agentId]);

  // Fetch documents count to update validation (depends on resolvedBrandId)
  useEffect(() => {
    const fetchDocumentsCount = async () => {
      // Wait for resolvedBrandId to be set
      if (!resolvedBrandId) {
        isDev && console.log('[StepKnowledgeBase] Waiting for brand resolution...');
        return;
      }

      try {
        const lookupIds = brandAliases.length > 0 ? brandAliases : [resolvedBrandId];
        isDev && console.log('[StepKnowledgeBase] Fetching documents for brand aliases:', lookupIds);
        const results = await Promise.allSettled(lookupIds.map(id => knowledgeApi.getDocuments(id)));
        const docs = mergeDocuments(results.flatMap(result => result.status === 'fulfilled' ? result.value : []));
        isDev && console.log('[StepKnowledgeBase] Fetched documents:', docs.length);
        // Update the data with fetched documents for validation
        onChange('documents', mapDocumentsForWizard(docs));
      } catch (error) {
        console.error('[StepKnowledgeBase] Failed to fetch documents:', error);
        // Set empty array on error to avoid validation issues
        onChange('documents', []);
      }
    };

    fetchDocumentsCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedBrandId, brandAliases.join('|'), refreshKey]); // Fetch when resolvedBrandId changes

  useEffect(() => {
    if (!uploadJob?.job_id || uploadJob.status === 'completed' || uploadJob.status === 'error') {
      return;
    }

    let cancelled = false;
    const timeout = window.setTimeout(async () => {
      try {
        const nextStatus = await knowledgeApi.getJobStatus(uploadJob.job_id);
        if (cancelled) return;

        setUploadJob(nextStatus);
        if (nextStatus.status === 'completed') {
          setRefreshKey(prev => prev + 1);
        }
      } catch (error: any) {
        if (cancelled) return;
        setUploadJob(prev => prev ? {
          ...prev,
          status: 'error',
          error: error?.message || 'Failed to check upload status',
        } : prev);
      }
    }, 1500);

    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
    };
  }, [uploadJob]);

  const handleUploadComplete = (response: UploadDocumentResponse) => {
    setShowWizard(false);
    setUploadJob({
      job_id: response.job_id,
      status: response.status === 'completed' ? 'completed' : 'processing',
      progress: {
        type: 'bulk',
        processed_items: 0,
        total_items: response.items_count,
        processed_chunks: 0,
        total_chunks: 0,
      },
    });

    if (response.status === 'completed') {
      setRefreshKey(prev => prev + 1);
    }
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  if (showWizard) {
    // Wait for brand resolution before showing wizard
    if (!resolvedBrandId) {
      return (
        <div className="max-w-6xl">
          <div className="bg-white shadow rounded-lg p-8">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-600">Preparing upload...</span>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div className="max-w-6xl">
        <DocumentUploadWizard
          brandId={resolvedBrandId}
          onComplete={handleUploadComplete}
          onCancel={() => setShowWizard(false)}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Knowledge Base</h2>
        <p className="mt-2 text-sm text-gray-600">
          Upload documents with structured metadata to prevent AI hallucinations
        </p>
      </div>

      <div className="mb-6">
        <button
          onClick={() => {
            setUploadJob(null);
            setShowWizard(true);
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Upload Document with Structured Metadata
        </button>
      </div>

      {uploadJob && (
        <div className={`mb-6 rounded-lg border p-4 ${
          uploadJob.status === 'error'
            ? 'border-red-200 bg-red-50'
            : uploadJob.status === 'completed'
              ? 'border-green-200 bg-green-50'
              : 'border-blue-200 bg-blue-50'
        }`}>
          <div className="flex items-start gap-3">
            {uploadJob.status === 'error' ? (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
            ) : uploadJob.status === 'completed' ? (
              <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5" />
            ) : (
              <div className="h-5 w-5 rounded-full border-2 border-blue-200 border-t-blue-600 animate-spin mt-0.5" />
            )}
            <div>
              <p className={`text-sm font-medium ${
                uploadJob.status === 'error'
                  ? 'text-red-900'
                  : uploadJob.status === 'completed'
                    ? 'text-green-900'
                    : 'text-blue-900'
              }`}>
                {uploadJob.status === 'completed'
                  ? 'Upload completed'
                  : uploadJob.status === 'error'
                    ? 'Upload failed'
                    : 'Processing upload'}
              </p>
              <p className={`mt-1 text-sm ${
                uploadJob.status === 'error'
                  ? 'text-red-700'
                  : uploadJob.status === 'completed'
                    ? 'text-green-700'
                    : 'text-blue-700'
              }`}>
                {uploadJob.status === 'error'
                  ? uploadJob.error || 'The upload job failed.'
                  : uploadJob.status === 'completed'
                    ? 'The knowledge base has been refreshed.'
                    : `${uploadJob.progress.processed_items || 0}/${uploadJob.progress.total_items || 0} items processed, ${uploadJob.progress.processed_chunks || 0} chunks embedded.`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Documents List - only show after brand resolution */}
      {resolvedBrandId ? (
        uploadJob && uploadJob.status !== 'completed' && uploadJob.status !== 'error' && data.documents.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-600">Processing documents before refreshing the list...</span>
            </div>
          </div>
        ) : (
          <DocumentsList 
            brandId={resolvedBrandId}
            onRefresh={handleRefresh}
            key={refreshKey}
          />
        )
      ) : (
        <div className="bg-white shadow rounded-lg p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-gray-600">Loading documents...</span>
          </div>
        </div>
      )}
    </div>
  );
}
