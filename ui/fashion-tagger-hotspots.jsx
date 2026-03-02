import { useState, useRef, useCallback } from "react";

// ─── API ──────────────────────────────────────────────────────────────────────
async function analyzeImage(base64Image, mediaType) {
  const prompt = `You are a precision fashion AI. Analyze this clothing image carefully.

Return ONLY valid JSON — no markdown, no code fences:
{
  "product_type": "e.g. wrap dress",
  "tags": [
    {
      "label": "tag name",
      "category": "one of: neckline|sleeve|fit|color|pattern|style|occasion|length|material|closure|detail|season"
    }
  ],
  "description": "2-3 sentence evocative marketing copy. Bold key product features with **double asterisks**.",
  "accessories": [
    { "label": "accessory name", "type": "shoes|bag|jewelry|hat|belt|sunglasses|watch|scarf|socks|other" },
    { "label": "accessory name", "type": "shoes|bag|jewelry|hat|belt|sunglasses|watch|scarf|socks|other" },
    { "label": "accessory name", "type": "shoes|bag|jewelry|hat|belt|sunglasses|watch|scarf|socks|other" }
  ]
}

Rules:
- 6-9 tags total, covering different aspects of the garment
- Tags should be specific: "v-neck" not "neckline", "mustard yellow" not "yellow"
- Order tags from top of garment to bottom`;

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1200,
      messages: [{
        role: "user",
        content: [
          { type: "image", source: { type: "base64", media_type: mediaType, data: base64Image } },
          { type: "text", text: prompt }
        ]
      }]
    })
  });

  if (!response.ok) throw new Error(`API error ${response.status}`);
  const data = await response.json();
  const raw = data.content[0].text;
  const clean = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```\s*$/, "").trim();
  return JSON.parse(clean);
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function parseBold(text) {
  const parts = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ t: text.slice(last, m.index), b: false });
    parts.push({ t: m[1], b: true });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ t: text.slice(last), b: false });
  return parts;
}

const ACC_EMOJI = {
  shoes: "👟", bag: "👜", jewelry: "💍", hat: "🧢",
  belt: "🪢", sunglasses: "🕶️", watch: "⌚", scarf: "🧣",
  socks: "🧦", other: "✨",
};

// Category → color + icon
const CAT = {
  neckline: { color: "#818CF8", icon: "◎" },
  sleeve:   { color: "#A78BFA", icon: "⌒" },
  fit:      { color: "#C084FC", icon: "⇕" },
  color:    { color: "#FBBF24", icon: "◉" },
  pattern:  { color: "#F87171", icon: "▦" },
  material: { color: "#F472B6", icon: "◈" },
  style:    { color: "#34D399", icon: "✦" },
  occasion: { color: "#2DD4BF", icon: "◆" },
  season:   { color: "#38BDF8", icon: "✿" },
  length:   { color: "#FB923C", icon: "↕" },
  closure:  { color: "#A3E635", icon: "⊕" },
  detail:   { color: "#FB7185", icon: "◑" },
};
const fallback = { color: "#94A3B8", icon: "◦" };

// ─── Tag Chip ─────────────────────────────────────────────────────────────────
function TagChip({ tag, index, revealed }) {
  const { color, icon } = CAT[tag.category] || fallback;
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "6px 13px 6px 9px",
      borderRadius: 40,
      border: `1px solid ${color}40`,
      background: `${color}12`,
      opacity: revealed ? 1 : 0,
      transform: revealed ? "translateY(0) scale(1)" : "translateY(6px) scale(0.93)",
      transition: `opacity 0.3s ease, transform 0.35s cubic-bezier(0.34,1.56,0.64,1)`,
      transitionDelay: `${index * 0.055}s`,
    }}>
      <span style={{ fontSize: 11, color, lineHeight: 1, flexShrink: 0 }}>{icon}</span>
      <span style={{
        fontSize: 13, fontWeight: 600,
        color: "rgba(255,255,255,0.88)",
        fontFamily: "'Syne',sans-serif",
        letterSpacing: "-0.1px",
      }}>
        {tag.label}
      </span>
      <span style={{
        fontSize: 10, color: `${color}bb`,
        fontWeight: 500, letterSpacing: "0.04em",
        marginLeft: 1,
      }}>
        {tag.category}
      </span>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function FashionTagger() {
  const [dataUrl, setDataUrl]     = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [result, setResult]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [dragOver, setDragOver]   = useState(false);
  const [revealed, setRevealed]   = useState(false);
  const fileRef = useRef(null);

  const handleFile = useCallback(async (file) => {
    if (!file?.type.startsWith("image/")) return;
    setError(null); setResult(null); setRevealed(false);
    setImageFile(file);
    setDataUrl(await fileToDataUrl(file));
  }, []);

  const handleAnalyze = async () => {
    if (!dataUrl || !imageFile) return;
    setLoading(true); setError(null); setResult(null); setRevealed(false);
    try {
      const b64 = dataUrl.split(",")[1];
      const data = await analyzeImage(b64, imageFile.type);
      setResult(data);
      setTimeout(() => setRevealed(true), 60);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={S.root}>
      <style>{CSS}</style>

      {/* ── Header ── */}
      <header style={S.header}>
        <div style={S.logo}>
          <div style={S.logoMark}>✦</div>
          <span style={S.logoText}>StyleTag<span style={S.logoAI}> AI</span></span>
        </div>
        <p style={S.tagline}>Vision-powered fashion intelligence</p>
      </header>

      <main style={S.main}>

        {/* ── Drop zone ── */}
        {!dataUrl && (
          <div
            style={{ ...S.dropzone, ...(dragOver ? S.dropzoneHover : {}) }}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => fileRef.current?.click()}
          >
            <div style={S.uploadInner}>
              <div style={S.uploadRing}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(99,102,241,0.85)" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p style={S.uploadLabel}>Drop your fashion image here</p>
              <p style={S.uploadSub}>JPG · PNG · WEBP</p>
            </div>
          </div>
        )}

        {/* ── Image + results ── */}
        {dataUrl && (
          <>
            {/* Image card */}
            <div style={S.imageCard}>
              <img src={dataUrl} alt="Fashion item" style={S.img} />

              {/* Bottom gradient */}
              <div style={S.gradBottom} />

              {/* Product type badge — bottom left */}
              {result && revealed && (
                <div style={S.productBadge}>
                  <span style={S.productBadgeText}>{result.product_type}</span>
                </div>
              )}

              {/* Change button — top right */}
              <button style={S.changeBtn} onClick={() => fileRef.current?.click()}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Change
              </button>

              {/* Analyze button — centred at bottom */}
              {!result && !loading && (
                <button style={S.analyzeBtn} onClick={handleAnalyze}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  Analyze Fashion
                </button>
              )}

              {/* Loading overlay */}
              {loading && (
                <div style={S.loadingOverlay}>
                  <div style={S.spinner} />
                  <p style={S.loadingText}>Analyzing with AI vision…</p>
                </div>
              )}
            </div>

            {/* ── Results panel ── */}
            {result && revealed && (
              <div style={S.results}>

                {/* Tags */}
                <div style={S.tagsWrap}>
                  {result.tags.map((tag, i) => (
                    <TagChip key={i} tag={tag} index={i} revealed={revealed} />
                  ))}
                </div>

                <div style={S.divider} />

                {/* Style story */}
                <div style={S.storyBlock}>
                  <span style={S.eyebrow}>✦ Style Story</span>
                  <p style={S.storyText}>
                    {parseBold(result.description).map((p, i) =>
                      p.b
                        ? <strong key={i} style={S.bold}>{p.t}</strong>
                        : <span key={i}>{p.t}</span>
                    )}
                  </p>
                </div>

                {/* Accessories */}
                {result.accessories?.length > 0 && (
                  <>
                    <div style={S.divider} />
                    <div style={S.accsBlock}>
                      <span style={S.eyebrow}>Pair with</span>
                      <div style={S.accsGrid}>
                        {result.accessories.map((acc, i) => {
                          const label = typeof acc === "object" ? acc.label : acc;
                          const type  = typeof acc === "object" ? (acc.type || "other") : "other";
                          return (
                            <div key={i} style={S.accChip}>
                              <span style={S.accEmoji}>{ACC_EMOJI[type] ?? ACC_EMOJI.other}</span>
                              <span style={S.accLabel}>{label}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </>
        )}

        {/* Error */}
        {error && (
          <div style={S.errorBox}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}
      </main>

      <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])} />
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const S = {
  root: {
    minHeight: "100vh", background: "#07090F",
    fontFamily: "'DM Sans',sans-serif", color: "#fff",
  },
  header: {
    padding: "18px 24px",
    display: "flex", alignItems: "center", justifyContent: "space-between",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  logo: { display: "flex", alignItems: "center", gap: 10 },
  logoMark: {
    width: 32, height: 32,
    background: "linear-gradient(135deg,#6366F1,#EC4899)",
    borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 14, color: "#fff",
  },
  logoText: { fontFamily: "'Syne',sans-serif", fontSize: 20, fontWeight: 800, letterSpacing: "-0.3px" },
  logoAI: {
    background: "linear-gradient(90deg,#6366F1,#EC4899)",
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
  },
  tagline: { fontSize: 11, color: "rgba(255,255,255,0.28)", letterSpacing: "0.06em", textTransform: "uppercase" },

  main: {
    maxWidth: 520, margin: "0 auto", padding: "24px 16px 80px",
    display: "flex", flexDirection: "column", gap: 0,
  },

  // Drop zone
  dropzone: {
    border: "2px dashed rgba(99,102,241,0.22)", borderRadius: 18,
    background: "rgba(255,255,255,0.025)", cursor: "pointer",
    minHeight: 240, display: "flex", alignItems: "center", justifyContent: "center",
    transition: "all 0.2s",
  },
  dropzoneHover: {
    border: "2px dashed rgba(99,102,241,0.65)",
    background: "rgba(99,102,241,0.06)", transform: "scale(1.008)",
  },
  uploadInner: { display: "flex", flexDirection: "column", alignItems: "center", gap: 10 },
  uploadRing: {
    width: 66, height: 66, borderRadius: 16,
    background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.18)",
    display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 6,
  },
  uploadLabel: { fontFamily: "'Syne',sans-serif", fontSize: 15, fontWeight: 700, color: "rgba(255,255,255,0.65)" },
  uploadSub: { fontSize: 12, color: "rgba(255,255,255,0.22)", letterSpacing: "0.07em" },

  // Image card — natural height, no cropping
  imageCard: {
    position: "relative", width: "100%",
    borderRadius: 18, overflow: "hidden",
    background: "#0d1117",
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
    flexShrink: 0,
  },
  img: {
    width: "100%", display: "block",
    maxHeight: 520, objectFit: "contain",   // contain = no cropping, full image visible
    background: "#0d1117",
  },

  gradBottom: {
    position: "absolute", bottom: 0, left: 0, right: 0, height: "30%",
    background: "linear-gradient(to top,rgba(7,9,15,0.85),transparent)",
    pointerEvents: "none",
  },

  productBadge: {
    position: "absolute", bottom: 14, left: 14,
    background: "rgba(7,9,15,0.75)", backdropFilter: "blur(12px)",
    border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8,
    padding: "5px 11px", animation: "fadeUp 0.4s ease both",
  },
  productBadgeText: {
    fontFamily: "'Syne',sans-serif", fontSize: 12, fontWeight: 700,
    color: "rgba(255,255,255,0.9)", textTransform: "capitalize",
  },

  changeBtn: {
    position: "absolute", top: 10, right: 10,
    display: "flex", alignItems: "center", gap: 5,
    background: "rgba(7,9,15,0.7)", backdropFilter: "blur(8px)",
    border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8,
    padding: "5px 11px", fontSize: 12, fontWeight: 600,
    color: "rgba(255,255,255,0.65)", cursor: "pointer", fontFamily: "'DM Sans',sans-serif",
  },
  analyzeBtn: {
    position: "absolute", bottom: 16, left: "50%", transform: "translateX(-50%)",
    display: "flex", alignItems: "center", gap: 8,
    background: "linear-gradient(135deg,#6366F1,#EC4899)", border: "none",
    borderRadius: 40, padding: "13px 28px", fontSize: 15, fontWeight: 700,
    fontFamily: "'Syne',sans-serif", color: "#fff", cursor: "pointer",
    boxShadow: "0 8px 28px rgba(99,102,241,0.45)", whiteSpace: "nowrap",
  },

  loadingOverlay: {
    position: "absolute", inset: 0,
    background: "rgba(7,9,15,0.7)", backdropFilter: "blur(6px)",
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 14,
  },
  spinner: {
    width: 36, height: 36,
    border: "3px solid rgba(99,102,241,0.18)", borderTopColor: "#6366F1",
    borderRadius: "50%", animation: "spin 0.75s linear infinite",
  },
  loadingText: { fontSize: 13, color: "rgba(255,255,255,0.5)", fontFamily: "'Syne',sans-serif" },

  // Results — flush below image card
  results: {
    background: "rgba(255,255,255,0.035)",
    border: "1px solid rgba(255,255,255,0.07)", borderTop: "none",
    borderRadius: "0 0 18px 18px",
    padding: "16px 16px 20px",
    display: "flex", flexDirection: "column", gap: 14,
  },
  tagsWrap: { display: "flex", flexWrap: "wrap", gap: 6 },

  divider: {
    height: 1,
    background: "linear-gradient(90deg,transparent,rgba(255,255,255,0.07),transparent)",
  },

  storyBlock: { display: "flex", flexDirection: "column", gap: 7 },
  eyebrow: {
    fontSize: 10, fontWeight: 700, color: "#818CF8",
    letterSpacing: "0.13em", textTransform: "uppercase", fontFamily: "'Syne',sans-serif",
  },
  storyText: { fontSize: 15, lineHeight: 1.78, color: "rgba(255,255,255,0.65)" },
  bold: { color: "#fff", fontWeight: 700 },

  accsBlock: { display: "flex", flexDirection: "column", gap: 10 },
  accsGrid: { display: "flex", flexWrap: "wrap", gap: 7 },
  accChip: {
    display: "flex", alignItems: "center", gap: 7,
    background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 22, padding: "6px 14px 6px 9px",
  },
  accEmoji: { fontSize: 15, lineHeight: 1, flexShrink: 0 },
  accLabel: { fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.7)", fontFamily: "'DM Sans',sans-serif" },

  errorBox: {
    display: "flex", alignItems: "center", gap: 8,
    background: "rgba(239,68,68,0.09)", border: "1px solid rgba(239,68,68,0.28)",
    borderRadius: 10, padding: "10px 14px", color: "#F87171", fontSize: 13, marginTop: 14,
  },
};

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes fadeUp  { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
`;
