import pathlib

p = pathlib.Path(r"C:\Inowix intelligence system\New folder\apps\dashboard\features\arie\arie-workspace.tsx")
lines = p.read_text().splitlines(keepends=True)

for i, line in enumerate(lines):
    if "const [icpProfiles" in line:
        lines.insert(i, '  const [activeTab, setActiveTab] = useState("icp");\n')
        break

p.write_text("".join(lines))
print("Added activeTab state")
