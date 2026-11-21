"""Merge allowance batch files, deduplicate employees and list data problems.

Usage: python3 -I pipeline.py <work dir> <config.json>

config.json lists the batches in order, each as
  {"batch": "الوجبة الأولى", "xlsx": "/path/file.xlsx"}           a batch Excel file, or
  {"batch": "الوجبة الأولى", "git_xlsx": "/path/full.xlsx"}       a batch rebuilt from an older
                                                                   comprehensive workbook.
Writes parsed.json, final_all.json, per_batch.json and report.json into the work dir.
Employee data never goes into the repository: keep the work dir outside it.
"""
import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sal import G, basic  # noqa: E402

GN = {'الرابعة': 'رابعة', 'العاشرة': 'عاشرة', 'الثالثة': 'ثالثة', 'الثانية': 'ثانية', 'اولى': 'أولى', 'الاولى': 'أولى',
      'الخامسة': 'خامسة', 'السادسة': 'سادسة', 'السابعة': 'سابعة', 'الثامنة': 'ثامنة', 'التاسعة': 'تاسعة'}
CERTS = {'ابتدائية', 'اعدادية', 'إعدادية', 'بدون مؤهل', 'بكالوريوس', 'بكالوروس', 'بكالويوس', 'دبلوم', 'دبلوم عالي',
         'دكتوراه', 'ماجستير', 'متوسطة', 'يقرأ ويكتب', 'يقرا ويكتب', 'يقراء ويكتب'}
CN = {'إعدادية': 'اعدادية', 'بكالوروس': 'بكالوريوس', 'بكالويوس': 'بكالوريوس', 'يقرا ويكتب': 'يقرأ ويكتب', 'يقراء ويكتب': 'يقرأ ويكتب'}
SEC = {'الشؤون الإدارية': 'قسم الشؤون الإدارية', 'قسم الشؤون الادراية': 'قسم الشؤون الإدارية', 'قسم الشؤون الادارية': 'قسم الشؤون الإدارية',
       'قطاع الامين': 'قطاع الأمين', 'قطاع الصدر الاول': 'قطاع الصدر الأول', 'قطاع الصدرالثاني': 'قطاع الصدر الثاني',
       'قطاع اور': 'قطاع حي اور', 'تشغيل والسيطرة والاتصالات': 'تشغيل السيطرة والاتصالات', 'السيطرة والاتصالات': 'تشغيل السيطرة والاتصالات',
       'صيانةوتشغيل الديزلات والوحدات الساندة': 'صيانة وتشغيل الديزلات والوحدات الساندة', 'قسم الانارة': 'قسم الإنارة',
       'قسم الرقابة الداخلي والتدقيق': 'قسم الرقابة الداخلية والتدقيق', 'مبيعات الطاقة': 'قسم مبيعات الطاقة',
       'الشؤون الفنية': 'قسم الشؤون الفنية', 'مكتب مدير الفرع': 'مدير الفرع', 'قسم التنفيذ والمشاريع': 'قسم التنفيذ والمشاريع الكهربائية',
       'قسم تنفيذ المشاريع': 'قسم التنفيذ والمشاريع الكهربائية', 'تنفيذ المشاريع': 'قسم التنفيذ والمشاريع الكهربائية',
       'قسم التخطيط والدراسات': 'قسم التخطيط'}
TT = [('رئيس حرفين', 'رئيس حرفيين'), ('ر.ملاحظيين', 'رئيس ملاحظين'), ('م. مدير', 'معاون مدير'), ('مبرمجيين', 'مبرمجين'),
      ('اقدم اولى', 'اقدم اول'), ('أقدم', 'اقدم'), ('كيميائين', 'كيميائيين'), ('رئيس بايلوجي', 'رئيس بايولوجي')]


def s(v):
    return re.sub(r'\s+', ' ', str(v)).strip() if v is not None else ''


