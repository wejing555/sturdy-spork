# 规范节点图生成器（参数化骨架）

这是一个以 GitHub 版本管理为核心的建筑节点图生成骨架，目标是把“已核实的规范条文、项目图纸和输入参数”转换为可编辑的 DXF，并在需要时导出 SVG/PDF。

## 设计边界

- GitHub 仓库只负责保存代码、规则、模板和来源记录；实际运行在 Python 环境或 BIM/CAD 工作站。
- 本项目不替代设计、审图或施工技术交底。
- 不允许程序猜测规范版本、条文数值、管径、标高、喷头间距或构造做法。
- 规则中的 B、尺寸和结论，在没有正式来源前必须保持“待核”。
- 生成结果默认是“参数化草图/校核辅助文件”；经过来源核对和专业人员复核后，才能作为项目文件使用。

## 推荐技术栈

- ezdxf（https://github.com/mozman/ezdxf）：生成和审计 DXF，并可通过绘图扩展导出 SVG/PDF。
- IfcOpenShell（https://github.com/IfcOpenShell/IfcOpenShell）：处理 IFC/BIM 数据、几何和模型校验。
- pyRevit（https://github.com/pyrevitlabs/pyRevit）：只有在安装 Autodesk Revit 的 Windows 工作站上才使用。

## 目录

- rules/：带来源字段的规则和参数定义。
- src/：确定性生成与校验代码。
- templates/：经过复核后才能启用的节点图模板。
- docs/：来源核验和出图检查清单。
- requirements.txt：Python 运行依赖。

## 当前示例

rules/obstruction_rule.example.yaml 仅演示如何记录“障碍物宽度超过阈值时需要复核下方喷头”的规则结构。示例中的 B 没有填入任何数值，也没有声称某个规范版本或页码。

运行参数化校核草图：

~~~
python -m src.generate_node --help
python -m src.generate_node \
  --obstruction-width-m <已核实障碍物宽度> \
  --threshold-m <已核实阈值> \
  --out output/obstruction_review.dxf
~~~

程序在未提供参数时拒绝运行，避免产生伪造的工程尺寸。

## 工作流程

1. 录入正式规范/图集/项目图纸的名称、版本、条文和页码。
2. 将经确认的输入参数写入规则文件或命令行。
3. 运行生成器，输出 DXF；必要时再导出 SVG/PDF。
4. 按 docs/validation-checklist.md 做来源、参数和几何关系复核。
5. 将复核意见、版本和输出文件一并提交，形成可追溯记录。
