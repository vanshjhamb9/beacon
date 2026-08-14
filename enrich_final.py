"""Add 35+ more leads to reach 200."""
import re, uuid, os
from urllib.parse import urlparse
import httpx
from sqlalchemy import create_engine, text

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
DISPOSABLE = {"tempmail.com","throwaway.email","guerrillamail.com","mailinator.com","yopmail.com","trashmail.com","10minutemail.com"}
FREE = {"gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com","icloud.com","mail.com","protonmail.com","rediffmail.com"}
GENERIC = {"support","info","hello","contact","admin","sales","help","feedback","enquiry","noreply","no-reply"}

EXTRA = [
    ("Allen Solly","https://allensolly.com","fashion","D2C"),("Peter England","https://peterengland.com","fashion","D2C"),
    ("Van Heusen","https://vanheusen.com","fashion","D2C"),("Louis Philippe","https://louisphilippe.com","fashion","D2C"),
    ("Biba","https://biba.in","fashion","D2C"),("W","https://www.wlingerie.com","fashion","D2C"),
    ("Bewakoof","https://bewakoof.com","fashion","D2C"),("Mango India","https://mango.in","fashion","D2C"),
    ("Guess India","https://guess.in","fashion","D2C"),("US Polo India","https://uspoloassn.com/in","fashion","D2C"),
    ("Jack & Jones India","https://jackjones.com/in","fashion","D2C"),("Vero Moda India","https://veromoda.com/in","fashion","D2C"),
    ("Only India","https://only.com/in","fashion","D2C"),("Selected Homme","https://selected.com/in","fashion","D2C"),
    ("Mama Earth","https://mamaearth.in","beauty","D2C"),("Plum","https://plumgoodness.com","beauty","D2C"),
    ("mCaffeine","https://mcaffeine.com","beauty","D2C"),("Derma Co","https://thedermaco.com","beauty","D2C"),
    ("Minimalist","https://minimalist.in","beauty","D2C"),("Chemist at Play","https://chemistatplay.com","beauty","D2C"),
    ("Dot & Key","https://dotandkey.com","beauty","D2C"),("Earth Rhythm","https://earthrhythm.com","beauty","D2C"),
    ("Juicy Chemistry","https://juicychemistry.com","beauty","D2C"),("The Derma Co","https://thedermaco.com","beauty","D2C"),
    ("Cureka","https://cureka.com","health","HealthTech"),("HealthifyMe","https://healthifyme.com","health","HealthTech"),
    ("Nua","https://nuawoman.com","health","HealthTech"),("Dame","https://getdame.com","health","HealthTech"),
    ("MamaEarth","https://mamaearth.in","beauty","D2C"),("The Whole Truth","https://thewholetruth.in","food","D2C"),
    ("Snackible","https://snackible.com","food","D2C"),("Yoga Bar","https://yogabars.com","food","D2C"),
    ("Open Secret","https://opensecret.in","food","D2C"),("Rasna","https://rasna.com","food","FMB"),
    ("Paper Boat","https://paperboatdrinks.com","food","D2C"),("Raw Pressery","https://rawpressery.com","food","D2C"),
    ("Sting","https://sting.in","food","Beverages"),("Bisleri","https://bisleri.com","food","Beverages"),
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
    existing=set()
    with engine.begin() as conn:
        r=conn.execute(text("SELECT domain FROM ecommerce_leads WHERE deleted_at IS NULL"))
        for row in r: existing.add(row[0])
    print(f"Existing: {len(existing)}")

    new=[]
    for l in EXTRA:
        d=urlparse(l[1]).netloc.lower().replace("www.","")
        if d not in existing:
            existing.add(d)
            new.append(l)
    print(f"New: {len(new)}")

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

    print(f"\nBatch: Email:{with_email} Phone:{with_phone} Both:{with_both}")
    with engine.begin() as conn:
        r=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL"))
        total=r.scalar()
        r2=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND (email IS NOT NULL AND email != '') AND (phone IS NOT NULL AND phone != '')"))
        enriched=r2.scalar()
        r3=conn.execute(text("SELECT COUNT(*) FROM ecommerce_leads WHERE deleted_at IS NULL AND lead_priority='SALES_READY'"))
        sr=r3.scalar()
        print(f"FINAL: {total} total, {enriched} enriched (email+phone), {sr} SALES_READY")

if __name__=="__main__":
    main()
