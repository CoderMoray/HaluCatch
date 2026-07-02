# 固化 Skill 指南

> **目标**：把当前 10 个分散的 .py 脚本合并为 1 个干净、参数化、可复用的数据分析 Skill。
> **前置条件**：已完成 `02_问题清单与修复任务.md` 中的第一阶段修复。

---

## 什么是 Skill

Skill 是一个**可复用的自动化工具包**。你把分析流程封装成 Skill 后，下次只需要一句话就能重跑整个管线：

```
"帮我用 MyCoach DID Skill 分析新一季度的门店数据"
```

而不是重新粘贴 10 个文件、手动改路径、复制粘贴代码。

---

## 整合目标：从 10 个文件到 1 个

### 当前的混乱结构

```
did_data_prep.py          ← 数据清洗（基础版）
did_tier_prep.py          ← 数据清洗（加城市层级版）—— 跟上面 90% 重复
did_amount_prep.py        ← 数据清洗（金额版）—— 又是大量重复
run_did.py                ← DID 回归（基础版）
run_did_tier.py           ← DID 回归（城市层级版）
run_did_amount.py         ← DID 回归（金额版）
deep_dive_tier1.py        ← 深度分析一线城市
deep_dive_tier2.py        ← 深度分析二线城市 ← 跟前一个逻辑完全一样！
deep_dive_tier3.py        ← 深度分析三线城市 ← 三个文件逻辑重复
onsite_analysis_tool.py   ← CVR 转化率分析
```

### 整合后的干净结构

```
mycoach_did/
├── SKILL.md              ← Skill 入口，描述用法和输入输出
├── config.yaml           ← 配置文件：数据路径、时间跨度、分组定义
├── prepare.py            ← 数据清洗 + 合并（统一入口，参数控制是否加城市层级）
├── analyze.py            ← DID 回归 + 事件研究 + 安慰剂检验（参数控制指标、分组）
├── deep_dive.py          ← 城市层级深度分析（--tier 参数控制）
├── cvr_analysis.py       ← CVR 转化率 Z-test + 因果声明
├── validate.py           ← 前提假设验证（平行趋势、安慰剂、模型诊断）
└── utils.py              ← 公共函数（norm_cdf, run_ols, format_results 等）
```

---

## SKILL.md 模板

> AI 助手请直接使用以下模板。**不要修改结构**，只替换 `[...]` 标记的部分。

```markdown
---
name: mycoach-did-analysis
description: MyCoach 门店教练效果 DID 因果推断分析。支持 onSite/onAir 对客流量/订单量的因果效应估计，自动验证平行趋势假设，输出城市层级细分报告。
version: 2.0
type: 代码工程型
---

# MyCoach DID 因果推断分析 Skill

## 功能概述

使用双重差分法 (Difference-in-Differences, DID) 估计 MyCoach 门店教练项目
(onSite 驻场教练 / onAir 远程教练) 对门店客流量和订单量的因果效应。

自动包含：
- 事件研究（平行趋势验证）
- 安慰剂检验
- 模型诊断（R²、条件数）
- 置信区间量化
- 城市层级细分

## 数据要求

### 输入文件

| 文件 | 说明 | 格式 |
|------|------|------|
| 门店信息管理列表_FY[X]Q[Y]W[Z].xlsx | 每季度门店列表 | Excel |
| [X]Q[X]-[X]Q[X] 门店销售转化率.csv | 门店销售明细 | CSV |

### 必需字段

| 字段 | 含义 | 所在文件 |
|------|------|----------|
| POS Apple ID | 门店唯一标识 | 门店信息列表 |
| POS Type | 门店类型 (APR/APP) | 门店信息列表 |
| MyCoach 是否参与 | 参与状态 (onSite/onAir/N) | 门店信息列表 |
| pos_id | 门店ID | 销售CSV |
| traffic_reid | 客流量 | 销售CSV |
| fy_calendar | 财务日历 (FY25Q2WK1) | 销售CSV |

## 使用方法

### 基础用法
```bash
python prepare.py --data-dir ./数据源 --quarters FY25Q2,FY25Q3,FY25Q4,FY26Q1,FY26Q2
python analyze.py --data merged_did_data.csv --outcome traffic_reid
python deep_dive.py --data merged_did_tier_data.csv --tier 2
```

### 全自动管线
```bash
python run_pipeline.py --data-dir ./数据源 --quarters FY25Q2-FY26Q2
```

## 输出

| 输出 | 说明 |
|------|------|
| `merged_did_data.csv` | 清洗后的面板数据 |
| `report_did.md` | DID 分析报告（含置信区间和前提验证） |
| `report_tier.md` | 城市层级细分报告 |
| `event_study.png` | 平行趋势事件研究图 |

## 因果推断声明

本 Skill 估计的效应基于 DID 方法。其因果解释依赖于 **平行趋势假设**：
处理组和对照组在干预前具有相同的客流变化趋势。

每次运行会自动验证此假设。如果平行趋势不成立，输出结果仅反映相关性。

## 局限性

1. 仅适用于 APR/APP 类型门店
2. 假设无溢出效应（一家门店被教练不影响附近门店）
3. 季度粒度，无法捕捉周/日级别的动态
4. 不区分 onSite 和 onAir 的质量差异（仅统计有无）
```

