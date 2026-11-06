# 数据字典

本文件定义时间线、人物、军事组织、来源和未决问题记录的推荐字段。可按研究需要扩展，但不得为了填满字段而编造内容。

## 1. 来源记录

source_id、title、creator、created_date、publication、document_type、source_nature、original_or_copy、archive_id、locator、original_url、accessed_url、accessed_at_utc、access_status、rights_status、snapshot_status、source_family、sha256、notes。

当前CSV实际使用`creator_or_publisher`保存作者或发布机构；既有字段名不因本次来源性质迁移而更名。

| 字段 | 取值或约束 |
|---|---|
| source_nature | 仅允许`P`（原始或同期）、`S`（学术研究）、`T`（一般二手）、`unknown`（来源性质未定）。不填I/U/F，不用于判断命题真伪。 |
| source_nature_original | PR #1收口迁移的原值档案：69项U→unknown的来源保留`U`；本次未改变的来源为空。不可拿此字段作为当前类型。 |
| source_nature_from_register | 关联表中的当前类型，应与对应SRC来源一致。既有61条FILE-F06/F07链接是项目文件定位，保留其文件角色，类型为`unknown`；不把FILE登记为新的原始史料。 |
| source_nature_from_register_original | 本次改动的145条关联字段保留原`U`（84条SRC关联、61条FILE关联）；其余为空。 |

`SOURCE_DETAILS.json`保留相同的143个稳定SOURCE-ID和当前/原值字段。`claimed_metadata_unverified`、`prior_access`及其他原值、旧等级、阅读记录仍按原状保存，不能把旧S/A/B等等级机械映射为P/S/T。

[来源性质迁移表](../sources/SOURCE_NATURE_MIGRATION.csv)逐项记录69个来源的原值、新值、修改原因、输入提交和迁移时间。当前字段为unknown不等于其命题有冲突，也不等于该命题已被否定。

## 2. 历史事件

event_id、date_start、date_end、time_precision、location、actors、event_description、claim_status、source_ids、limitations、counterevidence、last_reviewed。

## 3. 人物

person_id、name、name_variants、birth_date、death_date、role_at_time、unit_or_organization、activity_period、source_ids、uncertainties。

## 4. 军事单位

unit_id、unit_name、parent_unit、commander、effective_date、nominal_strength、actual_strength、combat_strength、noncombat_strength、casualties、location_or_sector、source_ids、counting_basis、uncertainties。

不同日期和统计口径的数据必须分开记录。

## 5. 未决问题

question_id、question、priority、known_evidence、conflicting_evidence、searches_attempted、next_steps、fiction_impact、status、last_reviewed。

## 6. 架空事件

fiction_id、real_history_baseline、fictional_change、divergence_date、causal_chain、affected_events、novel_chapters、explicitly_fictional。explicitly_fictional必须为true。

## 7. 空值

未知字段应使用空值或明确的unknown，并在备注说明原因。不得用0、估计值或默认日期代替未知。

## 8. 本次迁移的可运行检查

在仓库根目录运行：

```bash
python -B scripts/validate_source_nature.py
python -B scripts/test_source_nature.py
```

验证器读取迁移前提交`975725c`形成的冻结基线[fixture](../scripts/fixtures/source_nature_closeout_baseline.json)，校验143个来源无遗漏和重复、69项原值完整、当前字段枚举与引用一致，并逐表比较命题状态及非迁移字段。SOURCE_DETAILS的原值存档和研究标记另做完整投影校验。验证器只读，不重建基线，也不写回文件。

测试在临时副本中故意引入U残留、来源遗漏/重复、关联类型错配、原值丢失、命题状态改变和项目文件升格，确认验证器能拒绝。上述检查只验收本次字段迁移，不代表史实、独立互证或版权已通过。后续新增来源、修改命题状态必须独立审查并说明基线变更，不能为通过检查静默重建fixture。
