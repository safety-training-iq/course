"""Comprehensive allowance workbook for all merged batches.

Usage: python3 -I excel_full.py <work dir> <date dd/mm/yyyy> <out.xlsx>
"""
import collections
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sal import G, basic  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

ORG = 'فرع توزيع كهرباء الصدر - قسم الشؤون الإدارية - شعبة الإسناد الإداري - مستحقي العلاوات'
NAVY = '34679A'
HF = PatternFill('solid', fgColor=NAVY)
BD = Border(*(Side('thin', color='BBBBBB'),) * 4)
WARN = PatternFill('solid', fgColor='FFF0D6')
H = ["ت", "الوجبة", "ت في الوجبة", "الاسم", "رقم الانتساب", "القسم / الشعبة / القطاع", "العنوان الوظيفي", "الدرجة", "المرحلة الحالية",
     "الراتب الأساسي", "المرحلة المستحقة", "الراتب المستحق", "الزيادة الشهرية", "عدد العلاوات", "تاريخ العلاوة", "حالة العلاوة", "الشهادة",
     "ملاحظات", "تنبيه"]
W = [6, 24, 9, 32, 12, 34, 24, 9, 9, 13, 10, 13, 11, 9, 12, 12, 12, 26, 50]


def b(g, s):
    try:
        return basic(g, int(s))
    except (KeyError, ValueError, TypeError):
        return None


def header(ws, head, widths, freeze='A2'):
    ws.sheet_view.rightToLeft = True
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True, name='Arial', color='FFFFFF')
        c.fill = HF
        c.border = BD
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 32
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = freeze


