/** Stats row - Total Trades, Volume, Buys/Sells, Pending Orders. */

import { useAppState } from '../contexts/AppContext';

export function StatsRow() {
  const { state } = useAppState();

  const totalTrades = state.orders.length;
  const buys = state.orders.filter((o) => o.side === 'buy' && o.status === 'filled').length;
  const sells = state.orders.filter((o) => o.side === 'sell' && o.status === 'filled').length;
  const pending = state.orders.filter((o) => o.status === 'pending').length;
  const volume = state.orders
    .filter((o) => o.status === 'filled')
    .reduce((sum, o) => sum + (o.filled_price || 0) * o.quantity, 0);

  return (
    <div className="stats-row" data-testid="stats-row">
      <div className="stat-card">
        <div className="stat-label">Total Trades</div>
        <div className="stat-value">{totalTrades}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Volume</div>
        <div className="stat-value">${volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Buys / Sells</div>
        <div className="stat-value">{buys} / {sells}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Pending Orders</div>
        <div className="stat-value">{pending}</div>
      </div>
    </div>
  );
}
