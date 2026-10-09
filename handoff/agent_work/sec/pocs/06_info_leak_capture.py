import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd
df = pd.DataFrame({"a":[1]})

sql = "select * from query(replace('select * from duck#db_settings()', '#', ''))"
llm.guard(sql)
res = llm.run_sql(df, sql, timeout=5)
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_colwidth', 200)
interesting = res[res['name'].str.contains('dir|path|home|extension|memory|thread|temp|worker_thread|external|lock', case=False)]
print(interesting[['name','value']].to_string())
print()
print("total settings rows:", len(res))
