# 数据字典

本文件定义时间线、人物、军事组织、来源和未决问题记录的推荐字段。可按研究需要扩展，但不得为了填满字段而编造内容。

## 1. 来源记录

source_id、title、creator、created_date、publication、document_type、source_nature、original_or_copy、archive_id、locator、original_url、accessed_url、accessed_at_utc、access_status、rights_status、snapshot_status、source_family、sha256、notes。

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
