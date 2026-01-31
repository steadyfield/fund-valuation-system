"""
测试股票持仓信息（包含涨跌幅和占比）
"""
import sys
sys.path.append('.')

from fetch_data import get_fund_valuation

# 测试几只基金
test_funds = [
    ("161725", "招商中证白酒"),
    ("110020", "易方达沪深300ETF联接A"),
    ("003096", "中欧医疗健康混合A"),
]

print("=" * 80)
print("测试股票持仓信息（涨跌幅 + 占比）")
print("=" * 80)

for code, name in test_funds:
    print(f"\n测试基金：{name} ({code})")
    print("-" * 80)
    
    result = get_fund_valuation(code, name)
    
    if result['success'] and result['holdings']:
        print(f"\n基金估值：{result['estimation']:+.2f}%")
        print(f"数据来源：{result['data_source']}")
        print(f"\n前{len(result['holdings'])}大重仓股：")
        print(f"{'股票名称':<12} {'代码':<10} {'占比':<8} {'涨跌幅':<10} {'贡献度':<10}")
        print("-" * 80)
        
        for stock in result['holdings'][:10]:
            print(f"{stock['股票名称']:<12} {stock['股票代码']:<10} "
                  f"{stock['持仓比例']:>6.2f}% "
                  f"{stock['涨跌幅']:>+7.2f}% "
                  f"{stock.get('贡献度', 0):>+8.4f}%")
        
        # 计算总贡献度
        total_contribution = sum(s.get('贡献度', 0) for s in result['holdings'])
        print("-" * 80)
        print(f"持仓股票对估值的总贡献：{total_contribution:+.4f}%")
    else:
        print("❌ 获取失败")
    
    print("\n" + "=" * 80)

print("\n✅ 测试完成！")
print("\n说明：")
print("- 持仓比例：该股票在基金中的占比")
print("- 涨跌幅：该股票当日的涨跌幅")
print("- 贡献度：该股票对基金估值的贡献 = 持仓比例 × 涨跌幅 / 100")
