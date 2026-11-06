# Jinling Historical Archive｜金陵不退·南京保卫战史料库

**1937年南京保卫战历史资料整理、证据索引与研究项目**

本仓库整理与1937年南京保卫战相关的公开史料，建立可追溯、可复核、可持续修订的资料索引、事件时间线、人物与军事组织资料、交通与撤离模型，以及尚未解决的问题清单。

本项目同时服务于架空历史小说《金陵不退》的考据工作，但**历史资料库与小说创作设定严格分离**。


## 核心原则

> 宁缺毋滥，实事求是。没有证据就留白；有争议就并列；推断必须标注；小说虚构必须明确说明。

- 不编造档案编号、页码、原文、网址、日期、人数或人物言论。
- 不把搜索摘要当作已阅读的原始资料。
- 不把二手转述冒充原始档案，也不把同源转载算作独立互证。
- 不因小说剧情需要而修改历史事实。
- 资料不足时保留未知，不以“合理猜测”填补。
- 对网页来源原则上进行快照采集；是否能将完整快照公开上传，须另行核查版权、许可、网站条款及隐私风险。

## 研究范围

核心时间范围为1937年南京保卫战及南京陷落前后相关事件。研究重点包括唐生智与南京卫戍司令部、中国守军与日军、南京城市交通与平民疏散、南京安全区与国际救援、日军暴行及相关司法调查、历史照片与地图、证据冲突和未决问题。

## 来源性质、命题性质与证据状态

`source_nature`仅使用P（原始史料或同期记录）、S（学术研究）、T（一般二手资料）、unknown（来源性质未定）。unknown只表示暂不能确定来源类型，不表示相应历史命题存在冲突。

I（研究推断）、U（未决研究事项）、F（小说虚构）用于研究内容或命题性质，不能填入source_nature。命题是否有证据支持另记claim_status；P/S/T也不自动证明断言。详见[证据模型](docs/EVIDENCE_MODEL.md)。

## 目录

- docs：研究方法、证据规范、网页快照、版权及数据字典；
- timeline：逐日历史时间线与事件证据；
- persons：真实历史人物资料；
- military：军事组织、兵力及部署；
- evacuation：交通、疏散和运力研究；
- international：国际安全区与国际救援资料；
- atrocities：南京大屠杀及日军暴行相关史料；
- sources：来源索引、网页快照及来源元数据；
- models：可复算模型及测试记录；
- unresolved：未解决问题与来源冲突；
- fiction-boundary：历史事实与小说架空事件对照。

尚未完成的专题不得用占位文字伪装成已完成研究。

## 网页来源与快照

网页来源原则上保存采集快照和元数据。建议保存WARC或原始HTML、可阅读PDF副本、必要截图及JSON元数据，并计算SHA-256。**采集快照不等于取得公开再分发权**：版权不明、付费墙、登录限制或禁止再分发的内容，不公开上传全文，改为提供书目信息、合法访问链接和原创摘要。详见 [网页快照规范](docs/WEB_SNAPSHOT_POLICY.md)。

## 版权与使用

仓库公开可见不等于所有第三方资料均可自由转载。当前不对整个仓库作统一的第三方内容授权。各文件须遵守其自身许可和来源限制。详见 [版权与再利用政策](docs/COPYRIGHT_AND_REUSE.md)。

## 研究状态

本仓库处于建设阶段。研究结论可能修订；请查看文件中的证据状态、修订日期和来源定位。未决问题是研究记录的一部分。

## 参与贡献

欢迎提交档案线索、书目、来源定位、勘误和可复算数据。请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。任何贡献都需要核验，不会自动成为已确认史实。



## 项目规范

- [研究方法与质量控制](docs/RESEARCH_METHODOLOGY.md)
- [证据模型与标记规范](docs/EVIDENCE_MODEL.md)
- [网页来源与快照采集规范](docs/WEB_SNAPSHOT_POLICY.md)
- [版权与再利用政策](docs/COPYRIGHT_AND_REUSE.md)
- [数据字典](docs/DATA_DICTIONARY.md)
- [史料入库检查清单](docs/INGESTION_CHECKLIST.md)
- [公开发布状态](docs/PUBLICATION_STATUS.md)
- [贡献指南](CONTRIBUTING.md)

**当前已完成首批来源登记，历史研究仍在推进。** 原55份资料未整体导入公开仓库；第三方网页快照须逐项核查公开再分发权，不能仅因页面可访问就上传全文。

## English

Jinling Historical Archive is a source-traceable research repository about the Battle of Nanjing (1937). It documents sources, evidence, timelines, military organization, civilian evacuation research, international relief records, unresolved questions, and clearly separated counterfactual fiction notes. It does not claim that uncertain or disputed information is settled.

## 项目缘起

关于为什么发起这项工作，以及项目发起者的原话，见[项目缘起：为什么想留下《金陵不退》](docs/PROJECT_ORIGIN.md)。



## Task003-A 来源与快照入口

首批登记见[sources/SOURCE_REGISTER.csv](sources/SOURCE_REGISTER.csv)，采集清单见[sources/WEB_SNAPSHOT_REGISTER.csv](sources/WEB_SNAPSHOT_REGISTER.csv)。请先读[本批报告](docs/TASK003A_REPORT.md)和[字段及限制](docs/TASK003A_DATA_NOTES.md)。只有明确许可的FRUS网页公开响应载荷，其他来源主要提供元数据；入库不等于历史争议已解决。
