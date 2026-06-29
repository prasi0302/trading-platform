/** Landing page - app overview, architecture, tech stack, features. */

import { Link } from 'react-router-dom';

export function LandingPage() {
  return (
    <div className="landing">
      {/* Hero */}
      <section className="landing-hero">
        <h1>📈 TradingDesk Platform</h1>
        <p className="landing-subtitle">
          A microservices-based real-time stock trading application with simulated market data,
          order management, and portfolio tracking.
        </p>
        <Link to="/trading" className="landing-cta" style={{ textDecoration: 'none' }}>
          Enter Platform →
        </Link>
      </section>

      {/* Entry Points */}
      <section className="landing-cards">
        <Link to="/trading" className="landing-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <span className="landing-card-icon">📊</span>
          <h3>Trading Desk</h3>
          <p>Real-time charts, order execution, and live market data streaming</p>
        </Link>
        <Link to="/dashboard" className="landing-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <span className="landing-card-icon">💼</span>
          <h3>Portfolio Dashboard</h3>
          <p>Track holdings, P&L, sector allocation, and account performance</p>
        </Link>
        <Link to="/trading/alerts" className="landing-card" style={{ textDecoration: 'none', color: 'inherit' }}>
          <span className="landing-card-icon">🔔</span>
          <h3>Price Alerts</h3>
          <p>Set threshold alerts and get real-time notifications via WebSocket</p>
        </Link>
      </section>

      {/* How It Works */}
      <section className="landing-section">
        <h2>How Trading Works</h2>
        <div className="landing-flow">
          <div className="landing-flow-step">
            <span className="landing-flow-icon">📡</span>
            <div className="landing-flow-num">1. Stream</div>
            <div className="landing-flow-desc">Real-time price simulation via GBM</div>
          </div>
          <span className="landing-flow-arrow">→</span>
          <div className="landing-flow-step">
            <span className="landing-flow-icon">📋</span>
            <div className="landing-flow-num">2. Order</div>
            <div className="landing-flow-desc">Market, Limit, or Stop-Loss</div>
          </div>
          <span className="landing-flow-arrow">→</span>
          <div className="landing-flow-step">
            <span className="landing-flow-icon">⚡</span>
            <div className="landing-flow-num">3. Execute</div>
            <div className="landing-flow-desc">&lt;100ms fill with portfolio update</div>
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="landing-section">
        <h2>System Architecture</h2>
        <pre className="landing-arch">{`
                    ┌──────────────────────┐
                    │   CloudFront (CDN)   │
                    │   + React Frontend   │
                    └──────────┬───────────┘
                               │ /api/*  /ws
                               ▼
                    ┌──────────────────────┐
                    │   ALB (Load Balancer) │
                    └───┬──────┬──────┬────┘
                        │      │      │
           ┌────────────┘      │      └────────────┐
           ▼                   ▼                   ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ Market Data  │   │    Order     │   │  WebSocket   │
  │   Service    │   │   Service    │   │   Gateway    │
  │  (Simulate)  │   │  (Execute)   │   │  (Stream)    │
  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
         │                   │                   │
         │            ┌──────┴───────┐           │
         │            ▼              ▼           │
         │   ┌──────────────┐ ┌──────────────┐  │
         │   │  Portfolio   │ │    Alert     │  │
         │   │   Service    │ │   Service    │  │
         │   └──────┬───────┘ └──────┬───────┘  │
         │          │                │           │
    ┌────┴────┐     └────────┬───────┘     ┌────┴────┐
    ▼         ▼              ▼             ▼         
┌────────┐ ┌────────┐ ┌──────────────┐ ┌────────┐
│DynamoDB│ │   S3   │ │RDS PostgreSQL│ │ Redis  │
│ (Ticks)│ │(History)│ │  (Orders/    │ │(PubSub)│
└────────┘ └────────┘ │  Portfolio)  │ └────────┘
                       └──────────────┘
`}</pre>
      </section>

      {/* Tech Stack */}
      <section className="landing-section">
        <h2>Technology Stack</h2>
        <div className="landing-tech-grid">
          <div className="landing-tech-item">
            <div className="landing-tech-title">Backend</div>
            <div className="landing-tech-desc">Python 3.11 • FastAPI • SQLAlchemy • Pydantic</div>
          </div>
          <div className="landing-tech-item">
            <div className="landing-tech-title">Frontend</div>
            <div className="landing-tech-desc">React 18 • TypeScript • Vite • Lightweight Charts</div>
          </div>
          <div className="landing-tech-item">
            <div className="landing-tech-title">Database</div>
            <div className="landing-tech-desc">PostgreSQL 15 • DynamoDB • Redis</div>
          </div>
          <div className="landing-tech-item">
            <div className="landing-tech-title">Infrastructure</div>
            <div className="landing-tech-desc">AWS CDK • ECS Fargate • CloudFront • ALB</div>
          </div>
          <div className="landing-tech-item">
            <div className="landing-tech-title">Real-Time</div>
            <div className="landing-tech-desc">WebSocket • Redis Pub/Sub • GBM Simulation</div>
          </div>
          <div className="landing-tech-item">
            <div className="landing-tech-title">Observability</div>
            <div className="landing-tech-desc">Structured Logging • CloudWatch • Health Checks</div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="landing-section">
        <h2>Key Features</h2>
        <div className="landing-features">
          <div className="landing-feature">
            <strong>📈 Real-Time Streaming</strong>
            <p>WebSocket-powered live price updates with &lt;50ms delivery latency</p>
          </div>
          <div className="landing-feature">
            <strong>⚡ Fast Execution</strong>
            <p>Market orders fill in &lt;100ms with optimistic concurrency (no double-fills)</p>
          </div>
          <div className="landing-feature">
            <strong>📊 Interactive Charts</strong>
            <p>30-day price history with Lightweight Charts (TradingView OSS)</p>
          </div>
          <div className="landing-feature">
            <strong>🔔 Price Alerts</strong>
            <p>Set above/below thresholds — triggered in real-time via WebSocket push</p>
          </div>
          <div className="landing-feature">
            <strong>📋 Order Types</strong>
            <p>Market, Limit, and Stop-Loss orders with full lifecycle tracking</p>
          </div>
          <div className="landing-feature">
            <strong>🏗️ Microservices</strong>
            <p>6 independent services — deploy, scale, and update each independently</p>
          </div>
        </div>
      </section>
    </div>
  );
}
