import { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';

export default function Signup({ onSignupSuccess, onGoLogin }) {
  const [company, setCompany] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [selectedDrugs, setSelectedDrugs] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [availableDrugs, setAvailableDrugs] = useState([]);

  useEffect(() => {
    fetch(`${API}/available_drugs`)
      .then(r => r.json())
      .then(data => setAvailableDrugs(data))
      .catch(() => setAvailableDrugs([]));
  }, []);

  const toggleDrug = (drug) => {
    setSelectedDrugs(prev =>
      prev.includes(drug) ? prev.filter(d => d !== drug) : [...prev, drug]
    );
  };

  const handle = async () => {
    setError('');
    if (!company.trim()) { setError('Company name is required.'); return; }
    if (company.trim().length < 2) { setError('Company name must be at least 2 characters.'); return; }
    if (password.length < 4) { setError('Password must be at least 4 characters.'); return; }
    if (password !== confirm) { setError('Passwords do not match.'); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: company.trim(),
          password,
          drugs: selectedDrugs.join(',')
        })
      });
      const data = await res.json();
      if (res.ok) {
        onSignupSuccess(data);
      } else {
        setError(data.detail || 'Signup failed');
      }
    } catch {
      setError('Cannot connect to server. Is the backend running?');
    }
    setLoading(false);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

        .drs-bg {
          min-height: 100vh;
          background: linear-gradient(135deg, #a8d8ea 0%, #7ec8d8 30%, #5bb3c4 60%, #4a9eb5 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow: hidden;
        }

        .drs-bg::before {
          content: '';
          position: absolute;
          width: 320px; height: 320px;
          border-radius: 50%;
          border: 40px solid rgba(255,255,255,0.18);
          top: -80px; left: -80px;
          pointer-events: none;
        }
        .drs-bg::after {
          content: '';
          position: absolute;
          width: 220px; height: 220px;
          border-radius: 50%;
          border: 30px solid rgba(255,255,255,0.12);
          bottom: 40px; right: -60px;
          pointer-events: none;
        }

        .drs-card {
          background: rgba(255,255,255,0.92);
          backdrop-filter: blur(16px);
          border-radius: 24px;
          padding: 40px 40px 32px;
          width: 100%;
          max-width: 460px;
          box-shadow: 0 8px 40px rgba(30,100,140,0.18), 0 1.5px 6px rgba(30,100,140,0.08);
          position: relative;
          z-index: 1;
        }

        .drs-logo-text {
          font-family: 'Playfair Display', serif;
          font-size: 28px;
          font-weight: 700;
          color: #1a5276;
          letter-spacing: -0.5px;
          text-align: center;
          margin: 0 0 2px;
        }

        .drs-logo-sub {
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 0.22em;
          color: #5b9ab5;
          text-align: center;
          text-transform: uppercase;
          margin: 0 0 6px;
        }

        .drs-divider {
          width: 36px; height: 2px;
          background: linear-gradient(90deg, #5bb3c4, #1a5276);
          margin: 0 auto 24px;
          border-radius: 2px;
        }

        .drs-title {
          font-size: 19px;
          font-weight: 500;
          color: #1a3a4a;
          margin: 0 0 20px;
        }

        .drs-label {
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.1em;
          color: #5b7a8a;
          text-transform: uppercase;
          display: block;
          margin-bottom: 7px;
        }

        .drs-input-wrap {
          position: relative;
          margin-bottom: 16px;
        }

        .drs-input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: #7eb8c8;
          font-size: 14px;
          pointer-events: none;
        }

        .drs-input {
          width: 100%;
          border: 1.5px solid #c8e6ef;
          border-radius: 12px;
          padding: 11px 14px 11px 40px;
          font-size: 13px;
          font-family: 'DM Sans', sans-serif;
          color: #1a3a4a;
          background: rgba(240,250,255,0.7);
          box-sizing: border-box;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .drs-input:focus {
          border-color: #5bb3c4;
          box-shadow: 0 0 0 3px rgba(91,179,196,0.15);
          background: #fff;
        }

        .drs-input::placeholder { color: #aac8d4; }

        .drs-eye {
          position: absolute;
          right: 14px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          color: #7eb8c8;
          font-size: 14px;
          padding: 0;
          display: flex;
          align-items: center;
        }

        .drs-drug-hint {
          font-size: 11px;
          color: #9bbfcc;
          margin: 0 0 10px;
        }

        .drs-drug-box {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          max-height: 140px;
          overflow-y: auto;
          border: 1.5px solid #c8e6ef;
          border-radius: 12px;
          padding: 10px;
          background: rgba(240,250,255,0.5);
          margin-bottom: 6px;
        }

        .drs-drug-box::-webkit-scrollbar { width: 4px; }
        .drs-drug-box::-webkit-scrollbar-track { background: transparent; }
        .drs-drug-box::-webkit-scrollbar-thumb { background: #b0d8e4; border-radius: 4px; }

        .drs-drug-pill {
          padding: 4px 12px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          border: none;
          font-family: 'DM Sans', sans-serif;
          text-transform: capitalize;
          transition: background 0.15s, color 0.15s;
        }

        .drs-drug-pill.active {
          background: linear-gradient(135deg, #2e86ab, #1a6080);
          color: white;
        }

        .drs-drug-pill.inactive {
          background: #eaf5f9;
          color: #2e86ab;
        }

        .drs-drug-pill.inactive:hover {
          background: #d0edf5;
        }

        .drs-selected-count {
          font-size: 11px;
          color: #2e86ab;
          margin: 4px 0 18px;
          font-weight: 500;
        }

        .drs-error {
          background: #fff0f0;
          border: 1px solid #ffc5c5;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 12px;
          color: #c0392b;
          margin-bottom: 14px;
        }

        .drs-btn-primary {
          width: 100%;
          background: linear-gradient(135deg, #2e86ab 0%, #1a6080 100%);
          color: white;
          border: none;
          border-radius: 12px;
          padding: 13px;
          font-size: 15px;
          font-weight: 600;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          letter-spacing: 0.02em;
          transition: opacity 0.2s, transform 0.1s;
          margin-bottom: 16px;
          box-shadow: 0 4px 16px rgba(46,134,171,0.35);
        }

        .drs-btn-primary:hover:not(:disabled) { opacity: 0.92; transform: translateY(-1px); }
        .drs-btn-primary:active:not(:disabled) { transform: translateY(0); }
        .drs-btn-primary:disabled { opacity: 0.6; cursor: default; }

        .drs-or-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 16px;
        }

        .drs-or-line { flex: 1; height: 1px; background: #d8edf3; }
        .drs-or-text { font-size: 11px; color: #9bbfcc; }

        .drs-btn-secondary {
          width: 100%;
          background: transparent;
          color: #2e86ab;
          border: 1.5px solid #2e86ab;
          border-radius: 12px;
          padding: 12px;
          font-size: 14px;
          font-weight: 600;
          font-family: 'DM Sans', sans-serif;
          cursor: pointer;
          transition: background 0.2s;
        }

        .drs-btn-secondary:hover { background: rgba(46,134,171,0.07); }
      `}</style>

      <div className="drs-bg">
        <div className="drs-card">
          {/* Logo */}
          <p className="drs-logo-text">DrugRadar</p>
          <p className="drs-logo-sub">Pharmacovigilance Intelligence</p>
          <div className="drs-divider" />

          <p className="drs-title">Create Account</p>

          {/* Company */}
          <label className="drs-label">Company Name</label>
          <div className="drs-input-wrap">
            <span className="drs-input-icon">🏢</span>
            <input
              className="drs-input"
              value={company}
              onChange={e => setCompany(e.target.value)}
              placeholder="Enter your company name"
            />
          </div>

          {/* Password */}
          <label className="drs-label">Password</label>
          <div className="drs-input-wrap">
            <span className="drs-input-icon">🔒</span>
            <input
              className="drs-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              type={showPassword ? 'text' : 'password'}
              placeholder="Minimum 4 characters"
              style={{ paddingRight: '42px' }}
            />
            <button className="drs-eye" onClick={() => setShowPassword(p => !p)} tabIndex={-1}>
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {/* Confirm Password */}
          <label className="drs-label">Confirm Password</label>
          <div className="drs-input-wrap" style={{ marginBottom: '20px' }}>
            <span className="drs-input-icon">🔒</span>
            <input
              className="drs-input"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              type={showConfirm ? 'text' : 'password'}
              placeholder="Re-enter password"
              style={{ paddingRight: '42px' }}
              onKeyDown={e => e.key === 'Enter' && handle()}
            />
            <button className="drs-eye" onClick={() => setShowConfirm(p => !p)} tabIndex={-1}>
              {showConfirm ? '🙈' : '👁️'}
            </button>
          </div>

          {/* Drug portfolio */}
          <label className="drs-label">Drug Portfolio</label>
          <p className="drs-drug-hint">Select drugs your company monitors. Leave empty to monitor all.</p>
          <div className="drs-drug-box">
            {availableDrugs.map(drug => (
              <button
                key={drug}
                onClick={() => toggleDrug(drug)}
                className={`drs-drug-pill ${selectedDrugs.includes(drug) ? 'active' : 'inactive'}`}
              >
                {drug}
              </button>
            ))}
          </div>
          {selectedDrugs.length > 0 && (
            <p className="drs-selected-count">
              {selectedDrugs.length} drug{selectedDrugs.length > 1 ? 's' : ''} selected
            </p>
          )}

          {error && <div className="drs-error">{error}</div>}

          <button className="drs-btn-primary" onClick={handle} disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>

          <div className="drs-or-row">
            <div className="drs-or-line" />
            <span className="drs-or-text">already have an account?</span>
            <div className="drs-or-line" />
          </div>

          <button className="drs-btn-secondary" onClick={onGoLogin}>
            Back to Login
          </button>
        </div>
      </div>
    </>
  );
}
