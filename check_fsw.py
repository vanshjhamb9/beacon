import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='beacon', user='beacon', password='beacon_password')
cur = conn.cursor()

# Check fsw_lead_stages columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'fsw_lead_stages' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print('fsw_lead_stages columns:', cols)

cur.execute("SELECT * FROM fsw_lead_stages ORDER BY created_at DESC LIMIT 5")
col_names = [d[0] for d in cur.description]
for row in cur.fetchall():
    print(dict(zip(col_names, row)))

conn.close()
