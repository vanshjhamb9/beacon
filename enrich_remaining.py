"""Finish remaining leads + add 60 more to hit 200."""
import re, uuid, os
from urllib.parse import urlparse
import httpx
from sqlalchemy import create_engine, text

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
DISPOSABLE = {"tempmail.com","throwaway.email","guerrillamail.com","mailinator.com","yopmail.com","trashmail.com","10minutemail.com"}
FREE = {"gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com","icloud.com","mail.com","protonmail.com","rediffmail.com"}
GENERIC = {"support","info","hello","contact","admin","sales","help","feedback","enquiry","noreply","no-reply"}

# Remaining leads that timed out + 60 new leads to reach 200+
REMAINING = [
    ("Netmeds","https://netmeds.com","health","Pharma"),("Practo","https://practo.com","health","HealthTech"),
    ("Healthkart","https://healthkart.com","health","HealthTech"),("CureFit","https://cure.fit","health","HealthTech"),
    ("PhonePe","https://phonepe.com","fintech","Payments"),("Paytm","https://paytm.com","fintech","Payments"),
    ("Razorpay","https://razorpay.com","fintech","Payments"),("CRED","https://cred.club","fintech","Fintech"),
    ("PolicyBazaar","https://policybazaar.com","fintech","Insurance"),("Zerodha","https://zerodha.com","fintech","Brokerage"),
    ("Groww","https://groww.in","fintech","Investment"),("CarDekho","https://cardekho.com","automotive","AutoTech"),
    ("Cars24","https://cars24.com","automotive","AutoTech"),("Ola","https://olacabs.com","automotive","Mobility"),
    ("Delhivery","https://delhivery.com","logistics","Logistics"),("BlueDart","https://bluedart.com","logistics","Logistics"),
    ("Shiprocket","https://shiprocket.in","logistics","Logistics"),
    # 60 more leads to push past 200
    ("Nivea India","https://nivea.in","beauty","D2C"),("Forest Essentials","https://forestessentials.in","beauty","D2C"),
    ("Neemli Naturals","https://neemli.com","beauty","D2C"),("Spruce Shave Club","https://spruceshaveclub.com","beauty","D2C"),
    ("O3+","https://o3plus.com","beauty","D2C"),("TrueBrowns","https://truebrowns.com","fashion","D2C"),
    ("Forever21 India","https://forever21.in","fashion","D2C"),("Marks & Spencer India","https://marksandspencer.in","fashion","D2C"),
    ("Reliance Trends","https://reliancetrends.com","fashion","D2C"),("Intex","https://intex.in","electronics","D2C"),
    ("Xiaomi India","https://mi.com/in","electronics","D2C"),("OnePlus India","https://oneplus.com/in","electronics","D2C"),
    ("Realme India","https://realme.com/in","electronics","D2C"),("JBL India","https://jbl.co.in","electronics","D2C"),
    ("Hamleys India","https://hamleys.in","electronics","D2C"),("Kurla","https://kurlon.com","home","D2C"),
    ("Prestige","https://prestige.co.in","home","D2C"),("Milton","https://miltonhousewares.com","home","D2C"),
    ("Paper Boat","https://paperboatdrinks.com","food","D2C"),("ITC Master Chef","https://itchotels.com","food","D2C"),
    ("Brahmins","https://brahmins.com","food","D2C"),("Sattvik","https://sattvikfoods.com","food","D2C"),
    ("Madhusudan","https://madhusudan.com","food","D2C"),("Vijay Sales","https://vijaysales.com","quick_commerce","Marketplace"),
    ("Reliance Digital","https://reliancedigital.in","quick_commerce","Marketplace"),("Body Fit","https://bodyfit.in","fitness","Gym"),
    ("YogaFit India","https://yogafit.in","fitness","Gym"),("Mainland China","https://mainlandchina.com","restaurant","Casual Dining"),
    ("Bikano","https://bikano.com","restaurant","QSR"),("Bombay Brasserie","https://bombaybrasserie.com","restaurant","Casual Dining"),
    ("HairNSenses","https://hairnsenses.com","spa","Wellness"),("Skin Alive","https://skinalive.com","spa","Wellness"),
    ("NIIT","https://niit.com","education","EdTech"),("InterviewBit","https://interviewbit.com","education","EdTech"),
    ("Gradeup","https://gradeup.co","education","EdTech"),("Udemy India","https://udemy.com/in","education","EdTech"),
    ("Coursera India","https://coursera.org/in","education","EdTech"),("FabHotels","https://fabhotels.com","travel","OTA"),
    ("Vistara","https://airvistara.com","travel","Airline"),("IndiGo","https://goindigo.in","travel","Airline"),
    ("Air India","https://airindia.com","travel","Airline"),("Medlife","https://medlife.com","health","Pharma"),
    ("MFine","https://mfine.co","health","HealthTech"),("DocsApp","https://docsapp.in","health","HealthTech"),
    ("Upstox","https://upstox.com","fintech","Brokerage"),("WazirX","https://wazirx.com","fintech","Crypto"),
    ("Revolt Motors","https://revoltmotors.com","automotive","EV"),("Ecom Express","https://ecomexpress.in","logistics","Logistics"),
    ("Shadowfax","https://shadowfax.in","logistics","Logistics"),("Uber India","https://uber.com/in","automotive","Mobility"),
    ("Sennheiser India","https://sennheiser.com/in","electronics","D2C"),("Nike India","https://nike.com/in","fashion","D2C"),
    ("Adidas India","https://adidas.co.in","fashion","D2C"),("Puma India","https://puma.com/in","fashion","D2C"),
    ("Reebok India","https://reebok.com/in","fashion","D2C"),("Levi's India","https://levi.in","fashion","D2C"),
    ("H&M India","https://hm.com/in","fashion","D2C"),("Zara India","https://zara.com/in","fashion","D2C"),
    ("ASOS India","https://asos.com/in","fashion","D2C"),("Decathlon India","https://decathlon.in","fashion","D2C"),
    ("Myntra","https://myntra.com","fashion","D2C"),("Flipkart","https://flipkart.com","quick_commerce","Marketplace"),
]

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

