/** Price chart with symbol selector pills and historical data loading. */

import { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import { useAppState } from '../contexts/AppContext';
import { getHistory } from '../services/api';

const SYMBOLS = ['AAPL', 'NVDA', 'JPM', 'MSFT', 'TSLA'];

export function Chart() {
  const { state, dispatch } = useAppState();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const loadedSymbolRef = useRef<string>('');

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 320,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#6b7280',
      },
      grid: {
        vertLines: { color: '#f0f2f7' },
        horzLines: { color: '#f0f2f7' },
      },
      crosshair: {
        vertLine: { color: '#2563eb', width: 1, style: 2 },
        horzLine: { color: '#2563eb', width: 1, style: 2 },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#e8ecf2',
      },
      rightPriceScale: {
        borderColor: '#e8ecf2',
      },
    });

    const series = chart.addLineSeries({
      color: '#2563eb',
      lineWidth: 2,
      crosshairMarkerRadius: 4,
      crosshairMarkerBackgroundColor: '#2563eb',
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Load historical data when symbol changes
  useEffect(() => {
    if (!seriesRef.current) return;
    if (loadedSymbolRef.current === state.selectedSymbol) return;

    loadedSymbolRef.current = state.selectedSymbol;

    // Clear existing data
    seriesRef.current.setData([]);

    // Load 30 days of 1-hour candles
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);

    getHistory(state.selectedSymbol, '1h', start.toISOString(), end.toISOString())
      .then((candles) => {
        if (!seriesRef.current || loadedSymbolRef.current !== state.selectedSymbol) return;

        const data = candles.map((c) => ({
          time: Math.floor(new Date(c.timestamp).getTime() / 1000) as import('lightweight-charts').UTCTimestamp,
          value: c.close,
        }));

        if (data.length > 0) {
          seriesRef.current.setData(data);
          chartRef.current?.timeScale().fitContent();
        }
      })
      .catch(() => {
        // Silently fail — chart will populate from live data
      });
  }, [state.selectedSymbol]);

  // Update chart with real-time price data
  useEffect(() => {
    const tick = state.prices[state.selectedSymbol];
    if (!tick || !seriesRef.current) return;

    const time = Math.floor(new Date(tick.timestamp).getTime() / 1000) as import('lightweight-charts').UTCTimestamp;
    seriesRef.current.update({ time, value: tick.price });
  }, [state.prices, state.selectedSymbol]);

  const currentTick = state.prices[state.selectedSymbol];

  return (
    <div className="card chart-section" data-testid="chart-container">
      <div className="chart-header">
        <span className="chart-title">
          {state.selectedSymbol} — 30 DAY PRICE HISTORY
          {currentTick && (
            <span style={{ marginLeft: 12, color: '#1a1d29', fontWeight: 700, fontSize: '0.9rem' }}>
              ${currentTick.price.toFixed(2)}
            </span>
          )}
        </span>
        <div className="symbol-pills">
          {SYMBOLS.map((sym) => (
            <button
              key={sym}
              className={`symbol-pill ${sym === state.selectedSymbol ? 'active' : ''}`}
              onClick={() => dispatch({ type: 'SET_SELECTED_SYMBOL', payload: sym })}
              data-testid={`symbol-pill-${sym}`}
            >
              {sym}
            </button>
          ))}
        </div>
      </div>
      <div ref={chartContainerRef} data-testid="chart-canvas" />
    </div>
  );
}
