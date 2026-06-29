/** Main application with URL-based routing. */

import { useCallback } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AppProvider, useAppState } from './contexts/AppContext';
import { useSessionId } from './hooks/useSessionId';
import { useWebSocket } from './hooks/useWebSocket';
import { Dashboard } from './components/Dashboard';
import { LandingPage } from './components/LandingPage';
import { StatsRow } from './components/StatsRow';
import { Chart } from './components/Chart';
import { OrderForm } from './components/OrderForm';
import { LiveMarket } from './components/LiveMarket';
import { RecentTrades } from './components/RecentTrades';
import { OrdersView } from './components/OrdersView';
import { AlertsView } from './components/AlertsView';
import type { PriceTick } from './types';
import './index.css';

type TradingTab = 'trade' | 'orders' | 'alerts';

function AppShell() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();
  const location = useLocation();

  const handlePrice = useCallback(
    (tick: PriceTick) => {
      dispatch({ type: 'SET_PRICE', payload: tick });
    },
    [dispatch]
  );

  const handleOrder = useCallback(
    (_data: unknown) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: '📋 Order update received' });
    },
    [dispatch]
  );

  const handleAlert = useCallback(
    (_data: unknown) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: '🔔 Price alert triggered!' });
    },
    [dispatch]
  );

  const { connected, subscribe } = useWebSocket({
    sessionId,
    onPrice: handlePrice,
    onOrder: handleOrder,
    onAlert: handleAlert,
  });

  if (connected && state.watchlist.length > 0) {
    subscribe(['AAPL', 'MSFT', 'JPM', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']);
  }

  const isLanding = location.pathname === '/';

  return (
    <>
      {/* Nav bar - hidden on landing page */}
      {!isLanding && (
        <nav className="navbar">
          <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="navbar-brand-icon">△</div>
            <span>FINANCIAL PLATFORM</span>
          </Link>
          <div className="navbar-tabs">
            <Link to="/dashboard" className={`navbar-tab ${location.pathname === '/dashboard' ? 'active' : ''}`}>
              Dashboard
            </Link>
            <Link to="/trading" className={`navbar-tab ${location.pathname.startsWith('/trading') ? 'active' : ''}`}>
              Trading
            </Link>
          </div>
          <div className="navbar-status">
            <span>{new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
            <span className="status-dot" />
            <span>{connected ? 'All Systems Operational' : 'Reconnecting...'}</span>
          </div>
        </nav>
      )}

      {/* Notification */}
      {!isLanding && state.notifications.length > 0 && (
        <div style={{ maxWidth: 1400, margin: '0 auto', padding: '16px 32px 0' }}>
          <div className="notification" role="alert">
            {state.notifications[state.notifications.length - 1]}
          </div>
        </div>
      )}

      {/* Routes */}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trading" element={<TradingPage />} />
        <Route path="/trading/orders" element={<TradingPageWithTab tab="orders" />} />
        <Route path="/trading/alerts" element={<TradingPageWithTab tab="alerts" />} />
      </Routes>
    </>
  );
}

function TradingPage() {
  return <TradingPageWithTab tab="trade" />;
}

function TradingPageWithTab({ tab }: { tab: TradingTab }) {
  const { state } = useAppState();

  const currentTab = tab;

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Trading Desk</h1>
        <div className="page-tabs">
          <Link to="/trading" className={`page-tab ${currentTab === 'trade' ? 'active' : ''}`}>
            Trade
          </Link>
          <Link to="/trading/orders" className={`page-tab ${currentTab === 'orders' ? 'active' : ''}`}>
            Orders ({state.orders.length})
          </Link>
          <Link to="/trading/alerts" className={`page-tab ${currentTab === 'alerts' ? 'active' : ''}`}>
            Alerts ({state.alerts.length})
          </Link>
        </div>
      </div>

      {currentTab === 'trade' && (
        <>
          <StatsRow />
          <Chart />
          <div className="two-col">
            <OrderForm />
            <LiveMarket />
          </div>
          <RecentTrades />
        </>
      )}

      {currentTab === 'orders' && <OrdersView />}
      {currentTab === 'alerts' && <AlertsView />}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppShell />
      </AppProvider>
    </BrowserRouter>
  );
}
