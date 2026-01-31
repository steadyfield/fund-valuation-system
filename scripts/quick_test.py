"""快速测试持仓功能"""
import sys
sys.path.append('.')
from scripts.fetch_data import get_fund_valuation

# 测试3只基金
test_funds = [
    ("161725", "招商中证白酒"),
    ("110020", "易方达沪深300"),
    ("003096", "中欧医疗健康"),
]

print("=" * 80)
for code, name in test_funds:
    print(f"\n测试：{name} ({code})")
    result = get_fund_valuation(code, name)
    
    if result['success'] and result.get('holdings'):
        print(f"\n✅ 基金估值：{result['estimation']:+.2f}%")
        print(f"持仓数量：{len(result['holdings'])}只")
        print("\n前5大重仓股：")
        print(f"{'股票名称':<15} {'代码':<10} {'占比':<8} {'涨跌幅':<10}")
        print("-" * 60)
        for stock in result['holdings'][:5]:
            print(f"{stock['股票名称']:<15} {stock['股票代码']:<10} "
                  f"{stock['持仓比例']:>6.2f}% {stock['涨跌幅']:>+7.2f}%")
    else:
        print("❌ 获取失败或无持仓数据")
    print("=" * 80)
