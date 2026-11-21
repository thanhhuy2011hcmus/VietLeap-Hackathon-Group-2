# -*- coding: utf-8 -*-
"""
build_dashboard_ban_nop.py — dựng bản nộp gọn (Data Decision) từ dashboard v3.

Đọc reports/dashboard_stress_test_BDS_v3_vnese.html, sắp lại thành 6 phần theo
.claude/prompts/PROMPT_dashboard_ban_nop_gon.md, ghi reports/dashboard_stress_test_BDS_ban_nop_vnese.html.
Dữ liệu, mô hình và chữ của v3 giữ nguyên; script dừng nếu một đoạn cần sửa không còn đúng 1 lần.
Sau đó dịch cả v3 và bản nộp sang tiếng Anh (src/translate_dashboard.py) -> *_eng.html.
Chạy:  python src/build_dashboard_ban_nop.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, "reports")
src = os.path.join(REP, "dashboard_stress_test_BDS_v3_vnese.html")
out = os.path.join(REP, "dashboard_stress_test_BDS_ban_nop_vnese.html")
s = open(src, encoding="utf-8").read().replace("\r\n", "\n")


def one(text, a, b):
    assert text.count(a) == 1, f"không tìm thấy đúng 1 lần: {a[:70]}"
    return text.replace(a, b)


head, rest = s.split("<body>", 1)
body, script = rest.split("<script>", 1)
script = "<script>" + script

# ---------------- CSS bổ sung ----------------
CSS = """
nav a.focus{color:var(--ink);font-weight:700;border-bottom:2px solid var(--red);padding-bottom:2px}
.tabs{margin:28px 0 0}
.tabpane{display:none;padding-top:10px}.tabpane.on{display:block}
.tabh{font-family:"Source Serif 4",Georgia,serif;font-weight:800;font-size:26px;letter-spacing:-.3px;line-height:1.15;margin:8px 0 0}
.dbl-cap{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
section.focus{background:var(--card);border-top:4px solid var(--red)}
.focus-tag{display:inline-block;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:2px;color:#fff;background:var(--red);padding:3px 9px;border-radius:2px;margin-bottom:12px}
#dtab tr.go{cursor:pointer}#dtab tr.go:hover td{background:#eaede6}
#dtab td{vertical-align:top}
.rec.flash{box-shadow:0 0 0 3px var(--red)}
.gcards.four{grid-template-columns:repeat(4,1fr)}
@media(max-width:900px){.gcards.four{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.gcards.four{grid-template-columns:1fr}}
.gcard details{margin-top:6px}.gcard summary{cursor:pointer;color:var(--mute);font-size:12.5px}
details.more{margin-top:26px}details.more>summary{cursor:pointer;font-weight:600;color:var(--ink2);font-size:15px}
details.more[open]>summary{margin-bottom:12px}
"""
head = one(head, "</style>", CSS + "</style>")

# ---------------- tách các section cũ ----------------
sec = {}
for m in re.finditer(r'<section id="(p\d+)"><div class="wrap">\n(.*?)</div></section>', body, re.S):
    sec[m.group(1)] = m.group(2).rstrip("\n")
assert sorted(sec) == sorted(f"p{i}" for i in range(1, 11)), sec.keys()
hero = re.search(r'<header class="hero">.*?</header>', body, re.S).group(0)
footer = re.search(r"<footer>.*?</footer>", body, re.S).group(0)

KH = re.compile(r'<div class="kicker">(.*?)</div>\n<h2>(.*?)</h2>\n')


def as_tab(code):
    """Bỏ kicker cũ, H2 cũ thành tiêu đề tab (giữ nguyên chữ)."""
    return KH.sub(lambda m: f'<h3 class="tabh">{m.group(2)}</h3>\n', sec[code], count=1)


def kicker(code, new):
    return one(sec[code], KH.search(sec[code]).group(1), new)


# ---------------- tham chiếu số phần: đổi theo cấu trúc mới ----------------
hero = one(hero, "Nhóm theo bộ tiêu chí ở phần 7, kịch bản đang chọn ở phần 6.",
           "Nhóm theo bộ tiêu chí ở phần 3, kịch bản đang chọn ở phần 2.")
hero = one(hero,
           '<span><b>1–5</b> Chẩn đoán từ BCTC</span>→<span><b>6</b> Stress test 12 tháng</span>→<span><b>7</b> Phân 4 nhóm</span>→<span><b>8</b> Ngân hàng xử lý theo nhóm</span>→<span><b>9</b> Doanh nghiệp tự cứu</span>→<span><b>10</b> Hàm ý vĩ mô</span>',
           '<span><b>1</b> Chẩn đoán từ BCTC</span>→<span><b>2</b> Stress test 12 tháng</span>→<span><b>3</b> Phân 4 nhóm</span>→<span><b>4</b> Doanh nghiệp tự cứu</span>→<span><b>5</b> Ngân hàng xử lý theo nhóm</span>→<span><b>6</b> Hàm ý vĩ mô</span>')
sec["p1"] = one(sec["p1"], "Màu = nhóm phân loại ở phần 7", "Màu = nhóm phân loại ở phần 3")
sec["p5"] = one(sec["p5"], "cú sốc doanh số mặc định ở phần 6.", "cú sốc doanh số mặc định ở phần 2.")
sec["p7"] = one(sec["p7"], "— phần 5.", "— phần 1.")
sec["p7"] = one(sec["p7"], "khi đổi kịch bản ở phần 6.", "khi đổi kịch bản ở phần 2.")
script = one(script, "theo bộ tiêu chí ở phần 7.", "theo bộ tiêu chí ở phần 3.")

# ---------------- PHẦN 1 · CHẨN ĐOÁN ----------------
h2_p1 = KH.search(sec["p1"]).group(2)
tab1 = KH.sub("", sec["p1"], count=1)
TABS = [("Khoảng hụt", tab1), ("Xu hướng 4 quý", as_tab("p2")), ("Tiền bị khóa", as_tab("p3")),
        ("Đòn bẩy", as_tab("p4")), ("Bài học 2022–23", as_tab("p5"))]
s1 = f'''<section id="s1"><div class="wrap">
<div class="kicker">Phần 1 · Chẩn đoán từ báo cáo tài chính</div>
<h2>{h2_p1}</h2>
<div class="kpis" id="k1" style="margin-top:28px"></div>
<div class="card"><div class="dbl-cap"><div class="cap">Hệ số phủ tiền mặt 2025Q4 → 2026Q3, cùng đòn bẩy và tỷ trọng tồn kho quý gần nhất</div>
<div class="lg" style="font-size:13px;display:flex;gap:16px;flex-wrap:wrap"><span><svg width="14" height="14" style="vertical-align:-2px;margin-right:5px"><circle cx="7" cy="7" r="5" fill="none" stroke="#7c878c" stroke-width="2"/></svg>2025Q4</span><span><svg width="14" height="14" style="vertical-align:-2px;margin-right:5px"><circle cx="7" cy="7" r="6" fill="#a8322d"/></svg>2026Q3 (màu theo thang rủi ro)</span></div></div>
<div id="c1d"></div>
<div class="note">Thanh đứng tại 1,0× là mức đủ trả toàn bộ nợ ngắn hạn. Màu chấm đặc: xanh ≥ 1,2× · vàng 1–1,2× · cam 0,7–1× · đỏ &lt; 0,7×. Rê chuột vào chấm để xem số tuyệt đối. Chi tiết từng góc nhìn ở các tab bên dưới.</div></div>
<div class="presets tabs" id="tabs1">{"".join(f'<button type="button" data-tab="{i}"{" class=\"on\"" if i == 0 else ""}>{n}</button>' for i, (n, _) in enumerate(TABS))}</div>
{"".join(f'<div class="tabpane{" on" if i == 0 else ""}" id="tab1_{i}">' + chr(10) + html + chr(10) + '</div>' + chr(10) for i, (_, html) in enumerate(TABS))}</div></section>'''

# ---------------- PHẦN 2, 3 ----------------
s2 = '<section id="s2"><div class="wrap">\n' + kicker("p6", "Phần 2 · Mô hình hóa") + "\n</div></section>"
s3 = '<section id="s3"><div class="wrap">\n' + kicker("p7", "Phần 3 · Phân loại") + "\n</div></section>"

# ---------------- PHẦN 4 · TRỌNG TÂM ----------------
p9 = kicker("p9", "Phần 4 · Quyết định cho doanh nghiệp")
p9 = one(p9, '<div class="recs" id="recs"></div>',
         '<div class="cap">Bảng quyết định — bấm vào một dòng để xem thẻ chi tiết</div><div id="dtab" style="margin-bottom:30px"></div>\n<div class="recs" id="recs"></div>')
s4 = '<section id="s4" class="focus"><div class="wrap">\n<div class="focus-tag">TRỌNG TÂM · DATA DECISION</div>\n' + p9 + "\n</div></section>"

# ---------------- PHẦN 5 · NGÂN HÀNG (rút gọn) ----------------
p8 = kicker("p8", "Phần 5 · Quyết định cho ngân hàng")
m = re.search(r'<div class="grid2">\n<div>(<div class="cap">Bốn chính sách.*?</div><div id="t8"></div><div class="note">.*?</div>)</div>\n<div>(<div class="cap">Ai gánh khoảng hụt\?.*?</div><div id="c8"></div><div class="lg".*?</div>)</div>\n</div>', p8, re.S)
assert m, "không tách được khối phần 8"
p8 = p8.replace(m.group(0), m.group(1) + '\n<details class="more"><summary>Xem chi tiết: ai gánh khoảng hụt</summary><div style="max-width:640px">' + m.group(2) + "</div></details>")
p8 = one(p8, 'class="gcards" id="g8"', 'class="gcards four" id="g8"')
s5 = '<section id="s5"><div class="wrap">\n' + p8 + "\n</div></section>"

# ---------------- PHẦN 6 ----------------
s6 = '<section id="s6"><div class="wrap">\n' + kicker("p10", "Phần 6 · Hàm ý cho nền kinh tế") + "\n</div></section>"

nav = '''<nav><div class="in"><b>STRESS·BĐS</b>
<a href="#s1">1 · Chẩn đoán</a><a href="#s2">2 · Mô phỏng</a><a href="#s3">3 · Phân loại</a><a href="#s4" class="focus">4 · Quyết định DN</a><a href="#s5">5 · Ngân hàng</a><a href="#s6">6 · Kinh tế</a></div></nav>'''

body = "\n" + "\n\n".join([nav, hero, s1, s2, s3, s4, s5, s6, footer]) + '\n<div id="tip"></div>\n\n'

# ---------------- JS ----------------
# thẻ khuyến nghị có id để bảng quyết định cuộn tới
script = one(script, "const d=document.createElement('div');d.className='rec';",
             "const d=document.createElement('div');d.className='rec';d.id='rec-'+m.t;")
# thẻ nhóm ngân hàng: chỉ hiện dòng khuyến nghị đầu, 2 dòng còn lại trong <details>
script = one(script,
             "<dl><dt>Ngân hàng</dt>${PLAY[k].bank.map(x=>'<dd>• '+x+'</dd>').join('')}</dl>",
             "<dl><dt>Ngân hàng</dt><dd>• ${PLAY[k].bank[0]}</dd></dl><details><summary>thêm</summary><dl>${PLAY[k].bank.slice(1).map(x=>'<dd>• '+x+'</dd>').join('')}</dl></details>")

NEWJS = r"""
/* ---------- PHẦN 1 MỚI: KPI + dumbbell ---------- */
function pearson(xs,ys){const n=xs.length,mx=xs.reduce((a,b)=>a+b)/n,my=ys.reduce((a,b)=>a+b)/n;
 const c=xs.reduce((a,v,i)=>a+(v-mx)*(ys[i]-my),0),sx=Math.sqrt(xs.reduce((a,v)=>a+(v-mx)**2,0)),sy=Math.sqrt(ys.reduce((a,v)=>a+(v-my)**2,0));return c/sx/sy}
function k1(){
 const s=F.map(t=>last(t));const short=s.filter(b=>b.cov<1);const neg=s.filter(b=>b.gap<0).reduce((a,b)=>a+b.gap,0);
 const r=pearson(s.map(b=>b.de),s.map(b=>b.cov));
 const c=F.map(t=>D.cal[t]).sort((a,b)=>a-b);const med=c.length%2?c[(c.length-1)/2]:(c[c.length/2-1]+c[c.length/2])/2;
 document.getElementById('k1').innerHTML=[[`${short.length}/9`,'doanh nghiệp có hệ số phủ 2026Q3 dưới 1,0×'],[fmt(-neg)+' tỷ','tổng khoảng hụt 2026Q3 của các doanh nghiệp hụt'],[fmt(r,2),'tương quan Pearson giữa D/E và hệ số phủ'],[fmt(med,1)+'%','doanh thu trung vị nửa đầu 2023 so với quý 4/2022']].map(([v,l])=>`<div class="kpi"><div class="v num">${v}</div><div class="l">${l}</div></div>`).join('');
}
function dumbbell(){
 const rows=F.map(t=>({t,b0:D.firms[t].bs[0],b:last(t)})).sort((a,b)=>a.b.cov-b.b.cov);
 const W=1080,rh=36,T=34,L=190,R=200,H=T+rows.length*rh+30,g=svg('c1d',W,H),max=1.4;
 const x=v=>L+Math.min(Math.max(v,0),max)/max*(W-L-R);
 const cD=W-R+70,cI=W-20;
 [0,0.2,0.4,0.6,0.8,1,1.2,1.4].forEach(v=>{el('line',{x1:x(v),x2:x(v),y1:T-6,y2:H-24,stroke:v==1?C.ink:C.line,'stroke-width':v==1?2:1,'stroke-dasharray':v==1?'':'2 3'},g);el('text',{x:x(v),y:H-6,'text-anchor':'middle','font-size':12,fill:C.mute},g,fmt(v,1)+'×')});
 el('text',{x:x(1)+5,y:T-12,'font-size':12,fill:C.ink},g,'Ngưỡng đủ tiền 1,0×');
 el('text',{x:cD,y:T-12,'text-anchor':'end','font-size':12,'font-weight':600,fill:C.ink},g,'D/E');
 el('text',{x:cI,y:T-12,'text-anchor':'end','font-size':12,'font-weight':600,fill:C.ink},g,'Tồn kho/TSNH');
 rows.forEach((r,i)=>{const y=T+i*rh+rh/2;const b=r.b,c=tierCol(b.cov);
  if(i%2==0)el('rect',{x:0,y:y-rh/2,width:W,height:rh,fill:'#eef0ea',opacity:.6},g);
  el('text',{x:0,y:y+5,'font-size':14,'font-weight':600,fill:C.ink,'font-family':'JetBrains Mono'},g,r.t);
  el('text',{x:46,y:y+5,'font-size':12.5,fill:C.mute},g,NAME[r.t]);
  el('line',{x1:x(r.b0.cov),x2:x(b.cov),y1:y,y2:y,stroke:'#9aa5a3','stroke-width':3},g);
  const o=el('circle',{cx:x(r.b0.cov),cy:y,r:6,fill:'#f4f5f1',stroke:'#7c878c','stroke-width':2},g);
  const d=el('circle',{cx:x(b.cov),cy:y,r:7.5,fill:c,stroke:'#f4f5f1','stroke-width':1.5},g);
  const right=b.cov>=r.b0.cov;
  el('text',{x:x(b.cov)+(right?12:-12),y:y+4,'text-anchor':right?'start':'end','font-size':12,'font-family':'JetBrains Mono',fill:c,'font-weight':600},g,fx(b.cov));
  el('text',{x:cD,y:y+5,'text-anchor':'end','font-size':13,'font-family':'JetBrains Mono',fill:b.de>2?C.red:C.ink},g,fmt(b.de,2));
  el('text',{x:cI,y:y+5,'text-anchor':'end','font-size':13,'font-family':'JetBrains Mono',fill:C.ink},g,fmt(b.inventory/b.current_assets*100,0)+'%');
  const tt=q=>()=>`<b>${r.t} · ${NAME[r.t]}</b> — ${q.period}<br>Tiền + ĐT ngắn hạn: ${fmt(q.liquid)} tỷ<br>Nợ ngắn hạn: ${fmt(q.short_term_liabilities)} tỷ<br>Khoảng hụt: <b>${fmt(q.gap)}</b> tỷ<br>Hệ số phủ: ${fx(q.cov)}`;
  hover(d,tt(b));hover(o,tt(r.b0))});
}
function tabs1(){const box=document.getElementById('tabs1');
 box.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  [...box.children].forEach(c=>c.classList.toggle('on',c===b));
  document.querySelectorAll('#s1 .tabpane').forEach((p,i)=>p.classList.toggle('on',String(i)===b.dataset.tab))})}

/* ---------- PHẦN 4 MỚI: bảng quyết định ---------- */
const DEADLINE={D:'0–3 tháng',C:'3 tháng',B:'6 tháng',A:'theo dõi định kỳ'};
function short12(t){const w=t.split(/\s+/);return w.length>12?w.slice(0,12).join(' ').replace(/[;,:.]$/,'')+'…':t}
function dtable(){
 const r=F.map(t=>full(t)).sort((a,b)=>b.g.localeCompare(a.g)||a.cov-b.cov);
 let h='<table><tr><th>Mã</th><th>Nhóm</th><th>Quyết định chính</th><th>Con số then chốt</th><th>Hạn hành động</th></tr>';
 r.forEach(m=>{const key=(m.g=='D'||m.g=='C')?`hụt ${fmt(-m.gap)} tỷ · cần gia hạn ${fmt(m.rNeed,0)}%`:`dư ${fmt(m.gap)} tỷ · chịu sốc ${m.sMax>=100?'>100':fmt(m.sMax,0)}%`;
  h+=`<tr class="go" data-t="${m.t}"><td><b>${m.t}</b></td><td><span class="badge" style="background:${G[m.g].c}">${m.g} · ${G[m.g].n}</span></td><td style="font-size:13.5px">${short12(PLAY[m.g].dev)}</td><td class="num" style="font-size:13px;color:${m.gap<0?C.red:C.green}">${key}</td><td style="font-size:13.5px;font-weight:600">${DEADLINE[m.g]}</td></tr>`});
 const box=document.getElementById('dtab');box.innerHTML=h+'</table>';
 box.querySelectorAll('tr.go').forEach(tr=>tr.onclick=()=>{const c=document.getElementById('rec-'+tr.dataset.t);if(!c)return;c.scrollIntoView({behavior:'smooth',block:'center'});c.classList.add('flash');setTimeout(()=>c.classList.remove('flash'),1400)});
}
"""
script = one(script, "function run(){hero();p6();p6b();p7();p8();recs();p10()}",
             NEWJS + "function run(){hero();p6();p6b();p7();p8();recs();dtable();p10()}")
script = one(script, "p1();p2();p3();p4();p5();buildCtrl();run();",
             "k1();dumbbell();tabs1();p1();p2();p3();p4();p5();buildCtrl();run();")

head = one(head, "<title>Ai sẽ hụt tiền? — Stress test thanh khoản chủ đầu tư nhà ở niêm yết</title>",
           "<title>Ai sẽ hụt tiền? — Stress test thanh khoản chủ đầu tư nhà ở niêm yết (bản nộp)</title>")
html = head + "<body>" + body + script
for w in ["Nguy cấp", "Cứu được", "vỡ nợ"]:
    assert w not in html, w
open(out, "w", encoding="utf-8", newline="\n").write(html)
print(f"Đã ghi {out} ({len(html) / 1024:.0f} KB)")

# bản tiếng Anh của cả hai dashboard
from translate_dashboard import translate  # noqa: E402

for name in ["v3", "ban_nop"]:
    vi = os.path.join(REP, f"dashboard_stress_test_BDS_{name}_vnese.html")
    en = os.path.join(REP, f"dashboard_stress_test_BDS_{name}_eng.html")
    text = translate(open(vi, encoding="utf-8").read().replace("\r\n", "\n"))
    open(en, "w", encoding="utf-8", newline="\n").write(text)
    print(f"Đã ghi {en} ({len(text) / 1024:.0f} KB)")
