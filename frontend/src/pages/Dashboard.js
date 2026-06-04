import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

function SignalBadge({ level }) {
  const styles = {
    high:   { bg: 'rgba(185,28,28,0.10)', color: '#b91c1c', border: 'rgba(185,28,28,0.25)', label: '● HIGH' },
    medium: { bg: 'rgba(161,98,7,0.10)',  color: '#a16207', border: 'rgba(161,98,7,0.25)',  label: '● MEDIUM' },
    low:    { bg: 'rgba(21,128,61,0.10)', color: '#15803d', border: 'rgba(21,128,61,0.25)', label: '● LOW' },
  };
  const s = styles[level] || { bg: '#f3f4f6', color: '#6b7280', border: '#e5e7eb', label: '● N/A' };
  return (
    <span style={{
      background: s.bg, color: s.color,
      border: `1px solid ${s.border}`,
      padding: '4px 12px', borderRadius: '999px',
      fontSize: '11px', fontWeight: '700', letterSpacing: '0.05em',
      whiteSpace: 'nowrap'
    }}>
      {s.label}
    </span>
  );
}

export default function Dashboard({ user }) {
  const [drugs, setDrugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    fetch(`${API}/dashboard`)
      .then(r => r.json())
      .then(data => {
        if (user && user.drugs && user.drugs.length > 0) {
          const filtered = data.filter(d =>
            user.drugs.map(x => x.trim().toLowerCase()).includes(d.drug_name.toLowerCase())
          );
          setDrugs(filtered.length > 0 ? filtered : data);
        } else {
          setDrugs(data);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [user]);

  const handleSearch = async (val) => {
    setSearch(val);
    if (val.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const res = await fetch(`${API}/search?q=${encodeURIComponent(val)}`);
      const data = await res.json();
      setSearchResults(data);
    } catch (err) { console.error(err); }
    setSearching(false);
  };

  const totalReviews = drugs.reduce((a, d) => a + d.total_reviews, 0);
  const totalADE = drugs.reduce((a, d) => a + d.ade_count, 0);
  const highSignal = drugs.filter(d => d.signal_level === 'high').length;

  if (loading) {
    return (
      <>
        <style>{dashStyle}</style>
        <div className="db-bg">
          <div style={{ textAlign: 'center', color: '#5b9ab5', fontSize: '16px', paddingTop: '120px', fontFamily: "'DM Sans', sans-serif" }}>
            Loading dashboard...
          </div>
        </div>
      </>
    );
  }

  const stats = [
    { label: 'Drugs Monitored', value: drugs.length, icon: '💊', accent: '#2e86ab' },
    { label: 'Total Reviews',   value: totalReviews.toLocaleString(), icon: '📋', accent: '#2e86ab' },
    { label: 'ADE Flags',       value: totalADE.toLocaleString(), icon: '⚠️', accent: '#c0392b' },
    { label: 'High Signal',     value: highSignal, icon: '🔴', accent: '#c0392b' },
  ];

  return (
    <>
      <style>{dashStyle}</style>
      <div className="db-bg">



        <div className="db-content">

          {/* Page header */}
          <div className="db-page-header">
            <div>
              <h1 className="db-page-title">Safety Dashboard</h1>
              <p className="db-page-sub">Click any drug to investigate its full adverse event profile</p>
            </div>
            <div className="db-header-pill">Live Monitoring</div>
          </div>

          {/* Stat cards */}
          <div className="db-stats-grid">
            {stats.map(s => (
              <div className="db-stat-card" key={s.label}>
                <div className="db-stat-icon">{s.icon}</div>
                <div className="db-stat-value" style={{ color: s.accent }}>{s.value}</div>
                <div className="db-stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Search */}
          <div className="db-search-wrap">
            <span className="db-search-icon">🔍</span>
            <input
              className="db-search-input"
              value={search}
              onChange={e => handleSearch(e.target.value)}
              placeholder="Search any drug... (e.g. ibuprofen, sertraline)"
            />
            {searching && <span className="db-search-spinner">Searching...</span>}

            {searchResults.length > 0 && (
              <div className="db-search-dropdown">
                {searchResults.map(d => (
                  <div
                    key={d.drug_name}
                    className="db-search-item"
                    onClick={() => { nav(`/drug/${encodeURIComponent(d.drug_name)}`); setSearchResults([]); setSearch(''); }}
                  >
                    <span className="db-search-item-name">{d.drug_name}</span>
                    <span className="db-search-item-meta">{d.total_reviews} reviews &nbsp;·&nbsp; ADE: {(d.ade_rate * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Table card */}
          <div className="db-table-card">
            <div className="db-table-header-row">
              <span className="db-table-title">Monitored Drugs</span>
              <span className="db-table-count">{drugs.length} drugs</span>
            </div>

            <div className="db-table-scroll">
              <table className="db-table">
                <thead>
                  <tr className="db-thead-tr">
                    {['Drug', 'Signal', 'Total Reviews', 'ADE Count', 'Critical', 'ADE Rate'].map(h => (
                      <th key={h} className={`db-th ${h === 'Drug' ? 'db-th-left' : 'db-th-center'}`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {drugs.map((d, i) => (
                    <tr
                      key={d.drug_name}
                      className="db-tr"
                      style={{ background: i % 2 === 0 ? '#fff' : '#f8fbfd' }}
                      onClick={() => nav(`/drug/${encodeURIComponent(d.drug_name)}`)}
                      onMouseEnter={e => e.currentTarget.style.background = '#eaf5f9'}
                      onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : '#f8fbfd'}
                    >
                      <td className="db-td db-td-drug">{d.drug_name}</td>
                      <td className="db-td db-td-center"><SignalBadge level={d.signal_level} /></td>
                      <td className="db-td db-td-center">{d.total_reviews.toLocaleString()}</td>
                      <td className="db-td db-td-center db-td-ade">{d.ade_count.toLocaleString()}</td>
                      <td className="db-td db-td-center db-td-critical">{d.critical_count}</td>
                      <td className="db-td db-td-center">
                        <span className="db-rate-pill">{(d.ade_rate * 100).toFixed(1)}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}

const dashStyle = `
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.db-bg {
  min-height: 100vh;
  background: linear-gradient(160deg, #daf0f7 0%, #c2e8f0 40%, #a8d8ea 100%);
  font-family: 'DM Sans', sans-serif;
}

/* ── Navbar ── */
.db-navbar {
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(91,179,196,0.2);
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 16px rgba(30,100,140,0.07);
}
.db-navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.db-nav-logo { display: flex; align-items: baseline; gap: 12px; }
.db-nav-logo-text {
  font-family: 'Playfair Display', serif;
  font-size: 22px; font-weight: 700; color: #1a5276;
}
.db-nav-logo-sub {
  font-size: 11px; letter-spacing: 0.14em;
  text-transform: uppercase; color: #5b9ab5; font-weight: 500;
}
.db-nav-user { display: flex; align-items: center; gap: 8px; }
.db-nav-company {
  font-size: 14px; font-weight: 600; color: #1a3a4a;
}
.db-nav-dot {
  width: 4px; height: 4px; border-radius: 50%;
  background: #7eb8c8;
}
.db-nav-role { font-size: 13px; color: #5b9ab5; }

/* ── Content ── */
.db-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 36px 40px 60px;
}

/* ── Page header ── */
.db-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 28px;
}
.db-page-title {
  font-family: 'Playfair Display', serif;
  font-size: 30px; font-weight: 700; color: #1a3a4a;
  margin-bottom: 6px;
}
.db-page-sub { font-size: 14px; color: #5b7a8a; font-weight: 400; }
.db-header-pill {
  background: linear-gradient(135deg, #2e86ab, #1a6080);
  color: white;
  font-size: 12px; font-weight: 600;
  letter-spacing: 0.06em;
  padding: 6px 16px; border-radius: 999px;
  box-shadow: 0 2px 10px rgba(46,134,171,0.3);
  white-space: nowrap;
  margin-top: 6px;
}

/* ── Stat cards ── */
.db-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 28px;
}
.db-stat-card {
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px 20px 20px;
  text-align: center;
  box-shadow: 0 2px 16px rgba(30,100,140,0.10), 0 0 0 1px rgba(91,179,196,0.18);
  transition: transform 0.18s, box-shadow 0.18s;
}
.db-stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 28px rgba(30,100,140,0.15), 0 0 0 1px rgba(91,179,196,0.25);
}
.db-stat-icon { font-size: 22px; margin-bottom: 10px; }
.db-stat-value {
  font-family: 'Playfair Display', serif;
  font-size: 34px; font-weight: 700; line-height: 1; margin-bottom: 6px;
}
.db-stat-label {
  font-size: 12px; color: #7a9aaa; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
}

/* ── Search ── */
.db-search-wrap {
  position: relative;
  margin-bottom: 24px;
}
.db-search-icon {
  position: absolute; left: 16px; top: 50%;
  transform: translateY(-50%);
  font-size: 16px; pointer-events: none;
}
.db-search-input {
  width: 100%;
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(10px);
  border: 1.5px solid rgba(91,179,196,0.35);
  border-radius: 14px;
  padding: 16px 18px 16px 50px;
  font-size: 16px;
  font-family: 'DM Sans', sans-serif;
  color: #1a3a4a;
  outline: none;
  box-shadow: 0 2px 12px rgba(30,100,140,0.07);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.db-search-input:focus {
  border-color: #5bb3c4;
  box-shadow: 0 0 0 3px rgba(91,179,196,0.15), 0 2px 12px rgba(30,100,140,0.08);
  background: #fff;
}
.db-search-input::placeholder { color: #9bbfcc; font-size: 16px; }
.db-search-spinner {
  position: absolute; right: 16px; top: 50%;
  transform: translateY(-50%);
  font-size: 12px; color: #7eb8c8;
}
.db-search-dropdown {
  position: absolute; top: calc(100% + 6px);
  left: 0; right: 0; z-index: 20;
  background: rgba(255,255,255,0.97);
  border: 1.5px solid rgba(91,179,196,0.3);
  border-radius: 14px;
  box-shadow: 0 8px 28px rgba(30,100,140,0.14);
  overflow: hidden;
}
.db-search-item {
  padding: 12px 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eaf5f9;
  transition: background 0.12s;
}
.db-search-item:last-child { border-bottom: none; }
.db-search-item:hover { background: #eaf5f9; }
.db-search-item-name {
  font-size: 16px; font-weight: 600; color: #1a5276;
  text-transform: capitalize;
}
.db-search-item-meta { font-size: 14px; color: #7a9aaa; }

/* ── Table card ── */
.db-table-card {
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  box-shadow: 0 2px 20px rgba(30,100,140,0.10), 0 0 0 1px rgba(91,179,196,0.18);
  overflow: hidden;
}
.db-table-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px 16px;
  border-bottom: 1px solid rgba(91,179,196,0.15);
}
.db-table-title {
  font-family: 'Playfair Display', serif;
  font-size: 18px; font-weight: 700; color: #1a3a4a;
}
.db-table-count {
  font-size: 12px; color: #7a9aaa; font-weight: 500;
  background: rgba(91,179,196,0.12);
  padding: 4px 12px; border-radius: 999px;
}
.db-table-scroll { overflow-x: auto; }
.db-table {
  width: 100%; border-collapse: collapse;
  font-size: 14px;
}
.db-thead-tr {
  background: linear-gradient(135deg, #1a5276 0%, #2e86ab 100%);
}
.db-th {
  padding: 14px 20px;
  font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.9);
  text-transform: uppercase; letter-spacing: 0.08em;
  white-space: nowrap;
}
.db-th-left { text-align: left; }
.db-th-center { text-align: center; }
.db-tr { cursor: pointer; transition: background 0.12s; }
.db-td { padding: 14px 20px; color: #2c4a5a; }
.db-td-drug {
  font-weight: 700; color: #1a5276;
  text-transform: capitalize; font-size: 14px;
}
.db-td-center { text-align: center; }
.db-td-ade { color: #c0392b; font-weight: 600; }
.db-td-critical { color: #922b21; font-weight: 600; }
.db-rate-pill {
  background: rgba(46,134,171,0.1);
  color: #1a6080;
  border: 1px solid rgba(46,134,171,0.2);
  padding: 3px 10px; border-radius: 999px;
  font-size: 13px; font-weight: 600;
}

@media (max-width: 900px) {
  .db-content { padding: 24px 20px 40px; }
  .db-stats-grid { grid-template-columns: repeat(2, 1fr); }
  .db-navbar-inner { padding: 0 20px; }
  .db-nav-logo-sub { display: none; }
}
@media (max-width: 560px) {
  .db-stats-grid { grid-template-columns: 1fr 1fr; }
  .db-page-header { flex-direction: column; gap: 12px; }
}
`;
