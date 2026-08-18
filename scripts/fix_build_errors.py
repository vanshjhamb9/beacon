import pathlib

p = pathlib.Path(r"C:\Inowix intelligence system\New folder\apps\dashboard\features\arie\arie-workspace.tsx")
c = p.read_text()

# Add sales_package to CompanyAnalysis interface
old = "  revenue_score: any;\n}"
new = "  revenue_score: any;\n  sales_package?: { why_this_company: string; pitch_angle: string; };\n}"
if "sales_package" not in c:
    c = c.replace(old, new, 1)

# Add activeTab state
old2 = "  const [icpProfiles, setIcpProfiles]"
new2 = '  const [activeTab, setActiveTab] = useState("icp");\n  const [icpProfiles, setIcpProfiles]'
if "activeTab" not in c:
    c = c.replace(old2, new2, 1)

# Fix defaultValue
c = c.replace('defaultValue="icp"', 'value={activeTab} onValueChange={setActiveTab}')

p.write_text(c)
print("Fixed arie-workspace type errors")
