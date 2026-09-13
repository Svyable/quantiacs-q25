(() => {
  'use strict';
  const L = window.Q25Lab = {
    root: document.querySelector('[data-q25-lab]'), packet: null, rows: [], decisions: [], filtered: [], selectedKey: null,
    sortKey: 'dev_sharpe_12', visibleRows: 40, stabilityMetric: 'dev_sharpe_12', xMetric: '__causalMargin', yMetric: 'dev_sharpe_12', familyGroups: new Map()
  };
  if (!L.root) return;
  L.$ = (s, scope = L.root) => scope.querySelector(s);
  L.$$ = (s, scope = L.root) => Array.from(scope.querySelectorAll(s));
  L.isNum = (v) => v !== null && v !== '' && Number.isFinite(Number(v));
  L.n = (v) => L.isNum(v) ? Number(v) : null;
  L.esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  L.fmt = (v, d = 3) => L.isNum(v) ? Number(v).toFixed(d) : '—';
  L.pct = (v, d = 1) => L.isNum(v) ? `${(Number(v) * 100).toFixed(d)}%` : '—';
  L.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  L.human = (s) => String(s || '').replace(/^__/, '').replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
  L.metricFmt = (key, value) => /(?:cagr|drawdown|turnover|hit_rate|return|volatility)/i.test(key) ? L.pct(value, Math.abs(Number(value)) < .01 ? 2 : 1) : L.fmt(value);
  L.median = (arr) => { const a = arr.filter(Number.isFinite).sort((x,y)=>x-y); if (!a.length) return null; const m=Math.floor(a.length/2); return a.length%2?a[m]:(a[m-1]+a[m])/2; };
  L.svgEl = (name, attrs={}) => { const el=document.createElementNS('http://www.w3.org/2000/svg',name); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); return el; };

  L.pathContext = (path, obj) => {
    let campaign=obj.campaign||obj.campaign_id||obj.experiment||'';
    let lane=obj.lane||(path.length?String(path[0]):'');
    if(!campaign&&path[0]==='additional_campaigns'&&path[1]) campaign=String(path[1]);
    if(!campaign){const hit=path.find((p)=>typeof p==='string'&&/^(?:frontier|campaign|ebenezar|historical|topology)/i.test(p));if(hit)campaign=String(hit);}
    return {campaign:campaign||lane||'unscoped',lane:lane||'unscoped'};
  };
  L.looksLikeRow = (obj) => {
    if(!obj||Array.isArray(obj)||typeof obj!=='object'||typeof obj.id!=='string')return false;
    return Object.keys(obj).some((k)=>/(sharpe|score|cagr|sortino|calmar|drawdown|turnover|hit_rate|return|volatility)/i.test(k)&&(L.isNum(obj[k])||obj[k]===null))||typeof obj.status==='string';
  };
  L.extract = (data) => {
    const out=[],fams=[],seen=new Set(),seenFam=new Set();
    function walk(node,path=[]){
      if(Array.isArray(node)){node.forEach((x,i)=>walk(x,path.concat(i)));return;}
      if(!node||typeof node!=='object')return;
      if(L.looksLikeRow(node)){
        const ctx=L.pathContext(path,node),r={...node,__campaign:ctx.campaign,__lane:ctx.lane,__path:path.join('.')};
        r.__key=[r.__campaign,r.__lane,r.id,r.mode||'',r.__path].join('|');
        if(!seen.has(r.__key)){seen.add(r.__key);out.push(r);}
      }else if(typeof node.family==='string'&&typeof node.decision==='string'&&('best_score'in node||'decision_code'in node)){
        const ctx=L.pathContext(path,node),key=[ctx.campaign,node.family,node.decision_code||node.decision].join('|');
        if(!seenFam.has(key)){seenFam.add(key);fams.push({...node,__campaign:ctx.campaign,__lane:ctx.lane});}
      }
      Object.entries(node).forEach(([k,v])=>walk(v,path.concat(k)));
    }
    walk(data);return {rows:out,decisions:fams};
  };
  L.decisionFor = (campaign,family) => {
    if(!family)return null;const exact=L.decisions.find((d)=>d.__campaign===campaign&&d.family===family);if(exact)return exact;
    const matches=L.decisions.filter((d)=>d.family===family);return matches.length===1?matches[0]:null;
  };
  L.groupKey = (r) => `${r.__campaign}|${r.family||'—'}`;
  L.rebuildGroups = (source) => {
    const map=new Map();source.forEach((r)=>{const key=L.groupKey(r);if(!map.has(key))map.set(key,{key,campaign:r.__campaign,family:r.family||'—',rows:[]});map.get(key).rows.push(r);});
    map.forEach((g)=>{
      g.bases=g.rows.filter((r)=>r.mode==='base');
      g.destructive=g.rows.filter((r)=>['ablation','falsifier','control'].includes(String(r.mode||'').toLowerCase())&&r.family&&r.family!=='control');
      g.bestBase=g.bases.filter((r)=>L.isNum(r.dev_sharpe_12)).sort((a,b)=>Number(b.dev_sharpe_12)-Number(a.dev_sharpe_12))[0]||null;
      g.strongestControl=g.destructive.filter((r)=>L.isNum(r.dev_sharpe_12)).sort((a,b)=>Number(b.dev_sharpe_12)-Number(a.dev_sharpe_12))[0]||null;
      g.margin=g.bestBase&&g.strongestControl?Number(g.bestBase.dev_sharpe_12)-Number(g.strongestControl.dev_sharpe_12):null;
      g.decision=L.decisionFor(g.campaign,g.family);
    });return map;
  };
  L.enrichAll = () => {
    L.familyGroups=L.rebuildGroups(L.rows);
    L.rows=L.rows.map((r)=>{const g=L.familyGroups.get(L.groupKey(r)),decision=L.decisionFor(r.__campaign,r.family),research=L.n(r.research_sharpe_12),dev=L.n(r.dev_sharpe_12),sr0=L.n(r.dev_sharpe_0);return {...r,__decision:decision,__decisionCode:decision?(decision.decision_code||decision.decision||''):'',__matchedControl:g?.strongestControl||null,__causalMargin:r.mode==='base'&&g?.strongestControl&&dev!==null?dev-Number(g.strongestControl.dev_sharpe_12):null,__devDecay:dev!==null&&research!==null?dev-research:null,__costDrag:sr0!==null&&dev!==null?sr0-dev:null};});
    L.familyGroups=L.rebuildGroups(L.rows);
  };
  L.filteredGroups = () => {
    const map=new Map();L.filtered.filter((r)=>r.mode==='base').forEach((r)=>{const key=L.groupKey(r);if(!map.has(key))map.set(key,{key,campaign:r.__campaign,family:r.family||'—',bases:[]});map.get(key).bases.push(r);});
    map.forEach((g)=>{g.bestBase=g.bases.filter((r)=>L.isNum(r.dev_sharpe_12)).sort((a,b)=>Number(b.dev_sharpe_12)-Number(a.dev_sharpe_12))[0]||null;g.strongestControl=g.bestBase?.__matchedControl||null;g.margin=g.bestBase&&L.isNum(g.bestBase.__causalMargin)?Number(g.bestBase.__causalMargin):null;g.decision=g.bestBase?.__decision||L.decisionFor(g.campaign,g.family);});return [...map.values()];
  };
  L.decisionClass=(code)=>/CONTINUE/i.test(code)?'continue':/FREEZE|FALSIFIED|KILL|FAIL/i.test(code)?'freeze':'';
  L.paramLabel=(id,family)=>{let s=String(id||''),f=String(family||'');if(f&&s.toLowerCase().startsWith(f.toLowerCase()))s=s.slice(f.length).replace(/^[_-]+/,'');return s||id||'cell';};
})();
