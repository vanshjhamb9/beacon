import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='beacon', user='beacon', password='beacon_password')
cur = conn.cursor()

# Clear child tables first
for table in ['fsw_lead_timeline', 'fsw_lead_tasks', 'fsw_lead_notes', 'fsw_lead_actions']:
    try:
        cur.execute(f"DELETE FROM {table}")
        print(f"Cleared {table}: {cur.rowcount}")
    except Exception as e:
        print(f"{table}: {e}")

# Now clear FSW leads
cur.execute("DELETE FROM fsw_lead_stages")
print(f"Cleared fsw_lead_stages: {cur.rowcount}")

conn.commit()
conn.close()
print("Done - old leads cleared")
