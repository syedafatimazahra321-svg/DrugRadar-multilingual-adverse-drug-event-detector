import { useState } from 'react';
const API = 'http://localhost:8000/api';

export default function Login({ onLogin, onGoSignup }) {
  const [company, setCompany] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handle = async () => {
    if (!company.trim() || !password.trim()) {
      setError('Please enter both company name and password.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company: company.trim(), password })
      });
      const data = await res.json();
      if (res.ok) onLogin(data);
      else setError(data.detail || 'Login failed');
    } catch {
      setError('Cannot connect to server. Is the backend running?');
    }
    setLoading(false);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

        .dr-bg {
          min-height: 100vh;
          background: linear-gradient(135deg, #a8d8ea 0%, #7ec8d8 30%, #5bb3c4 60%, #4a9eb5 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow: hidden;
        }

        /* decorative circles */
        .dr-bg::before {
          content: '';
          position: absolute;
          width: 320px; height: 320px;
          border-radius: 50%;
          border: 40px solid rgba(255,255,255,0.18);
          top: -80px; left: -80px;
          pointer-events: none;
        }
        .dr-bg::after {
          content: '';
          position: absolute;
          width: 220px; height: 220px;
          border-radius: 50%;
          border: 30px solid rgba(255,255,255,0.12);
          bottom: 40px; right: -60px;
          pointer-events: none;
        }

        .dr-card {
          background: rgba(255,255,255,0.92);
          backdrop-filter: blur(16px);
          border-radius: 24px;
          padding: 44px 40px 36px;
          width: 380px;
          box-shadow: 0 8px 40px rgba(30,100,140,0.18), 0 1.5px 6px rgba(30,100,140,0.08);
          position: relative;
          z-index: 1;
        }

        .dr-logo-text {
          font-family: 'Playfair Display', serif;
          font-size: 32px;
          font-weight: 700;
          color: #1a5276;
          letter-spacing: -0.5px;
          text-align: center;
          margin: 0 0 2px;
        }

        .dr-logo-sub {
          font-family: 'DM Sans', sans-serif;
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 0.22em;
          color: #5b9ab5;
          text-align: center;
          text-transform: uppercase;
          margin: 0 0 6px;
        }

        .dr-divider {
          width: 36px; height: 2px;
          background: linear-gradient(90deg, #5bb3c4, #1a5276);
          margin: 0 auto 28px;
          border-radius: 2px;
        }

        .dr-welcome {
          font-size: 20px;
          font-weight: 500;
          color: #1a3a4a;
          margin: 0 0 22px;
          font-family: 'DM Sans', sans-serif;
        }

        .dr-label {
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.1em;
          color: #5b7a8a;
          text-transform: uppercase;
          display: block;
          margin-bottom: 7px;
        }

        .dr-input-wrap {
          position: relative;
          margin-bottom: 18px;
        }

        .dr-input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: #7eb8c8;
          font-size: 15px;
          pointer-events: none;
        }

        .dr-input {
          width: 100%;
          border: 1.5px solid #c8e6ef;
          border-radius: 12px;
          padding: 12px 14px 12px 40px;
          font-size: 13px;
          font-family: 'DM Sans', sans-serif;
          color: #1a3a4a;
          background: rgba(240,250,255,0.7);
          box-sizing: border-box;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .dr-input:focus {
          border-color: #5bb3c4;
          box-shadow: 0 0 0 3px rgba(91,179,196,0.15);
          background: #fff;
        }

        .dr-input::placeholder { color: #aac8d4; }

        .dr-eye {
          position: absolute;
          right: 14px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          color: #7eb8c8;
          font-size: 15px;
          padding: 0;
          display: flex;
          align-items: center;
        }

        .dr-error {
          background: #fff0f0;
          border: 1px solid #ffc5c5;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 12px;
          color: #c0392b;
          margin-bottom: 14px;
        }

        .dr-btn-primary {
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

        .dr-btn-primary:hover:not(:disabled) { opacity: 0.92; transform: translateY(-1px); }
        .dr-btn-primary:active:not(:disabled) { transform: translateY(0); }
        .dr-btn-primary:disabled { opacity: 0.6; cursor: default; }

        .dr-or-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 16px;
        }

        .dr-or-line { flex: 1; height: 1px; background: #d8edf3; }

        .dr-or-text { font-size: 11px; color: #9bbfcc; }

        .dr-btn-secondary {
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
          transition: background 0.2s, color 0.2s;
        }

        .dr-btn-secondary:hover {
          background: rgba(46,134,171,0.07);
        }
      `}</style>

      <div className="dr-bg">
        <div className="dr-card">
          {/* Logo */}
          <p className="dr-logo-text">DrugRadar</p>
          <p className="dr-logo-sub">Pharmacovigilance Intelligence</p>
          <div className="dr-divider" />

          <p className="dr-welcome">Welcome back</p>

          {/* Company */}
          <label className="dr-label">Company Name</label>
          <div className="dr-input-wrap">
            <span className="dr-input-icon">🏢</span>
            <input
              className="dr-input"
              value={company}
              onChange={e => setCompany(e.target.value)}
              placeholder="Enter company name"
              onKeyDown={e => e.key === 'Enter' && handle()}
            />
          </div>

          {/* Password */}
          <label className="dr-label">Password</label>
          <div className="dr-input-wrap" style={{ marginBottom: '22px' }}>
            <span className="dr-input-icon">🔒</span>
            <input
              className="dr-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              style={{ paddingRight: '42px' }}
              onKeyDown={e => e.key === 'Enter' && handle()}
            />
            <button className="dr-eye" onClick={() => setShowPassword(p => !p)} tabIndex={-1}>
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {error && <div className="dr-error">{error}</div>}

          <button className="dr-btn-primary" onClick={handle} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <div className="dr-or-row">
            <div className="dr-or-line" />
            <span className="dr-or-text">or</span>
            <div className="dr-or-line" />
          </div>

          <button className="dr-btn-secondary" onClick={onGoSignup}>
            Create new account
          </button>
        </div>
      </div>
    </>
  );
}
