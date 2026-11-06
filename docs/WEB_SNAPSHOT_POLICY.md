# 网页来源与快照采集规范

## 1. 基本要求

凡通过网页取得的研究来源，原则上都应建立网页快照采集记录。网页快照用于保存采集时可见的页面状态，避免链接失效或内容更新后无法追溯。

**采集快照不等于取得公开再分发权。** 完整快照是否可以提交到本公开仓库，必须经过版权、许可、网站条款、隐私和访问限制审查。

## 2. 建议保存的快照形式

在技术条件允许且合法的情况下，优先保存：
- WARC或WARC.GZ：保存网页响应及相关资源；
- 原始HTML：保存实际取得的页面响应，并记录是否经过脚本渲染或清理；
- PDF阅读副本：便于人工阅读和引用定位；
- 页面截图：作为视觉辅助，不能替代文本来源；
- 元数据JSON：记录URL、时间、标题、发布者、日期、哈希、许可和文件关系。

不要把经过编辑的阅读副本标为原始快照。

## 3. 每份网页快照的目录

建议结构：

sources/web-snapshots/SOURCE-ID/
- metadata.json
- snapshot.warc.gz（如可取得且允许公开）
- original.html（如可取得且允许公开）
- reading-copy.pdf（如可制作且允许公开）
- screenshots/
- README.md

若完整内容不能公开，目录中只保存metadata.json、原创研究摘要、合法访问链接及限制说明；不得上传被禁止再分发的完整页面。

## 4. 元数据字段

至少记录source_id、title、creator_or_publisher、original_url、final_url、retrieved_at_utc、published_at、updated_at、language、content_type、http_status、snapshot_format、snapshot_filename、sha256、completeness、capture_method、access_conditions、license_or_rights_basis、redistribution_status、citation_locator和notes。

未知字段留空并说明，不得猜测。

## 5. 采集流程

1. 记录原始URL。
2. 访问网页并记录最终URL和访问时间。
3. 确认页面标题、作者/机构、发布日期及更新日期。
4. 判断页面是否完整、是否需要登录、是否付费或受访问控制。
5. 检查版权声明、开放许可和网站使用条款。
6. 在许可和技术条件允许时保存快照。
7. 计算快照文件SHA-256。
8. 对照网页检查快照是否缺页、缺图或动态内容未捕获。
9. 更新来源索引并建立快照关联。
10. 在公开前再次审核再分发权限和隐私风险。

## 6. 公开发布限制

- 公有领域或明确允许再分发的页面，可按其许可保存和发布。
- 开放许可页面必须保留署名、许可链接及要求的说明。
- 版权不明、明确禁止再分发或仅允许个人访问的页面，不公开上传完整快照。
- 付费墙、登录限制和技术访问控制不得绕过。
- 不上传Cookie、Authorization头、会话令牌、个人账户信息或不必要的个人数据。
- 不得以网页快照名义规避第三方版权。

## 7. 安全与完整性

快照是数据，不是可执行程序。不要在浏览器中直接运行未知页面脚本。WARC、HTML、PDF及截图均应记录哈希。去除脚本、重排版或OCR后的版本必须标为派生阅读副本，不能冒充原始响应。

## 8. 网页失效

网页无法访问时，记录失败日期、状态码或错误信息；寻找合法的官方镜像、档案馆副本或互联网档案链接；不得声称已保存快照，也不得用搜索摘要伪装成页面全文。

网页快照状态建议：captured_public、captured_private_only、metadata_only、capture_failed、rights_pending。
