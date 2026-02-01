import akshare as ak
import pandas as pd
import json
import os
from datetime import datetime
import pytz
import time
import requests

# === 配置区 ===
WATCH_LIST = {
	# === A股主动 ===
	"018957": "中航机遇领航混合C",
	"002112": "德邦鑫星价值灵活配置混合C",
	"016371": "信澳业绩驱动混合C",
	"019432": "永赢睿信混合C",
	"016858": "国金量化多因子股票C",
	"002834": "华夏锦绣灵活配置混合C",
	"021526": "南华丰汇混合C",
	"015868": "国泰海通中证1000指数增强C",
	"008319": "博道久航混合C",
	"007950": "招商量化精选股票C",
	"017874": "国金量化多策略灵活配置混合C",
	"016491": "华安事件驱动量化策略混合C",
	"017493": "东方红新动力灵活配置混合C",
	"501060": "中金中证优选300指数(LOF)A",
	
	# === A股指数 ===
	"020341": "工银瑞信黄金ETF联接E",
	"021375": "中欧中证红利低波动100指数A",
	"008163": "南方红利低波50ETF联接A",
	"007467": "华泰柏瑞中证红利低波动ETF联接C",
	"024117": "中欧国证自由现金流指数A",
	"023919": "国泰富时现金流ETF联接A",
    
    # === QDII海外 ===
	"012922": "易方达全球成长精选混合(QDII)C",
	"017731": "嘉实全球产业升级股票(QDII)C",
	"018147": "建信新兴市场优选混合(QDII)C",
	"016668": "景顺长城全球半导体芯片产业股票(QDII-FOF-LOF)C",
	"018230": "易方达全球优选企业混合(QDII)C",
	"021842": "国富全球科技互联混合(QDII)C",
	"014002": "浦银安盛全球智能科技股票(QDII)C",
	"019118": "景顺长城纳斯达克科技市值加权ETF联接(QDII)E",
	"012868": "易方达标普信息科技指数(QDII-LOF)C",
	"019172": "摩根纳斯达克100指数(QDII)A",
	"016452": "南方纳斯达克100指数(QDII)A",
	"019736": "宝盈纳斯达克100指数(QDII)A",
	"019305": "摩根标普500指数(QDII)C",
	"012860": "易方达标普500指数(QDII-LOF)C",
	"006075": "博时标普500ETF联接(QDII)C",
	
	# === A股偏债混合 ===
	"016367": "嘉实多利收益债券C",
	"018278": "博时稳健增利债券C",
	"014847": "博时恒乐债券C",
	"000069": "国投瑞银中高等级债券A",
	"024307": "兴业兴和盛债券C",
	"160323": "华夏磐泰混合(LOF)A",
	"017820": "鹏华丰利债券(LOF)C",
	"011250": "嘉实稳裕混合C",
	"710302": "富安达增强收益债券C",
	"017763": "银河领先债券C",
	"019594": "嘉实稳宁纯债债券C",
	"009271": "博时信用优选债券A",
	"015727": "中泰双利债券A",
}

# 全局缓存：股票实时价格
STOCK_PRICE_CACHE = {}

def get_stock_realtime_prices(stock_codes):
    """
    批量获取股票实时价格
    使用新浪财经接口，速度快
    """
    global STOCK_PRICE_CACHE
    
    if not stock_codes:
        return {}
    
    prices = {}
    
    # 分批处理，每次最多50只股票
    batch_size = 50
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i:i+batch_size]
        
        try:
            # 使用akshare获取实时行情
            for code in batch:
                try:
                    # 判断市场
                    if code.startswith('6'):
                        symbol = f"sh{code}"
                    else:
                        symbol = f"sz{code}"
                    
                    # 获取实时行情
                    df = ak.stock_zh_a_spot_em()
                    stock_data = df[df['代码'] == code]
                    
                    if not stock_data.empty:
                        current_price = float(stock_data['最新价'].iloc[0])
                        prev_close = float(stock_data['昨收'].iloc[0])
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                        
                        prices[code] = {
                            'current': current_price,
                            'prev_close': prev_close,
                            'change_pct': change_pct
                        }
                        STOCK_PRICE_CACHE[code] = prices[code]
                except:
                    # 如果获取失败，尝试使用缓存
                    if code in STOCK_PRICE_CACHE:
                        prices[code] = STOCK_PRICE_CACHE[code]
                    continue
            
            time.sleep(0.1)  # 避免请求过快
            
        except Exception as e:
            print(f"批量获取股票价格失败: {e}")
            continue
    
    return prices

def calculate_fund_valuation_from_holdings(holdings, net_value):
    """
    根据持仓和股票实时价格计算基金估值
    
    算法：
    1. 获取所有重仓股的实时涨跌幅
    2. 按持仓比例加权计算
    3. 考虑股票仓位（通常80-95%）
    """
    if not holdings or not net_value:
        return None
    
    # 提取股票代码
    stock_codes = [h['股票代码'] for h in holdings if h.get('股票代码')]
    
    if not stock_codes:
        return None
    
    # 获取股票实时价格
    stock_prices = get_stock_realtime_prices(stock_codes)
    
    if not stock_prices:
        return None
    
    # 计算加权涨跌幅
    total_weight = 0
    weighted_change = 0
    
    for holding in holdings:
        code = holding.get('股票代码')
        ratio = holding.get('持仓比例', 0)
        
        if code in stock_prices:
            change_pct = stock_prices[code]['change_pct']
            weighted_change += change_pct * ratio
            total_weight += ratio
    
    if total_weight == 0:
        return None
    
    # 计算基金估值涨跌幅
    # 假设股票仓位为total_weight（实际持仓比例）
    fund_change_pct = weighted_change / 100  # 转换为百分比
    
    # 计算估算净值
    estimated_value = net_value * (1 + fund_change_pct / 100)
    
    return {
        'estimation': round(fund_change_pct, 2),
        'est_value': round(estimated_value, 4),
        'stock_count': len(stock_prices),
        'total_weight': round(total_weight, 2),
        'source': '成分股实时计算'
    }

