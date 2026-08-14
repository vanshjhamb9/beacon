"""Synchronous fast enrichment — 3s timeout, direct DB writes, no async overhead."""
import re, uuid, os, time
from urllib.parse import urlparse
import httpx
from sqlalchemy import create_engine, text

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
DISPOSABLE = {"tempmail.com","throwaway.email","guerrillamail.com","mailinator.com","yopmail.com","trashmail.com","10minutemail.com"}
FREE = {"gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com","icloud.com","mail.com","protonmail.com","rediffmail.com"}
GENERIC = {"support","info","hello","contact","admin","sales","help","feedback","enquiry","noreply","no-reply"}

LEADS = [
    ("Mamaearth","https://mamaearth.in","beauty","D2C"),("Beardo","https://thebeardoilclub.com","beauty","D2C"),
    ("mCaffeine","https://mcaffeine.com","beauty","D2C"),("Sugar Cosmetics","https://sugarcosmetics.com","beauty","D2C"),
    ("Plum Goodness","https://plumgoodness.com","beauty","D2C"),("WOW Skin Science","https://wowskinscience.com","beauty","D2C"),
    ("Bombay Shaving Company","https://bombayshavingcompany.com","beauty","D2C"),("The Man Company","https://themancompany.com","beauty","D2C"),
    ("Juicy Chemistry","https://juicychemistry.com","beauty","D2C"),("Pilgrim","https://pilgrim.in","beauty","D2C"),
    ("Derma Co","https://dermaco.in","beauty","D2C"),("Minimalist","https://minimalist.ind.in","beauty","D2C"),
    ("Dot Key","https://dotkey.in","beauty","D2C"),("Chemist at Play","https://chemistatplay.com","beauty","D2C"),
    ("Lakme","https://lakmeindia.com","beauty","D2C"),("Biotique","https://biotique.com","beauty","D2C"),
    ("Himalaya Wellness","https://himalayawellness.in","beauty","D2C"),("Nivea India","https://nivea.in","beauty","D2C"),
    ("Good Vibes","https://goodvibes.co.in","beauty","D2C"),("Arata","https://arata.in","beauty","D2C"),
    ("Ustraa","https://ustraa.com","beauty","D2C"),("Vahdam Teas","https://vahdamteas.com","beauty","D2C"),
    ("Berrylush","https://berrylush.com","fashion","D2C"),("Libas","https://libas.in","fashion","D2C"),
    ("Snitch","https://snitch.co.in","fashion","D2C"),("Bewakoof","https://bewakoof.com","fashion","D2C"),
    ("The Souled Store","https://thesouledstore.com","fashion","D2C"),("Fabindia","https://fabindia.com","fashion","D2C"),
    ("Nicobar","https://nicobar.com","fashion","D2C"),("Jaypore","https://jaypore.com","fashion","D2C"),
    ("Okhai","https://okhai.org","fashion","D2C"),("FableStreet","https://fablestreet.com","fashion","D2C"),
    ("Bhaane","https://bhaane.com","fashion","D2C"),("Andamen","https://andamen.com","fashion","D2C"),
    ("Nush","https://nush.in","fashion","D2C"),("Allen Solly","https://allensolly.com","fashion","D2C"),
    ("Peter England","https://peterengland.com","fashion","D2C"),("Van Heusen","https://vanheusen.com","fashion","D2C"),
    ("Louis Philippe","https://louisphilippe.com","fashion","D2C"),("Pantaloons","https://pantaloons.com","fashion","D2C"),
    ("Westside","https://westside.com","fashion","D2C"),("Max Fashion","https://maxfashion.com","fashion","D2C"),
    ("boAt","https://boatrocks.com","electronics","D2C"),("Noise","https://gonoise.com","electronics","D2C"),
    ("Fire-Boltt","https://fireboltt.com","electronics","D2C"),("pTron","https://ptron.in","electronics","D2C"),
    ("Ambrane","https://ambraneindia.com","electronics","D2C"),("Syska","https://syska.com","electronics","D2C"),
    ("Zebronics","https://zebronics.com","electronics","D2C"),("Croma","https://croma.com","electronics","D2C"),
    ("Pepperfry","https://pepperfry.com","home","D2C"),("Urban Ladder","https://urbanladder.com","home","D2C"),
    ("HomeCentre","https://homecentre.com","home","D2C"),("Godrej Interio","https://godrejinterio.com","home","D2C"),
    ("Address Home","https://addresshome.com","home","D2C"),("WoodenStreet","https://woodenstreet.com","home","D2C"),
    ("Durian","https://durian.in","home","D2C"),("Nilkamal","https://nilkamal.com","home","D2C"),
    ("Wakefit","https://wakefit.co","home","D2C"),("Sleepwell","https://sleepwell.in","home","D2C"),
    ("Roastea","https://roastea.com","food","D2C"),("Sleepy Owl","https://sleepyowl.co","food","D2C"),
    ("Blue Tokai","https://bluetokai.com","food","D2C"),("Raw Pressery","https://rawpressery.com","food","D2C"),
    ("Yoga Bar","https://yogabar.in","food","D2C"),("True Elements","https://trueelements.com","food","D2C"),
    ("Slurrp Farm","https://slurrpfarm.com","food","D2C"),("Licious","https://licious.in","food","D2C"),
    ("FreshToHome","https://freshtohome.com","food","D2C"),("iD Fresh Food","https://idfreshfood.com","food","D2C"),
    ("Zepto","https://zepto.in","quick_commerce","Marketplace"),("Blinkit","https://blinkit.com","quick_commerce","Marketplace"),
    ("DMart","https://dmart.in","quick_commerce","Marketplace"),("Tata CLiQ","https://tatacliq.com","quick_commerce","Marketplace"),
    ("Nykaa","https://nykaa.com","quick_commerce","Marketplace"),("Purplle","https://purplle.com","quick_commerce","Marketplace"),
    ("FirstCry","https://firstcry.com","quick_commerce","Marketplace"),("CraftsVilla","https://craftsvilla.com","quick_commerce","Marketplace"),
    ("Cult.fit","https://cult.fit","fitness","Gym"),("Gold's Gym India","https://goldsgym.in","fitness","Gym"),
    ("Fitness First India","https://fitnessfirst.co.in","fitness","Gym"),("Anytime Fitness India","https://anytimefitness.co.in","fitness","Gym"),
    ("Snap Fitness India","https://snapfitness.com/in","fitness","Gym"),("Talwalkars","https://talwalkars.com","fitness","Gym"),
    ("F45 India","https://f45training.in","fitness","Gym"),("The Quad Fitness","https://thequadfitness.com","fitness","Gym"),
    ("Iron Fitness","https://ironfitness.in","fitness","Gym"),("Power World Gym","https://powerworldgym.com","fitness","Gym"),
    ("Fitness One","https://fitnessone.in","fitness","Gym"),("CrossFit India","https://crossfit.in","fitness","Gym"),
    ("Raw Gym","https://rawgym.in","fitness","Gym"),("Transform Fitness","https://transformfitness.in","fitness","Gym"),
    ("Core Fitness","https://corefitness.in","fitness","Gym"),
    ("Barbeque Nation","https://barbequenation.com","restaurant","Casual Dining"),("Theobroma","https://theobroma.in","restaurant","Bakery"),
    ("Haldiram's","https://haldirams.com","restaurant","QSR"),("Wow! Momo","https://wowmomo.com","restaurant","QSR"),
    ("Chai Point","https://chaipoint.com","restaurant","QSR"),("Sagar Ratna","https://sagarratna.com","restaurant","Casual Dining"),
    ("O2 Spa","https://o2spa.com","spa","Wellness"),("Tattva Spa","https://tattvaspa.com","spa","Wellness"),
    ("Kaya Skin Clinic","https://kayaskinclinic.com","spa","Wellness"),("VLCC","https://vlcc.com","spa","Wellness"),
    ("Oliva Clinic","https://olivaclinic.com","spa","Wellness"),("Berkowits","https://berkowits.in","spa","Wellness"),
    ("Byju's","https://byjus.com","education","EdTech"),("Unacademy","https://unacademy.com","education","EdTech"),
    ("Vedantu","https://vedantu.com","education","EdTech"),("Physics Wallah","https://physicswallah.com","education","EdTech"),
    ("Great Learning","https://greatlearning.in","education","EdTech"),("Simplilearn","https://simplilearn.com","education","EdTech"),
    ("upGrad","https://upgrad.com","education","EdTech"),("Coding Ninjas","https://codingninjas.com","education","EdTech"),
    ("Scaler","https://scaler.com","education","EdTech"),("Testbook","https://testbook.com","education","EdTech"),
    ("MakeMyTrip","https://makemytrip.com","travel","OTA"),("Goibibo","https://goibibo.com","travel","OTA"),
    ("Yatra","https://yatra.com","travel","OTA"),("Cleartrip","https://cleartrip.com","travel","OTA"),
    ("OYO","https://oyorooms.com","travel","OTA"),("Treebo","https://treebohotels.com","travel","OTA"),
    ("1mg","https://1mg.com","health","Pharma"),("PharmEasy","https://pharmeasy.in","health","Pharma"),
    ("Netmeds","https://netmeds.com","health","Pharma"),("Practo","https://practo.com","health","HealthTech"),
    ("Healthkart","https://healthkart.com","health","HealthTech"),("CureFit","https://cure.fit","health","HealthTech"),
    ("PhonePe","https://phonepe.com","fintech","Payments"),("Paytm","https://paytm.com","fintech","Payments"),
    ("Razorpay","https://razorpay.com","fintech","Payments"),("CRED","https://cred.club","fintech","Fintech"),
    ("PolicyBazaar","https://policybazaar.com","fintech","Insurance"),("Zerodha","https://zerodha.com","fintech","Brokerage"),
    ("Groww","https://groww.in","fintech","Investment"),("CarDekho","https://cardekho.com","automotive","AutoTech"),
    ("Cars24","https://cars24.com","automotive","AutoTech"),("Ola","https://olacabs.com","automotive","Mobility"),
    ("Delhivery","https://delhivery.com","logistics","Logistics"),("BlueDart","https://bluedart.com","logistics","Logistics"),
    ("Shiprocket","https://shiprocket.in","logistics","Logistics"),
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

    # Dedup
    seen=set()
    unique=[]
    for l in LEADS:
        d=urlparse(l[1]).netloc.lower().replace("www.","")
        if d not in seen:
            seen.add(d)
            unique.append(l)
    print(f"Unique leads: {len(unique)}")

    enriched,with_email,with_phone,with_both=[],0,0,0

    with httpx.Client(headers=HEADERS,follow_redirects=True) as client:
        for i,(name,url,ind,cat) in enumerate(unique):
            emails,phones=scrape(client,url)
            has_e,has_p=bool(emails),bool(phones)
            if has_e: with_email+=1
            if has_p: with_phone+=1
            if has_e and has_p: with_both+=1

            enriched.append({"name":name,"url":url,"ind":ind,"cat":cat,"emails":emails,"phones":phones})

            if emails or phones:
                email=emails[0] if emails else ""
                phone=phones[0] if phones else ""
                pri="SALES_READY" if has_e and has_p else ("WARM_LEAD" if has_e or has_p else "LOW")
                sc=85 if has_e and has_p else (70 if has_e or has_p else 50)
                domain=urlparse(url).netloc.replace("www.","")
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO ecommerce_leads (id,created_at,updated_at,company_name,website,domain,platform,industry,category,country,city,state,description,product_count,estimated_size,social_links,instagram_url,facebook_url,linkedin_url,owner_name,founder_name,decision_maker_role,email,phone,contact_source,contact_confidence,shopify_detected,woocommerce_detected,magento_detected,chatbot_detected,whatsapp_detected,crm_detected,comai_score,lead_priority,sales_reason,pain_points,source)
                        VALUES (:id,NOW(),NOW(),:name,:url,:domain,'unknown',:ind,:cat,'India','','','Web scraped lead',0,'{}','{}','','','','','','',:email,:phone,'website_scrape',:conf,false,false,false,false,false,false,:sc,:pri,'','{}','enrichment')
                        ON CONFLICT (domain) DO UPDATE SET email=EXCLUDED.email, phone=EXCLUDED.phone, comai_score=EXCLUDED.comai_score, lead_priority=EXCLUDED.lead_priority, contact_source=EXCLUDED.contact_source, contact_confidence=EXCLUDED.contact_confidence, updated_at=NOW()
                    """),{"id":str(uuid.uuid4()),"name":name,"url":url,"domain":domain,"ind":ind,"cat":cat,"email":email,"phone":phone,"conf":0.8 if has_e and has_p else 0.5,"sc":sc,"pri":pri})

            mark="OK" if has_e or has_p else "---"
            print(f"[{i+1:3d}/{len(unique)}] {name:30s} E:{len(emails)} P:{len(phones)} {mark}",flush=True)

    print(f"\n{'='*60}")
    print(f"DONE: {len(unique)} leads | Email:{with_email} Phone:{with_phone} Both:{with_both}")
    print(f"{'='*60}")

if __name__=="__main__":
    main()
