# 来源索引与网页快照

本目录保存来源元数据、引用定位、来源关系及经过版权审查的网页快照。

- web-snapshots：网页快照及元数据；
- templates：来源记录模板；
- 来源总索引可使用CSV、JSON或XLSX维护，公开发布时尽量提供机器可读的CSV/JSON版本。

基本规则：
1. 每个来源使用稳定唯一ID。
2. 同一来源的不同版本应记录版本关系。
3. 同源转载不得重复计为独立来源。
4. 网页快照必须关联来源ID和SHA-256。
5. 无法公开全文时只发布元数据、合法链接和原创摘要。
6. 不能确认的字段留空并说明，不得编造。


## 本批附表

SOURCE_REGISTER.csv为完整来源登记入口；SOURCE_DETAILS.json保留旧获取状态和未核字段。WEB_SNAPSHOT_REGISTER.csv索引实际采集，RIGHTS_REVIEW.csv控制全文发布。HISTORICAL_CLAIM_LINKS.csv是既有研究命题关联，含未决状态，不可直接当已发生事件全集。详细定义见 ../docs/TASK003A_DATA_NOTES.md。

## Task004字段读取说明

Task003 V0.2基线共有152条来源，其中unknown为69条（45.39%），并非多数。source_nature只表达来源性质，命题状态另看claim_status；同一份原文的转载、目录、翻译和扫描不会自动形成独立互证。read_scope_v02记录V0.2的阅读范围，空白不能解释为从未阅读，也不能解释为已读全文；应回来源详情与逐条阅读日志核对。Task004新增阅读另存日志，保留旧值，不为消除空白强行归类。


## Task004 当前候选

本轮新增来源登记、阅读和采集日志分别见 `sources/SOURCE_REGISTER.csv`、`sources/READING_LOG_TASK004.json`、`sources/CAPTURES_TASK004.json`（均为仓库根相对路径）。新增原始全文不公开；旧报告保留为历史版本。当前事实和限制以逐条状态及 Task004 修订日志为准。

## 2026-11-11 P 级史料线索 R1

[分类登记](P_LEVEL_SOURCE_LEADS_R1.csv)记录18条核查结果，[复核说明](../docs/P_LEVEL_SOURCE_LEADS_R1_REVIEW.md)列出可引用范围。SRC-0176 已录入同期函件副本影像的来源元数据。
