"""调试持仓数据结构"""
import akshare as ak
import pandas as pd

code = "161725"  # 招商中证白酒

print(f"测试基金：{code}")
print("=" * 80)

try:
    # 尝试获取持仓
    df = ak.fund_portfolio_hold_em(symbol=code, date="")
    
    if df.empty:
        print("❌ 返回数据为空，尝试指定日期...")
        df = ak.fund_portfolio_hold_em(symbol=code, date="20240930")
    
    if not df.empty:
        print(f"✅ 获取到 {len(df)} 条数据")
        print("\n列名：")
        print(df.columns.tolist())
        print("\n前5行数据：")
        print(df.head())
        print("\n数据类型：")
        print(df.dtypes)
    else:
        print("❌ 无法获取持仓数据")
        
except Exception as e:
    print(f"❌ 错误：{e}")
    import traceback
    traceback.print_exc()
