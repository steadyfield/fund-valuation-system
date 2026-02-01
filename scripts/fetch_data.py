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

def get_stock_name(stock_code):
    """获取股票真实名称（增强版）"""
    try:
        # 方法1: 从个股信息获取
        info = ak.stock_individual_info_em(symbol=stock_code)
        if not info.empty:
            name_row = info[info['item'] == '股票简称']
            if not name_row.empty:
                return str(name_row['value'].values[0])
    except:
        pass
    
    try:
        # 方法2: 从实时行情获取
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == stock_code]
        if not stock.empty:
            return str(stock['名称'].values[0])
    except:
        pass
    
    try:
        # 方法3: 从历史数据获取
        hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
        if not hist.empty and '股票名称' in hist.columns:
            return str(hist['股票名称'].iloc[0])
    except:
        pass
    
    return None

def get_stock_change(stock_code):
    """获取股票当日涨跌幅"""
    try:
        # 方法1: 从实时行情获取
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == stock_code]
        if not stock.empty:
            change = float(stock['涨跌幅'].values[0])
            return change
    except:
        pass
    
    try:
        # 方法2: 从个股信息获取
        info = ak.stock_individual_info_em(symbol=stock_code)
        if not info.empty:
            change_row = info[info['item'] == '涨跌幅']
            if not change_row.empty:
                change_str = str(change_row['value'].values[0]).replace('%', '')
                return float(change_str)
    except:
        pass
    
    return 0.0

def get_fund_valuation(code, name):
    """获取基金完整信息（包含股票涨跌幅）"""
    print(f"[{code}] {name}...", end=" ")
    
    try:
        # 获取估值
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

        # 获取持仓
        holdings = []
        try:
            # 获取最新持仓数据
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date="")
            
            if not portfolio.empty:
                # 直接处理股票数据（无需筛选资产类别）
                for _, row in portfolio.head(10).iterrows():
                    stock_code = str(row['股票代码'])
                    stock_name = str(row['股票名称'])
                    holding_ratio = float(row['占净值比例'])
                    
                    # 如果股票名称是占位符，尝试获取真实名称
                    if stock_name.startswith('股票') or stock_name == '' or len(stock_name) < 2:
                        real_name = get_stock_name(stock_code)
                        if real_name:
                            stock_name = real_name
                    
                    # 获取股票当日涨跌幅
                    stock_change = get_stock_change(stock_code)
                    
                    holdings.append({
                        "股票名称": stock_name,
                        "股票代码": stock_code,
                        "持仓比例": round(holding_ratio, 2),
                        "涨跌幅": round(stock_change, 2),
                        "贡献度": round(holding_ratio * stock_change / 100, 4)
                    })
                print(f"✓{len(holdings)}股")
            else:
                print("无持仓")
        except Exception as e:
            print(f"✗{str(e)[:20]}")

        return {
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
    print(f"开始抓取 {len(WATCH_LIST)} 只基金的准确估值数据")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)

    results = []
    success_count = 0
    
    for i, (code, name) in enumerate(WATCH_LIST.items(), 1):
        print(f"[{i}/{len(WATCH_LIST)}] ", end="")
        data = get_fund_valuation(code, name)
        results.append(data)
        
        if data['success']:
            success_count += 1
        
        if i < len(WATCH_LIST):
            time.sleep(0.2)

    beijing_tz = pytz.timezone('Asia/Shanghai')
    last_updated = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    final_output = {
        "last_updated": last_updated,
        "total_count": len(results),
        "success_count": success_count,
        "funds": results
    }

    with open("data/funds.json", "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"完成！成功: {success_count}/{len(results)}")
    print("=" * 60)

if __name__ == "__main__":
    main()

