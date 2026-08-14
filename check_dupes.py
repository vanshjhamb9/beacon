import re, os

tables = {}
for root, dirs, files in os.walk("apps/api/app/models"):
    for f in files:
        if f.endswith(".py") and f != "__init__.py" and f != "base.py":
            path = os.path.join(root, f)
            content = open(path).read()
            for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', content):
                name = m.group(1)
                if name in tables:
                    print(f"DUPLICATE: {name} in {tables[name]} AND {path}")
                else:
                    tables[name] = path
