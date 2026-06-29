/** Orders view - shows all orders with status, cancel functionality. */

import { useEffect } from 'react';
import { useAppState } from '../contexts/AppContext';
import { useSessionId } from '../hooks/useSessionId';
import { cancelOrder, getOrders } from '../services/api';

export function OrdersView() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();

  useEffect(() => {
    getOrders(sessionId)
      .then((orders) => dispatch({ type: 'SET_ORDERS', payload: orders }))
      .catch(() => {});
  }, [sessionId, dispatch]);

  const handleCancel = async (orderId: string) => {
    try {
      await cancelOrder(orderId, sessionId);
      const updated = await getOrders(sessionId);
      dispatch({ type: 'SET_ORDERS', payload: updated });
    } catch {
      // Ignore
    }
  };

  const pendingOrders = state.orders.filter((o) => o.status === 'pending');
  const filledOrders = state.orders.filter((o) => o.status === 'filled');
  const cancelledOrders = state.orders.filter((o) => o.status === 'cancelled');

  return (
    <div>
      {/* Pending Orders */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Pending Orders ({pendingOrders.length})</div>
        {pendingOrders.length === 0 ? (
          <div className="empty-state">No pending orders</div>
        ) : (
          <table className="trades-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {pendingOrders.map((order) => (
                <tr key={order.id}>
                  <td><strong>{order.symbol}</strong></td>
                  <td>
                    <span className={`badge ${order.side === 'buy' ? 'badge-buy' : 'badge-sell'}`}>
                      {order.side.toUpperCase()}
                    </span>
                  </td>
                  <td>{order.type.replace('_', ' ')}</td>
                  <td>{order.quantity}</td>
                  <td>${(order.price || 0).toFixed(2)}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(order.created_at).toLocaleTimeString('en-US', { hour12: false })}
                  </td>
                  <td>
                    <button
                      onClick={() => handleCancel(order.id)}
                      style={{
                        padding: '4px 12px',
                        borderRadius: 4,
                        border: '1px solid var(--red)',
                        background: 'var(--red-light)',
                        color: 'var(--red)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Filled Orders */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Filled Orders ({filledOrders.length})</div>
        {filledOrders.length === 0 ? (
          <div className="empty-state">No filled orders yet</div>
        ) : (
          <table className="trades-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Fill Price</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {filledOrders.map((order) => (
                <tr key={order.id}>
                  <td style={{ color: 'var(--text-muted)' }}>
                    {order.filled_at ? new Date(order.filled_at).toLocaleTimeString('en-US', { hour12: false }) : '—'}
                  </td>
                  <td><strong>{order.symbol}</strong></td>
                  <td>
                    <span className={`badge ${order.side === 'buy' ? 'badge-buy' : 'badge-sell'}`}>
                      {order.side.toUpperCase()}
                    </span>
                  </td>
                  <td>{order.quantity}</td>
                  <td>${(order.filled_price || 0).toFixed(2)}</td>
                  <td><strong>${((order.filled_price || 0) * order.quantity).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Cancelled Orders */}
      {cancelledOrders.length > 0 && (
        <div className="card">
          <div className="card-title">Cancelled Orders ({cancelledOrders.length})</div>
          <table className="trades-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {cancelledOrders.map((order) => (
                <tr key={order.id} style={{ opacity: 0.6 }}>
                  <td>{order.symbol}</td>
                  <td>{order.side.toUpperCase()}</td>
                  <td>{order.type.replace('_', ' ')}</td>
                  <td>{order.quantity}</td>
                  <td>${(order.price || 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