---

## config.yaml 模板

```yaml
# MyCoach DID 分析配置

data:
  source_dir: "./数据源"
  quarters:
    - FY25Q2
    - FY25Q3
    - FY25Q4
    - FY26Q1
    - FY26Q2

  store_files_pattern: "门店信息管理列表_{quarter}*.xlsx"
  sales_file_pattern: "*门店销售转化率.csv"

filters:
  pos_types: ["APR", "APP"]           # 仅分析这两个类型
  mycoach_statuses: ["onSite", "onAir", "N"]  # 保留的参与状态
  min_traffic_per_period: 0           # 最低客流量阈值

analysis:
  outcome_variable: "traffic_reid"     # 结果变量（traffic_reid 或 order_count）
  time_column: "quarter"
  entity_column: "pos_id"
  treatment_column: "mycoach_status"
  control_group: "N"                   # 对照组名称
  treatment_groups: ["onSite", "onAir"]  # 处理组名称

  did:
    model: "TWFE"                      # 双向固定效应
    robust_se: "HC1"                  # 异方差稳健标准误
    confidence_level: 0.95            # 置信水平

  validation:
    event_study: true                  # 事件研究
    placebo_test: true                # 安慰剂检验
    placebo_lead: 1                   # 安慰剂前移期数
    condition_number_threshold: 30    # 共线性警告阈值

deep_dive:
  tiers: [1, 2, 3]                   # 城市层级：1=一线, 2=二线, 3=下沉
  pos_type_split: true               # 是否按 POS 类型分别分析

output:
  format: "md"                        # 报告格式（md 或 html）
  include_confidence_intervals: true
  include_limitations: true
```

---

## 整合步骤

AI 助手请按以下顺序执行：

### 步骤 1：抽取公共函数

创建 `utils.py`，包含：
- `run_ols()` — 通用 OLS 回归
- `norm_cdf()` — 正态 CDF（基于 scipy）
- `format_result()` — 统一的结果格式化输出
- `check_columns()` — 输入列校验

### 步骤 2：合并数据准备脚本

创建 `prepare.py`，接受 `--add-tier` 参数来控制是否添加城市层级列。

### 步骤 3：合并 DID 分析脚本

创建 `analyze.py`，接受：
- `--outcome`：traffic_reid 或 amount
- `--pos-type`：APR、APP 或 all
- `--validate`：是否执行前提验证
- `--confidence`：置信水平

### 步骤 4：合并城市层级分析

将 `deep_dive_tier1/2/3.py` 合并为 `deep_dive.py`，接受 `--tier` 参数。

### 步骤 5：修复 CVR 分析

创建 `cvr_analysis.py`，包含：
- 用 `scipy.stats.norm` 替代山寨 p-value 公式
- 加因果结论声明模板

### 步骤 6：创建前提验证脚本

创建 `validate.py`，参考 `03_补充验证代码模板.py`。

### 步骤 7：创建自动管线脚本

创建 `run_pipeline.py`，一键执行：
```
prepare → analyze → validate → deep_dive(×3) → cvr_analysis → 生成报告
```

### 步骤 8：写 SKILL.md 和 config.yaml

参考上方模板，填入正确路径和参数。

---

## 整合完成后的检查

- [ ] 原始 10 个 .py 中只有 utils.py 包含重复定义
- [ ] `python analyze.py --outcome traffic_reid` 能得到与旧 run_did.py 相同的结果
- [ ] `python deep_dive.py --tier 2` 能得到与旧 deep_dive_tier2.py 相同的结果
- [ ] `python validate.py` 能输出事件研究 + 安慰剂检验 + 诊断
- [ ] 所有输出都包含置信区间
- [ ] 所有脚本有基本的错误处理
- [ ] SKILL.md 完整描述输入、输出、局限性
- [ ] config.yaml 包含所有可配置参数
