# PDF 图纸扫描流水线

> **安全提醒**：当前仓库 `wejing555/sturdy-spork` 是公开仓库。不要把观棠项目原始图纸、合同、变更或其他非公开资料提交到这里。
>
> 这个仓库现在只保存**扫描脚本、规则和工作流模板**。真正项目资料应当：
> 1. 在本机运行扫描脚本；或
> 2. 复制这套脚本到一个**私有仓库**后再使用 GitHub Actions。

## 本地运行（推荐当前使用）

Python 3.10+：

```bash
python -m pip install "PyMuPDF>=1.24,<2"
python tools/scan_drawings.py "D:/观棠项目/图纸" --out "D:/观棠项目/scan_output" --render candidates --dpi 220
```

扫描器会递归查找 PDF，并输出：

- `manifest.json`：文件路径、大小、SHA256、页数、解析状态；
- `pages.csv`：所有页面索引、文字量、关键词评分；
- `candidate_pages.csv`：设计说明、给排水、雨水、采暖、试验、保温、变更等候选页；
- `text/<文件>/pXXXX.txt`：每页 PDF 文字层；
- `rendered/<文件>/pXXXX.png`：候选页高清 PNG；
- `summary.json`：扫描统计。

## 证据规则

扫描器只做机械工作，不做设计结论：

- 不根据文件名判断最新版；
- 不根据其他楼栋推断本楼栋参数；
- 不把 BIM/OCR/历史方案自动升级为正式设计依据；
- 不把关键词命中页直接认定为正确答案；
- 不做 OCR，避免低质量识别替代视觉审图。OCR 仅在后续确实需要时作为兜底；
- 候选页必须由 ChatGPT/专业人员结合正式图纸、变更和图签继续复核。

## GitHub Actions

仓库中包含 `.github/workflows/drawing-scan.yml` 模板。它用于私有仓库时可以：

1. 把 PDF 放到 `drawings/` 或手工指定目录；
2. 运行 `Drawing Scan` workflow；
3. 自动输出 `drawing-scan-<run number>` artifact；
4. 下载 artifact 后进行视觉复核和证据矩阵更新。

### 当前公开仓库不要上传项目图纸

`sturdy-spork` 当前 visibility 为 public，因此请不要为了触发 Actions 把观棠图纸提交到此仓库。等有私有仓库后，再把 `tools/scan_drawings.py` 与 workflow 复制过去。

## 当前观棠用途

不需要重新扫描全部资料。优先对剩余证据缺口定向扫描：

- 五栋住宅雨水：建筑设计说明、屋面平面、雨水斗/雨水管标注；
- 3# 采暖：若需要将温度、管材、盘管规格写成具体项目事实，再定向复核；
- 试验参数：设计说明中的试压、灌水、通球、冲洗条款；
- 保温：设计说明/节能专篇/正式变更中的保温材料、厚度和适用范围；
- PE 转换：如取得正式节点或厂家报审资料，再补连接构造。
