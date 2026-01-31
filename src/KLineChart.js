import React, { useState, useEffect } from 'react';
import './KLineChart.css';

/**
 * K线图组件
 * 支持：基金、股票、全球资产
 * 技术指标：MA5/10/20/60, MACD, RSI, 布林带
 */
function KLineChart({ code, name, type }) {
  const [klineData, setKlineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('90'); // 90天、180天、365天
  const [showIndicators, setShowIndicators] = useState({
    MA: true,
    MACD: false,
    RSI: false,
    BB: false
  });

  useEffect(() => {
    loadKLineData();
  }, [code, period]);

  const loadKLineData = async () => {
    setLoading(true);
    try {
      // 这里需要后端API支持，暂时使用模拟数据
      const response = await fetch(`/api/kline?code=${code}&type=${type}&days=${period}`);
      const data = await response.json();
      setKlineData(data);
    } catch (error) {
      console.error('加载K线数据失败:', error);
    }
    setLoading(false);
  };

  const toggleIndicator = (indicator) => {
    setShowIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator]
    }));
  };

  if (loading) {
    return <div className="kline-loading">加载K线数据中...</div>;
  }

  if (!klineData || klineData.length === 0) {
    return <div className="kline-error">暂无K线数据</div>;
  }

  // 计算价格范围
  const prices = klineData.map(d => d.close);
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const priceRange = maxPrice - minPrice;

  return (
    <div className="kline-container">
      <div className="kline-header">
        <h3>{name} ({code})</h3>
        <div className="kline-controls">
          <div className="period-selector">
            <button 
              className={period === '90' ? 'active' : ''}
              onClick={() => setPeriod('90')}
            >
              3个月
            </button>
            <button 
              className={period === '180' ? 'active' : ''}
              onClick={() => setPeriod('180')}
            >
              6个月
            </button>
            <button 
              className={period === '365' ? 'active' : ''}
              onClick={() => setPeriod('365')}
            >
              1年
            </button>
          </div>
          
          <div className="indicator-selector">
            <button 
              className={showIndicators.MA ? 'active' : ''}
              onClick={() => toggleIndicator('MA')}
            >
              MA均线
            </button>
            <button 
              className={showIndicators.MACD ? 'active' : ''}
              onClick={() => toggleIndicator('MACD')}
            >
              MACD
            </button>
            <button 
              className={showIndicators.RSI ? 'active' : ''}
              onClick={() => toggleIndicator('RSI')}
            >
              RSI
            </button>
            <button 
              className={showIndicators.BB ? 'active' : ''}
              onClick={() => toggleIndicator('BB')}
            >
              布林带
            </button>
          </div>
        </div>
      </div>

      <div className="kline-chart">
        <svg width="100%" height="400" viewBox="0 0 1000 400">
          {/* 价格网格线 */}
          {[0, 1, 2, 3, 4].map(i => {
            const y = 50 + (i * 70);
            const price = maxPrice - (i * priceRange / 4);
            return (
              <g key={i}>
                <line x1="50" y1={y} x2="950" y2={y} stroke="#2a2e39" strokeWidth="1" />
                <text x="10" y={y + 5} fill="#8b949e" fontSize="12">
                  {price.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* K线 */}
          {klineData.map((d, i) => {
            const x = 50 + (i * (900 / klineData.length));
            const closeY = 50 + ((maxPrice - d.close) / priceRange) * 300;
            const openY = d.open ? 50 + ((maxPrice - d.open) / priceRange) * 300 : closeY;
            const highY = d.high ? 50 + ((maxPrice - d.high) / priceRange) * 300 : closeY;
            const lowY = d.low ? 50 + ((maxPrice - d.low) / priceRange) * 300 : closeY;
            
            const isUp = d.close >= (d.open || d.close);
            const color = isUp ? '#f78166' : '#7ee787';
            
            return (
              <g key={i}>
                {/* 上下影线 */}
                {d.high && d.low && (
                  <line 
                    x1={x} 
                    y1={highY} 
                    x2={x} 
                    y2={lowY} 
                    stroke={color} 
                    strokeWidth="1"
                  />
                )}
                {/* K线实体 */}
                <rect
                  x={x - 2}
                  y={Math.min(closeY, openY)}
                  width="4"
                  height={Math.abs(closeY - openY) || 1}
                  fill={color}
                />
              </g>
            );
          })}

          {/* MA均线 */}
          {showIndicators.MA && (
            <>
              {/* MA5 */}
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.MA5) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 50 + ((maxPrice - d.MA5) / priceRange) * 300;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#58a6ff"
                strokeWidth="1.5"
              />
              {/* MA10 */}
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.MA10) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 50 + ((maxPrice - d.MA10) / priceRange) * 300;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#f7931a"
                strokeWidth="1.5"
              />
              {/* MA20 */}
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.MA20) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 50 + ((maxPrice - d.MA20) / priceRange) * 300;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#ee6c4d"
                strokeWidth="1.5"
              />
            </>
          )}

          {/* 布林带 */}
          {showIndicators.BB && (
            <>
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.BB_Upper) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 50 + ((maxPrice - d.BB_Upper) / priceRange) * 300;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#8b949e"
                strokeWidth="1"
                strokeDasharray="3,3"
              />
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.BB_Lower) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 50 + ((maxPrice - d.BB_Lower) / priceRange) * 300;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#8b949e"
                strokeWidth="1"
                strokeDasharray="3,3"
              />
            </>
          )}
        </svg>

        {/* MACD指标 */}
        {showIndicators.MACD && (
          <div className="indicator-panel macd-panel">
            <h4>MACD</h4>
            <svg width="100%" height="150" viewBox="0 0 1000 150">
              {klineData.map((d, i) => {
                if (!d.Histogram) return null;
                const x = 50 + (i * (900 / klineData.length));
                const height = Math.abs(d.Histogram) * 500;
                const y = d.Histogram >= 0 ? 75 - height : 75;
                const color = d.Histogram >= 0 ? '#f78166' : '#7ee787';
                
                return (
                  <rect
                    key={i}
                    x={x - 2}
                    y={y}
                    width="4"
                    height={height}
                    fill={color}
                  />
                );
              })}
            </svg>
          </div>
        )}

        {/* RSI指标 */}
        {showIndicators.RSI && (
          <div className="indicator-panel rsi-panel">
            <h4>RSI</h4>
            <svg width="100%" height="100" viewBox="0 0 1000 100">
              <line x1="50" y1="20" x2="950" y2="20" stroke="#f78166" strokeWidth="1" strokeDasharray="3,3" />
              <line x1="50" y1="80" x2="950" y2="80" stroke="#7ee787" strokeWidth="1" strokeDasharray="3,3" />
              <text x="10" y="25" fill="#f78166" fontSize="10">70</text>
              <text x="10" y="85" fill="#7ee787" fontSize="10">30</text>
              
              <polyline
                points={klineData.map((d, i) => {
                  if (!d.RSI) return null;
                  const x = 50 + (i * (900 / klineData.length));
                  const y = 100 - d.RSI;
                  return `${x},${y}`;
                }).filter(Boolean).join(' ')}
                fill="none"
                stroke="#58a6ff"
                strokeWidth="2"
              />
            </svg>
          </div>
        )}
      </div>

      {/* 最新数据 */}
      <div className="kline-stats">
        <div className="stat">
          <span>最新价</span>
          <strong>{klineData[klineData.length - 1].close.toFixed(2)}</strong>
        </div>
        {showIndicators.MA && (
          <>
            <div className="stat">
              <span>MA5</span>
              <strong style={{color: '#58a6ff'}}>
                {klineData[klineData.length - 1].MA5?.toFixed(2) || '-'}
              </strong>
            </div>
            <div className="stat">
              <span>MA10</span>
              <strong style={{color: '#f7931a'}}>
                {klineData[klineData.length - 1].MA10?.toFixed(2) || '-'}
              </strong>
            </div>
            <div className="stat">
              <span>MA20</span>
              <strong style={{color: '#ee6c4d'}}>
                {klineData[klineData.length - 1].MA20?.toFixed(2) || '-'}
              </strong>
            </div>
          </>
        )}
        {showIndicators.RSI && (
          <div className="stat">
            <span>RSI</span>
            <strong>{klineData[klineData.length - 1].RSI?.toFixed(2) || '-'}</strong>
          </div>
        )}
      </div>
    </div>
  );
}

export default KLineChart;
