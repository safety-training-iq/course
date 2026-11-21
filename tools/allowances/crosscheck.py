"""Cross-check one batch against all earlier batches and write its workbooks.

Usage: python3 -I crosscheck.py <work dir> <batch> <date> <results.xlsx> <filtered.xlsx>
Needs parsed.json, per_batch.json and report.json from pipeline.py. Writes <work>/batch_admin.json
for gen_pages.py.
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sal import basic  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

ORG = 'فرع توزيع كهرباء الصدر - قسم الشؤون الإدارية - شعبة الإسناد الإداري'
NAVY = '34679A'
HF = PatternFill('solid', fgColor=NAVY)
BD = Border(*(Side('thin', color='BBBBBB'),) * 4)
NEW, MORE, SAME, CONF = 'جديد (لا يوجد في وجبة سابقة)', 'علاوات مختلفة (مكمّلة)', 'مكرر بنفس البيانات', 'تعارض في تاريخ العلاوة'
INSIDE = 'مكرر داخل الوجبة نفسها'
FILL = {CONF: 'FDE4E5', INSIDE: 'FDE4E5', SAME: 'FFF0D6', MORE: 'EAF1F8'}


def nm(x):
    x = re.sub(r'[ً-ْـ]', '', str(x))
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي')):
        x = x.replace(a, b)
    return x.replace(' ', '')


def b(g, st):
    try:
        return basic(g, int(st))
    except (KeyError, ValueError, TypeError):
        return None


def sheet(wb, title, head, rows, widths, money=(), colorcol=None, band=None, freeze='A2'):
    ws = wb.create_sheet(title[:31])
    ws.sheet_view.rightToLeft = True
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True, name='Arial', color='FFFFFF')
        c.fill = HF
        c.border = BD
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 32
    for r in rows:
        ws.append(r)
    alt = PatternFill('solid', fgColor='F3F6FA')
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.border = BD
            c.font = Font(name='Arial')
            c.alignment = Alignment(wrap_text=True, vertical='top')
        for k in money:
            row[k].number_format = '#,##0'
        f = FILL.get(row[colorcol].value) if colorcol is not None else None
        if colorcol is not None and not f and len(row) > colorcol + 1 and row[colorcol + 1].value:
            f = 'FFF0D6'
        if f:
            for c in row:
                c.fill = PatternFill('solid', fgColor=f)
        if band is not None and isinstance(row[band].value, int) and row[band].value % 2 == 0:
            for c in row:
                c.fill = alt
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = freeze
    ws.auto_filter.ref = f"A1:{get_column_letter(len(head))}{max(len(rows), 1) + 1}"
    return ws


def main(work, B, date, out_results, out_filtered):
    P = json.load(open(os.path.join(work, 'parsed.json'), encoding='utf8'))
    PB = json.load(open(os.path.join(work, 'per_batch.json'), encoding='utf8'))
    R = json.load(open(os.path.join(work, 'report.json'), encoding='utf8'))
    order = list(P)
    prev = order[:order.index(B)]
    fill = {(x[0], x[1], x[2]): x[3] for x in R['idfill']}
    recs = []
    for bn in order[:order.index(B) + 1]:
        for e, n in zip(P[bn], PB[bn]):
            e = dict(e)
            e['norm'] = n
            if not e['id'] and (bn, e['seq'], e['name']) in fill:
                e['id'] = fill[(bn, e['seq'], e['name'])]
                e['idf'] = True
            recs.append(e)
    key = lambda e: 'i' + e['id'] if e['id'] else 'n' + nm(e['name'])  # noqa: E731
    grp = collections.defaultdict(list)
    for e in recs:
        grp[key(e)].append(e)
    lines = lambda e: '، '.join(f"{x['stage']}←{x['due']} ({x['date'] or '—'})" for x in e['lines'])  # noqa: E731
    eB = [e for e in recs if e['batch'] == B]
    TYPES, dup, detail, conf, new = {}, [], [], [], []
    gno = 0
    for e in eB:
        others = [x for x in grp[key(e)] if x is not e]
        if not others:
            new.append(e)
            TYPES[id(e)] = NEW
            continue
        gno += 1
        kB = {(x['stage'], x['due']): x['date'] for x in e['lines']}
        cf, covered = [], set()
        for o in others:
            for x in o['lines']:
                kk = (x['stage'], x['due'])
                covered.add(kk)
                if kk in kB and kB[kk] and x['date'] and kB[kk] != x['date']:
                    cf.append(f"العلاوة {kk[0]}←{kk[1]}: {kB[kk]} في {B} و{x['date']} في {o['batch']}")
        inside = [o for o in others if o['batch'] == B]
        typ = INSIDE if inside else CONF if cf else SAME if set(kB) <= covered else MORE
        TYPES[id(e)] = typ
        g = [e] + others
        diffs = []
        for fld, lab in (('grade', 'الدرجة'), ('title', 'العنوان الوظيفي'), ('section', 'الجهة'), ('cert', 'الشهادة')):
            vals = {x['norm'][{'grade': 5, 'title': 4, 'section': 3, 'cert': 8}[fld]] for x in g if x[fld]}
            if len(vals) > 1:
                diffs.append(f"{lab}: " + ' / '.join(sorted(vals)))
        if len({nm(x['name']) for x in g}) > 1:
            diffs.append('الاسم: ' + ' / '.join(sorted({x['name'] for x in g})))
        n = e['norm']
        dup.append([gno, e['seq'], e['name'], (e['id'] or '') + (' (من وجبة أخرى)' if e.get('idf') else ''), n[3], n[5], lines(e),
                    ' + '.join(f"{o['batch']} ت{o['seq']}" for o in others), ' | '.join(f"{o['batch']}: {lines(o)}" for o in others),
                    typ, '؛ '.join(cf + diffs)])
        for x in g:
            xn = x['norm']
            L = x['lines']
            detail.append([gno, x['batch'], x['seq'], x['name'], x['id'], xn[3], xn[4], xn[5], L[0]['stage'] if L else None,
                           b(xn[5], L[0]['stage']) if L else None, max(y['due'] or 0 for y in L) if L else None,
                           b(xn[5], max(y['due'] or 0 for y in L)) if L else None, L[-1]['date'] if L else '', xn[8]])
        if cf:
            conf.append([e['seq'], e['name'], e['id'], ' + '.join(f"{o['batch']} ت{o['seq']}" for o in others), '؛ '.join(cf)])
    errB = [[x[1], x[2], x[3], x[4]] for x in R['err'] if x[0] == B]
    seqB = [[m] for x, m in R['seq'] if x == B]
    idfB = [[x[1], x[2], x[3]] for x in R['idfill'] if x[0] == B]
    noidB = [[e['seq'], e['name'], e['norm'][3]] for e in eB if not e['id']]
    seqc = collections.Counter(e['seq'] for e in eB)
    adm = []
    dinfo = {(r[1], r[2]): r for r in dup}
    for e in eB:
        n = e['norm']
        fl = []
        if (e['seq'], e['name']) in dinfo:
            d = dinfo[(e['seq'], e['name'])]
            fl.append(f"{d[9]}: ورد أيضاً في {d[7]} ({d[8]})" + (f"؛ {d[10]}" if d[10] else ''))
        fl += [x[3] for x in errB if x[0] == e['seq'] and x[2] == e['name']]
        if e.get('idf'):
            fl.append(f'رقم الانتساب غير موجود في ملف {B}، أُكمل من وجبة أخرى بمطابقة الاسم')
        elif not e['id']:
            fl.append('لا يوجد رقم انتساب')
        if seqc[e['seq']] > 1:
            fl.append(f"التسلسل {e['seq']} مكرر في ملف {B}")
        adm.append([e['seq'], e['id'], e['name'], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10], '؛ '.join(fl), TYPES[id(e)]])
    json.dump(adm, open(os.path.join(work, 'batch_admin.json'), 'w', encoding='utf8'), ensure_ascii=False)

    # --- results workbook
    wb = Workbook()
    sm = wb.active
    sm.title = 'ملخص'
    sm.sheet_view.rightToLeft = True
    sm.cell(1, 1, ORG).font = Font(bold=True, size=13, name='Arial', color=NAVY)
    sm.cell(2, 1, f'نتائج مقاطعة {B} من العلاوات مع {prev[0]} إلى {prev[-1]} · {date}').font = Font(bold=True, size=12, name='Arial', color='E1323A')
    ct = collections.Counter(TYPES.values())
    items = [(f'عدد الأسماء في ملف {B}', len(eB)), ('أسماء جديدة لا توجد في الوجبات السابقة', len(new)), ('أسماء موجودة في وجبات سابقة (مكرر)', len(dup))]
    items += [('   منها: ' + k, ct[k]) for k in (MORE, SAME, CONF, INSIDE) if ct[k]]
    items += [(f'أخطاء في {B}', len(errB)), ('ملاحظات التسلسل', len(seqB)), ('أسماء بلا رقم انتساب في الملف', len(noidB) + len(idfB)),
              ('   منها أُكمل رقمها من وجبة أخرى', len(idfB)), ('   ومنها بقيت بلا رقم', len(noidB))]
    r = 4
    for k, v in items:
        sm.cell(r, 1, k).font = Font(name='Arial', bold=not k.startswith('   '))
        sm.cell(r, 2, v).font = Font(name='Arial', bold=True)
        r += 1
    r += 1
    sm.cell(r, 1, 'توزيع المكرر حسب الوجبة السابقة').font = Font(bold=True, size=12, name='Arial', color=NAVY)
    r += 1
    cb = collections.Counter(x for row in dup for x in {p.split(' ت')[0] for p in row[7].split(' + ')})
    for bn in prev + [B]:
        if cb[bn]:
            sm.cell(r, 1, bn).font = Font(name='Arial')
            sm.cell(r, 2, cb[bn]).font = Font(name='Arial')
            r += 1
    r += 1
    sm.cell(r, 1, 'دليل الألوان: أحمر = تعارض أو مكرر داخل الوجبة، برتقالي = مكرر بنفس البيانات أو تنبيه، أزرق = علاوات مكمّلة').font = Font(name='Arial', color='566579')
    sm.column_dimensions['A'].width = 60
    sm.column_dimensions['B'].width = 12
    short = B.replace('الوجبة ', '')
    pri = [CONF, INSIDE, SAME, MORE]
    sheet(wb, 'المكرر - ملخص', ['م', f'ت في {short}', 'الاسم', 'رقم الانتساب', 'الجهة', 'الدرجة', f'العلاوات في {short} (المرحلة←المستحقة والتاريخ)',
                                'ورد أيضاً في', 'العلاوات في الوجبات الأخرى', 'نوع التكرار', 'التعارض والاختلافات'],
          sorted(dup, key=lambda x: (pri.index(x[9]), x[1] if isinstance(x[1], int) else 0)), [5, 8, 30, 16, 28, 8, 34, 30, 50, 22, 50], colorcol=9)
    sheet(wb, 'المكرر - مقارنة تفصيلية', ['م', 'الوجبة', 'ت في الوجبة', 'الاسم', 'رقم الانتساب', 'الجهة', 'العنوان الوظيفي', 'الدرجة', 'المرحلة',
                                         'الراتب الأساسي', 'المرحلة المستحقة', 'الراتب المستحق', 'تاريخ آخر علاوة', 'الشهادة'],
          detail, [5, 18, 8, 30, 11, 28, 22, 8, 7, 12, 9, 12, 12, 11], money=(9, 11), band=0)
    sheet(wb, 'التعارضات', [f'ت في {short}', 'الاسم', 'رقم الانتساب', 'ورد أيضاً في', 'التعارض'], conf, [9, 30, 11, 36, 70])
    sheet(wb, 'الأخطاء', [f'ت في {short}', 'رقم الانتساب', 'الاسم', 'الخطأ'], errB, [9, 11, 30, 60])
    sheet(wb, 'أخطاء التسلسل', ['الملاحظة'], seqB, [60])
    sheet(wb, 'أرقام انتساب أُكملت', [f'ت في {short}', 'الاسم', 'رقم الانتساب المأخوذ من وجبة أخرى'], idfB, [9, 32, 24])
    sheet(wb, 'بلا رقم انتساب', [f'ت في {short}', 'الاسم', 'الجهة'], noidB, [9, 32, 30])
    sheet(wb, 'الأسماء الجديدة', [f'ت في {short}', 'رقم الانتساب', 'الاسم', 'الجهة', 'العنوان الوظيفي', 'الدرجة', 'العلاوات', 'الشهادة'],
          [[e['seq'], e['id'], e['name'], e['norm'][3], e['norm'][4], e['norm'][5], lines(e), e['norm'][8]] for e in new], [9, 11, 30, 28, 22, 8, 40, 11])
    full = [[a[0], a[1], a[2], a[3], a[4], a[5], a[6], b(a[5], a[6]), a[7], b(a[5], a[7]), a[9], a[8], a[12]] for a in adm]
    sheet(wb, f'{B} كاملة', ['ت', 'رقم الانتساب', 'الاسم', 'الجهة', 'العنوان الوظيفي', 'الدرجة', 'المرحلة', 'الراتب الأساسي', 'المرحلة المستحقة',
                             'الراتب المستحق', 'تاريخ العلاوة', 'الشهادة', 'الحالة بعد المقاطعة'], full, [7, 11, 30, 28, 22, 8, 7, 12, 9, 12, 12, 11, 26],
          money=(7, 9), colorcol=12)
    wb.save(out_results)

    # --- filtered workbook: drop rows whose allowances all appear in an earlier batch
    keep = [a for a in adm if a[12] != SAME]
    drop = [a for a in adm if a[12] == SAME]
    H = ['ت', 'ت في ملف الوجبة', 'الاسم', 'رقم الانتساب', 'القسم / الشعبة / القطاع', 'العنوان الوظيفي', 'الدرجة', 'المرحلة', 'الراتب الأساسي',
         'المرحلة المستحقة', 'الراتب المستحق', 'تاريخ العلاوة', 'الشهادة', 'الحالة بعد المقاطعة', 'تنبيه']
    W = [6, 9, 32, 12, 32, 24, 9, 8, 13, 10, 13, 12, 12, 24, 60]
    row = lambda i, a: [i, a[0], a[2], int(a[1]) if str(a[1]).isdigit() else (a[1] or None), a[3], a[4], a[5], a[6], b(a[5], a[6]),  # noqa: E731
                        a[7], b(a[5], a[7]), a[9], a[8], a[12], a[11] or None]
    wb = Workbook()
    sm = wb.active
    sm.title = 'ملخص'
    sm.sheet_view.rightToLeft = True
    sm['A1'] = ORG
    sm['A1'].font = Font(bold=True, size=13, name='Arial', color=NAVY)
    sm['A2'] = f'{B} من العلاوات بعد التصفية · {date}'
    sm['A2'].font = Font(bold=True, size=12, name='Arial', color='E1323A')
    ck = collections.Counter(a[12] for a in keep)
    items = [(f'عدد الأسماء في ملف {B}', len(adm)), ('المستبعد (علاواته كلها موجودة في وجبة سابقة)', len(drop)), ('عدد الأسماء بعد التصفية', len(keep)),
             ('   منها جديد لا يوجد في وجبة سابقة', ck[NEW]), ('   منها علاوات مكمّلة لوجبة سابقة (أُبقيت لأن علاواتها جديدة)', ck[MORE]),
             ('   منها تعارض في تاريخ العلاوة (أُبقيت مع تنبيه)', ck[CONF])]
    if ck[INSIDE]:
        items.append(('   منها مكرر داخل الوجبة نفسها (أُبقيت مع تنبيه)', ck[INSIDE]))
    items += [('سجلات فيها تنبيه بعد التصفية', sum(1 for a in keep if a[11])), ('مجموع الرواتب الأساسية', sum(b(a[5], a[6]) or 0 for a in keep)),
              ('مجموع الرواتب المستحقة', sum(b(a[5], a[7]) or 0 for a in keep))]
    for i, (k, v) in enumerate(items, 4):
        sm.cell(i, 1, k).font = Font(name='Arial', bold=not k.startswith('   '))
        c = sm.cell(i, 2, v)
        c.font = Font(name='Arial', bold=True)
        c.number_format = '#,##0'
    r = len(items) + 5
    sm.cell(r, 1, 'ما الذي أُجري في التصفية').font = Font(bold=True, size=12, name='Arial', color=NAVY)
    for k in ['استبعاد من وردت كل علاواته في وجبة سابقة بنفس المراحل (لا علاوة جديدة له).',
              'إبقاء من له علاوات جديدة في هذه الوجبة حتى لو ورد اسمه سابقاً، مع ذكر الوجبة السابقة في التنبيه.',
              'إكمال أرقام الانتساب الناقصة من الوجبات الأخرى بمطابقة الاسم.', 'توحيد كتابة الجهات والعناوين والشهادات والدرجات.',
              'حساب الراتب الأساسي والمستحق من سلم الرواتب.', 'تلوين السجلات: أحمر = تعارض، أزرق = علاوات مكمّلة، برتقالي = تنبيه آخر.']:
        r += 1
        sm.cell(r, 1, '• ' + k).font = Font(name='Arial')
    sm.column_dimensions['A'].width = 78
    sm.column_dimensions['B'].width = 16
    tr = str.maketrans('أإآة', 'اااه')
    for title, data in ((f'{B} بعد التصفية', sorted(keep, key=lambda a: a[0] if isinstance(a[0], int) else 0)),
                        ('أبجدي', sorted(keep, key=lambda a: a[2].translate(tr))), ('المستبعد', drop)):
        sheet(wb, title, H, [row(i, a) for i, a in enumerate(data, 1)], W, money=(8, 10), colorcol=13, freeze='D2')
    wb.save(out_filtered)
    print(B, 'names', len(eB), 'new', len(new), 'dup', len(dup), dict(ct), 'conflicts', len(conf), 'errors', len(errB), 'kept', len(keep), 'dropped', len(drop))


if __name__ == '__main__':
    main(*sys.argv[1:6])
