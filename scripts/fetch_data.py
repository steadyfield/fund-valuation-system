import akshare as ak
import pandas as pd
import json
import os
from datetime import datetime
import pytz
import time

# === 配置区 ===
# 格式：{"代码": "名称"}
WATCH_LIST = {
    # === 宽基指数基金 ===
    "110020": "易方达沪深300ETF联接A",
    "000961": "天弘沪深300指数A",
    "110003": "易方达上证50指数A",
    "001548": "天弘上证50指数A",
    "160119": "南方中证500ETF联接A",
    "110026": "易方达创业板ETF联接A",
    "003765": "广发创业板ETF联接A",
    "005827": "易方达蓝筹精选混合",
    "001632": "天弘中证500指数A",
    "161017": "富国中证500指数增强",
    
    # === 科技主题 ===
    "161033": "富国中证智能汽车指数(LOF)A",
    "161028": "富国中证新能源汽车指数(LOF)A",
    "001156": "申万菱信新能源汽车主题混合",
    "001410": "信达澳银新能源产业股票",
    "001475": "易方达国防军工混合",
    "003834": "华夏能源革新股票A",
    
    # === 医药医疗 ===
    "161726": "招商国证生物医药指数(LOF)A",
    "001550": "天弘中证医药100指数A",
    "001551": "天弘中证医药100指数C",
    "003096": "中欧医疗健康混合A",
    "110023": "易方达医疗保健行业混合",
    "002190": "农银汇理医疗保健股票",
    
    # === 消费主题 ===
    "161725": "招商中证白酒指数(LOF)A",
    "160632": "鹏华酒指数(LOF)A",
    "000248": "汇添富中证主要消费ETF联接A",
    "001631": "天弘中证食品饮料指数A",
    "160222": "国泰国证食品饮料行业指数",
    
    # === 金融地产 ===
    "161121": "易方达银行指数(LOF)A",
    "001594": "天弘中证银行指数A",
    "160628": "鹏华地产指数(LOF)A",
    "001595": "天弘中证证券保险指数A",
    "160625": "鹏华证券保险指数(LOF)A",
    
    # === 军工国防 ===
    "161024": "富国中证军工指数(LOF)A",
    
    # === 新能源环保 ===
    "501057": "汇添富中证新能源汽车产业指数(LOF)A",
    
    # === 有色金属 ===
    "512400": "有色金属ETF",
    "160620": "鹏华中证A股资源产业指数(LOF)",
    "161819": "银华中证内地资源指数(LOF)",
    "160216": "国泰大宗商品配置(LOF)",
    
    # === 黄金贵金属 ===
    "000217": "华安黄金易ETF联接A",
    "518880": "华安黄金易ETF",
    "518800": "国泰黄金ETF",
    
    # === QDII海外 ===
    "004046": "华安纳斯达克100(QDII)",
    "040046": "华安纳斯达克100指数(QDII)",
    "161125": "易方达标普500指数(QDII-LOF)A",
    "270042": "广发纳斯达克100指数A(QDII)",
    "164906": "交银中证海外中国互联网指数(QDII-LOF)",
    
    # === 债券基金 ===
    "003376": "易方达安盈回报混合A",
    "110035": "易方达双债增强债券A",
    "000205": "易方达投资级信用债债券A",
    "110017": "易方达增强回报债券A",
    "110037": "易方达纯债债券A",
    "003358": "易方达中债3-5年期国债指数A",
    
    # === 混合型明星基金 ===
    "163406": "兴全合润混合(LOF)",
    "163402": "兴全趋势投资混合(LOF)",
    "110011": "易方达中小盘混合",
    "006229": "易方达成长精选混合A",
    
    # === 红利主题 ===
    "100032": "富国中证红利指数增强A",
    "501029": "华宝标普中国A股红利机会指数(LOF)A",
}

