import duckdb, pandas as pd
mydf = pd.DataFrame({"x":[1,2,3]})
print("vars has mydf:", 'mydf' in globals())
try:
    print(duckdb.sql("select * from mydf"))
except Exception as e:
    print("FAIL duckdb.sql:", type(e).__name__, e)

try:
    print(duckdb.execute("select * from mydf").df())
except Exception as e:
    print("FAIL duckdb.execute:", type(e).__name__, e)

def f():
    localdf = pd.DataFrame({"y":[9,9]})
    try:
        print(duckdb.sql("select * from localdf"))
    except Exception as e:
        print("FAIL local duckdb.sql:", type(e).__name__, e)
f()
