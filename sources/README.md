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
