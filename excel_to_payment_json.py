"""从《各账户打款统计》Excel 生成 dashboard JSON。

数据源：领星 API 生成的 D:\\firehouse\\各账户打款统计_YYYYMMDD.xlsx
（2026-09-10 起，领星 API 统计已替代原「手工汇总」流程）

注意：
- 只输出下列 5 个数据 sheet，「说明」页必须排除
- 银饰账户 F 列有合并单元格，非首行读出来是 MergedCell → None（与历史数据一致）
- D 列日期统一成 MM/DD/YYYY；「待定」原样保留
"""
import openpyxl, json, sys, re
from openpyxl.cell.cell import MergedCell
from datetime import datetime, date

SHEET_ORDER = ["境外账户", "耳环账户", "银饰账户", "手链", "项链.戒指"]


def safe_read(cell):
    if isinstance(cell, MergedCell):
        return None
    return cell.value


def to_num(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    cleaned = s.replace('$', '').replace('£', '').replace('€', '').replace('¥', '').replace(',', '').replace(' ', '')
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except Exception:
        return s


def fmt_date(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime('%m/%d/%Y')
    if isinstance(val, date):
        return val.strftime('%m/%d/%Y')
    s = str(val).strip()
    if not s:
        return None
    # "9/5/2026" -> "09/05/2026"（与历史 dashboard 数据格式一致）
    m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m:
        return '%02d/%02d/%s' % (int(m.group(1)), int(m.group(2)), m.group(3))
    return s


def build(xlsx_path, pull_time):
    wb = openpyxl.load_workbook(xlsx_path)
    sheets = {}
    for sn in SHEET_ORDER:
        if sn not in wb.sheetnames:
            print(f"  ⚠️ 缺少 sheet: {sn}")
            continue
        ws = wb[sn]
        rows = []
        for r in range(2, ws.max_row + 1):
            a = safe_read(ws.cell(r, 1))
            b = safe_read(ws.cell(r, 2))
            c = safe_read(ws.cell(r, 3))
            d = safe_read(ws.cell(r, 4))
            e = safe_read(ws.cell(r, 5))
            f = safe_read(ws.cell(r, 6))
            if all(v is None for v in [a, b, c, d, e, f]):
                continue
            rows.append({
                'A': str(a).strip() if a is not None else '',
                'B': str(b).strip() if b is not None else '',
                'C': to_num(c),
                'D': fmt_date(d),
                'E': to_num(e),
                'F': to_num(f),
            })
        sheets[sn] = rows
    return {'pull_time': pull_time, 'sheets': sheets}


if __name__ == '__main__':
    xlsx = sys.argv[1]
    out = sys.argv[2]
    pt = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime('%Y-%m-%d %H:%M')
    data = build(xlsx, pt)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = sum(len(rows) for rows in data['sheets'].values())
    print(f"Wrote {out}: {len(data['sheets'])} sheets, {total} rows, pull_time={pt}")
    for sn, rows in data['sheets'].items():
        data_rows = sum(1 for r in rows if r['A'] != '合计')
        print(f"  [{sn}] {data_rows} 数据行 + 合计")
