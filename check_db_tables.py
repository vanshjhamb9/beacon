import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='beacon', user='beacon', password='beacon_password')
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
relevant = [t for t in tables if any(k in t for k in ['ofc', 'lead', 'opportunity', 'first', 'campaign', 'company'])]
print('Relevant tables:', relevant)

for table in relevant[:10]:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cur.fetchone()[0]
        if count > 0:
            print(f'\n{table}: {count} rows')
            cur.execute(f'SELECT * FROM "{table}" LIMIT 1')
            cols = [d[0] for d in cur.description]
            print(f'  Columns: {cols[:15]}')
    except Exception as e:
        print(f'{table}: error - {e}')

conn.close()
