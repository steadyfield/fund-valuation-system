import React, { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 读取 public/data/funds.json
    fetch('/data/funds.json')
      .then(res => {
        if (!res.ok) throw new Error('数据文件不存在');
        return res.json();
      })
      .then(jsonData => {
        setData(jsonData);
        setLoading(false);
      })
      .catch(err => {
        console.error("加载失败:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>正在加载资产数据...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="error">
        <h2>⚠️ 暂无数据</h2>
        <p>请按照以下步骤操作：</p>
        <ol>
          <li>进入 GitHub 仓库的 <strong>Actions</strong> 标签</li>
          <li>选择 <strong>Auto Fund Valuation & Deploy</strong></li>
          <li>点击 <strong>Run workflow</strong> 按钮</li>
          <li>等待 2-3 分钟后刷新本页面</li>
        </ol>
      </div>
    );
  }

  return (
    <div className="container">
      <header className="header">
        <h1>📊 基金估值雷达</h1>
        <div className="header-info">
          <span className="last-updated">🕐 更新时间: {data.last_updated}</span>
          <button 
            className="refresh-btn" 
            onClick={() => window.location.reload()}
            title="刷新数据"
          >
            🔄 刷新
          </button>
        </div>
      </header>

      <div className="grid">
        {data.funds.map((fund) => (
          <div key={fund.code} className="card">
            <div className="card-header">
              <h3>{fund.name}</h3>
              <span className="code">{fund.code}</span>
            </div>

            {fund.success ? (
              <>
                <div className={`estimation ${fund.estimation >= 0 ? 'up' : 'down'}`}>
                  {fund.estimation > 0 ? '+' : ''}{fund.estimation.toFixed(2)}%
                  <small>实时估值</small>
                </div>

                <div className="holdings">
                  <h4>前五大重仓穿透</h4>
                  {fund.holdings && fund.holdings.length > 0 ? (
                    <ul>
                      {fund.holdings.map((stock, index) => (
                        <li key={index}>
                          <span>{stock.股票名称}</span>
                          <span className="weight">{stock.持仓比例}%</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-data">暂无持仓数据</p>
                  )}
                </div>
              </>
            ) : (
              <div className="fund-error">
                <p>⚠️ 数据获取失败</p>
                <small>{fund.error || '未知错误'}</small>
              </div>
            )}
          </div>
        ))}
      </div>

      <footer className="footer">
        <p>数据来源于公开接口，仅供参考 | 工作日每小时自动更新</p>
      </footer>
    </div>
  );
}

export default App;
