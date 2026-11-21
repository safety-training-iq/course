"""Build the allowance pages from the merged data.

Usage: python3 -I gen_pages.py <work dir> <out dir> <date dd/mm/yyyy> [batch for batch pages]

Reads final_all.json (and <work>/batch_admin.json when a batch is given) and writes into <out dir>:
  admin.html          full page with salaries and IDs (keep private)
  public.html         employee page without IDs, workplaces or salaries, with a no-script list
  search.html         search-only page: name, job title and allowance date
  batch_public.html / batch_admin.html for the given batch
"""
import datetime
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, 'templates')
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700'
         '&family=Noto+Kufi+Arabic:wght@600;800&display=swap">\n')
HEAD = ('<!DOCTYPE html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
ORG = 'فرع توزيع كهرباء الصدر - قسم الشؤون الإدارية - شعبة الإسناد الإداري'
NOTICE_ALL = ('<b>تنبيه:</b> هذه هي الوجبات المنجزة إلى الآن فقط، وسوف تُضاف بقية الوجبات تدريجياً عند إكمالها. '
              'إذا لم تجد اسمك فقد يكون ضمن وجبة لم تُضف بعد.')
TYPES = ["تعارض في تاريخ العلاوة", "مكرر بنفس البيانات", "علاوات مختلفة (مكمّلة)", "جديد (لا يوجد في وجبة سابقة)"]


def rd(name):
    return open(os.path.join(TPL, name), encoding='utf8').read()


def jdump(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def page(title, css, data_tag, js, app_inner='', css_id=True, js_id=True):
    return (HEAD + f'<title>{title}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + FONTS +
            (f'<style id="app-css">{css}</style>\n' if css_id else f'<style>{css}</style>\n') +
            f'<div id="app">{app_inner}</div>\n{data_tag}\n' + (f'<script id="app-js">{js}</script>\n' if js_id else f'<script>{js}</script>\n') +
            '</body>\n</html>\n')


def norm(s):
    s = re.sub(r'[ً-ْـ]', '', s)
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ٱ', 'ا'), ('ة', 'ه'), ('ى', 'ي')):
        s = s.replace(a, b)
    return s.strip()


def fallback(rows, logo, title, notice, today):
    """Static list shown when scripts do not run (for example an iPhone file preview)."""
    def status(d):
        try:
            dt = datetime.datetime.strptime(d, '%d/%m/%Y').date()
        except (TypeError, ValueError):
            return 'soon', 'يُراجَع التاريخ'
        return ('due', 'مستحقة') if dt <= today else (('soon', 'خلال 30 يوماً') if (dt - today).days <= 30 else ('later', 'قادمة'))
    tr = str.maketrans('أإآة', 'اااه')
    rows = sorted(rows, key=lambda r: norm(r[0]).translate(tr))
    groups = {}
    for r in rows:
        groups.setdefault(norm(r[0])[:1] or '#', []).append(r)
    e = html.escape
    out = [f'<header class="mast wrap"><img src="{logo}" alt="شعار الفرع" width="84" height="84"><div class="txt">'
           f'<div class="eyebrow">كشف العلاوات السنوية 2026</div><h1>{e(title)}</h1>',
           '<p class="lede">الأسماء مرتبة أبجدياً. اضغط على الحرف الأول من اسمك للانتقال إليه.</p></div></header>',
           f'<div class="wrap"><div class="notice">{notice}</div>',
           f'<div class="stats"><div class="stat"><b>{len(rows):,}</b><span>موظفاً</span></div></div>',
           '<p class="lede" style="margin-top:10px"><b>ملاحظة:</b> هذه نسخة للعرض فقط. للبحث بالاسم افتح الملف في متصفح (Safari أو Chrome).</p>',
           '<nav style="display:flex;flex-wrap:wrap;gap:6px;margin:14px 0">' +
           ''.join(f'<a href="#L{i}" style="padding:4px 10px;border:1px solid var(--line);border-radius:6px;color:var(--navy);'
                   f'text-decoration:none;font-weight:700">{e(k)}</a>' for i, k in enumerate(groups)) + '</nav></div>',
           '<main class="wrap">']
    for i, (k, rs) in enumerate(groups.items()):
        out.append(f'<div class="letter" id="L{i}">{e(k)}<small>{len(rs)}</small></div><div class="flat">')
        for name, ttl, grade, st, due, cert, nxt in (r[:7] for r in rs):
            c, lab = status(nxt)
            out.append(f'<div class="emp"><div class="nm">{e(name)}</div><div class="org">{e(ttl or "—")}</div><div class="pay"><div class="ln">'
                       f'<span><span class="k">المرحلة</span> {e(str(st))} <span class="arrow">←</span> {e(str(due))}</span>'
                       f'<span><span class="k">العلاوة</span> {e(nxt or "—")}</span></div></div><div class="tags"><span class="tag g">{e(grade)}</span>'
                       f'<span class="tag">{e(cert)}</span><span class="pill {c}">{lab}</span></div></div>')
        out.append('</div>')
    out.append('</main>')
    return ''.join(out)


def public_page(rows, title_suffix, notice, today, ptitle):
    css, js = rd('admin.css'), rd('public.js')
    if title_suffix:
        a = '<span class="bolt">مستحقي العلاوات</span>'
        assert js.count(a) == 1
        js = js.replace(a, f'<span class="bolt">مستحقي العلاوات - {title_suffix}</span>')
        old = re.search(r'notice"\)\.innerHTML=`[^`]*`', js).group(0)
        js = js.replace(old, f'notice").innerHTML=`{notice}`')
    logo = re.search(r'const LOGO = "(data:image/png;base64,[^"]+)"', js).group(1)
    data = [[r[2], r[4], r[5], r[6], r[7], r[8], r[9], ''] for r in rows]
    title = f'{ORG} - مستحقي العلاوات' + (f' - {title_suffix}' if title_suffix else '')
    inner = fallback(data, logo, title, notice, today)
    return page(ptitle, css, f'<script id="emp-data" type="application/json">{jdump(data)}</script>', js, inner, css_id=False, js_id=False)


def admin_page(rows, meta, batch=None):
    css, js = rd('admin.css'), rd('admin.js')
    ptitle = 'مستحقي العلاوات - فرع توزيع كهرباء الصدر'
    if batch:
        short = batch.replace('الوجبة ', '')
        js = re.sub(r'const BATCHES = \[[^\]]*\];', 'const BATCHES = ' + json.dumps(TYPES, ensure_ascii=False) + ';', js, count=1)
        ptitle = f'إدارة {batch} - مستحقي العلاوات'
        for a, b in [('"كل الوجبات"', '"كل الحالات"'), ('"دليل الموظفين"', f'"{batch} - إدارة"'),
                     ('const TITLE = "مستحقي العلاوات - فرع توزيع كهرباء الصدر";', f'const TITLE = "{ptitle}";'),
                     ('<span class="bolt">مستحقي العلاوات</span></h1>', f'<span class="bolt">مستحقي العلاوات - إدارة {batch}</span></h1>'),
                     ('واعزل الموظفين حسب الوجبة أو', 'واعزل الموظفين حسب حالة المقاطعة (جديد، مكمّل، مكرر، تعارض) أو'),
                     ('<label for="fBatch">الوجبة<select', '<label for="fBatch">حالة المقاطعة<select'),
                     ('>حسب الوجبة</button>', '>حسب حالة المقاطعة</button>'),
                     ('const HEAD = ["ت","الوجبة","ت في الوجبة",', 'const HEAD = ["ت","حالة المقاطعة","ت في الوجبة",'),
                     ('for="f_batch">الوجبة<input', 'for="f_batch">حالة المقاطعة<input'),
                     ('const COLMAP = {batch:["الوجبة"],', 'const COLMAP = {batch:["حالة المقاطعة","الوجبة"],')]:
            assert js.count(a) == 1, a
            js = js.replace(a, b)
        js = re.sub(r'\$\("notice"\)\.innerHTML = `[^`]*`;',
                    f'$("notice").innerHTML = `<b>للإدارة فقط:</b> هذه الصفحة تعرض {batch} كاملة مع الرواتب وأرقام الانتساب ونتائج مقاطعتها '
                    f'بالوجبات السابقة. كل سجل فيه مشكلة يظهر عليه تنبيه، ويمكن عزلها من فلتر «فيها تنبيه» أو من «حالة المقاطعة».`;', js, count=1)
        assert 'للإدارة فقط' in js, short
    data = jdump({"meta": meta, "rows": rows})
    return page(ptitle, css, f'<script id="emp-data" type="application/json">{data}</script>', js)


def search_page(rows, date):
    t = rd('search.html')
    return t.replace('__DATA__', jdump([[r[2], r[4], r[9]] for r in rows])).replace('__DATE__', date)


def main(work, out, date, batch=None):
    os.makedirs(out, exist_ok=True)
    today = datetime.datetime.strptime(date, '%d/%m/%Y').date()
    rows = json.load(open(os.path.join(work, 'final_all.json'), encoding='utf8'))
    nb = len({b for r in rows for b in r[12].split('، ')})
    meta = {"updated": date, "source": f"الوجبات المنجزة ({nb} وجبات)"}
    w = lambda n, t: open(os.path.join(out, n), 'w', encoding='utf8').write(t)  # noqa: E731
    w('admin.html', admin_page(rows, meta))
    w('public.html', public_page(rows, '', NOTICE_ALL, today, 'مستحقي العلاوات - فرع توزيع كهرباء الصدر'))
    w('search.html', search_page(rows, date))
    if batch:
        brows = json.load(open(os.path.join(work, 'batch_admin.json'), encoding='utf8'))
        w('batch_public.html', public_page(brows, batch, f'<b>تنبيه:</b> هذه الصفحة تعرض أسماء {batch} فقط.', today, f'{batch} - مستحقي العلاوات'))
        w('batch_admin.html', admin_page(brows, {"updated": date, "source": f"{batch} مع نتائج مقاطعتها"}, batch))
    print('pages written to', out)


if __name__ == '__main__':
    main(*sys.argv[1:])
