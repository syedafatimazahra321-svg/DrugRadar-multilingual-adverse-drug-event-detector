import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid,
} from 'recharts';

const API = 'http://localhost:8000/api';

const T = {
  navy:       '#1B3A5C',
  navyLight:  '#2E5F8A',
  teal:       '#4A9BAD',
  tealLight:  '#E8F4F7',
  bg:         '#EAF4F7',
  white:      '#FFFFFF',
  cardShadow: '0 2px 8px rgba(27,58,92,0.08)',
  border:     '#D0E8EE',
  textMain:   '#1B3A5C',
  textSub:    '#5A7A8A',
  textMuted:  '#8AAAB8',
  fontFamily: "'Segoe UI', 'Inter', sans-serif",
};

const card = {
  backgroundColor: T.white,
  borderRadius: '14px',
  boxShadow: T.cardShadow,
  border: `1px solid ${T.border}`,
  padding: '22px 24px',
  marginBottom: '20px',
  fontFamily: T.fontFamily,
};

const sectionTitle = {
  fontSize: '17px',
  fontWeight: '700',
  color: T.textMain,
  margin: '0 0 16px 0',
  letterSpacing: '-0.01em',
};

function PatternsCard({ drugName, topSymptom }) {
  const [patterns, setPatterns] = useState([]);
  useEffect(() => {
    if (!topSymptom) return;
    fetch(`${API}/drug/patterns?drug_name=${encodeURIComponent(drugName)}&symptom=${topSymptom}`)
      .then(r => r.json())
      .then(data => setPatterns(Array.isArray(data) ? data : []))
      .catch(() => setPatterns([]));
  }, [drugName, topSymptom]);
  if (patterns.length === 0) return null;
  const descMap = {
    empty_stomach: 'mention taking on empty stomach',
    daily_use: 'involve daily use',
    long_term: 'involve long-term use',
    evening: 'involve evening/bedtime dosing',
    with_food: 'mention taking with food',
    high_dose: 'mention high or extra dosing',
  };
  return (
    <div style={card}>
      <h2 style={sectionTitle}>Context Patterns — when does "{topSymptom}" occur?</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {patterns.map(p => (
          <div key={p.pattern} style={{ background: 'linear-gradient(135deg, #EAF7EF 0%, #D8F0E3 100%)', border: '1px solid #A8DFC0', borderRadius: '10px', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px', fontWeight: '800', color: '#1a7a4a', minWidth: '48px' }}>{p.percentage}%</span>
            <span style={{ fontSize: '14px', color: T.textMain }}>of <strong>{topSymptom}</strong> reports {descMap[p.pattern] || ''}</span>
            <span style={{ fontSize: '12px', color: T.textMuted, marginLeft: 'auto' }}>{p.count} posts</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function PostCard({ post }) {
  const [expanded, setExpanded] = useState(false);
  const bucketStyles = {
    critical: { bg: '#FEF2F2', border: '#FECACA', badge: '#DC2626', badgeBg: '#FEE2E2' },
    moderate: { bg: '#FFFBEB', border: '#FDE68A', badge: '#D97706', badgeBg: '#FEF3C7' },
    weak:     { bg: '#F8FAFC', border: T.border,  badge: T.textMuted, badgeBg: '#F1F5F9' },
  };
  const s = bucketStyles[post.severity_bucket] || bucketStyles.weak;

  const DRUG_WORDS = ['ibuprofen','aspirin','metformin','lisinopril','warfarin',
    'paracetamol','naproxen','sertraline','gabapentin','tramadol','levothyroxine',
    'atorvastatin','omeprazole','amoxicillin','prednisone'];
  const SYMPTOM_WORDS = ['pain','nausea','vomiting','headache','dizziness','rash',
    'fatigue','swelling','diarrhea','bleeding','insomnia','anxiety','cramps',
    'itching','fever','constipation','numbness'];

  function highlight(text) {
    if (!text) return '';
    let result = text;
    DRUG_WORDS.forEach(w => {
      const re = new RegExp(`\\b${w}\\b`, 'gi');
      result = result.replace(re, `<mark style="background:#DBEAFE;padding:1px 4px;border-radius:4px;font-weight:600">$&</mark>`);
    });
    SYMPTOM_WORDS.forEach(w => {
      const re = new RegExp(`\\b${w}\\b`, 'gi');
      result = result.replace(re, `<mark style="background:#FEE2E2;padding:1px 4px;border-radius:4px;font-weight:600">$&</mark>`);
    });
    return result;
  }

  const text = post.review_text || '';
  const displayText = expanded ? text : text.slice(0, 280);

  return (
    <div style={{ backgroundColor: s.bg, border: `1px solid ${s.border}`, borderRadius: '10px', padding: '16px', fontFamily: T.fontFamily }}>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
        <span style={{ backgroundColor: s.badgeBg, color: s.badge, fontSize: '11px', fontWeight: '700', padding: '3px 10px', borderRadius: '999px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {post.severity_bucket}
        </span>
        <span style={{ fontSize: '13px', color: T.textSub, marginLeft: '4px' }}>Confidence: <strong>{(post.confidence * 100).toFixed(0)}%</strong></span>
        <span style={{ fontSize: '13px', color: T.textSub }}>Rating: <strong>{post.rating}/10</strong></span>
      </div>
      <p style={{ fontSize: '14px', color: T.textMain, margin: 0, lineHeight: '1.6' }}
        dangerouslySetInnerHTML={{ __html: highlight(displayText) + (expanded || text.length <= 280 ? '' : '...') }}
      />
      {text.length > 280 && (
        <button onClick={() => setExpanded(!expanded)}
          style={{ fontSize: '13px', color: T.teal, background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0 0 0', fontWeight: '600' }}>
          {expanded ? '↑ Show less' : '↓ Show more'}
        </button>
      )}
      {post.symptoms_found && (
        <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
          {post.symptoms_found.split('; ').filter(Boolean).map(sym => (
            <span key={sym} style={{ backgroundColor: '#FEE2E2', color: '#B91C1C', fontSize: '11px', padding: '3px 10px', borderRadius: '999px', fontWeight: '500' }}>{sym}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DrugDetail() {
  const { drugName: rawDrugName } = useParams();
  const drugName = decodeURIComponent(rawDrugName);
  const nav = useNavigate();
  const [drug, setDrug] = useState(null);
  const [symptoms, setSymptoms] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [posts, setPosts] = useState([]);
  const [severity, setSeverity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [topSymptom, setTopSymptom] = useState('pain');
  const [postFilter, setPostFilter] = useState('ALL');

  useEffect(() => {
    const encoded = encodeURIComponent(drugName);
    const base = `${API}/drug`;
    const safe = (p) => p.catch(() => null);
    Promise.all([
      safe(fetch(`${base}/detail?drug_name=${encoded}`).then(r => r.json())),
      safe(fetch(`${base}/symptoms?drug_name=${encoded}`).then(r => r.json())),
      safe(fetch(`${base}/timeline?drug_name=${encoded}`).then(r => r.json())),
      safe(fetch(`${base}/conditions?drug_name=${encoded}`).then(r => r.json())),
      safe(fetch(`${base}/posts?drug_name=${encoded}&per_page=20`).then(r => r.json())),
      safe(fetch(`${base}/severity?drug_name=${encoded}`).then(r => r.json())),
    ]).then(([drugData, sym, time, cond, postsData, sev]) => {
      setDrug(drugData || null);
      setSymptoms(Array.isArray(sym) ? sym : []);
      setTopSymptom(Array.isArray(sym) && sym.length > 0 ? sym[0].symptom : 'pain');
      setTimeline(Array.isArray(time) ? time : []);
      setConditions(Array.isArray(cond) ? cond : []);
      setPosts(postsData?.posts || []);
      setSeverity(Array.isArray(sev) ? sev : []);
      setLoading(false);
    });
  }, [drugName]);

  if (loading) return (
    <div style={{ minHeight: '100vh', background: T.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: T.fontFamily }}>
      <div style={{ textAlign: 'center', color: T.textSub }}>
        <div style={{ fontSize: '32px', marginBottom: '12px' }}>💊</div>
        <div style={{ fontSize: '16px', fontWeight: '600' }}>Loading {drugName}...</div>
      </div>
    </div>
  );

  if (!drug || drug.detail) return (
    <div style={{ minHeight: '100vh', background: T.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: T.fontFamily }}>
      <div style={{ textAlign: 'center', color: '#DC2626' }}>
        <div style={{ fontSize: '32px', marginBottom: '12px' }}>⚠️</div>
        <div style={{ fontSize: '16px', fontWeight: '600' }}>Drug not found.</div>
      </div>
    </div>
  );

  const signalColors = {
    high:   { bg: '#FEE2E2', color: '#DC2626' },
    medium: { bg: '#FEF3C7', color: '#D97706' },
    low:    { bg: '#D1FAE5', color: '#059669' },
  };
  const sig = signalColors[drug.signal_level] || signalColors.low;

  // Plain-English summary
  const topCondition = conditions.length > 0 ? conditions[0] : null;
  const topConditionName = topCondition?.condition || null;
  const topConditionSeverity = topCondition ? parseFloat(topCondition.avg_severity).toFixed(2) : null;
  const topSymptomLabel = symptoms.length > 0 ? symptoms[0].symptom : null;
  const summaryText = drug && [
    `${drugName.charAt(0).toUpperCase() + drugName.slice(1)} shows ${drug.signal_level?.toUpperCase() || '—'} signal.`,
    `${(drug.ade_rate * 100).toFixed(1)}% of ${drug.total_reviews?.toLocaleString() || '—'} reviews report adverse events.`,
    topSymptomLabel ? `Most common complaint is ${topSymptomLabel}.` : null,
    topConditionName && topConditionSeverity ? `${topConditionName} patients show the highest severity (${topConditionSeverity} avg).` : null,
  ].filter(Boolean).join(' ');

  // Filtered posts
  const filteredPosts = postFilter === 'ALL'
    ? posts
    : posts.filter(p => p.severity_bucket?.toLowerCase() === postFilter.toLowerCase());

  return (
    <div style={{ minHeight: '100vh', background: T.bg, fontFamily: T.fontFamily }}>
      <div style={{ maxWidth: '1120px', margin: '0 auto', padding: '28px 24px' }}>

        <button onClick={() => nav('/')}
          style={{ background: 'none', border: 'none', color: T.teal, cursor: 'pointer', fontSize: '14px', fontWeight: '600', padding: '0 0 18px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
          ← Back to Dashboard
        </button>

        {/* Plain-English Summary Card */}
        {summaryText && (
          <div style={{ background: `linear-gradient(135deg, #1B3A5C 0%, #2E5F8A 100%)`, borderRadius: '14px', padding: '20px 24px', marginBottom: '16px', boxShadow: '0 4px 20px rgba(27,58,92,0.2)', display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <span style={{ fontSize: '26px', flexShrink: 0 }}>🩺</span>
            <p style={{ margin: 0, fontSize: '15px', lineHeight: '1.7', color: '#E0F0FF', fontFamily: T.fontFamily }}>
              {summaryText}
            </p>
          </div>
        )}

        {/* Header */}
        <div style={{ background: `linear-gradient(135deg, ${T.navy} 0%, ${T.navyLight} 100%)`, borderRadius: '16px', padding: '28px 32px', marginBottom: '22px', boxShadow: '0 4px 20px rgba(27,58,92,0.2)' }}>
          {/* Drug name centered */}
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', justifyContent: 'center' }}>
              <h1 style={{ fontSize: '32px', fontWeight: '800', color: T.white, textTransform: 'capitalize', margin: 0 }}>{drugName}</h1>
              <span style={{ backgroundColor: sig.bg, color: sig.color, fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '999px', letterSpacing: '0.05em' }}>
                ● {drug.signal_level?.toUpperCase()} SIGNAL
              </span>
            </div>
          </div>

          {/* Stat tabs row */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            {[
              { label: 'Total Reviews', value: drug.total_reviews?.toLocaleString(), icon: '📋' },
              { label: 'ADE Flags', value: drug.ade_count?.toLocaleString(), icon: '🚩' },
              { label: 'ADE Rate', value: `${(drug.ade_rate * 100).toFixed(1)}%`, icon: '📊' },
            ].map(({ label, value, icon }) => (
              <div key={label} style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '12px', padding: '14px 24px', textAlign: 'center', minWidth: '130px' }}>
                <div style={{ fontSize: '18px', marginBottom: '4px' }}>{icon}</div>
                <div style={{ fontSize: '22px', fontWeight: '800', color: T.white, lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: '11px', color: '#93C5FD', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '4px' }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Download button bottom-right */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
            <a href={`${API}/drug/report?drug_name=${encodeURIComponent(drugName)}`}
              target="_blank" rel="noreferrer"
              style={{ backgroundColor: T.white, color: T.navy, padding: '10px 20px', borderRadius: '10px', fontSize: '13px', fontWeight: '700', textDecoration: 'none', whiteSpace: 'nowrap', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
              📄 Download PDF Report
            </a>
          </div>
        </div>

        {/* Symptoms + Severity */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={card}>
            <h2 style={sectionTitle}>Top Reported Symptoms</h2>
            {symptoms.length === 0
              ? <p style={{ color: T.textMuted, fontSize: '14px' }}>No symptom data.</p>
              : (
                <ResponsiveContainer width='100%' height={240}>
                  <BarChart data={symptoms} layout='vertical'>
                    <XAxis type='number' tick={{ fontSize: 11 }} />
                    <YAxis type='category' dataKey='symptom' width={95} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey='count' fill={T.teal} radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
          </div>

          <div style={card}>
            <h2 style={sectionTitle}>Severity Breakdown</h2>
            {severity.map(s => {
              const sevColors = { critical: '#DC2626', moderate: '#D97706', weak: T.textMuted };
              const sevBg    = { critical: '#FEE2E2', moderate: '#FEF3C7', weak: '#F1F5F9' };
              const total = severity.reduce((a, x) => a + x.count, 0);
              const pct = total ? Math.round(s.count / total * 100) : 0;
              return (
                <div key={s.severity_bucket} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px', alignItems: 'center' }}>
                    <span style={{ backgroundColor: sevBg[s.severity_bucket], color: sevColors[s.severity_bucket], fontSize: '11px', fontWeight: '700', padding: '2px 10px', borderRadius: '999px', textTransform: 'uppercase' }}>
                      {s.severity_bucket}
                    </span>
                    <span style={{ color: T.textSub, fontWeight: '600' }}>{s.count} <span style={{ color: T.textMuted, fontWeight: '400' }}>({pct}%)</span></span>
                  </div>
                  <div style={{ backgroundColor: '#EEF2F5', borderRadius: '999px', height: '8px' }}>
                    <div style={{ backgroundColor: sevColors[s.severity_bucket], width: `${pct}%`, height: '8px', borderRadius: '999px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Timeline */}
        <div style={card}>
          <h2 style={sectionTitle}>ADE Reports Over Time</h2>
          {timeline.length === 0
            ? <p style={{ color: T.textMuted, fontSize: '14px' }}>No timeline data.</p>
            : (
              <ResponsiveContainer width='100%' height={200}>
                <LineChart data={timeline}>
                  <CartesianGrid strokeDasharray='3 3' stroke='#E8F0F3' />
                  <XAxis dataKey='month' tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type='monotone' dataKey='count' stroke='#E05252' strokeWidth={2.5} dot={{ r: 4, fill: '#E05252' }} />
                </LineChart>
              </ResponsiveContainer>
            )}
        </div>

        {/* Conditions */}
        {conditions.length > 0 && (
          <div style={card}>
            <h2 style={sectionTitle}>Condition Breakdown</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: T.tealLight }}>
                  <th style={{ textAlign: 'left', padding: '10px 12px', color: T.textSub, fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Condition</th>
                  <th style={{ textAlign: 'center', padding: '10px 12px', color: T.textSub, fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ADE Reports</th>
                  <th style={{ textAlign: 'center', padding: '10px 12px', color: T.textSub, fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Avg Severity</th>
                </tr>
              </thead>
              <tbody>
                {conditions.map((c, i) => {
                  const sevVal = parseFloat(c.avg_severity);
                  const sevColor = sevVal > 0.6 ? '#DC2626' : sevVal > 0.3 ? '#D97706' : T.textMuted;
                  return (
                    <tr key={i} style={{ backgroundColor: i % 2 === 0 ? T.white : T.tealLight, borderBottom: `1px solid ${T.border}` }}>
                      <td style={{ padding: '10px 12px', color: T.textMain, fontWeight: '500' }}>{c.condition || 'Unknown'}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: '600', color: T.textMain }}>{c.count}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'center', color: sevColor, fontWeight: '700' }}>{sevVal.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Most At-Risk Patient Group */}
            {topCondition && (
              <div style={{ marginTop: '16px', background: 'linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%)', border: '1px solid #FECACA', borderRadius: '12px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '22px' }}>⚠️</span>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: '#B91C1C', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>Highest Risk Group</div>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: '#7F1D1D' }}>
                    {topCondition.condition || 'Unknown'} patients
                    <span style={{ fontWeight: '400', color: '#991B1B' }}> — avg severity {parseFloat(topCondition.avg_severity).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <PatternsCard drugName={drugName} topSymptom={topSymptom} />

        {/* Flagged Posts */}
        <div style={card}>
          <h2 style={sectionTitle}>
            Flagged Posts — Evidence{' '}
            <span style={{ fontSize: '13px', color: T.textMuted, fontWeight: '400' }}>({filteredPosts.length} shown)</span>
          </h2>

          {/* Filter buttons */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {['ALL', 'CRITICAL', 'MODERATE'].map(f => (
              <button
                key={f}
                onClick={() => setPostFilter(f)}
                style={{
                  padding: '6px 16px',
                  borderRadius: '999px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  border: postFilter === f ? 'none' : `1px solid ${T.border}`,
                  background: postFilter === f
                    ? (f === 'CRITICAL' ? '#DC2626' : f === 'MODERATE' ? '#D97706' : T.navy)
                    : T.white,
                  color: postFilter === f ? '#FFFFFF' : T.textSub,
                  transition: 'all 0.15s',
                  letterSpacing: '0.05em',
                }}
              >
                {f}
              </button>
            ))}
          </div>

          {filteredPosts.length === 0
            ? <p style={{ color: T.textMuted, fontSize: '14px' }}>No posts match this filter.</p>
            : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {filteredPosts.map(p => <PostCard key={p.id} post={p} />)}
              </div>
            )}
        </div>

      </div>
    </div>
  );
}
