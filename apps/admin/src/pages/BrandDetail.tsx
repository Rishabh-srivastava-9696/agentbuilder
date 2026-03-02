import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeftIcon, PencilIcon } from '@heroicons/react/24/outline';
import { brandApi, agentApi, type Brand, type BrandIdentity } from '../api/client';
import BrandModal from '../components/BrandModal';

// ── Mini widget preview ────────────────────────────────────────
function WidgetPreview({ brand }: { brand: Brand }) {
  const identity: BrandIdentity = brand.colors || {};
  const mode = identity.default_mode ?? 'dark';
  const primary = identity.primary_color ?? '#6366f1';
  const logo = mode === 'dark' ? identity.chat_logo_dark_url : identity.chat_logo_light_url;
  const chips = identity.suggestion_chips
    ? identity.suggestion_chips.split(',').map(c => c.trim()).filter(Boolean)
    : [];

  // Derive simple tokens inline for preview
  const r = parseInt(primary.slice(1, 3) || '99', 16);
  const g = parseInt(primary.slice(3, 5) || '66', 16);
  const b = parseInt(primary.slice(5, 7) || 'f1', 16);
  const rgba = (a: number) => `rgba(${r},${g},${b},${a})`;

  const dark = mode === 'dark';
  const panelBg = dark
    ? (identity.dark_bg_gradient || `linear-gradient(160deg,#080d14 0%,#0d1520 30%,#061008 100%)`)
    : (identity.light_bg_gradient || `linear-gradient(160deg,#fdfaf5 0%,#ede8df 100%)`);
  const titleColor = dark ? '#ffffff' : '#1a1208';
  const subtitleColor = dark ? 'rgba(255,255,255,0.45)' : 'rgba(60,40,20,0.5)';
  const novaColor = dark ? 'rgba(255,255,255,0.5)' : 'rgba(60,40,20,0.4)';
  const chipBg = rgba(0.1);
  const chipBorder = rgba(0.22);
  const chipColor = dark ? 'rgba(255,255,255,0.6)' : rgba(0.85);
  const inputBg = dark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.85)';
  const inputBorder = dark ? 'rgba(255,255,255,0.1)' : rgba(0.2);
  const inputColor = dark ? 'rgba(255,255,255,0.38)' : 'rgba(60,40,20,0.45)';
  const sendBg = `linear-gradient(135deg,${primary},${rgba(0.7)})`;
  const bubbleBg = dark ? '#111' : '#fff';
  const bubbleBorder = rgba(0.2);

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16 }}>
      {/* Panel preview */}
      <div style={{
        width: 240, height: 400, borderRadius: 18, overflow: 'hidden',
        background: panelBg, position: 'relative',
        boxShadow: '0 12px 40px rgba(0,0,0,0.3)',
        flexShrink: 0,
      }}>
        {/* Orb */}
        <div style={{
          position: 'absolute', top: '38%', left: '50%',
          transform: 'translate(-50%,-50%)',
          width: 180, height: 180, borderRadius: '50%',
          background: `radial-gradient(circle,${rgba(0.12)} 0%,transparent 70%)`,
          pointerEvents: 'none',
        }} />

        {/* Topbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 14px 0', position: 'relative', zIndex: 10 }}>
          <span style={{ fontFamily: 'system-ui', fontSize: 10, fontWeight: 700, letterSpacing: '3px', textTransform: 'uppercase', color: novaColor }}>
            NOVA
          </span>
          <div style={{ width: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={novaColor} strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </div>
        </div>

        {/* Hero */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, textAlign: 'center', padding: '0 20px', marginTop: 20 }}>
          <div style={{ marginBottom: 12, height: 44, width: 44, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {logo ? (
              <img src={logo} alt={brand.name} style={{ maxHeight: 44, maxWidth: 80, objectFit: 'contain' }} />
            ) : (
              <div style={{
                width: 44, height: 44, borderRadius: '50%',
                background: bubbleBg, border: `1.5px solid ${bubbleBorder}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, fontWeight: 700, color: primary,
              }}>
                {brand.name.charAt(0)}
              </div>
            )}
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: titleColor, marginBottom: 6, lineHeight: 1.2 }}>
            {identity.hero_title || `I'm ${brand.name} AI`}
          </div>
          <div style={{ fontSize: 10, fontWeight: 300, color: subtitleColor, lineHeight: 1.5 }}>
            {identity.hero_subtitle || 'How can I help you today?'}
          </div>
        </div>

        {/* Bottom */}
        <div style={{ padding: '0 10px 14px', position: 'relative', zIndex: 10 }}>
          {chips.length > 0 && (
            <div style={{ display: 'flex', gap: 5, overflowX: 'auto', marginBottom: 8, scrollbarWidth: 'none' }}>
              {chips.slice(0, 3).map(chip => (
                <span key={chip} style={{
                  flexShrink: 0, padding: '4px 8px', borderRadius: 100,
                  fontSize: 8, whiteSpace: 'nowrap',
                  background: chipBg, border: `1px solid ${chipBorder}`, color: chipColor,
                }}>
                  {chip}
                </span>
              ))}
            </div>
          )}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 5,
            borderRadius: 10, padding: '4px 4px 4px 10px',
            background: inputBg, border: `1px solid ${inputBorder}`,
          }}>
            <span style={{ flex: 1, fontSize: 9, color: inputColor }}>Ask something...</span>
            <div style={{
              width: 24, height: 24, borderRadius: 7,
              background: sendBg, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Bubble preview */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 48, height: 48, borderRadius: '50%',
          background: bubbleBg, border: `1.5px solid ${bubbleBorder}`,
          boxShadow: `0 6px 20px ${rgba(0.25)}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute', inset: -6, borderRadius: '50%',
            border: `1px solid ${rgba(0.3)}`,
            opacity: 0.6,
          }} />
          {logo ? (
            <img src={logo} alt={brand.name} style={{ height: 26, width: 'auto', objectFit: 'contain' }} />
          ) : (
            <span style={{ fontSize: 16, fontWeight: 700, color: primary }}>
              {brand.name.charAt(0)}
            </span>
          )}
        </div>
        <span style={{ fontSize: 10, color: '#999', textAlign: 'center' }}>bubble</span>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────
export default function BrandDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [isEditOpen, setIsEditOpen] = useState(false);

  const { data: brand, isLoading } = useQuery({
    queryKey: ['brand', id],
    queryFn: () => brandApi.get(id!).then(res => res.data),
    enabled: !!id,
  });

  const { data: agents = [] } = useQuery({
    queryKey: ['agents', id],
    queryFn: () => agentApi.list(id).then(res => res.data),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: (agentId: string) => agentApi.delete(agentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agents', id] }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!brand) {
    return <div className="text-gray-500 p-8">Brand not found.</div>;
  }

  const identity: BrandIdentity = brand.colors || {};
  const mode = identity.default_mode ?? 'dark';
  const primary = identity.primary_color ?? '#6366f1';
  const chips = identity.suggestion_chips
    ? identity.suggestion_chips.split(',').map(c => c.trim()).filter(Boolean)
    : [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link to="/brands" className="text-gray-400 hover:text-gray-600">
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{brand.name}</h1>
          <p className="text-sm text-gray-500">{brand.industry} · {brand.description}</p>
        </div>
        <button
          onClick={() => setIsEditOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-500"
        >
          <PencilIcon className="h-4 w-4" />
          Edit Brand
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Identity summary */}
        <div className="space-y-6">
          {/* Basic Info */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Basic Info</h2>
            <dl className="space-y-3">
              {brand.website && (
                <div>
                  <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Website</dt>
                  <dd className="mt-1 text-sm text-primary-600">
                    <a href={brand.website} target="_blank" rel="noopener noreferrer">{brand.website}</a>
                  </dd>
                </div>
              )}
              {brand.logo_url && (
                <div>
                  <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Brand Logo</dt>
                  <dd className="mt-1">
                    <img src={brand.logo_url} alt={brand.name} className="h-10 object-contain" />
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Created</dt>
                <dd className="mt-1 text-sm text-gray-700">{new Date(brand.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>

          {/* Widget Identity */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Widget Identity</h2>
            <dl className="space-y-3">
              <div className="flex items-center justify-between">
                <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Widget Mode</dt>
                <dd>
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    mode === 'dark' ? 'bg-gray-800 text-white' : 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                  }`}>
                    {mode === 'dark' ? '🌙' : '☀️'} {mode}
                  </span>
                </dd>
              </div>

              <div className="flex items-center justify-between">
                <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Accent Color</dt>
                <dd className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full border border-gray-200" style={{ background: primary }} />
                  <span className="text-sm font-mono text-gray-700">{primary}</span>
                </dd>
              </div>

              {identity.hero_title && (
                <div>
                  <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Hero Title</dt>
                  <dd className="mt-1 text-sm text-gray-700">{identity.hero_title}</dd>
                </div>
              )}

              {identity.hero_subtitle && (
                <div>
                  <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">Hero Subtitle</dt>
                  <dd className="mt-1 text-sm text-gray-700">{identity.hero_subtitle}</dd>
                </div>
              )}

              {chips.length > 0 && (
                <div>
                  <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Suggestion Chips</dt>
                  <dd className="flex flex-wrap gap-2">
                    {chips.map(chip => (
                      <span
                        key={chip}
                        className="px-3 py-1 rounded-full text-xs font-medium border"
                        style={{ background: primary + '18', borderColor: primary + '40', color: primary }}
                      >
                        {chip}
                      </span>
                    ))}
                  </dd>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 pt-1">
                {identity.chat_logo_dark_url && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Logo (Dark)</dt>
                    <dd className="bg-gray-900 rounded p-2 w-fit">
                      <img src={identity.chat_logo_dark_url} alt="dark" className="h-7 object-contain" />
                    </dd>
                  </div>
                )}
                {identity.chat_logo_light_url && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Logo (Light)</dt>
                    <dd className="bg-gray-100 rounded p-2 w-fit">
                      <img src={identity.chat_logo_light_url} alt="light" className="h-7 object-contain" />
                    </dd>
                  </div>
                )}
              </div>
            </dl>
          </div>

          {/* Agents */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900">Agents</h2>
              <Link
                to={`/agents/new?brand_id=${id}`}
                className="text-xs font-medium text-primary-600 hover:text-primary-500"
              >
                + New Agent
              </Link>
            </div>
            {agents.length === 0 ? (
              <p className="text-sm text-gray-500">No agents yet.</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {agents.map(agent => (
                  <li key={agent.id} className="py-3 flex items-center justify-between">
                    <div>
                      <Link to={`/agents/${agent.id}`} className="text-sm font-medium text-gray-900 hover:text-primary-600">
                        {agent.name}
                      </Link>
                      <p className="text-xs text-gray-400 mt-0.5">{agent.description}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        agent.status === 'active' ? 'bg-green-100 text-green-700' :
                        agent.status === 'inactive' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {agent.status}
                      </span>
                      <button
                        onClick={() => {
                          if (window.confirm('Delete this agent?')) deleteMutation.mutate(agent.id);
                        }}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right: Widget preview */}
        <div>
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-2">Widget Preview</h2>
            <p className="text-xs text-gray-400 mb-6">
              Live preview at the admin-configured <strong>{mode}</strong> mode.
            </p>
            <WidgetPreview brand={brand} />
          </div>
        </div>
      </div>

      <BrandModal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        brand={brand}
      />
    </div>
  );
}
