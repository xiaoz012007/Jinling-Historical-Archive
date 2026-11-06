# Task003-A 入库范围与字段说明

本批登记143个来源记录：继承128个稳定SRC，补登记原资料中已有但未单列的15个明确引用。没有开展新一轮总调查。72条Task002新增证据入口、来源记录数、URL数和快照数都不是独立证据数。

## 文件分工

- sources/SOURCE_REGISTER.csv：沿用现有22字段。`claim_ids`指向HISTORICAL_CLAIM_LINKS.csv中的完整claim_id，不含F或未决问题。`sha256`为选定响应实体或旧缓存的校验值，不是来源抽象身份。
- SOURCE_DETAILS.json：保留旧获取状态、未核作者/日期等原始字段、载体差异和空值原因。`claimed_metadata_unverified`不表示字段已确认；旧P/S等级也不直接沿用成现P/S/T。
- URL_INVENTORY.json：精确URL在本地资料中的出现位置。导航链接与片段地址不补造全文URL。不同scheme/转载链接不自动算独立作品。
- WEB_SNAPSHOT_REGISTER.csv：逐实际采集事件登记，来源可对应多个URL。访问UTC、HTTP状态与最终URL只据采集记录；HEAD没有响应体，HTTP200也可能是错误页。权利状态与访问状态分开。
- LEGACY_HTML_INVENTORY.json：19份已有缓存，17份目标正文、1份模板、1份挑战页。旧采集时刻/状态/最终URL未知时留null；复制时间不充当原采集时间。全部原件内部保留。
- RIGHTS_REVIEW.csv：逐来源的保守发布资格。允许公开元数据不代表允许全文；仅PUBLIC_SNAPSHOT_WHITELIST.json列明的10个载荷文件进入公开快照目录。
- PROJECT_FILE_REGISTER.csv：原55份文件的身份、校验值。FILE-Fxx是项目文件定位，不是同期原史料。没有公开原文件。
- HISTORICAL_CLAIM_LINKS.csv：462条既有研究命题关联，含待核、单源与项目数据观察，不是462个已证史实。原686关联剔除19条F、119条阶段缺口、86条未决问题，数量不混用。源表table/row_id指Task003内部原表，不承诺这些原表已公开。
- timeline/EVENT_REGISTER.csv与EVENT_SOURCE_LINKS.csv：仅首批12条有限命题（10个来源、12个关联），状态继承；官方目录仅证明所列题名和日期，不能推出收发/阅读/执行。其余候选不自动加入事件表。
- unresolved/OPEN_QUESTIONS.csv和QUESTION_SOURCE_LINKS.csv：原34问题及证据状态保留；本次未解决这些史实争议。last_reviewed为空表示不伪造新的史料核验日期。

## 快照边界

HTML为接收的实体字节；WARC是1个末次HTTP响应记录，响应首部只保留白名单，既无凭据也无子资源/重定向响应体。`response_body_complete=true`只表示收到的响应未截断，不能宣称页面视觉/历史文献完整。`completeness=partial`对公开五页明确指缺附属资源。未制作PDF阅读副本或截图；二者不是本批的已交付内容。原始HTML中的外部资源地址不等于这些资源已获许可或已归档。

阅读与抓取分开：本轮对获准公开的五个FRUS HTML核读正文及许可范围，其他自动采集保持not_completed/未全面阅读。Task002既有阅读记录另存，不被本次抓取覆盖。源码脚本公开并非历史论证，代码不自动获得MIT许可。

## 许可与继承

维持现仓库无全库统一LICENSE状态。第三方全文许可只适用于明确对象；本批原创登记说明可公开提交，但尚未替项目所有者采纳CC BY或MIT。所有输入只读，修订另存Task003A。来源族/关系边是去重线索，最终独立性须沿具体命题的信息链判断。

空字符串/null表示没有取得或没有核定；不能解释为0、无此事或已被否定。历史事件、研究判断、网页版权、采集成功是四个不同维度。


## 公开下载链接限制

91个已登记入口中，3个第三方现代书刊扫描下载地址用`URL_WITHHELD:URL-ID`显式替代；该标记不是URL。对应5条SRC仍保留题名、页码、URL-ID、CAP-ID、哈希、限制及命题关系。完整原地址与实际访问链保存于内部总表，未从研究记录删除。暂缓提供直链不等于认定违法；其托管权利链尚未取得。公开审查表为sources/rights/PUBLIC_LINK_REVIEW.json。其余88个入口保留实际链接；Yale、国家档案局等官方直链可以用于来源定位，仍未批准复制全文。

context_label从原表name/entity_name继承，只提供主语；claim_text_status区分18个空命题关联与444个有既有文字的关联。来源关系表新增inherited_relation/inherited_status/change_reason，旧标签与本轮受限判定均可追踪。
