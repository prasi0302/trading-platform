/** Recent Trades table matching reference design. */

import { useEffect } from 'react';
import { useAppState } from '../contexts/AppContext';
import { useSessionId } from '../hooks/useSessionId';
import { getOrders } from '../services/api';

export function RecentTrades() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();

  useEffect(() => {
    getOrders(sessionId)
      .then((orders) => dispatch({ type: 'SET_ORDERS', payload: orders }))
      .catch(() => {});
  }, [sessionId, dispatch]);

  const filledOrders = state.orders.filter((o) => o.status === 'filled');

  return (
    <div className="card" data-testid="recent-trades">
      <div className="card-title">Recent Trades</div>
      {filledOrders.length === 0 ? (
        <div className="empty-state">No trades yet — place your first order above</div>
      ) : (
        <table className="trades-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {filledOrders.map((order) => {
              const time = order.filled_at
                ? new Date(order.filled_at).toLocaleTimeString('en-US', { hour12: false })
                : '—';
              const value = (order.filled_price || 0) * order.quantity;

              return (
                <tr key={order.id} data-testid={`trade-row-${order.id}`}>
                  <td style={{ color: 'var(--text-muted)' }}>{time}</td>
                  <td><strong>{order.symbol}</strong></td>
                  <td>
                    <span className={`badge ${order.side === 'buy' ? 'badge-buy' : 'badge-sell'}`}>
                      {order.side.toUpperCase()}
                    </span>
                  </td>
                  <td>{order.quantity}</td>
                  <td>${(order.filled_price || 0).toFixed(2)}</td>
                  <td><strong>${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
