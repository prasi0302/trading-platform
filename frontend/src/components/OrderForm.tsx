/** Order form matching reference design - symbol dropdown, buy/sell toggle, market/limit toggle, quantity, execute button. */

import { useState } from 'react';
import { useAppState } from '../contexts/AppContext';
import { useSessionId } from '../hooks/useSessionId';
import { submitOrder, getOrders } from '../services/api';
import type { OrderRequest } from '../types';

const ALL_SYMBOLS = ['AAPL', 'NVDA', 'JPM', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META'];

export function OrderForm() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState(10);
  const [limitPrice, setLimitPrice] = useState<number | ''>('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const request: OrderRequest = {
      symbol: state.selectedSymbol,
      type: orderType,
      side,
      quantity,
      session_id: sessionId,
    };

    if (orderType === 'limit' && limitPrice) {
      request.price = Number(limitPrice);
    }

    try {
      const order = await submitOrder(request);
      dispatch({ type: 'ADD_ORDER', payload: order });
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: `✅ ${side.toUpperCase()} ${quantity} ${state.selectedSymbol} @ $${(order.filled_price || limitPrice || 'MKT').toString()}`,
      });
      // Refresh order list
      const orders = await getOrders(sessionId);
      dispatch({ type: 'SET_ORDERS', payload: orders });
      // Reset form
      setQuantity(10);
      setLimitPrice('');
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      dispatch({ type: 'ADD_NOTIFICATION', payload: `❌ Order failed: ${message}` });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" data-testid="order-form">
      <div className="card-title">New Order</div>
      <form onSubmit={handleSubmit}>
        {/* Symbol selector */}
        <select
          className="order-symbol-select"
          value={state.selectedSymbol}
          onChange={(e) => dispatch({ type: 'SET_SELECTED_SYMBOL', payload: e.target.value })}
          data-testid="order-form-symbol"
        >
          {ALL_SYMBOLS.map((sym) => (
            <option key={sym} value={sym}>
              {sym} — ${state.prices[sym]?.price.toFixed(2) || '...'}
            </option>
          ))}
        </select>

        {/* Buy / Sell toggle */}
        <div className="toggle-row">
          <button
            type="button"
            className={`toggle-btn ${side === 'buy' ? 'active-buy' : ''}`}
            onClick={() => setSide('buy')}
            data-testid="order-form-side-buy"
          >
            BUY
          </button>
          <button
            type="button"
            className={`toggle-btn ${side === 'sell' ? 'active-sell' : ''}`}
            onClick={() => setSide('sell')}
            data-testid="order-form-side-sell"
          >
            SELL
          </button>
        </div>

        {/* Market / Limit toggle */}
        <div className="toggle-row">
          <button
            type="button"
            className={`toggle-btn ${orderType === 'market' ? 'active-type' : ''}`}
            onClick={() => setOrderType('market')}
            data-testid="order-form-type-market"
          >
            MARKET
          </button>
          <button
            type="button"
            className={`toggle-btn ${orderType === 'limit' ? 'active-type' : ''}`}
            onClick={() => setOrderType('limit')}
            data-testid="order-form-type-limit"
          >
            LIMIT
          </button>
        </div>

        {/* Quantity */}
        <input
          type="number"
          className="order-input"
          min={1}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          placeholder="Quantity"
          data-testid="order-form-quantity"
        />

        {/* Limit price (only for limit orders) */}
        {orderType === 'limit' && (
          <input
            type="number"
            className="order-input"
            step="0.01"
            min={0.01}
            value={limitPrice}
            onChange={(e) => setLimitPrice(e.target.value ? Number(e.target.value) : '')}
            placeholder="Limit Price"
            data-testid="order-form-price"
            required
          />
        )}

        {error && <div className="error-message" role="alert">{error}</div>}

        {/* Execute button */}
        <button
          type="submit"
          disabled={submitting}
          className={`execute-btn ${side}`}
          data-testid="order-form-submit"
        >
          {submitting
            ? 'Executing...'
            : `Execute ${orderType.toUpperCase()} ${side.toUpperCase()}`}
        </button>
      </form>
    </div>
  );
}
