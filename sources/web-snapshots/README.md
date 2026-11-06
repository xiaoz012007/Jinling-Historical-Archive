# 网页快照目录

网页来源原则上应进行快照采集，但只有在确认具有公开再分发权时，才将完整快照提交到本公开仓库。

推荐每个来源单独建目录：

SOURCE-ID/
- metadata.json
- snapshot.warc.gz（许可允许且可取得时）
- original.html（许可允许时）
- reading-copy.pdf（许可允许时）
- screenshots/
- README.md

若权利状态不明确，目录中只保存元数据、访问链接、原创摘要及rights_pending说明，不上传全文。

快照文件必须记录SHA-256、采集时间、最终URL、完整性和转换说明。