def get_accurate_valuation(code):
    """
    获取最准确的估值数据
    优先使用天天基金实时接口
    """
    try:
        # 天天基金实时估值接口（最准确）
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data_str = response.text
            data_str = data_str.replace('jsonpgz(', '').replace(');', '')
            data = json.loads(data_str)
            
            return {
                'estimation': float(data['gszzl']),
                'net_value': float(data['dwjz']),
                'est_value': float(data['gsz']),
                'update_time': data['gztime'],
                'source': '天天基金实时'
            }
    except:
        pass
    
    # 备用方法1: akshare
    try:
        gz_data = ak.fund_em_value_estimation_em(symbol=code)
        if not gz_data.empty:
            return {
                'estimation': float(gz_data['估值涨跌幅'].iloc[0]),
                'net_value': float(gz_data['单位净值'].iloc[0]) if '单位净值' in gz_data.columns else 0,
                'est_value': float(gz_data['估算净值'].iloc[0]) if '估算净值' in gz_data.columns else 0,
                'update_time': str(gz_data['最新更新时间'].iloc[0]),
                'source': 'akshare'
            }
    except:
        pass
    
    # 备用方法2: 从净值计算
    try:
        fund_info = ak.fund_open_fund_info_em(fund=code, indicator="单位净值走势")
        if not fund_info.empty and len(fund_info) >= 2:
            latest = float(fund_info['单位净值'].iloc[-1])
            previous = float(fund_info['单位净值'].iloc[-2])
            estimation = ((latest - previous) / previous) * 100
            return {
                'estimation': estimation,
                'net_value': latest,
                'est_value': latest,
                'update_time': str(fund_info['净值日期'].iloc[-1]),
                'source': '净值计算'
            }
    except:
        pass
    
    return None

def get_fund_valuation(code, name):
    """获取基金完整信息（包含实时计算估值）"""
    print(f"[{code}] {name}...", end=" ")
    
    try:
        # 1. 获取官方估值
        valuation = get_accurate_valuation(code)
        if valuation:
            estimation = valuation['estimation']
            net_value = valuation['net_value']
            est_value = valuation['est_value']
            est_time = valuation['update_time']
            data_source = valuation['source']
            print(f"{estimation:+.2f}%", end=" ")
        else:
            estimation = 0.0
            net_value = 0.0
            est_value = 0.0
            est_time = "无数据"
            data_source = "无"
            print("无估值", end=" ")

        # 2. 获取持仓
        holdings = []
        try:
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date="")
            if not portfolio.empty:
                stock_holdings = portfolio[portfolio['资产类别'] == '股票']
                if not stock_holdings.empty:
                    for _, row in stock_holdings.head(10).iterrows():
                        holdings.append({
                            "股票名称": str(row['股票名称']),
                            "持仓比例": float(row['占净值比例']),
                            "股票代码": str(row['股票代码']),
                        })
                    print(f"✓{len(holdings)}股", end=" ")
        except:
            pass

        # 3. 根据持仓计算实时估值
        realtime_valuation = None
        if holdings and net_value > 0:
            realtime_valuation = calculate_fund_valuation_from_holdings(holdings, net_value)
            if realtime_valuation:
                print(f"[实时:{realtime_valuation['estimation']:+.2f}%]", end="")
        
        print()  # 换行

        result = {
            "code": code,
            "name": name,
            "estimation": round(estimation, 2),
            "net_value": round(net_value, 4) if net_value > 0 else None,
            "est_value": round(est_value, 4) if est_value > 0 else None,
            "update_time": est_time,
            "data_source": data_source,
            "holdings": holdings,
            "success": True
        }
        
        # 添加实时计算估值
        if realtime_valuation:
            result['realtime_estimation'] = realtime_valuation['estimation']
            result['realtime_est_value'] = realtime_valuation['est_value']
            result['realtime_source'] = realtime_valuation['source']
            result['realtime_stock_count'] = realtime_valuation['stock_count']
            result['realtime_weight'] = realtime_valuation['total_weight']
        
        return result

    except Exception as e:
        print(f"✗ {str(e)[:30]}")
        return {
            "code": code,
            "name": name,
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print(f"开始抓取 {len(WATCH_LIST)} 只基金的实时估值数据")
    print("包含：官方估值 + 成分股实时计算估值")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)

    results = []
    success_count = 0
    realtime_count = 0
    
    for i, (code, name) in enumerate(WATCH_LIST.items(), 1):
        print(f"[{i}/{len(WATCH_LIST)}] ", end="")
        data = get_fund_valuation(code, name)
        results.append(data)
        
        if data['success']:
            success_count += 1
            if data.get('realtime_estimation') is not None:
                realtime_count += 1
        
        if i < len(WATCH_LIST):
            time.sleep(0.3)  # 稍微增加间隔，因为要获取股票价格

    beijing_tz = pytz.timezone('Asia/Shanghai')
    last_updated = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    final_output = {
        "last_updated": last_updated,
        "total_count": len(results),
        "success_count": success_count,
        "realtime_count": realtime_count,
        "funds": results
    }

    with open("data/funds.json", "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"完成！")
    print(f"成功: {success_count}/{len(results)}")
    print(f"实时计算: {realtime_count}/{success_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()

