import sys, os
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd
print("llm module loaded OK:", llm.__file__)
df = pd.DataFrame({"a":[1,2,3], "b":["x","y","z"]})
print(llm.guard("select 1"))