def get_fund_valuation(code, name):
    """获取基金的实时估值和持仓信息"""
    print(f"正在处理: {name} ({code})...")
    
    try:
        # 1. 获取实时估值数据（天天基金）
        estimation = 0.0
        est_time = "无实时数据"
        net_value = 0.0
        
        try:
            # 获取实时估值
            gz_data = ak.fund_em_value_estimation_em(symbol=code)
            if not gz_data.empty:
                estimation = float(gz_data['估值涨跌幅'].iloc[0])
                est_time = str(gz_data['最新更新时间'].iloc[0])
                
                # 尝试获取净值
                try:
                    net_value = float(gz_data['单位净值'].iloc[0])
                except:
                    pass
                    
                print(f"  ✓ 估值: {estimation:+.2f}%")
        except Exception as e:
            print(f"  ⚠ 无实时估值数据: {str(e)[:50]}")
            # 对于没有实时估值的基金，尝试获取净值涨跌幅
            try:
                fund_info = ak.fund_open_fund_info_em(fund=code, indicator="单位净值走势")
                if not fund_info.empty and len(fund_info) >= 2:
                    latest = float(fund_info['单位净值'].iloc[-1])
                    previous = float(fund_info['单位净值'].iloc[-2])
                    estimation = ((latest - previous) / previous) * 100
                    net_value = latest
                    est_time = str(fund_info['净值日期'].iloc[-1])
                    print(f"  ✓ 使用净值计算涨跌: {estimation:+.2f}%")
            except Exception as e2:
                print(f"  ⚠ 无法获取净值数据: {str(e2)[:50]}")

        # 2. 获取前十大重仓股（最新季报）
        holdings = []
        try:
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date="")
            if not portfolio.empty:
                # 获取股票持仓
                stock_holdings = portfolio[portfolio['资产类别'] == '股票']
                if not stock_holdings.empty:
                    # 取前10大重仓
                    top_holdings = stock_holdings.head(10)
                    holdings = []
                    for _, row in top_holdings.iterrows():
                        holdings.append({
                            "股票名称": str(row['股票名称']),
                            "持仓比例": float(row['占净值比例']),
                            "股票代码": str(row['股票代码']),
                            "持股数": str(row.get('持股数', '-')),
                            "持股市值": str(row.get('持股市值', '-'))
                        })
                    print(f"  ✓ 获取到 {len(holdings)} 只重仓股")
                else:
                    print(f"  ⚠ 无股票持仓数据")
        except Exception as e:
            print(f"  ⚠ 无法获取持仓: {str(e)[:50]}")
            # 尝试备用方法
            try:
                portfolio_backup = ak.fund_portfolio_holdings_stock_at_recent_report(symbol=code)
                if not portfolio_backup.empty:
                    holdings = []
                    for _, row in portfolio_backup.head(10).iterrows():
                        holdings.append({
                            "股票名称": str(row['股票名称']),
                            "持仓比例": float(row['持仓比例']),
                            "股票代码": str(row['股票代码']),
                            "持股数": "-",
                            "持股市值": "-"
                        })
                    print(f"  ✓ 使用备用方法获取到 {len(holdings)} 只重仓股")
            except:
                pass

        # 3. 获取基金基本信息
        fund_type = "未知"
        fund_company = "未知"
        fund_manager = "未知"
        
        try:
            fund_info_basic = ak.fund_individual_basic_info_xq(symbol=code)
            if not fund_info_basic.empty:
                info_dict = dict(zip(fund_info_basic['item'], fund_info_basic['value']))
                fund_type = info_dict.get('基金类型', '未知')
                fund_company = info_dict.get('基金公司', '未知')
                fund_manager = info_dict.get('基金经理', '未知')
                print(f"  ✓ 类型: {fund_type}, 公司: {fund_company}")
        except:
            pass

        return {
            "code": code,
            "name": name,
            "estimation": round(estimation, 2),
            "net_value": round(net_value, 4) if net_value > 0 else None,
            "update_time": est_time,
            "holdings": holdings,
            "fund_type": fund_type,
            "fund_company": fund_company,
            "fund_manager": fund_manager,
            "success": True
        }

    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")
        return {
            "code": code,
            "name": name,
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print("基金估值数据抓取开始")
    print("=" * 60)
    print(f"总共需要抓取 {len(WATCH_LIST)} 只基金")
    print()
    
    # 确保输出目录存在
    os.makedirs("data", exist_ok=True)

    results = []
    success_count = 0
    
    for i, (code, name) in enumerate(WATCH_LIST.items(), 1):
        print(f"[{i}/{len(WATCH_LIST)}] ", end="")
        data = get_fund_valuation(code, name)
        results.append(data)
        
        if data['success']:
            success_count += 1
        
        # 避免请求过快，每个基金间隔0.5秒
        if i < len(WATCH_LIST):
            time.sleep(0.5)
        print()

    # 获取北京时间作为最后更新时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    last_updated = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    final_output = {
        "last_updated": last_updated,
        "total_count": len(results),
        "success_count": success_count,
        "funds": results
    }

    # 写入 JSON
    output_file = "data/funds.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"数据更新完成！")
    print(f"成功: {success_count}/{len(results)}")
    print(f"输出文件: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