def ds(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime('%d/%m/%Y')
    t = re.sub(r'/+', '/', s(v)).replace('-', '/')
    p = t.split('/')
    if len(p) == 3 and p[0].isdigit() and len(p[0]) == 4:
        p = p[::-1]
    return '/'.join([p[0].zfill(2), p[1].zfill(2), p[2]]) if len(p) == 3 else t


def num(v):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def nm(x):
    x = re.sub(r'[ً-ْـ]', '', str(x))
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي')):
        x = x.replace(a, b)
    return x.replace(' ', '')


def valid(d):
    try:
        datetime.datetime.strptime(d, '%d/%m/%Y')
        return True
    except ValueError:
        return False


def parse_xlsx(path, batch):
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if any(s(v) in ('الاسم', 'اسم الموظف') for v in r))
    col = {}
    for i, h in enumerate(s(v) for v in rows[hi]):
        if h in ('ت', 'تسلسل'):
            col['seq'] = i
        elif 'الانتساب' in h:
            col['id'] = i
        elif h in ('الاسم', 'اسم الموظف'):
            col['name'] = i
        elif h in ('الشعبة والقسم', 'موقع العمل'):
            col['section'] = i
        elif 'العنوان' in h:
            col['title'] = i
        elif 'الشهادة' in h:
            col['cert'] = i
        elif 'الدرجة' in h:
            col['grade'] = i
        elif 'المرحلة' in h and ('جديد' in h or 'مستحق' in h):
            col['due'] = i
        elif 'المرحلة' in h:
            col['stage'] = i
        elif 'الراتب' in h:
            col.setdefault('basic' if 'basic' not in col else 'dueSal', i)
        elif 'تاريخ' in h:
            col['date'] = i
        elif 'ملاحظ' in h or 'شكر' in h:
            col['notes'] = i
    emps, cur = [], None
    for ri, r in enumerate(rows[hi + 1:], start=hi + 2):
        def g(k):
            return r[col[k]] if k in col and col[k] < len(r) else None
        if all(v is None for v in r):
            continue
        if s(g('name')):
            cur = dict(batch=batch, row=ri, seq=g('seq'), id=s(g('id')), name=s(g('name')), section=s(g('section')),
                       title=s(g('title')), cert=s(g('cert')), grade=s(g('grade')), notes=s(g('notes')), lines=[])
            if cur['id'].endswith('.0'):
                cur['id'] = cur['id'][:-2]
            emps.append(cur)
        elif cur is None or g('stage') is None:
            continue
        elif s(g('notes')) and s(g('notes')) not in cur['notes']:
            cur['notes'] = (cur['notes'] + ' / ' + s(g('notes'))).strip(' /')
        cur['lines'].append(dict(stage=num(g('stage')), basic=num(g('basic')), due=num(g('due')), dueSal=num(g('dueSal')), date=ds(g('date'))))
    return emps