def clean_email(e):
    e=e.lower().strip()
    d=e.split("@")[-1] if "@" in e else ""
    if d in DISPOSABLE or not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$",e): return None
    return e

def clean_phone(p):
    d=re.sub(r"[^\d]","",p)
    if d.startswith("91") and len(d)==12: d=d[2:]
    if len(d)==10 and d[0] in "6789": return f"+91{d}"
    return None

def scrape(client, url):
    emails,phones=set(),set()
    for p in [url, url.rstrip("/")+"/contact-us", url.rstrip("/")+"/contact"]:
        try:
            r=client.get(p,follow_redirects=True,timeout=3)
            if r.status_code==200:
                for e in EMAIL_RE.findall(r.text):
                    c=clean_email(e)
                    if c: emails.add(c)
                for ph in PHONE_RE.findall(r.text):
                    c=clean_phone(ph)
                    if c: phones.add(c)
                for m in re.findall(r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",r.text):
                    c=clean_email(m)
                    if c: emails.add(c)
                for t in re.findall(r"tel:([+0-9\s\-()]+)",r.text):
                    c=clean_phone(t)
                    if c: phones.add(c)
        except: pass
    spec=[e for e in emails if e.split("@")[0] not in GENERIC]
    if spec: emails=set(spec)
    corp=[e for e in emails if e.split("@")[-1] not in FREE]
    if corp: emails=set(corp)
    return list(emails)[:3],list(phones)[:2]

def main():
    db_url=os.getenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/beacon")
    engine=create_engine(db_url)
    
    # Get existing domains
    existing=set()
    with engine.begin() as conn:
        r=conn.execute(text("SELECT domain FROM ecommerce_leads WHERE deleted_at IS NULL"))
        for row in r: existing.add(row[0])
    print(f"Existing domains: {len(existing)}")

    # Filter new only
    new=[]
    for l in REMAINING:
        d=urlparse(l[1]).netloc.lower().replace("www.","")
        if d not in existing:
            existing.add(d)
            new.append(l)
    print(f"New leads to process: {len(new)}")

    with_email,with_phone,with_both=0,0,0
    with httpx.Client(headers=HEADERS,follow_redirects=True) as client:
        for i,(name,url,ind,cat) in enumerate(new):
            emails,phones=scrape(client,url)
            has_e,has_p=bool(emails),bool(phones)
            if has_e: with_email+=1
            if has_p: with_phone+=1
            if has_e and has_p: with_both+=1

            email=emails[0] if emails else ""
            phone=phones[0] if phones else ""
            pri="SALES_READY" if has_e and has_p else ("WARM_LEAD" if has_e or has_p else "LOW")
            sc=85 if has_e and has_p else (70 if has_e or has_p else 50)
            domain=urlparse(url).netloc.replace("www.","")
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO ecommerce_leads (id,created_at,updated_at,company_name,website,domain,platform,industry,category,country,city,state,description,product_count,estimated_size,social_links,instagram_url,facebook_url,linkedin_url,owner_name,founder_name,decision_maker_role,email,phone,contact_source,contact_confidence,shopify_detected,woocommerce_detected,magento_detected,chatbot_detected,whatsapp_detected,crm_detected,comai_score,lead_priority,sales_reason,pain_points,source)
                    VALUES (:id,NOW(),NOW(),:name,:url,:domain,'unknown',:ind,:cat,'India','','','Web scraped lead',0,'{}','{}','','','','','','',:email,:phone,'website_scrape',:conf,false,false,false,false,false,false,:sc,:pri,'','{}','enrichment')
                    ON CONFLICT (domain) DO UPDATE SET email=EXCLUDED.email, phone=EXCLUDED.phone, comai_score=EXCLUDED.comai_score, lead_priority=EXCLUDED.lead_priority, updated_at=NOW()
                """),{"id":str(uuid.uuid4()),"name":name,"url":url,"domain":domain,"ind":ind,"cat":cat,"email":email,"phone":phone,"conf":0.8 if has_e and has_p else 0.5,"sc":sc,"pri":pri})

            mark="OK" if has_e or has_p else "---"
            print(f"[{i+1:3d}/{len(new)}] {name:30s} E:{len(emails)} P:{len(phones)} {mark}",flush=True)

    print(f"\nBatch done: Email:{with_email} Phone:{with_phone} Both:{with_both}")

    # Final count
    with engine.begin() as conn:
        r=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL"))
        total=r.scalar()
        r2=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')"))
        enriched=r2.scalar()
        print(f"\nFINAL: {total} total leads, {enriched} with email+phone")

if __name__=="__main__":
    main()
