"""Build realistic mocked /api/ask payloads (shape = app/llm.py answer()).
The SQL is REAL: it is run (through the repo's own guard + DuckDB sandbox) on the real demo dataset, so numbers are true;
only the LLM prose ("answer", "caveats") is hand-written from those numbers.
Run (backend venv, no bytecode written into the repo):
  PYTHONDONTWRITEBYTECODE=1 /home/user/work/venv/bin/python -B -I /home/user/work/ui/scripts/build_mocks.py
"""
import sys, json, pathlib
sys.path.insert(0, '/home/user/Anhad23mahajan/lumen')
from app import analytics as A, llm
from app.analytics import clean

df = A.demo_df()
def run(sql):
    r = llm.run_sql(df, sql)
    return list(r.columns), clean(r.astype(object).where(r.notna(), None).values.tolist())

def mk(sql, chart, answer, caveats='', verified=True):
    cols, rows = run(sql)
    if chart.get('x') not in cols or chart.get('y') not in cols:
        chart = {'type': 'table'} if chart.get('type') != 'number' else chart
    return {'sql': sql, 'chart': chart, 'columns': cols, 'rows': rows, 'verified': verified, 'answer': answer, 'caveats': caveats}

M = {}
M['number'] = mk("SELECT SUM(amount) AS total_sales FROM data WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'",
                 {'type': 'number', 'x': 'total_sales', 'y': 'total_sales'}, 'Total sales in 2025 were 4,802,950.', '')
M['number-text'] = mk("SELECT product, SUM(amount) AS total_sales FROM data GROUP BY product ORDER BY total_sales DESC LIMIT 1",
                      {'type': 'number', 'x': 'product', 'y': 'total_sales'}, 'Hoodie is the best seller, with total sales of 6,195,600 (about 75% of everything sold).')
M['number-null'] = {'sql': "SELECT SUM(amount) AS total_sales FROM data WHERE region = 'Mars'", 'chart': {'type': 'number', 'x': 'total_sales', 'y': 'total_sales'},
                    'columns': ['total_sales'], 'rows': [[None]], 'verified': True, 'answer': 'There are no sales recorded for the Mars region.', 'caveats': ''}
M['bar'] = mk("SELECT product, SUM(amount) AS total_sales FROM data GROUP BY product ORDER BY total_sales DESC",
              {'type': 'bar', 'x': 'product', 'y': 'total_sales'}, 'Hoodie leads with 6,195,600 in sales, far ahead of Mug (800,700) and Tote bag (763,500). Sticker pack is the smallest at 112,980.')
M['line'] = mk("SELECT date_trunc('month', order_date) AS month, SUM(amount) AS total_sales FROM data GROUP BY 1 ORDER BY 1",
               {'type': 'line', 'x': 'month', 'y': 'total_sales'}, 'Monthly sales were lowest in August 2024 (166,260) and reached their highest point in December 2025 (622,160). Winters are consistently stronger than summers.')
M['pie'] = mk("SELECT region, SUM(amount) AS total_sales FROM data GROUP BY region ORDER BY total_sales DESC",
              {'type': 'pie', 'x': 'region', 'y': 'total_sales'}, 'Campus is the largest region at 2,867,900, followed by Online (2,535,100). North (1,656,220) and South (1,238,360) together make up about a third of sales.')
M['table'] = mk("SELECT order_date, product, region, quantity, unit_price, amount FROM data ORDER BY amount DESC, order_date LIMIT 10",
                {'type': 'table'}, 'These are the 10 largest single orders. Every one of them is a Hoodie order of 3 units at 900 each, worth 2,700.')
M['unverified'] = mk("SELECT region, AVG(amount) AS avg_order FROM data GROUP BY region ORDER BY avg_order DESC",
                     {'type': 'bar', 'x': 'region', 'y': 'avg_order'}, 'Campus has the highest average order line value (about 933), with South close behind (about 930).',
                     'The question did not say whether to average per order line or per day. This answer averages per order line.', verified=False)
M['unverified-number'] = {'sql': 'SELECT COUNT(*) AS n FROM data', 'chart': {'type': 'number', 'x': 'n', 'y': 'n'}, 'columns': ['n'], 'rows': [[9046]], 'verified': False,
                          'answer': 'There are 9,046 rows, but that may not be the number of customers you meant.', 'caveats': 'Rows are order lines, not unique customers.'}
long_ans = ('Across the whole of 2024 and 2025, sales were dominated by a single product (Hoodie), which accounted for roughly three quarters of revenue, '
            'while the remaining four products shared the rest. Within regions, Campus and Online led, with North and South noticeably behind. '
            'Seasonality is strong: December is the best month on average (about 560,000) and July the weakest (about 181,000). '
            'The single biggest day was 14 March 2025, with 115 order lines worth 105,030 against a typical day of about 20.')
long_sql = ("SELECT region, product, date_trunc('month', order_date) AS month, SUM(amount) AS total_sales_across_the_whole_period_for_this_region_and_product_combination, "
            "COUNT(*) AS number_of_order_lines_in_the_month, AVG(amount) AS average_order_line_value FROM data WHERE order_date >= '2024-01-01' GROUP BY 1, 2, 3 ORDER BY total_sales_across_the_whole_period_for_this_region_and_product_combination DESC LIMIT 12")
cols, rows = run(long_sql)
M['longtext'] = {'sql': long_sql, 'chart': {'type': 'table'}, 'columns': cols, 'rows': rows, 'verified': True, 'answer': long_ans,
                 'caveats': 'Months with fewer than five orders were included. The 14 March 2025 spike is treated as a real event, not a data-entry mistake. ' * 3}
