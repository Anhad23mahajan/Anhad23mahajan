import duckdb, os
D = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/duck"
os.chdir(D)
os.makedirs(D+"/allowed", exist_ok=True); open(D+"/allowed/ok.csv","w").write("a\n1\n")
try: os.symlink("/etc/hostname", D+"/allowed/link.csv")
except FileExistsError: pass
def q(con, sql):
    try: return "OK " + str(con.execute(sql).fetchall())[:50]
    except Exception as e: return type(e).__name__ + ": " + str(e).splitlines()[0][:90]
con = duckdb.connect(":memory:")
con.execute(f"SET allowed_directories=['{D}/allowed/']"); con.execute(f"SET allowed_paths=['{D}/secret.csv']")
con.execute("SET enable_external_access=false"); con.execute("SET lock_configuration=true")
print("allowed dir file      :", q(con, f"SELECT * FROM read_csv('{D}/allowed/ok.csv')"))
print("allowed path file     :", q(con, f"SELECT * FROM read_csv('{D}/secret.csv')"))
print("traversal via ..      :", q(con, f"SELECT * FROM read_csv('{D}/allowed/../secret.csv')"))
print("traversal out of dir  :", q(con, f"SELECT * FROM read_csv('{D}/allowed/../../../../../etc/hostname')"))
print("symlink inside allowed:", q(con, f"SELECT * FROM read_csv('{D}/allowed/link.csv')"))
print("glob in allowed dir   :", q(con, f"SELECT count(*) FROM glob('{D}/allowed/*')"))
print("settings: threads", q(duckdb.connect(), "SET threads=1"), "| http cache setting:", q(duckdb.connect(), "SET enable_http_metadata_cache=false"))
print("disabled_filesystems  :", end=" ")
c = duckdb.connect(":memory:"); print(q(c, "SET disabled_filesystems='LocalFileSystem'"), "->", q(c, f"SELECT * FROM read_csv('{D}/secret.csv')"))
c2 = duckdb.connect(":memory:"); c2.execute("SET disabled_filesystems='LocalFileSystem'"); 
print("  can still re-enable?  ", q(c2, "SET disabled_filesystems=''"))
