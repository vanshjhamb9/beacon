import psycopg2
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='beacon', user='beacon', password='beacon_password')
cur = conn.cursor()

# Total events
cur.execute('SELECT COUNT(*) FROM raw_events')
print('Total events:', cur.fetchone()[0])

# By source
cur.execute('SELECT source, COUNT(*) FROM raw_events GROUP BY source ORDER BY COUNT(*) DESC')
print('\nBy source:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# Check signal_tags distribution
cur.execute("SELECT metadata FROM raw_events WHERE source = 'reddit' LIMIT 10")
print('\nReddit metadata samples:')
for r in cur.fetchall():
    m = r[0] if isinstance(r[0], dict) else json.loads(r[0])
    tags = m.get('signal_tags', [])
    print(f'  tags: {tags}, author: {m.get("author", "?")}, subreddit: {m.get("subreddit", "?")}')

# Check for buying intent keywords in titles
cur.execute("SELECT title, source, url FROM raw_events WHERE source = 'reddit' LIMIT 20")
print('\nReddit titles:')
for r in cur.fetchall():
    print(f'  [{r[1]}] {r[0][:80]} -> {r[2][:60]}')

# Check Product Hunt
cur.execute("SELECT title, content, url FROM raw_events WHERE source = 'product_hunt' LIMIT 10")
print('\nProduct Hunt samples:')
for r in cur.fetchall():
    print(f'  {r[0][:60]} | {(r[1] or "")[:60]} | {r[2][:60]}')

# Check Hacker News
cur.execute("SELECT title, content, url FROM raw_events WHERE source = 'hacker_news' LIMIT 10")
print('\nHacker News samples:')
for r in cur.fetchall():
    print(f'  {r[0][:60]} | {(r[1] or "")[:60]} | {r[2][:60]}')

cur.close()
conn.close()