M['long-unbroken-single'] = {'sql': 'SELECT donor FROM data LIMIT 1', 'chart': {'type': 'number', 'x': 'donor', 'y': 'donor'}, 'columns': ['donor'],
                             'rows': [['Brightfield-Foundation-for-Community-Education-and-Healthcare-Partnerships']], 'verified': True,
                             'answer': 'The largest donor was the Brightfield Foundation for Community Education and Healthcare Partnerships.', 'caveats': ''}
M['empty-rows-bar'] = {'sql': 'SELECT 1 WHERE false', 'chart': {'type': 'bar', 'x': 'a', 'y': 'b'}, 'columns': ['a', 'b'], 'rows': [], 'verified': True, 'answer': 'Nothing matched.', 'caveats': ''}
M['null-in-bar'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'region', 'y': 'total'}, 'columns': ['region', 'total'],
                    'rows': [['North', 1700000], [None, 900000], ['South', None], ['Online', 2500000]], 'verified': True, 'answer': 'Two regions have gaps.', 'caveats': ''}
M['negatives-bar'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'program', 'y': 'net'}, 'columns': ['program', 'net'],
                      'rows': [['Housing', -12500], ['Food', -8200], ['Youth', -3100], ['Legal', -400]], 'verified': True, 'answer': 'Every programme ran at a loss; Housing the most (-12,500).', 'caveats': ''}
M['mixed-negatives-bar'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'program', 'y': 'net'}, 'columns': ['program', 'net'],
                            'rows': [['Housing', 8400], ['Food', -8200], ['Youth', 3100], ['Legal', -400]], 'verified': True, 'answer': 'Housing is the biggest surplus; Food the biggest deficit.', 'caveats': ''}
M['long-labels-bar'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'program', 'y': 'total'}, 'columns': ['program', 'total'],
                        'rows': [[f'Operations / {n} programme and community partnerships fund', v] for n, v in
                                 [('Housing', 52000), ('Food security', 41000), ('Youth education', 33000), ('Elder care', 21000), ('Legal aid', 9000)]],
                        'verified': True, 'answer': 'Housing is the biggest programme.', 'caveats': ''}
M['pie-many'] = {'sql': 'SELECT ...', 'chart': {'type': 'pie', 'x': 'category', 'y': 'total'}, 'columns': ['category', 'total'],
                 'rows': [[f'Category {i:02d}', 900 - i * 25] for i in range(28)], 'verified': True, 'answer': 'Sales are spread across 28 categories.', 'caveats': ''}
M['pie-negative'] = {'sql': 'SELECT ...', 'chart': {'type': 'pie', 'x': 'k', 'y': 'v'}, 'columns': ['k', 'v'], 'rows': [['A', 50], ['B', -20], ['C', 30]], 'verified': True, 'answer': 'B is negative.', 'caveats': ''}
M['fiscal-years'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'fy', 'y': 'total'}, 'columns': ['fy', 'total'],
                     'rows': [['2023-24', 210000], ['2024-25', 340000], ['2025-26', 280000]], 'verified': True, 'answer': 'FY2024-25 was the best year.', 'caveats': ''}
M['date-single'] = {'sql': 'SELECT ...', 'chart': {'type': 'number', 'x': 'month', 'y': 'total'}, 'columns': ['month', 'total'],
                    'rows': [['2025-12-01T00:00:00', 622160]], 'verified': True, 'answer': 'December 2025 was the best month, with sales of 622,160.', 'caveats': ''}
M['number-huge'] = {'sql': 'SELECT ...', 'chart': {'type': 'number', 'x': 'n', 'y': 'n'}, 'columns': ['n'], 'rows': [[2548000000]], 'verified': True, 'answer': 'Total is 2.548 billion.', 'caveats': ''}
M['number-negative'] = {'sql': 'SELECT ...', 'chart': {'type': 'number', 'x': 'n', 'y': 'n'}, 'columns': ['n'], 'rows': [[-45210.5]], 'verified': True, 'answer': 'Net change is -45,210.5.', 'caveats': ''}
M['number-small'] = {'sql': 'SELECT ...', 'chart': {'type': 'number', 'x': 'n', 'y': 'n'}, 'columns': ['n'], 'rows': [[0.0536]], 'verified': True, 'answer': 'The average conversion rate is 5.36%.', 'caveats': ''}
M['bar-decimals'] = {'sql': 'SELECT ...', 'chart': {'type': 'bar', 'x': 'channel', 'y': 'rate'}, 'columns': ['channel', 'rate'],
                     'rows': [['Email', 0.0612], ['Search', 0.0547], ['Social', 0.0431], ['Referral', 0.0398]], 'verified': True, 'answer': 'Email converts best at 6.1%.', 'caveats': ''}
M['html-in-text'] = {'sql': "SELECT '<img src=x onerror=window.__xss=1>' AS a", 'chart': {'type': 'bar', 'x': 'a', 'y': 'b'}, 'columns': ['a', 'b'],
                     'rows': [["<img src=x onerror=window.__xss=1>", 5], ["O'Brien \"quoted\" <b>bold</b> & co", 3]], 'verified': True,
                     'answer': 'x <script>window.__xss=2</script> "y" \'z\' & <b>bold</b>', 'caveats': '<i>italic</i>'}
pathlib.Path('/home/user/work/ui/mocks.json').write_text(json.dumps(M, indent=1, ensure_ascii=False))
for k, v in M.items(): print(k, len(v['rows']), 'rows', v['chart'], [r for r in v['rows'][:2]])
