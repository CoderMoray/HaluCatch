# HaluCatch 补漏清单

**用完即弃** — 开发 agent 执行完毕后删除本文档。

---

## 1. Encoding: `errors='replace'` → `errors='backslashreplace'`

**文件**: `halucatch_core.py`，第 45、50 行（两处）

```diff
- with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
+ with open(fpath, 'r', encoding='utf-8', errors='backslashreplace') as f:
```

---

## 2. README 文件结构树更新

**文件**: `README.md`，第 115-124 行

当前树引用了已删除的文件，替换为：

```
├── docs/
│   ├── CHANGELOG.md
│   ├── FAQ.md
│   ├── decision-flowchart.html
│   └── decision-flowchart-prompt.md
├── tests/
│   ├── __init__.py
│   └── test_halucatch.py     ← 21 个单元测试
└── .gitignore
```

---

## 3. README FAQ 补 3 条

**文件**: `README.md`，第 235 行（「许可」之前）追加：

```markdown
**Q: 怎么快速上手？**
A: 3 步——1. 跑一次审查看通俗版了解问题；2. 打开行动版按清单逐项修复；3. 修复后重新审查验证改善。

**Q: 出现文件编码错误怎么办？**
A: HaluCatch 以 UTF-8 读取文件。非 UTF-8 编码（如 GBK）会保留原始字节转义标记，不会静默丢数据。

**Q: 「Phase 4 闭环」怎么用？**
A: 审查完成后选「执行修复」→ 方案发给 AI 实施 → 重新审查验证。或选「我有更好建议」→ 描述想法 → 重生成方案。
```

---

## 验收

```bash
grep -c "errors='replace'" halucatch_core.py   # 应 0
grep -c "test-prompt\|v6-to-v7" README.md       # 应 0
grep -c "3 步\|编码错误\|Phase 4" README.md      # 各应 1
pytest tests/ -v                                  # 21/21
```
