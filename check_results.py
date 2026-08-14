import json

with open("exports/comai_buyability_results.json") as f:
    data = json.load(f)

for item in data[:5]:
    print(f"{item['company']}:")
    print(f"  Score: {item['buyability_score']}, Stage: {item['business_stage']}")
    print(f"  Chatbot: {item['chatbot_detected']}, WhatsApp: {item['whatsapp_detected']}")
    print(f"  Platform: {item['platform']}, Products: {item['product_count']}")
    print(f"  Founder: {item['founder_name']}, Email: {item['email']}")
    print(f"  Missing: {item['missing_signals']}")
    print()