def main(work, date, out):
    today = datetime.datetime.strptime(date, '%d/%m/%Y').date()
    F = ["seq", "id", "name", "section", "title", "grade", "stage", "due", "cert", "next", "notes", "flag", "batch"]
    rows = [dict(zip(F, a)) for a in json.load(open(os.path.join(work, 'final_all.json'), encoding='utf8'))]
    R = json.load(open(os.path.join(work, 'report.json'), encoding='utf8'))
    P = json.load(open(os.path.join(work, 'parsed.json'), encoding='utf8'))
    BO = list(P)
    tr = str.maketrans('أإآة', 'اااه')
    rows.sort(key=lambda r: (r['name'].translate(tr), r['seq'] if isinstance(r['seq'], int) else 0))

    def status(d):
        try:
            dt = datetime.datetime.strptime(d, '%d/%m/%Y').date()
        except (TypeError, ValueError):
            return 'تاريخ غير صحيح'
        return 'مستحقة' if dt <= today else ('خلال 30 يوماً' if (dt - today).days <= 30 else 'قادمة')
    for r in rows:
        r['basic'], r['dueSal'] = b(r['grade'], r['stage']), b(r['grade'], r['due'])
        r['inc'] = r['dueSal'] - r['basic'] if r['basic'] is not None and r['dueSal'] is not None else None
        r['n'] = int(r['due']) - int(r['stage']) if str(r['due']).isdigit() and str(r['stage']).isdigit() else None
        r['status'] = status(r['next'])

    def out_row(i, r):
        return [i, r['batch'], r['seq'], r['name'], int(r['id']) if str(r['id']).isdigit() else (r['id'] or None), r['section'], r['title'],
                r['grade'], r['stage'], r['basic'], r['due'], r['dueSal'], r['inc'], r['n'], r['next'], r['status'], r['cert'],
                r['notes'] or None, r['flag'] or None]

    def sheet(ws, data):
        header(ws, H, W, 'E2')
        for i, r in enumerate(data, 1):
            ws.append(out_row(i, r))
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.border = BD
                c.font = Font(name='Arial')
            for k in (9, 11, 12):
                row[k].number_format = '#,##0'
            if row[18].value:
                for c in row:
                    c.fill = WARN
        ws.auto_filter.ref = f"A1:{get_column_letter(len(H))}{len(data) + 1}"

    def simple(ws, head, data, widths, money=()):
        header(ws, head, widths)
        for r in data:
            ws.append(r)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.border = BD
                c.font = Font(name='Arial')
                c.alignment = Alignment(wrap_text=True, vertical='top')
            for k in money:
                row[k].number_format = '#,##0'
        ws.auto_filter.ref = f"A1:{get_column_letter(len(head))}{len(data) + 1}"

    wb = Workbook()
    sm = wb.active
    sm.title = 'ملخص'
    sm.sheet_view.rightToLeft = True
    sm.cell(1, 1, ORG).font = Font(bold=True, size=14, name='Arial', color=NAVY)
    sm.cell(2, 1, f'الكشف الشامل لجميع الوجبات المنجزة · تاريخ الإعداد {date}').font = Font(name='Arial', color='566579')
    sm.cell(3, 1, 'تنبيه: هذه الوجبات المنجزة إلى الآن فقط، وسوف تُضاف بقية الوجبات تدريجياً عند إكمالها.').font = Font(bold=True, name='Arial', color='9A5B00')

    def table(r, title, head, data, money=()):
        sm.cell(r, 1, title).font = Font(bold=True, size=12, name='Arial', color=NAVY)
        r += 1
        for j, h in enumerate(head, 1):
            c = sm.cell(r, j, h)
            c.font = Font(bold=True, name='Arial', color='FFFFFF')
            c.fill = HF
            c.border = BD
            c.alignment = Alignment(horizontal='center', wrap_text=True)
        for row in data:
            r += 1
            for j, v in enumerate(row, 1):
                c = sm.cell(r, j, v)
                c.border = BD
                c.font = Font(name='Arial', bold=row[0] == 'المجموع')
                if j - 1 in money:
                    c.number_format = '#,##0'
        return r + 3

    def agg(keyf, order=None):
        d = collections.OrderedDict()
        for r in rows:
            for k in keyf(r):
                a = d.setdefault(k, [0, 0, 0, 0])
                a[0] += 1
                a[1] += r['inc'] or 0
                a[2] += r['status'] == 'مستحقة'
                a[3] += bool(r['flag'])
        ks = order if order else sorted(d, key=lambda k: -d[k][0])
        data = [[k] + d[k] for k in ks if k in d]
        data.append(['المجموع'] + [sum(x[i] for x in data) for i in range(1, 5)])
        return data
    hd = ['عدد الموظفين', 'مجموع الزيادة الشهرية', 'علاوات مستحقة', 'سجلات فيها تنبيه']
    tb, td = sum(r['basic'] or 0 for r in rows), sum(r['dueSal'] or 0 for r in rows)
    r = table(5, 'الأرقام العامة', ['البند', 'القيمة'], [
        ['مجموع السجلات في ملفات الوجبات', sum(len(v) for v in P.values())], ['عدد الموظفين بعد معالجة التكرار', len(rows)],
        ['مجموع الرواتب الأساسية الحالية', tb], ['مجموع الرواتب المستحقة بعد العلاوة', td], ['مجموع الزيادة الشهرية', td - tb],
        ['علاوات مستحقة (تاريخها حلّ)', sum(x['status'] == 'مستحقة' for x in rows)],
        ['علاوات خلال 30 يوماً', sum(x['status'] == 'خلال 30 يوماً' for x in rows)], ['علاوات قادمة', sum(x['status'] == 'قادمة' for x in rows)],
        ['حالات تكرار عولجت', len(R['dup'])], ['أخطاء في الملفات', len(R['err'])], ['سجلات فيها تنبيه', sum(bool(x['flag']) for x in rows)],
        ['بلا رقم انتساب', len(R['noid'])], ['أرقام انتساب أُكملت بالمطابقة بالاسم', len(R['idfill'])]], money=(1,))
    r = table(r, 'حسب الوجبة (الموظف الوارد في أكثر من وجبة يُحسب في كل منها)', ['الوجبة'] + hd, agg(lambda x: x['batch'].split('، '), BO), money=(2,))
    r = table(r, 'حسب الدرجة', ['الدرجة'] + hd, agg(lambda x: [x['grade']], G), money=(2,))
    r = table(r, 'حسب الشهادة', ['الشهادة'] + hd, agg(lambda x: [x['cert'] or 'غير مذكورة']), money=(2,))
    table(r, 'حسب الجهة', ['الجهة'] + hd, agg(lambda x: [x['section']]), money=(2,))
    sm.column_dimensions['A'].width = 46
    for c in 'BCDE':
        sm.column_dimensions[c].width = 18
    sheet(wb.create_sheet('الكل - أبجدي'), rows)
    det = []
    for bn, es in P.items():
        for e in es:
            for x in e['lines']:
                det.append([bn, e['seq'], e['name'], int(e['id']) if str(e['id']).isdigit() else e['id'], e['grade'], x['stage'], x['basic'],
                            x['due'], x['dueSal'], x['date']])
    simple(wb.create_sheet('تفاصيل العلاوات'), ['الوجبة', 'ت في الوجبة', 'الاسم', 'رقم الانتساب', 'الدرجة', 'المرحلة', 'الراتب الأساسي',
                                              'المرحلة الجديدة', 'الراتب الجديد', 'تاريخ الاستحقاق'], det, [22, 9, 32, 12, 9, 8, 13, 9, 13, 13], money=(6, 8))
    for bt in BO:
        sheet(wb.create_sheet(bt[:31]), [x for x in rows if bt in x['batch'].split('، ')])
    simple(wb.create_sheet('التكرار'), ['الاسم', 'رقم الانتساب', 'ورد في', 'نوع التكرار', 'التفاصيل'], R['dup'], [32, 12, 46, 24, 70])
    simple(wb.create_sheet('الأخطاء'), ['الوجبة', 'ت', 'رقم الانتساب', 'الاسم', 'الخطأ'], R['err'], [22, 7, 12, 32, 80])
    simple(wb.create_sheet('بلا رقم انتساب'), ['الوجبة', 'ت', 'الاسم', 'الجهة'], R['noid'], [22, 7, 34, 36])
    simple(wb.create_sheet('أرقام انتساب أُكملت'), ['الوجبة', 'ت', 'الاسم', 'رقم الانتساب المأخوذ من وجبة أخرى'], R['idfill'], [22, 7, 34, 24])
    simple(wb.create_sheet('أخطاء التسلسل'), ['الوجبة', 'الملاحظة'], R['seq'], [22, 90])
    used = set(wb.sheetnames)
    for sec in sorted({x['section'] for x in rows}, key=lambda s: s.translate(tr)):
        n = (sec or 'غير محدد').replace('/', '-')[:31]
        while n in used:
            n = n[:29] + '_2'
        used.add(n)
        sheet(wb.create_sheet(n), [x for x in rows if x['section'] == sec])
    wb.save(out)
    print('sheets', len(wb.sheetnames), 'rows', len(rows), 'lines', len(det), 'increase', td - tb)


if __name__ == '__main__':
    main(*sys.argv[1:4])
