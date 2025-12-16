import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function SideNav({ isOpen, onClose }) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/study', label: 'Study', icon: '📚' },
    { path: '/news', label: 'News', icon: '📰' },
    { path: '/notes', label: 'Notes', icon: '📝' },
    { path: '/morning', label: 'Morning', icon: '🌅' },
  ];

  const handleNavigation = (path) => {
    navigate(path);
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100"
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            zIndex: 1040,
            transition: 'opacity 0.3s ease'
          }}
          onClick={onClose}
        />
      )}

      {/* Side Navbar */}
      <div
        className="position-fixed top-0 start-0 h-100"
        style={{
          width: isOpen ? '280px' : '0',
          zIndex: 1050,
          transition: 'width 0.3s ease',
          overflow: 'hidden'
        }}
      >
        <div
          className="h-100 aqua-card"
          style={{
            width: '280px',
            boxShadow: '4px 0 20px rgba(0, 0, 0, 0.15)',
            padding: '20px'
          }}
        >
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h5 style={{ color: 'var(--mac-accent)', margin: 0 }}>Navigation</h5>
            <button
              className="btn mac-button btn-sm"
              onClick={onClose}
              style={{ minWidth: '30px', padding: '4px 8px' }}
            >
              ✕
            </button>
          </div>

          <nav className="d-flex flex-column gap-2">
            {menuItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  className={`btn text-start mac-button ${isActive ? 'active' : ''}`}
                  onClick={() => handleNavigation(item.path)}
                  style={{
                    padding: '12px 16px',
                    fontSize: '1rem',
                    background: isActive
                      ? 'linear-gradient(180deg, #cde2ff, #b3d4ff)'
                      : 'linear-gradient(180deg, #f7fbff, #d9e7ff)',
                    border: isActive ? '2px solid var(--mac-accent)' : '1px solid var(--mac-border)',
                    color: 'var(--mac-ink)',
                    fontWeight: isActive ? '600' : '400'
                  }}
                >
                  <span style={{ marginRight: '12px', fontSize: '1.2rem' }}>{item.icon}</span>
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </>
  );
}

export default SideNav;

