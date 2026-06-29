/** Live Market - list of symbols with real-time prices and % change. */

import { useAppState } from '../contexts/AppContext';
import { DEFAULT_SYMBOLS } from '../constants';

export function LiveMarket() {
  const { state } = useAppState();

  return (
    <div className="card" data-testid="live-market">
      <div className="card-title">Live Market</div>
      <ul className="market-list">
        {DEFAULT_SYMBOLS.map(({ ticker, name }) => {
          const tick = state.prices[ticker];
          // Simulate % change from initial price
          const initialPrices: Record<string, number> = {
            AAPL: 175, GOOGL: 140, MSFT: 380, AMZN: 180,
            TSLA: 250, JPM: 190, NVDA: 800, META: 500,
          };
          const initial = initialPrices[ticker] || 100;
          const change = tick ? ((tick.price - initial) / initial) * 100 : 0;
          const isUp = change >= 0;

          return (
            <li key={ticker} className="market-item" data-testid={`market-item-${ticker}`}>
              <div className="market-item-left">
                <span className="market-item-symbol">{ticker}</span>
                <span className="market-item-name">{name}</span>
              </div>
              <div className="market-item-right">
                <div className="market-item-price">
                  {tick ? `$${tick.price.toFixed(2)}` : '—'}
                </div>
                {tick && (
                  <div className={`market-item-change ${isUp ? 'up' : 'down'}`}>
                    {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
