import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DrugDetail from './pages/DrugDetail';
import Login from './pages/Login';
import Signup from './pages/Signup';

export default function App() {
  const [user, setUser] = useState(null);
  const [showSignup, setShowSignup] = useState(false);

  // Not logged in — show login or signup
  if (!user) {
    if (showSignup) {
      return (
        <Signup
          onSignupSuccess={(data) => {
            setUser(data);
            setShowSignup(false);
          }}
          onGoLogin={() => setShowSignup(false)}
        />
      );
    }

    return (
      <Login
        onLogin={setUser}
        onGoSignup={() => setShowSignup(true)}
      />
    );
  }

  // Logged in — show full app
  return (
    <Router>
      <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
        <nav
          style={{
            backgroundColor: '#1e3a8a',
            color: 'white',
            padding: '14px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <span style={{ fontSize: '22px' }}>🔬</span>

          <Link
            to="/"
            style={{
              fontSize: '20px',
              fontWeight: 'bold',
              color: 'white',
              textDecoration: 'none'
            }}
          >
            DrugRadar
          </Link>

          <span
            style={{
              color: '#93c5fd',
              fontSize: '13px',
              marginLeft: '4px'
            }}
          >
            Pharmacovigilance Intelligence
          </span>

          {/* Nav section */}
          <div
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}
          >
            <span style={{ color: '#bfdbfe', fontSize: '13px' }}>
              {user.company.charAt(0).toUpperCase() + user.company.slice(1)}
            </span>

            <button
              onClick={() => setUser(null)}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #93c5fd',
                color: '#93c5fd',
                borderRadius: '6px',
                padding: '4px 12px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </nav>

        <Routes>
          <Route path='/' element={<Dashboard user={user} />} />
          <Route path='/drug/:drugName' element={<DrugDetail />} />
        </Routes>
      </div>
    </Router>
  );
}