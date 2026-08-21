# 规则文件

规则文件必须同时记录“判定逻辑”和“来源证据”。

最低字段：

- id：稳定的规则编号。
- status：draft、verified 或 retired。
- source.standard：规范或图集名称。
- source.edition：版本/年份。
- source.clause：条文号。
- source.page：页码或图集页号。
- source.evidence_file：项目中实际使用的原始文件名。
- parameters：输入参数、单位、数值和核验状态。
- decision：仅描述经过来源确认的逻辑和动作。

禁止在规则文件中使用“常见做法”“一般按”“经验取值”替代正式来源。找不到原始依据时，数值必须为 null，状态必须为 pending_verification。
