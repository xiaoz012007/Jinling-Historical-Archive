# V0.2新增表及字段

空字符串或JSON null表示该字段没有可用值，须结合limitations或unknown_reason读取；不是0，也不是事件没有发生。来源性质沿用[证据模型](EVIDENCE_MODEL.md)。

| 表 | 主键与主要外键 | 用途 |
|---|---|---|
| sources/SOURCE_REGISTER.csv | source_id；source_family | 当前来源登记，稳定编号；不等于独立史料计数 |
| sources/SOURCE_DETAILS.json | source_id | 详细身份、旧值、获取与阅读边界 |
| sources/READING_LOG_V02.json | source_id / existing_source_id | 本轮实际阅读范围；与访问记录分离 |
| sources/WEB_SNAPSHOT_REGISTER_V02.csv | capture_id；source_ids | 本轮新增/复用/失败及原响应hash |
| sources/SOURCE_REVISIONS_V02.json | source_id及原记录ID | 原值、新值、原因及原页定位 |
| timeline/南京保卫战统一时间线.csv | event_id；source_ids | 1937-11-19至12-31可定位事件；缺口另表 |
| timeline/NANJING_1937_TIMELINE.json | event_id | 同一当前时间线的机器可读版本 |
| timeline/EVENT_EVIDENCE_INDEX.csv | event_id；source_id | 命题与具体文献位置的关联 |
| persons/PERSON_REGISTER.csv | record_id；person_id；source_ids | 一人多职务记录；formal、nominal、actual和temporary分别留存 |
| military/CHINESE_ORDER_OF_BATTLE.csv | 部队稳定ID；来源ID | 中国部队层级、任务和证据边界 |
| military/JAPANESE_ORDER_OF_BATTLE.csv | 部队稳定ID；来源ID | 日方单位及资料限制，不从目录补全实力 |
| evacuation/TRANSPORT_CAPACITY_PARAMETERS.csv | 参数ID及来源/决策ID | 历史观察与F/I测试输入分列 |
| evacuation/EVACUATION_SCENARIOS.csv | 情景名及模型版本 | 条件计算，不能作为实际获救记录 |
| international/国际救援人员活动时间线.csv | 事件/断言ID；source_ids | 同期活动、书信形成与后证分开 |
| atrocities/重要事件证据表.csv | 事件/断言ID；source_ids | 司法认定、证言、转译日记及研究各自边界 |
| unresolved/OPEN_QUESTIONS.csv | original_id；source_ids | 继承34问题原文和原状态，本轮新增证据单列 |
| fiction-boundary/FICTION_EVENTS.csv | fiction_event_id；core_setting_id；dependencies | 全部为F设定；后果分析字段显式为I |
| fiction-boundary/REAL_VS_FICTION_TIMELINE.csv | fiction_event_id | 左侧历史参照与右侧小说候选保持不同字段 |

统一时间字段：date_start、date_end表示来源所支持的日期或范围；time_precision表示日、时段、文面时刻等；time_role用于区分event、document_formation、issue、transmit、receive、deliver、read、execute、later_record。字段空缺不得默认00:00。1938等后证不延长本轮1937事件范围。

citation_locator是印刷页、PDF物理页、目录编号或已声明提取段号。应同时标明位置类型，不把镜像文件名当馆藏编号。source_family用于识别同源；counterevidence记录异文、反向证据或尚未取得的反查材料，不能以无反证记录表示已经证实。

未决表保留task002_original_status、original_question；resolved表示整个原问题是否达到关闭条件，resolution_scope说明实际只关闭了哪些文本或定位缺口。部分进展可以与resolved=false并存。

各专题更细字段以其随表说明及阅读日志为准；本字典不对未知时间、人物、数字或档案编号规定默认填充值。