def parse_git(path, batch):
    """Rebuild one batch from an older comprehensive workbook: its detail sheet keeps every allowance line."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    # Attributes live on the merged all-staff sheet, one row per employee, found by ID or by name.
    attrs = {}
    for r in list(wb['الكل - أبجدي'].iter_rows(values_only=True))[1:]:
        if r[3]:
            a = dict(id=s(r[4]) if r[4] is not None else '', section=s(r[5]), title=s(r[6]), grade=s(r[7]), cert=s(r[16]), notes=s(r[17]))
            attrs['n' + nm(r[3])] = a
            if a['id']:
                attrs['i' + a['id']] = a
    emps, by = [], {}
    for r in list(wb['تفاصيل العلاوات'].iter_rows(values_only=True))[1:]:
        if r[0] != batch:
            continue
        k = (r[1], s(r[2]))
        if k not in by:
            a = attrs.get('i' + s(r[3])) if r[3] is not None else None
            a = a or attrs.get('n' + nm(r[2]), {})
            by[k] = dict(batch=batch, seq=r[1], id=s(r[3]) if r[3] is not None else a.get('id', ''), name=s(r[2]),
                         section=a.get('section', ''), title=a.get('title', ''), cert=a.get('cert', ''),
                         grade=s(r[4]) or a.get('grade', ''), notes=a.get('notes', ''), lines=[])
            emps.append(by[k])
        by[k]['lines'].append(dict(stage=num(r[5]), basic=num(r[6]), due=num(r[7]), dueSal=num(r[8]), date=ds(r[9])))
    return emps


def normalize(e, R):
    e['grade'] = GN.get(e['grade'], e['grade'])
    if e['title'] in CERTS and e['cert'] not in CERTS:
        R['swap'].append([e['batch'], e['seq'], e['name'], e['title'], e['cert']])
        e['title'], e['cert'] = e['cert'], e['title']
    if '/' in e['cert'] and e['cert'].split('/')[0].strip() in CERTS:
        extra = e['cert'].split('/', 1)[1].strip()
        e['cert'] = e['cert'].split('/')[0].strip()
        e['notes'] = (e['notes'] + ' / ' + extra).strip(' /')
    e['cert'] = CN.get(e['cert'], e['cert'])
    e['section'] = ' '.join(SEC.get(e['section'], e['section']).split())
    t = e['title']
    for a, b in TT:
        t = t.replace(a, b)
    e['title'] = t


def issues_of(e):
    iss, g, prev = [], e['grade'], None
    for line in e['lines']:
        st, b, du, dsal, dt = line['stage'], line['basic'], line['due'], line['dueSal'], line['date']
        if g not in G:
            iss.append(f'الدرجة «{g}» غير معروفة')
            break
        if None in (st, b, du, dsal):
            iss.append('سطر علاوة ناقص')
            continue
        if basic(g, st) != b:
            iss.append(f'الراتب الأساسي للمرحلة {st} مكتوب {b:,} والصحيح حسب الدرجة {g} {basic(g, st):,}')
        if basic(g, du) != dsal:
            iss.append(f'الراتب المستحق للمرحلة {du} مكتوب {dsal:,} والصحيح حسب الدرجة {g} {basic(g, du):,}')
        if du != st + 1:
            iss.append(f'المرحلة المستحقة {du} لا تلي المرحلة {st}')
        if prev is not None and st != prev:
            iss.append(f'تسلسل المراحل منقطع ({prev} ثم {st})')
        prev = du
        if dt and not valid(dt):
            iss.append(f'تاريخ العلاوة {dt} غير صحيح')
    if not e['title']:
        iss.append('العنوان الوظيفي فارغ')
    if not e['cert']:
        iss.append('الشهادة فارغة')
    elif e['cert'] not in CERTS:
        iss.append(f"الشهادة مكتوبة «{e['cert']}» وهي ليست شهادة")
    return iss


def apply_patch(emps, patch, batch):
    """Apply known corrections to a rebuilt batch: replaced allowance lines and added people.

    patch = {"lines": {name: [[stage, due, date], ...]}, "add": [{seq, id, name, section, title, grade, cert, lines, note}]}
    A line with an empty date means the date is not known; it is not reported as wrong.
    """
    def mk(g, ls):
        return [dict(stage=a, basic=basic(g, a) if g in G else None, due=b, dueSal=basic(g, b) if g in G else None, date=d) for a, b, d in ls]
    by = {nm(e['name']): e for e in emps}
    for name, ls in patch.get('lines', {}).items():
        e = by[nm(name)]
        e['lines'] = mk(GN.get(e['grade'], e['grade']), ls)
    for a in patch.get('add', []):
        e = dict(batch=batch, seq=a['seq'], id=a['id'], name=a['name'], section=a.get('section', ''), title=a['title'],
                 grade=a['grade'], cert=a['cert'], notes=a.get('note', ''), lines=mk(GN.get(a['grade'], a['grade']), a['lines']))
        emps.append(e)


def main(work, cfg):
    R = collections.defaultdict(list)
    batches = [c['batch'] for c in cfg]
    parsed = {}
    for c in cfg:
        parsed[c['batch']] = parse_xlsx(c['xlsx'], c['batch']) if 'xlsx' in c else parse_git(c['git_xlsx'], c['batch'])
        if 'patch' in c:
            apply_patch(parsed[c['batch']], json.load(open(c['patch'], encoding='utf8')), c['batch'])
    json.dump(parsed, open(os.path.join(work, 'parsed.json'), 'w', encoding='utf8'), ensure_ascii=False, default=str)
    recs = []
    for b in batches:
        for e in parsed[b]:
            normalize(e, R)
            e['issues'] = issues_of(e)
            recs.append(e)
    for b in batches:
        si = [e['seq'] for e in parsed[b]]
        ints = [x for x in si if isinstance(x, int)]
        for k, v in collections.Counter(si).items():
            if v > 1:
                R['seq'].append([b, f'التسلسل {k} مكرر {v} مرات'])
        for x in si:
            if not isinstance(x, int):
                R['seq'].append([b, f'تسلسل غير رقمي «{x if x is not None else "فارغ"}»'])
        gaps = sorted(set(range(1, max(ints) + 1)) - set(ints)) if ints else []
        if gaps:
            R['seq'].append([b, 'تسلسلات ناقصة: ' + '، '.join(map(str, gaps))])
        for i in range(1, len(ints)):
            if ints[i] < ints[i - 1]:
                R['seq'].append([b, f'التسلسل {ints[i]} جاء بعد {ints[i - 1]}'])
        R['count'].append([b, len(parsed[b]), max(ints) if ints else 0])
    name2ids = collections.defaultdict(set)
    for e in recs:
        if e['id']:
            name2ids[nm(e['name'])].add(e['id'])
    for e in recs:
        if not e['id'] and len(name2ids.get(nm(e['name']), ())) == 1:
            e['id'] = next(iter(name2ids[nm(e['name'])]))
            e['idf'] = True
            R['idfill'].append([e['batch'], e['seq'], e['name'], e['id']])
    grp = collections.defaultdict(list)
    for e in recs:
        grp['i' + e['id'] if e['id'] else 'n' + nm(e['name'])].append(e)
    out = []
    for es in grp.values():
        bl = []
        for e in es:
            if e['batch'] not in bl:
                bl.append(e['batch'])
        lines, conflict = {}, []
        for e in es:
            for line in e['lines']:
                kk = (line['stage'], line['due'])
                if kk in lines and lines[kk][0]['date'] != line['date']:
                    conflict.append(f"العلاوة {kk[0]}←{kk[1]} بتاريخ {lines[kk][0]['date']} في {lines[kk][1]} و{line['date']} في {e['batch']}")
                lines.setdefault(kk, (line, e['batch']))
        main_e = max(es, key=lambda e: (max((x['due'] or 0) for x in e['lines']) if e['lines'] else 0, batches.index(e['batch'])))
        L = sorted(lines.values(), key=lambda x: (x[0]['stage'] or 0))
        iss = []
        for e in es:
            for i in e['issues']:
                if i not in iss:
                    iss.append(i)
        if len(es) > 1:
            same = len({tuple((x['stage'], x['due']) for x in e['lines']) for e in es}) == 1
            kind = ('مكرر داخل نفس الوجبة' if len({e['batch'] for e in es}) == 1 else 'مكرر بنفس البيانات' if same and not conflict
                    else 'تعارض في تواريخ العلاوة' if conflict else 'علاوات مختلفة في كل وجبة')
            diffs = []
            for fld, lab in (('name', 'الاسم'), ('grade', 'الدرجة'), ('title', 'العنوان الوظيفي'), ('section', 'الجهة'), ('cert', 'الشهادة')):
                vals = []
                for e in es:
                    v = e[fld]
                    if v and (nm(v) if fld == 'name' else v) not in [(nm(x) if fld == 'name' else x) for x in vals]:
                        vals.append(v)
                if len(vals) > 1:
                    diffs.append(f"{lab}: " + ' / '.join(vals))
            stv = sorted(set(lines))
            gap = any(stv[i][0] != stv[i - 1][1] for i in range(1, len(stv)))
            R['dup'].append([main_e['name'], main_e['id'] or '—', ' + '.join(f"{e['batch']} ت{e['seq']}" for e in es), kind,
                             '؛ '.join(conflict + diffs + (['المراحل غير متصلة بين الوجبات'] if gap else []))])
            iss += conflict
            if diffs:
                iss.append('اختلاف بين الوجبات في ' + '، '.join(d.split(':')[0] for d in diffs))
        stage = L[0][0]['stage'] if L else ''
        due = max(x[0]['due'] or 0 for x in L) if L else ''
        nxt = max(L, key=lambda x: x[0]['due'] or 0)[0]['date'] if L else ''
        out.append(dict(seq=main_e['seq'], id=main_e['id'], name=main_e['name'], section=main_e['section'], title=main_e['title'],
                        grade=main_e['grade'], stage=stage, due=due, cert=main_e['cert'], next=nxt, notes=main_e['notes'],
                        flag='؛ '.join(iss), batch='، '.join(bl)))
        for e in es:
            for i in e['issues']:
                R['err'].append([e['batch'], e['seq'], e['id'] or '—', e['name'], i])
    tg = collections.defaultdict(collections.Counter)
    for r in out:
        tg[r['title']][r['grade']] += 1
    for r in out:
        c = tg[r['title']]
        top, cnt = c.most_common(1)[0]
        if r['title'] and r['grade'] != top and c[r['grade']] <= max(1, cnt * 0.03) and cnt >= 10:
            m = f"العنوان «{r['title']}» يقابل عادة الدرجة {top}، والدرجة المكتوبة {r['grade']}"
            r['flag'] = (r['flag'] + '؛ ' + m).strip('؛ ')
            R['err'].append([r['batch'], r['seq'], r['id'] or '—', r['name'], m])
    sc = collections.Counter(r['section'] for r in out)
    R['oddsec'] = [[k, v] for k, v in sorted(sc.items()) if v <= 2 or k == 'غير محدد']
    R['noid'] = [[r['batch'], r['seq'], r['name'], r['section']] for r in out if not r['id']]
    FL = ["seq", "id", "name", "section", "title", "grade", "stage", "due", "cert", "next", "notes", "flag", "batch"]
    out.sort(key=lambda r: (batches.index(r['batch'].split('، ')[0]), r['seq'] if isinstance(r['seq'], int) else 0))
    json.dump([[r[k] for k in FL] for r in out], open(os.path.join(work, 'final_all.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    perb = {}
    for e in recs:
        L = [x for x in e['lines'] if x['stage'] is not None]
        perb.setdefault(e['batch'], []).append([e['seq'], e['id'], e['name'], e['section'], e['title'], e['grade'],
                                                L[0]['stage'] if L else '', max((x['due'] or 0) for x in L) if L else '', e['cert'],
                                                L[-1]['date'] if L else '', e['notes'], '؛ '.join(e['issues']), e['batch'], bool(e.get('idf'))])
    json.dump(perb, open(os.path.join(work, 'per_batch.json'), 'w', encoding='utf8'), ensure_ascii=False)
    json.dump(R, open(os.path.join(work, 'report.json'), 'w', encoding='utf8'), ensure_ascii=False)
    print('records', len(recs), 'unique', len(out), 'dup', len(R['dup']), collections.Counter(d[3] for d in R['dup']),
          'errs', len(R['err']), 'noid', len(R['noid']), 'idfill', len(R['idfill']))
    for b, n_, mx in R['count']:
        print(' ', b, n_, 'max seq', mx)


if __name__ == '__main__':
    main(sys.argv[1], json.load(open(sys.argv[2], encoding='utf8')))
