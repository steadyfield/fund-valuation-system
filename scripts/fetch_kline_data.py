"""
获取K线数据和技术指标
支持：基金、股票、全球资产
"""
import akshare as ak
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import pytz

def calculate_ma(data, periods=[5, 10, 20, 60]):
    """计算移动平均线"""
    for period in periods:
        data[f'MA{period}'] = data['close'].rolling(window=period).mean()
    return data

def calculate_macd(data, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = data['close'].ewm(span=fast).mean()
    ema_slow = data['close'].ewm(span=slow).mean()
    data['MACD'] = ema_fast - ema_slow
    data['Signal'] = data['MACD'].ewm(span=signal).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    return data

def calculate_rsi(data, period=14):
    """计算RSI指标"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """计算布林带"""
    data['BB_Middle'] = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    data['BB_Upper'] = data['BB_Middle'] + (std_dev * std)
    data['BB_Lower'] = data['BB_Middle'] - (std_dev * std)
    return data

def get_fund_kline(code, days=180):
    """获取基金K线数据"""
    try:
        # 获取基金历史净值
        df = ak.fund_open_fund_info_em(fund=code, indicator="单位净值走势")
        if df.empty:
            return None
        
        # 转换格式
        df = df.tail(days)
        df['date'] = pd.to_datetime(df['净值日期'])
        df['close'] = df['单位净值'].astype(float)
        df['volume'] = 0  # 基金没有成交量
        
        # 计算技术指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        
        # 转换为JSON格式
        result = []
        for _, row in df.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'close': round(float(row['close']), 4),
                'MA5': round(float(row['MA5']), 4) if pd.notna(row['MA5']) else None,
                'MA10': round(float(row['MA10']), 4) if pd.notna(row['MA10']) else None,
                'MA20': round(float(row['MA20']), 4) if pd.notna(row['MA20']) else None,
                'MA60': round(float(row['MA60']), 4) if pd.notna(row['MA60']) else None,
                'MACD': round(float(row['MACD']), 4) if pd.notna(row['MACD']) else None,
                'Signal': round(float(row['Signal']), 4) if pd.notna(row['Signal']) else None,
                'Histogram': round(float(row['Histogram']), 4) if pd.notna(row['Histogram']) else None,
                'RSI': round(float(row['RSI']), 2) if pd.notna(row['RSI']) else None,
                'BB_Upper': round(float(row['BB_Upper']), 4) if pd.notna(row['BB_Upper']) else None,
                'BB_Middle': round(float(row['BB_Middle']), 4) if pd.notna(row['BB_Middle']) else None,
                'BB_Lower': round(float(row['BB_Lower']), 4) if pd.notna(row['BB_Lower']) else None,
            })
        
        return result
    except Exception as e:
        print(f"获取基金K线失败 {code}: {e}")
        return None

def get_stock_kline(code, days=180):
    """获取A股K线数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return None
        
        df['date'] = pd.to_datetime(df['日期'])
        df['close'] = df['收盘'].astype(float)
        df['open'] = df['开盘'].astype(float)
        df['high'] = df['最高'].astype(float)
        df['low'] = df['最低'].astype(float)
        df['volume'] = df['成交量'].astype(float)
        
        # 计算技术指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        
        result = []
        for _, row in df.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': round(float(row['open']), 2),
                'high': round(float(row['high']), 2),
                'low': round(float(row['low']), 2),
                'close': round(float(row['close']), 2),
                'volume': int(row['volume']),
                'MA5': round(float(row['MA5']), 2) if pd.notna(row['MA5']) else None,
                'MA10': round(float(row['MA10']), 2) if pd.notna(row['MA10']) else None,
                'MA20': round(float(row['MA20']), 2) if pd.notna(row['MA20']) else None,
                'MA60': round(float(row['MA60']), 2) if pd.notna(row['MA60']) else None,
                'MACD': round(float(row['MACD']), 4) if pd.notna(row['MACD']) else None,
                'Signal': round(float(row['Signal']), 4) if pd.notna(row['Signal']) else None,
                'Histogram': round(float(row['Histogram']), 4) if pd.notna(row['Histogram']) else None,
                'RSI': round(float(row['RSI']), 2) if pd.notna(row['RSI']) else None,
                'BB_Upper': round(float(row['BB_Upper']), 2) if pd.notna(row['BB_Upper']) else None,
                'BB_Middle': round(float(row['BB_Middle']), 2) if pd.notna(row['BB_Middle']) else None,
                'BB_Lower': round(float(row['BB_Lower']), 2) if pd.notna(row['BB_Lower']) else None,
            })
        
        return result
    except Exception as e:
        print(f"获取股票K线失败 {code}: {e}")
        return None

def get_global_asset_kline(symbol, asset_type, days=180):
    """获取全球资产K线数据（加密货币、美股、指数等）"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        
        if df.empty:
            return None
        
        df = df.reset_index()
        df['close'] = df['Close'].astype(float)
        df['open'] = df['Open'].astype(float)
        df['high'] = df['High'].astype(float)
        df['low'] = df['Low'].astype(float)
        df['volume'] = df['Volume'].astype(float)
        
        # 计算技术指标
        df = calculate_ma(df)
        df = calculate_macd(df)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        
        result = []
        for _, row in df.iterrows():
            result.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'open': round(float(row['open']), 2),
                'high': round(float(row['high']), 2),
                'low': round(float(row['low']), 2),
                'close': round(float(row['close']), 2),
                'volume': int(row['volume']),
                'MA5': round(float(row['MA5']), 2) if pd.notna(row['MA5']) else None,
                'MA10': round(float(row['MA10']), 2) if pd.notna(row['MA10']) else None,
                'MA20': round(float(row['MA20']), 2) if pd.notna(row['MA20']) else None,
                'MA60': round(float(row['MA60']), 2) if pd.notna(row['MA60']) else None,
                'MACD': round(float(row['MACD']), 4) if pd.notna(row['MACD']) else None,
                'Signal': round(float(row['Signal']), 4) if pd.notna(row['Signal']) else None,
                'Histogram': round(float(row['Histogram']), 4) if pd.notna(row['Histogram']) else None,
                'RSI': round(float(row['RSI']), 2) if pd.notna(row['RSI']) else None,
                'BB_Upper': round(float(row['BB_Upper']), 2) if pd.notna(row['BB_Upper']) else None,
                'BB_Middle': round(float(row['BB_Middle']), 2) if pd.notna(row['BB_Middle']) else None,
                'BB_Lower': round(float(row['BB_Lower']), 2) if pd.notna(row['BB_Lower']) else None,
            })
        
        return result
    except Exception as e:
        print(f"获取全球资产K线失败 {symbol}: {e}")
        return None

if __name__ == "__main__":
    # 测试
    print("测试基金K线：110020")
    fund_data = get_fund_kline("110020", days=90)
    if fund_data:
        print(f"获取到 {len(fund_data)} 条数据")
        print(f"最新: {fund_data[-1]}")
    
    print("\n测试股票K线：600519")
    stock_data = get_stock_kline("600519", days=90)
    if stock_data:
        print(f"获取到 {len(stock_data)} 条数据")
        print(f"最新: {stock_data[-1]}")
    
    print("\n测试全球资产K线：AAPL")
    global_data = get_global_asset_kline("AAPL", "stock_us", days=90)
    if global_data:
        print(f"获取到 {len(global_data)} 条数据")
        print(f"最新: {global_data[-1]}")
