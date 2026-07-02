"""
验证脚本模板：DID 前提假设检查
================================
此脚本展示如何对 MyCoach DID 分析做前提假设验证。
AI 助手应参考此模板，适配实际数据后生成可运行的版本。

用法（修复完成后）：
    python validate_did.py --data merged_did_data.csv

输出：
    1. 事件研究图 — 平行趋势诊断
    2. 安慰剂检验结果
    3. 模型诊断报告
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ──────────────────────────────────────────────────────
# 工具函数（供 AI 参考，不要照搬；适配你的数据）
# ──────────────────────────────────────────────────────

def event_study(df, treatment_col, outcome_col, entity_col, time_col):
    """
    事件研究：画出干预前后各期的系数。

    参数
    ----
    df : DataFrame
        包含四列的面板数据
    treatment_col : str
        标记是否为处理组的列名（0/1 或 True/False）
    outcome_col : str
        结果变量列名（如 traffic_reid）
    entity_col : str
        个体 ID 列名（如 pos_id）
    time_col : str
        时间列名（如 quarter），已编码为整数索引

    返回
    ----
    dict : {"pre_trends": [...], "post_effects": [...]}
        pre_trends: 干预前各期的 (系数, se, p)
        post_effects: 干预后各期的 (系数, se, p)
    """
    # 找到每家门店被首次干预的时间
    df = df.copy()
    
    # 需要知道每家门店第一次被处理的时间
    # 假设已经有了 first_treat_time 列
    # 如果没有，需要先从数据中计算
    
    # 生成相对时间哑变量
    min_rel = int(df['rel_time'].min())
    max_rel = int(df['rel_time'].max())
    
    entity_dummies = pd.get_dummies(df[entity_col], drop_first=True, dtype=float)
    time_dummies = pd.get_dummies(df[time_col], drop_first=True, dtype=float)
    
    rel_dummies = {}
    for k in range(min_rel, max_rel + 1):
        if k != -1:  # 以 t=-1 为基期（标准做法）
            rel_dummies[f'rel_{k}'] = (df['rel_time'] == k).astype(float)
    
    if not rel_dummies:
        raise ValueError("无法生成相对时间哑变量，请检查数据")
    
    X_parts = [pd.DataFrame(rel_dummies), entity_dummies, time_dummies]
    X = pd.concat(X_parts, axis=1)
    X.insert(0, 'Intercept', 1.0)
    
    Y = df[outcome_col].values
    X_mat = X.values
    
    coefs, residuals, rank, s = np.linalg.lstsq(X_mat, Y, rcond=None)
    n, p = X_mat.shape
    dof = n - p
    
    Y_pred = X_mat @ coefs
    sigma2 = np.sum((Y - Y_pred)**2) / dof
    
    try:
        XtX_inv = np.linalg.inv(X_mat.T @ X_mat)
    except np.linalg.LinAlgError:
        XtX_inv = np.linalg.pinv(X_mat.T @ X_mat)
    
    se = np.sqrt(np.abs(np.diag(XtX_inv) * sigma2))
    
    # 提取相对时间系数
    results = {}
    for i, col in enumerate(X.columns):
        if col.startswith('rel_'):
            k = int(col.replace('rel_', ''))
            t_stat = coefs[i] / se[i]
            p_val = 2 * stats.norm.sf(abs(t_stat))  # ← 用 scipy，不是山寨公式
            results[k] = (coefs[i], se[i], p_val)
    
    return results


def placebo_test(df, outcome_col, entity_col, time_col, treat_col):
    """
    安慰剂检验：把干预时间点前移，假处理不应显著。

    返回
    ----
    tuple : (真实系数, 真实p值, 安慰剂系数, 安慰剂p值)
    """
    # --- 真实模型 ---
    real_coef, real_p = _run_simple_did(df, outcome_col, entity_col, time_col, treat_col)
    
    # --- 安慰剂模型：干预时间前移 1 期 ---
    df_placebo = df.copy()
    # 假设已有 first_treat_time 列，将其减去 1
    if 'first_treat_time' in df_placebo.columns:
        df_placebo['first_treat_time'] = df_placebo['first_treat_time'] - 1
        df_placebo[treat_col] = (
            df_placebo[time_col] >= df_placebo['first_treat_time']
        ).astype(float)
        placebo_coef, placebo_p = _run_simple_did(
            df_placebo, outcome_col, entity_col, time_col, treat_col
        )
    else:
        placebo_coef, placebo_p = None, None
    
    return real_coef, real_p, placebo_coef, placebo_p


def _run_simple_did(df, outcome_col, entity_col, time_col, treat_col):
    """简化的 DID 回归，返回处理系数和 p-value。"""
    entity_dummies = pd.get_dummies(df[entity_col], drop_first=True, dtype=float)
    time_dummies = pd.get_dummies(df[time_col], drop_first=True, dtype=float)
    
    X = pd.concat([
        pd.DataFrame({'treat': df[treat_col].astype(float)}),
        entity_dummies,
        time_dummies,
    ], axis=1)
    X.insert(0, 'Intercept', 1.0)
    
    Y = df[outcome_col].values
    X_mat = X.values
    
    coefs, _, _, _ = np.linalg.lstsq(X_mat, Y, rcond=None)
    Y_pred = X_mat @ coefs
    n, p = X_mat.shape
    dof = n - p
    sigma2 = np.sum((Y - Y_pred)**2) / dof
    
    try:
        XtX_inv = np.linalg.inv(X_mat.T @ X_mat)
    except np.linalg.LinAlgError:
        XtX_inv = np.linalg.pinv(X_mat.T @ X_mat)
    
    se = np.sqrt(np.abs(np.diag(XtX_inv) * sigma2))
    
    treat_idx = list(X.columns).index('treat')
    t_stat = coefs[treat_idx] / se[treat_idx]
    p_val = 2 * stats.norm.sf(abs(t_stat))  # ← scipy
    
    return coefs[treat_idx], p_val


def model_diagnostics(X_mat, Y, coefs):
    """模型诊断：R²、条件数、VIF 近似。"""
    Y_pred = X_mat @ coefs
    ss_res = np.sum((Y - Y_pred)**2)
    ss_tot = np.sum((Y - Y.mean())**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    cond_number = np.linalg.cond(X_mat)
    
    return {
        'R²': r_squared,
        '条件数': cond_number,
        '共线性警告': cond_number > 30,
        '样本量': X_mat.shape[0],
        '特征数': X_mat.shape[1],
    }


# ──────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DID 前提假设验证')
    parser.add_argument('--data', required=True, help='CSV 数据路径')
    parser.add_argument('--outcome', default='traffic_reid', help='结果变量列名')
    parser.add_argument('--entity', default='pos_id', help='个体 ID 列名')
    parser.add_argument('--time', default='q_idx', help='时间索引列名')
    parser.add_argument('--treatment', default='is_treated', help='处理标记列名')
    args = parser.parse_args()
    
    # ── 加载数据 ──
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ 文件不存在: {args.data}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    print(f"✅ 加载 {len(df)} 行数据")
    
    # ── 确保必要的列存在 ──
    required_cols = [args.outcome, args.entity, args.time]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ 缺少必要列: {missing}")
        print(f"   可用列: {list(df.columns)}")
        sys.exit(1)
    
    # ── 1. 事件研究（平行趋势检验）──
    print("\n" + "=" * 60)
    print("📊 1. 事件研究 — 平行趋势诊断")
    print("=" * 60)
    
    # 注意：这里需要你的数据中已有 rel_time 和 is_treated 列
    # 如果没有，请先在数据预处理中生成
    if 'rel_time' in df.columns and args.treatment in df.columns:
        try:
            es_results = event_study(
                df, args.treatment, args.outcome, args.entity, args.time
            )
            
            print(f"\n{'相对时期':<12} {'系数':>10} {'标准误':>10} {'p值':>10}")
            print("-" * 45)
            
            pretrend_sig = False
            for k in sorted(es_results.keys()):
                coef, se, p = es_results[k]
                flag = ""
                if k < 0 and p < 0.05:
                    flag = " ⚠️"
                    pretrend_sig = True
                print(f"  t={k:<8d} {coef:>10.1f} {se:>10.1f} {p:>10.3f}{flag}")
            
            if pretrend_sig:
                print("\n❌ 干预前存在显著趋势差异 → 平行趋势假设不成立")
            else:
                print("\n✅ 干预前趋势差异不显著 → 支持平行趋势假设")
        except Exception as e:
            print(f"⚠️ 事件研究执行失败: {e}")
            print("   请确保数据中有 rel_time 和 is_treated 列")
    else:
        print("⚠️ 跳过事件研究：缺少 rel_time 或 is_treated 列")
        print(f"   当前列: {list(df.columns)}")
        print("   请先生成以下列：")
        print("   - rel_time: 相对干预时间的偏移（-2, -1, 0, 1, 2, ...）")
        print(f"   - {args.treatment}: 是否处于处理期（0/1）")
    
    # ── 2. 安慰剂检验 ──
    print("\n" + "=" * 60)
    print("💊 2. 安慰剂检验 — 假干预不应显著")
    print("=" * 60)
    
    if args.treatment in df.columns:
        try:
            real_c, real_p, placebo_c, placebo_p = placebo_test(
                df, args.outcome, args.entity, args.time, args.treatment
            )
            
            print(f"\n真实处理效应:  {real_c:>10.1f}  (p={real_p:.4f})")
            if placebo_c is not None:
                print(f"安慰剂效应:    {placebo_c:>10.1f}  (p={placebo_p:.4f})")
                
                if real_p < 0.05 and placebo_p >= 0.05:
                    print("\n✅ 真实效应显著 → 安慰剂不显著 → 支持因果推断")
                elif placebo_p < 0.05:
                    print("\n❌ 安慰剂也显著 → 可能存在未观测的混淆因素")
                else:
                    print("\n⚠️ 真实效应不显著 → 即便安慰剂不显著，结论也有限")
            else:
                print("\n⚠️ 无法执行安慰剂检验：缺少 first_treat_time 列")
        except Exception as e:
            print(f"⚠️ 安慰剂检验执行失败: {e}")
    else:
        print(f"⚠️ 跳过安慰剂检验：缺少 {args.treatment} 列")
    
    # ── 3. 模型诊断 ──
    print("\n" + "=" * 60)
    print("🔍 3. 模型诊断")
    print("=" * 60)
    
    # 简单 OLS 诊断
    try:
        entity_dummies = pd.get_dummies(df[args.entity], drop_first=True, dtype=float)
        time_dummies = pd.get_dummies(df[args.time], drop_first=True, dtype=float)
        treat_df = pd.DataFrame({'treat': df[args.treatment].astype(float)}) if args.treatment in df.columns else None
        
        parts = [pd.DataFrame({'Intercept': np.ones(len(df))})]
        if treat_df is not None:
            parts.append(treat_df)
        parts.extend([entity_dummies, time_dummies])
        
        X_full = pd.concat(parts, axis=1)
        Y_full = df[args.outcome].values
        X_mat = X_full.values
        
        coefs, _, _, _ = np.linalg.lstsq(X_mat, Y_full, rcond=None)
        
        diag = model_diagnostics(X_mat, Y_full, coefs)
        for k, v in diag.items():
            if isinstance(v, bool):
                status = "⚠️" if v else "✅"
                print(f"  {k}: {status}")
            elif isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")
        
        # 常识检查
        if args.treatment in df.columns and treat_df is not None:
            treat_idx = list(X_full.columns).index('treat')
            treat_coef = coefs[treat_idx]
            if treat_coef < 0:
                print("\n⚠️ 注意：处理效应为负，请确认符合业务预期")
        
        if diag['R²'] < 0.1:
            print("\n⚠️ R² < 0.1，模型解释力极低，请检查数据质量")
        
        if diag['样本量'] < 30:
            print("\n⚠️ 样本量 < 30，估计结果可能不稳定")
            
    except Exception as e:
        print(f"⚠️ 模型诊断失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 全部检查完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
