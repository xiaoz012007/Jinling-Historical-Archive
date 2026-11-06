import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const base=process.env.EVAC_MODEL_DIR || path.dirname(fileURLToPath(import.meta.url));
const outputDir=process.env.EVAC_OUTPUT_DIR || path.join(base,'outputs');
await fs.mkdir(outputDir,{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(base,'model_data.json'),'utf8'));
const py=JSON.parse(await fs.readFile(path.join(base,'python_results.json'),'utf8'));
const ev=JSON.parse(await fs.readFile(path.join(base,'historical_claims.json'),'utf8'));
const wb=Workbook.create();
const names=['结果与口径','B条件输入','逐日资源与人群','A历史证据','三案与敏感性'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const s=sheets[names[0]],p=sheets[names[1]],d=sheets[names[2]],a=sheets[names[3]],q=sheets[names[4]];
const v=(sh,cell,x)=>sh.getRange(cell).values=[[x]];
const f=(sh,cell,x)=>sh.getRange(cell).formulas=[[x]];
const merge=(sh,r,text)=>{sh.mergeCells(r);v(sh,r.split(':')[0],text);};
const header=(sh,r)=>{sh.getRange(r).format={fill:'#17344D',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:36};};
for(const sh of Object.values(sheets)){
 sh.showGridLines=false;sh.getRange('A1:AJ70').format.font={name:'Arial',size:11,color:'#172D40'};
 sh.getRange('A1:AJ70').format.rowHeight=24;sh.getRange('A1:AJ70').format.columnWidth=15;
 sh.freezePanes.freezeRows(5);
}
merge(s,'A1:H1','金陵不退：交通历史与条件撤离模型');header(s,'A1:H1');
merge(s,'A2:H2','EV-B-003-01 ｜ 所有输出均为条件推演。未测得历史实际运输、后方安全抵达或获救总人数。');
s.getRange('A2:H2').format.wrapText=true;s.getRange('A2:H2').format.rowHeight=40;
v(p,'A1','B 共同资源与组织条件');header(p,'A1:H1');v(p,'A3','选择方案');v(p,'C3',2);
p.getRange('C3').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:3}};
f(p,'C4','=IF(C3=1,"保守",IF(C3=2,"中等",IF(C3=3,"乐观","非法情景")))');v(p,'A4','当前方案');v(p,'A5','输入可计算');
p.getRange('A8:H8').values=[['参数键','参数','值','单位','分类','依据 / 边界','日序说明','']];header(p,'A8:H8');
const pr={}; data.common_parameters.forEach((x,i)=>{const r=i+9;pr[x.key]=r;p.getRange(`A${r}:H${r}`).values=[[x.key,x.label,x.value,x.unit,'I 共用条件',x.basis,x.key.endsWith('day')||x.key.endsWith('end')?'0=1937-11-19；42=12-31':'','']];});
p.getRange('A37:H37').values=[['参数键','组织变量','活动值','保守','中等','乐观','单位','关联F决策']];header(p,'A37:H37');
const org={}; data.organization_parameters.forEach((x,i)=>{const r=i+38;org[x.key]=r;p.getRange(`A${r}:H${r}`).values=[[x.key,x.label,null,x.values['EV-B-C01'],x.values['EV-B-C02'],x.values['EV-B-C03'],x.unit,x.linked_fiction_ids]];f(p,`C${r}`,`=IF($C$3=1,IF(ISNUMBER(D${r}),D${r},""),IF($C$3=2,IF(ISNUMBER(E${r}),E${r},""),IF($C$3=3,IF(ISNUMBER(F${r}),F${r},""),"")))`);});
merge(p,'A45:H45','黄色为可编辑 I 测试值；F 决策仅建立因果接口，未赋予经历史验证的效应量。');
merge(p,'A46:H46','修改共同资源会同时改变三案；三案只改变六项组织参数。快照比较须运行本目录构建脚本刷新。');
p.getRange('A45:H46').format.wrapText=true;p.getRange('A45:H46').format.rowHeight=40;
p.getRange('C3').format.fill='#FFF0C2';p.getRange('C9:C33').format.fill='#FFF0C2';p.getRange('D38:F43').format.fill='#FFF0C2';
p.getRange('C9:C33').setNumberFormat('#,##0.##');
p.getRange('A1:A46').format.columnWidth=20;p.getRange('B1:B46').format.columnWidth=29;p.getRange('F8:F33').format.columnWidth=62;p.getRange('H37:H43').format.columnWidth=54;p.getRange('F9:F33').format.wrapText=true;p.getRange('A9:H33').format.rowHeight=42;
const P=k=>`'B条件输入'!$C$${pr[k]??org[k]}`;
const intKeys=['demand','rail_slots','rail_seats','cars','car_seats','walk_cap','boats','boat_seats','boat_dispatch','dock_cap','handoff_cap','gate_cap','start_day','land_end','boat_end'];
const valid=['COUNT(C9:C33)=25','COUNT(C38:C43)=6','MIN(C9:C33)>=0','MIN(C38:C43)>=0','OR(C3=1,C3=2,C3=3)',...['fuel','walk_finish','weather'].map(k=>`C${pr[k]}<=1`),...['load','civil_share','walk_org','handoff'].map(k=>`C${org[k]}<=1`),...intKeys.map(k=>`INT(C${pr[k]})=C${pr[k]}`),`OR(C${pr.return_enabled}=0,C${pr.return_enabled}=1)`,`C${pr.road_out}+C${pr.road_return}>0`,`C${pr.boat_out}>0`,`C${pr.boat_return}>0`,`C${pr.start_day}<=C${pr.land_end}`,`C${pr.start_day}<=C${pr.boat_end}`,`C${pr.land_end}<=42`,`C${pr.boat_end}<=42`];
f(p,'C5',`=IF(AND(${valid.join(',')}),1,0)`);
const guard=x=>`=IF('B条件输入'!$C$5=1,${x},"")`;
const dailyLabels=['日序','日期','陆路开放I','水路开放I','可用列车','可用汽车','汽车往返循环','小船循环','原点船初','每船装载槽','每船民用槽','可供去程航次','铁路民用能力','汽车民用能力','小船民用能力','步行集结能力','原点需求初','铁路出发','汽车出发','小船出发','步行出发','独立出发总数','条件使用航次','使用船只','回航船只','原点船末','对岸船末','船客后续完成','步行首段完成','链条完成','累计链条完成','累计步行待完成','累计岸边待转运','原点待出发','人群守恒差','船池守恒差'];
merge(d,'A1:J1','逐日资源、出发分配与转运链');header(d,'A1:AJ1');v(d,'A2','方案');f(d,'B2',"='B条件输入'!C4");merge(d,'D2:O2','分配顺序：铁路 → 汽车 → 小船 → 步行。共享出城入口；每人仅进入一路。');
d.getRange('A5:AJ5').values=[dailyLabels];header(d,'A5:AJ5');d.getRange('A5:AJ5').format.rowHeight=50;d.getRange('B1:B48').format.columnWidth=17;
for(let i=0;i<43;i++){
 const r=i+6, prev=r-1;
 v(d,`A${r}`,i);f(d,`B${r}`,`=DATE(1937,11,19)+A${r}`);
 const formulas=[
 `IF(AND(A${r}>=${P('start_day')},A${r}<=${P('land_end')}),1,0)`,
 `IF(AND(A${r}>=${P('start_day')},A${r}<=${P('boat_end')}),1,0)`,
 `INT(${P('rail_slots')}*${P('weather')})*C${r}`,
 `INT(${P('cars')}*${P('fuel')})`,
 `INT(${P('road_work')}*${P('weather')}/(${P('road_out')}+${P('road_return')}+${P('road_handling')}))*C${r}`,
 `IF(${P('return_enabled')}=1,INT(${P('boat_work')}*${P('weather')}/(${P('boat_out')}+${P('boat_return')}+${P('boat_handling')})),IF(${P('boat_work')}*${P('weather')}>=${P('boat_out')}+${P('boat_handling')},1,0))*D${r}`,
 i?`Z${prev}`:P('boats'),`INT(${P('boat_seats')}*${P('load')})`,`INT(J${r}*${P('civil_share')})`,
 `MIN(MIN(I${r},${P('boat_dispatch')})*H${r},IF(J${r}>0,INT(${P('dock_cap')}/J${r}),0))`,
 `E${r}*INT(INT(${P('rail_seats')}*${P('load')})*${P('civil_share')})`,
 `F${r}*G${r}*INT(INT(${P('car_seats')}*${P('load')})*${P('civil_share')})`,
 `L${r}*K${r}`,`INT(INT(${P('walk_cap')}*${P('weather')})*${P('walk_org')})*C${r}`,
 i?`AH${prev}`:P('demand'),`MIN(M${r},Q${r},${P('gate_cap')})`,`MIN(N${r},Q${r}-R${r},${P('gate_cap')}-R${r})`,
 `MIN(O${r},Q${r}-R${r}-S${r},${P('gate_cap')}-R${r}-S${r})`,
 `MIN(P${r},Q${r}-R${r}-S${r}-T${r},${P('gate_cap')}-R${r}-S${r}-T${r})`,
 `SUM(R${r}:U${r})`,`IF(K${r}>0,ROUNDUP(T${r}/K${r},0),0)`,`IF(H${r}>0,ROUNDUP(W${r}/H${r},0),0)`,
 `X${r}*${P('return_enabled')}`,`I${r}-X${r}+Y${r}`,`${P('boats')}-Z${r}`,
 `MIN(INT(T${r}*${P('handoff')}),${P('handoff_cap')})`,`INT(U${r}*${P('walk_finish')})`,
 `R${r}+S${r}+AB${r}+AC${r}`,i?`AE${prev}+AD${r}`:`AD${r}`,i?`AF${prev}+U${r}-AC${r}`:`U${r}-AC${r}`,i?`AG${prev}+T${r}-AB${r}`:`T${r}-AB${r}`,`Q${r}-V${r}`,`${P('demand')}-AH${r}-AE${r}-AF${r}-AG${r}`,`${P('boats')}-Z${r}-AA${r}`
 ];d.getRange(`C${r}:AJ${r}`).formulas=[formulas.map(guard)];
}
d.getRange('B6:B48').setNumberFormat('yyyy-mm-dd');d.getRange('C6:AJ48').setNumberFormat('#,##0');
s.getRange('A5:D5').values=[['指标','当前方案条件值','单位','含义']];header(s,'A5:H5');
const metrics=[['方案',"='B条件输入'!C4",'','通过唯一选择器切换'],['独立出发人数',guard("SUM('逐日资源与人群'!V6:V48)"),'人','离开原点；尚未全数完成预设链条'],['完成预设链条',guard("'逐日资源与人群'!AE48"),'人','铁路/汽车首段，或步行首段，或跨江后续接运完成'],['步行待完成',guard("'逐日资源与人群'!AF48"),'人','保留在途存量；不推定死亡或返城'],['北岸待转运',guard("'逐日资源与人群'!AG48"),'人','已跨江但后续链未完成；不重复增加总人数'],['原点待出发',guard("'逐日资源与人群'!AH48"),'人','未进入分配的剩余候选需求'],['历史实际运输',null,'人','未知，不能填0'],['历史安全抵达',null,'人','未知，模型链条终点不等于安全后方'],['历史最终获救',null,'人','未知，不能把情景结果改称获救'],['原点剩余小船',guard("'逐日资源与人群'!Z48"),'艘','默认不回航，船池只能消耗'],['对岸小船',guard("'逐日资源与人群'!AA48"),'艘','未证明可回航；1开关仅条件压力测试']];
metrics.forEach(([l,formula,u,n],i)=>{let r=i+6;v(s,`A${r}`,l);if(formula)f(s,`B${r}`,formula);else v(s,`B${r}`,'未知');v(s,`C${r}`,u);merge(s,`D${r}:H${r}`,n);});
const nominalBoatCycles=`IF(${P('return_enabled')}=1,INT(${P('boat_work')}/(${P('boat_out')}+${P('boat_return')}+${P('boat_handling')})),IF(${P('boat_work')}>=${P('boat_out')}+${P('boat_handling')},1,0))`;
const waterDays=`(${P('boat_end')}-${P('start_day')}+1)`;
const nominalBoatTrips=`IF(${P('return_enabled')}=0,MIN(${P('boats')},${P('boat_dispatch')}*${waterDays})*${nominalBoatCycles},MIN(${P('boats')},${P('boat_dispatch')})*${nominalBoatCycles}*${waterDays})`;
v(s,'A17','名义首段槽位');f(s,'B17',guard(`(${P('land_end')}-${P('start_day')}+1)*(${P('rail_slots')}*${P('rail_seats')}+${P('cars')}*${P('car_seats')}*INT(${P('road_work')}/(${P('road_out')}+${P('road_return')}+${P('road_handling')}))+${P('walk_cap')})+${nominalBoatTrips}*${P('boat_seats')}`));v(s,'C17','槽位');merge(s,'D17:H17','无天气、燃料、军民及入口折减的资源上界；不是人数实绩。');
merge(s,'A19:H19','A 历史边界：长江号是铁路渡轮；两艘客渡未具名；外国舰船、客船、军船均不自动进入民用船池。');
merge(s,'A20:H20','名义能力只描述无折减资源槽位；可用能力经天气、油料、循环、码头约束；出发与链条完成须再受需求守恒约束。');
merge(s,'A21:H21','本模型不是对实际历史撤出量的估算，也不把三案差值认定为唐生智措施的真实因果效应。');
s.getRange('A19:H21').format.wrapText=true;s.getRange('A19:H21').format.rowHeight=44;s.getRange('A1:A21').format.columnWidth=28;s.getRange('B6:B16').setNumberFormat('#,##0');
a.getRange('A1:F1').values=[['A 历史断言','来源','定位','可采用范围','未解决边界','状态']];header(a,'A1:F1');
ev.forEach((x,i)=>a.getRange(`A${i+3}:F${i+3}`).values=[[x.claim,x.source_ids.join(';'),x.locator,x.allowed_narration,x.limitations,x.claim_status]]);
a.getRange(`A3:F${ev.length+2}`).format.wrapText=true;a.getRange(`A3:F${ev.length+2}`).format.rowHeight=92;for(const col of ['A','D','E'])a.getRange(`${col}1:${col}20`).format.columnWidth=48;a.getRange('B1:C20').format.columnWidth=27;
merge(q,'A1:H1','三案及敏感性：同一计算区逐次重算的快照');header(q,'A1:H1');
merge(q,'A2:H2','更改任何参数后，旧快照不自动变成当前结果；活动情景实时见首页。重新运行构建脚本刷新全部快照。');q.getRange('A2:H2').format.wrapText=true;q.getRange('A2:H2').format.rowHeight=42;
v(q,'A3','快照参数一致性');
const snapshotChecks=[...data.common_parameters.map(x=>`${P(x.key)}=${x.value}`),...data.organization_parameters.flatMap(x=>['D','E','F'].map((c,j)=>`'B条件输入'!${c}${org[x.key]}=${Object.values(x.values)[j]}`))];
f(q,'C3',`=IF(AND(${snapshotChecks.join(',')}),"参数与快照一致","参数已改变：请刷新")`);
q.getRange('A5:H5').values=[['方案','名义首段槽位','独立出发','条件链条完成','步行待完成','岸边待转运','原点待出发','实得救人数']];header(q,'A5:H5');
q.getRange('B6:G8').setNumberFormat('#,##0');q.getRange('C12:F34').setNumberFormat('#,##0');
const pythonKeys=['land_open','water_open','rail_services','car_ready','car_cycles','boat_cycles','boat_origin_start','boat_loaded_seats','boat_civil_seats','boat_voyage_offer','rail_offer','car_offer','boat_offer','walk_offer','demand_start','rail_departures','car_departures','boat_departures','walk_departures','departures','boat_voyages','boats_used','boats_returned','boat_origin_end','boat_far_shore_end','boat_onward','walk_completed','chain_completed','completed_cumulative','pending_walk','pending_shore','demand_end','people_balance','boat_balance'];
const qa={model_id:data.model_id,engine:'artifact-tool',cases:[],boundary_tests:[],native_excel_tested:false};
for(let c=1;c<=3;c++){
 v(p,'C3',c);wb.recalculate();const actual=d.getRange('C6:AJ48').values;const expected=py[c-1];let n=0;
 for(let i=0;i<43;i++)for(let j=0;j<34;j++){if(actual[i][j]!==expected.daily[i][pythonKeys[j]])throw Error(`mismatch case ${c} day ${i} ${pythonKeys[j]} actual=${actual[i][j]} expected=${expected.daily[i][pythonKeys[j]]}`);n++;}
 const t=expected.totals;const totals=s.getRange('B7:B11').values.map(r=>r[0]);if(s.getRange('B17').values[0][0]!==t.nominal_first_leg_slots)throw Error('nominal mismatch');
 q.getRange(`A${c+5}:H${c+5}`).values=[[['保守','中等','乐观'][c-1],t.nominal_first_leg_slots,...totals,'未知']];qa.cases.push({scenario_id:expected.totals.scenario_id,compared_numeric_cells:n,passed:true,results:totals});
}
// Exercise inputs in the same live build and restore all edits before final export.
for(const [name,key,val,expect] of [['zero demand','demand',0,0],['zero weather','weather',0,0],['blank demand','demand',null,''],['negative boats','boats',-1,'']]){
 const cell=`C${pr[key]}`,old=p.getRange(cell).values[0][0];v(p,cell,val);wb.recalculate();const result=s.getRange('B7').values[0][0];if(result!==expect)throw Error(name+': '+result);qa.boundary_tests.push({name,passed:true});v(p,cell,old);
}
v(p,'C3',4);wb.recalculate();if(s.getRange('B7').values[0][0]!=='')throw Error('invalid selector');qa.boundary_tests.push({name:'invalid selector',passed:true});v(p,'C3',2);
const blankCell=`D${org.load}`,oldUnselected=p.getRange(blankCell).values[0][0];v(p,blankCell,null);wb.recalculate();if(s.getRange('B7').values[0][0]!==36598)throw Error('unselected blank blocks valid case');v(p,'C3',1);wb.recalculate();if(s.getRange('B7').values[0][0]!=='')throw Error('selected blank not blocked');v(p,blankCell,oldUnselected);v(p,'C3',2);qa.boundary_tests.push({name:'blank inactive allowed; blank selected blocked',passed:true});
// Independently calculated sensitivity snapshots are verified using this same Excel build.
const sensitivities=JSON.parse(await fs.readFile(path.join(base,'sensitivity_results.json'),'utf8'));
q.getRange('A11:H11').values=[['中案改变一项','输入值','独立出发','条件链条完成','原点待出发','原点小船','参数类别','含义']];header(q,'A11:H11');
for(let j=0;j<sensitivities.length;j++){
 const x=sensitivities[j],key=x.changed_parameter;const cell=pr[key]?`C${pr[key]}`:`E${org[key]}`;const old=p.getRange(cell).values[0][0];v(p,cell,x.changed_value);wb.recalculate();const departure=s.getRange('B7').values[0][0],chain=s.getRange('B8').values[0][0];if(departure!==x.departures||chain!==x.conditional_chain_completed)throw Error('sensitivity mismatch '+key+' '+x.changed_value);q.getRange(`A${12+j}:H${12+j}`).values=[[key,x.changed_value,departure,chain,x.origin_waiting,x.boats_origin,org[key]?'组织':'资源/外部条件','条件压力测试']];v(p,cell,old);
}
qa.sensitivity_cases=sensitivities.length;
v(p,'C3',2);wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:4000});qa.formula_error_scan=errors.ndjson;
const inspection=await wb.inspect({kind:'table',range:'结果与口径!A5:H16',include:'values,formulas',tableMaxRows:12,tableMaxCols:8,maxChars:5000});
await fs.writeFile(path.join(base,'workbook_inspect.ndjson'),inspection.ndjson);
await fs.writeFile(path.join(base,'workbook_validation.json'),JSON.stringify(qa,null,2));
for(const [name,range,suffix] of [[names[0],'A1:H21','summary'],[names[1],'A1:H16','inputs'],[names[1],'A37:H46','organization'],[names[2],'A5:L15','resources'],[names[2],'M5:V15','departures'],[names[2],'W5:AJ15','conservation'],[names[3],'A1:F7','evidence'],[names[4],'A1:H20','comparison']]){
 const png=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(path.join(outputDir,`${suffix}.png`),new Uint8Array(await png.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(outputDir,'evacuation_model.xlsx'));
await fs.copyFile(path.join(outputDir,'evacuation_model.xlsx'),path.join(base,'evacuation_model.xlsx'));
console.log(JSON.stringify(qa));
