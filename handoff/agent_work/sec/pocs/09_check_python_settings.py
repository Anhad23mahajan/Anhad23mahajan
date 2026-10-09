import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd
df = pd.DataFrame({"a":[1]})
sql = "select * from query(replace('select * from duck#db_settings()', '#', ''))"
llm.guard(sql)
res = llm.run_sql(df, sql, timeout=5)
py_settings = res[res['name'].str.contains('python', case=False)]
print(py_settings[['name','value','description']].to_string())
