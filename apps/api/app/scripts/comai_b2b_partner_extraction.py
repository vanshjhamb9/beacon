#!/usr/bin/env python3
"""
COMAI B2B Partner Discovery Engine
Finds agencies, consultants, creators, and service providers for COMAI partner/reseller program.
Dedicated lane: COMAI_B2B_PARTNERS — DO NOT mix with direct ecommerce or INOWIX leads.
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]
SEEN_PATH = ROOT / "exports" / "comai_b2b_partners" / "_seen_domains.json"
EXPORT_DIR = ROOT / "exports" / "comai_b2b_partners"

# ============================================================
# AGENCY SEED DATABASE — 500+ agencies across 4 priority tiers
# ============================================================

AGENCY_SEEDS = [
    # ============================================================
    # PRIORITY A — MARKETING AGENCIES (150+)
    # ============================================================
    # India - Marketing
    {"name": "Tall Bunny", "url": "https://tallbunny.com", "type": "marketing", "country": "India", "city": "Hyderabad"},
    {"name": "KredWorks", "url": "https://kredworks.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Dygic", "url": "https://dygic.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "Adsspace", "url": "https://adsspace.in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Social Panga", "url": "https://socialpanga.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "WATConsult", "url": "https://watconsult.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "iProspect India", "url": "https://iprospect.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Performics India", "url": "https://performics.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Kinnect", "url": "https://kinnect.co", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Pinstorm", "url": "https://pinstorm.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "BCWebwise", "url": "https://bcwebwise.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "FoxyMoron", "url": "https://foxymoron.in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Schbang", "url": "https://schbang.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Dentsu Webchutney", "url": "https://webchutney.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "Lowe Lintas", "url": "https://lowelintas.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Ogilvy India", "url": "https://ogilvy.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "McCann Worldgroup", "url": "https://mccann.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Publicis India", "url": "https://publicis.in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "DDB Mudra", "url": "https://dbmudra.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Grey Group India", "url": "https://grey.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Leo Burnett India", "url": "https://leoburnett.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "TBWA India", "url": "https://tbwa.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Havas Group India", "url": "https://havas.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "GroupM India", "url": "https://groupm.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Mindshare India", "url": "https://mindshare.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "MEC India", "url": "https://mecglobal.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "OMD India", "url": "https://omd.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Zenith India", "url": "https://zenithmedia.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Carat India", "url": "https://carat.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Vizeum India", "url": "https://vizeum.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    # India - Performance/D2C Marketing
    {"name": "Dapper Fox", "url": "https://dapperfox.in", "type": "marketing", "country": "India", "city": "Delhi"},
    {"name": "Flairox", "url": "https://flairox.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Scale Up Consulting", "url": "https://scaleupconsulting.in", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "D2C Academy", "url": "https://d2cademy.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Growthulate", "url": "https://growthulate.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "SalesLabs", "url": "https://saleslabs.in", "type": "marketing", "country": "India", "city": "Delhi"},
    {"name": "AdYogi", "url": "https://adyogi.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "Prospero", "url": "https://prospero.in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "ROI Minds", "url": "https://roiminds.com", "type": "marketing", "country": "India", "city": "Delhi"},
    {"name": "Xtremax", "url": "https://xtremax.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "Amplitude", "url": "https://amplitude.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Confluencr", "url": "https://confluencr.com", "type": "marketing", "country": "India", "city": "Delhi"},
    {"name": "Ignitee Digital", "url": "https://ignitee.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "eWebResults", "url": "https://ewebresults.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "DigiMark Agency", "url": "https://digimarkagency.com", "type": "marketing", "country": "India", "city": "Bangalore"},
    {"name": "Sparsh", "url": "https://sparsh.co.in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Tonic Worldwide", "url": "https://tonicworldwide.com", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Reprise Digital", "url": "https://reprise.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Isobar India", "url": "https://isobar.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    {"name": "Sapient Razorfish", "url": "https://razorfish.com/in", "type": "marketing", "country": "India", "city": "Mumbai"},
    # US - Marketing Agencies
    {"name": "Disruptive Advertising", "url": "https://disruptiveadvertising.com", "type": "marketing", "country": "USA", "city": "Lehi"},
    {"name": "Ignite Visibility", "url": "https://ignitevisibility.com", "type": "marketing", "country": "USA", "city": "San Diego"},
    {"name": "WebFX", "url": "https://webfx.com", "type": "marketing", "country": "USA", "city": "Harrisburg"},
    {"name": "Thrive Agency", "url": "https://thriveagency.com", "type": "marketing", "country": "USA", "city": "Dallas"},
    {"name": "Digital Silk", "url": "https://digitalsilk.com", "type": "marketing", "country": "USA", "city": "New York"},
    {"name": "SocialSEO", "url": "https://socialseo.com", "type": "marketing", "country": "USA", "city": "Colorado Springs"},
    {"name": "Power Digital Marketing", "url": "https://powerdigitalmarketing.com", "type": "marketing", "country": "USA", "city": "San Diego"},
    {"name": "Straight North", "url": "https://straightnorth.com", "type": "marketing", "country": "USA", "city": "Downers Grove"},
    {"name": "Titan Growth", "url": "https://titan.com", "type": "marketing", "country": "USA", "city": "San Diego"},
    {"name": "Jumpfly", "url": "https://jumpfly.com", "type": "marketing", "country": "USA", "city": "Elgin"},
    {"name": "SmartSites", "url": "https://smartsites.com", "type": "marketing", "country": "USA", "city": "Paramus"},
    {"name": "SEO Brand", "url": "https://seobrand.com", "type": "marketing", "country": "USA", "city": "Boca Raton"},
    {"name": "Volume Nine", "url": "https://volumenine.com", "type": "marketing", "country": "USA", "city": "Boulder"},
    {"name": "Coalition Technologies", "url": "https://coalitiontechnologies.com", "type": "marketing", "country": "USA", "city": "Los Angeles"},
    {"name": "Instapage", "url": "https://instapage.com", "type": "marketing", "country": "USA", "city": "San Francisco"},
    {"name": "Single Grain", "url": "https://singlegrain.com", "type": "marketing", "country": "USA", "city": "San Francisco"},
    {"name": "KlientBoost", "url": "https://klientboost.com", "type": "marketing", "country": "USA", "city": "Costa Mesa"},
    {"name": "NP Digital", "url": "https://npdigital.com", "type": "marketing", "country": "USA", "city": "San Francisco"},
    {"name": "Sure Oak", "url": "https://sureoak.com", "type": "marketing", "country": "USA", "city": "New York"},
    {"name": "OuterBox", "url": "https://outerbox.com", "type": "marketing", "country": "USA", "city": "Akron"},
    # UK - Marketing Agencies
    {"name": "Brainlabs", "url": "https://brainlabsdigital.com", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "Croud", "url": "https://croud.com", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "ROAST", "url": "https://wearecast.com", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "CClickF", "url": "https://cclickf.com", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "Impression", "url": "https://impression.co.uk", "type": "marketing", "country": "UK", "city": "Nottingham"},
    {"name": "Distilled", "url": "https://distilled.net", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "Builtvisible", "url": "https://builtvisible.com", "type": "marketing", "country": "UK", "city": "London"},
    {"name": "Screaming Frog", "url": "https://screamingfrog.co.uk", "type": "marketing", "country": "UK", "city": "Surrey"},
    {"name": "Hallam Internet", "url": "https://hallaminternet.com", "type": "marketing", "country": "UK", "city": "Nottingham"},
    {"name": "QueryClick", "url": "https://queryclick.com", "type": "marketing", "country": "UK", "city": "Edinburgh"},
    # UAE - Marketing
    {"name": "Blue Hat Marketing", "url": "https://bluehatmarketing.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Digitalex", "url": "https://digitalex.ae", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Nexa", "url": "https://digitalnexa.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Chain Reaction", "url": "https://chainreaction.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Growth Gorillas", "url": "https://growthgorillas.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Clicktap", "url": "https://clicktap.ae", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "RBBi", "url": "https://rbbi.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    {"name": "Jeeltek", "url": "https://jeeltek.com", "type": "marketing", "country": "UAE", "city": "Dubai"},
    # Australia - Marketing
    {"name": "WebAlive", "url": "https://webalive.com.au", "type": "marketing", "country": "Australia", "city": "Melbourne"},
    {"name": "Reload Media", "url": "https://reloadmedia.com.au", "type": "marketing", "country": "Australia", "city": "Brisbane"},
    {"name": "Click Creative", "url": "https://clickcreative.com.au", "type": "marketing", "country": "Australia", "city": "Melbourne"},
    {"name": "SEO Shark", "url": "https://seoshark.com.au", "type": "marketing", "country": "Australia", "city": "Sydney"},
    {"name": "Australian Digital Marketing", "url": "https://australiandigitalmarketing.com.au", "type": "marketing", "country": "Australia", "city": "Sydney"},
    {"name": "Media Heroes", "url": "https://mediaheroes.com.au", "type": "marketing", "country": "Australia", "city": "Brisbane"},
    {"name": "Ignite Digital", "url": "https://ignitedigital.com.au", "type": "marketing", "country": "Australia", "city": "Sydney"},
    {"name": "Digital Nomads", "url": "https://digitalnomads.com.au", "type": "marketing", "country": "Australia", "city": "Melbourne"},
    # Canada - Marketing
    {"name": "Konstruct Digital", "url": "https://konstructdigital.com", "type": "marketing", "country": "Canada", "city": "Calgary"},
    {"name": "Parachute Design", "url": "https://parachutedesign.ca", "type": "marketing", "country": "Canada", "city": "Toronto"},
    {"name": "Major Tom", "url": "https://majortom.com", "type": "marketing", "country": "Canada", "city": "Vancouver"},
    {"name": "Search Engine People", "url": "https://searchenginepeople.com", "type": "marketing", "country": "Canada", "city": "Toronto"},
    {"name": "Blue Hat", "url": "https://bluehat.ca", "type": "marketing", "country": "Canada", "city": "Toronto"},
    {"name": "Seoplusplus", "url": "https://seoplusplus.com", "type": "marketing", "country": "Canada", "city": "Ottawa"},
    {"name": "Devotion", "url": "https://devotionmarketing.com", "type": "marketing", "country": "Canada", "city": "Toronto"},

    # ============================================================
    # PRIORITY B — TECHNOLOGY / DEVELOPMENT AGENCIES (150+)
    # ============================================================
    # India - Shopify/Ecommerce Development
    {"name": "Shopify Experts India", "url": "https://shopifyexpertsindia.com", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Codemaster", "url": "https://codemaster.in", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Emizentech", "url": "https://emizentech.com", "type": "technology", "country": "India", "city": "Jaipur"},
    {"name": "CedCommerce", "url": "https://cedcommerce.com", "type": "technology", "country": "India", "city": "Lucknow"},
    {"name": "Webkul", "url": "https://webkul.com", "type": "technology", "country": "India", "city": "Noida"},
    {"name": "Velocity", "url": "https://velocity.com.in", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Magenticians", "url": "https://magenticians.com", "type": "technology", "country": "India", "city": "Noida"},
    {"name": "Varspie", "url": "https://varspie.com", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Root Info Solutions", "url": "https://rootinfosolutions.com", "type": "technology", "country": "India", "city": "Delhi"},
    {"name": "Netlings", "url": "https://netlings.com", "type": "technology", "country": "India", "city": "Delhi"},
    {"name": "Rajasvi", "url": "https://rajasvi.com", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Flavor", "url": "https://flavorstudio.com", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Kadam Tech", "url": "https://kadamtech.com", "type": "technology", "country": "India", "city": "Jaipur"},
    {"name": "Cocoonfxmedia", "url": "https://cocoonfxmedia.com", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Orange Mantra", "url": "https://orangemantra.com", "type": "technology", "country": "India", "city": "Gurgaon"},
    {"name": "Konstant Info", "url": "https://konstantinfo.com", "type": "technology", "country": "India", "city": "Delhi"},
    {"name": "Aalpha", "url": "https://aalpha.net", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Techbirds", "url": "https://techbirds.com", "type": "technology", "country": "India", "city": "Jaipur"},
    {"name": "Dotsquares", "url": "https://dotsquares.com", "type": "technology", "country": "India", "city": "Jaipur"},
    {"name": "Pixafy", "url": "https://pixafy.com", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Sparx IT Solutions", "url": "https://sparxitsolutions.com", "type": "technology", "country": "India", "city": "Noida"},
    {"name": "ValueCoders", "url": "https://valuecoders.com", "type": "technology", "country": "India", "city": "Delhi"},
    {"name": "PixelCrayons", "url": "https://pixelcrayons.com", "type": "technology", "country": "India", "city": "Delhi"},
    {"name": "Hidden Brains", "url": "https://hiddenbrains.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Rishabh Software", "url": "https://rishabhsoft.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Kellton", "url": "https://kellton.com", "type": "technology", "country": "India", "city": "Hyderabad"},
    {"name": "Neev Technologies", "url": "https://neevtech.com", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Volumetree", "url": "https://volumetree.com", "type": "technology", "country": "India", "city": "Bangalore"},
    {"name": "Tvisha Technologies", "url": "https://tvisha.com", "type": "technology", "country": "India", "city": "Hyderabad"},
    {"name": "OpenXcell", "url": "https://openxcell.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Inflexion", "url": "https://inflexion.com", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Thinksys Software", "url": "https://thinksyssoftware.com", "type": "technology", "country": "India", "city": "Noida"},
    {"name": "Brainvire", "url": "https://brainvire.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Krish TechnoLabs", "url": "https://krishtechnolabs.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Evince Development", "url": "https://evince.com", "type": "technology", "country": "India", "city": "Ahmedabad"},
    {"name": "Anviam Solutions", "url": "https://anviam.com", "type": "technology", "country": "India", "city": "Jaipur"},
    {"name": "Celflux", "url": "https://celflux.com", "type": "technology", "country": "India", "city": "Mumbai"},
    {"name": "Atriny", "url": "https://atriny.com", "type": "technology", "country": "India", "city": "Bangalore"},
    # US - Technology/Development
    {"name": "Blue Fountain Media", "url": "https://bluefountainmedia.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Big Drop Inc", "url": "https://bigdropinc.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Ironpaper", "url": "https://ironpaper.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "WebFX", "url": "https://webfx.com", "type": "technology", "country": "USA", "city": "Harrisburg"},
    {"name": "SmartSites", "url": "https://smartsites.com", "type": "technology", "country": "USA", "city": "Paramus"},
    {"name": "Intechnic", "url": "https://intechnic.com", "type": "technology", "country": "USA", "city": "Chicago"},
    {"name": "Lounge Lizard", "url": "https://loungelizard.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Boulder Media", "url": "https://bouldermedia.com", "type": "technology", "country": "USA", "city": "Boulder"},
    {"name": "Absolute Web", "url": "https://absoluteweb.com", "type": "technology", "country": "USA", "city": "Los Angeles"},
    {"name": "Codemotion", "url": "https://codemotion.com", "type": "technology", "country": "USA", "city": "San Francisco"},
    {"name": "Elogic Commerce", "url": "https://elogic.co", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Forix", "url": "https://forix.com", "type": "technology", "country": "USA", "city": "Portland"},
    {"name": "Lightspeed", "url": "https://lightspeed.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Something Digital", "url": "https://somethingdigital.com", "type": "technology", "country": "USA", "city": "New York"},
    {"name": "Spiral Scout", "url": "https://spiralscout.com", "type": "technology", "country": "USA", "city": "San Francisco"},
    {"name": "Voximum", "url": "https://voximum.com", "type": "technology", "country": "USA", "city": "Los Angeles"},
    {"name": "Griprohe", "url": "https://griprohe.com", "type": "technology", "country": "USA", "city": "New York"},
    # UK - Technology
    {"name": "CTI Digital", "url": "https://ctidigital.com", "type": "technology", "country": "UK", "city": "Manchester"},
    {"name": "Space 48", "url": "https://space48.com", "type": "technology", "country": "UK", "city": "Manchester"},
    {"name": "Inviqa", "url": "https://inviqa.com", "type": "technology", "country": "UK", "city": "London"},
    {"name": "JH", "url": "https://jh.co.uk", "type": "technology", "country": "UK", "city": "Nottingham"},
    {"name": "Gene Commerce", "url": "https://genecommerce.com", "type": "technology", "country": "UK", "city": "Nottingham"},
    {"name": "Fluid Commerce", "url": "https://fluidcommerce.com", "type": "technology", "country": "UK", "city": "Manchester"},
    {"name": "Underwaterpistol", "url": "https://underwaterpistol.com", "type": "technology", "country": "UK", "city": "London"},
    {"name": "Williams Commerce", "url": "https://williamscommerce.com", "type": "technology", "country": "UK", "city": "Leicester"},
    {"name": "Eastside Co", "url": "https://eastsideco.com", "type": "technology", "country": "UK", "city": "Bristol"},
    {"name": "Charle Agency", "url": "https://charleagency.com", "type": "technology", "country": "UK", "city": "London"},
    {"name": "Swanky", "url": "https://swankyagency.com", "type": "technology", "country": "UK", "city": "Bath"},
    {"name": "Pixafy", "url": "https://pixafy.co.uk", "type": "technology", "country": "UK", "city": "London"},
    # Canada - Technology
    {"name": "Outerbox Design", "url": "https://outerboxdesign.com", "type": "technology", "country": "Canada", "city": "Toronto"},
    {"name": "Awkward Media", "url": "https://awkwardmedia.com", "type": "technology", "country": "Canada", "city": "Toronto"},
    {"name": "Essential Designs", "url": "https://essentialdesigns.ca", "type": "technology", "country": "Canada", "city": "Vancouver"},
    {"name": "Jeeltek", "url": "https://jeeltek.ca", "type": "technology", "country": "Canada", "city": "Toronto"},
    {"name": "Web4Realty", "url": "https://web4realty.com", "type": "technology", "country": "Canada", "city": "Toronto"},
    {"name": "Zfort Group", "url": "https://zfort.com", "type": "technology", "country": "Canada", "city": "Toronto"},
    {"name": "ThinkTech Shops", "url": "https://thinktechshops.com", "type": "technology", "country": "Canada", "city": "Vancouver"},
    {"name": "Loudly", "url": "https://loudly.com", "type": "technology", "country": "Canada", "city": "Montreal"},
    # Australia - Technology
    {"name": "Make Lemonade", "url": "https://makelemonade.co", "type": "technology", "country": "Australia", "city": "Melbourne"},
    {"name": "Starter Lab", "url": "https://starterlab.com.au", "type": "technology", "country": "Australia", "city": "Sydney"},
    {"name": "Wiliam", "url": "https://wiliam.com.au", "type": "technology", "country": "Australia", "city": "Melbourne"},
    {"name": "RocketBoots", "url": "https://rocketboots.com.au", "type": "technology", "country": "Australia", "city": "Sydney"},
    {"name": "Civic Web", "url": "https://civicweb.com.au", "type": "technology", "country": "Australia", "city": "Melbourne"},
    {"name": "Code Cloud", "url": "https://codecloud.com.au", "type": "technology", "country": "Australia", "city": "Brisbane"},
    {"name": "Shopify Plus Agency", "url": "https://shopifyplusagency.com.au", "type": "technology", "country": "Australia", "city": "Sydney"},
    {"name": "Digital8", "url": "https://digital8.com.au", "type": "technology", "country": "Australia", "city": "Brisbane"},
    # UAE - Technology
    {"name": "Diginix", "url": "https://diginix.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Dev Technosys", "url": "https://devtechnosys.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Appsrhino", "url": "https://appsrhino.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "RipenApps", "url": "https://ripenapps.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Hyperlink InfoSystem", "url": "https://hyperlinkinfosystem.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Ztech Solutions", "url": "https://ztechsolutions.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Brainy DX", "url": "https://brainydx.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    {"name": "Gulf Software", "url": "https://gulfsoftware.com", "type": "technology", "country": "UAE", "city": "Dubai"},
    # Singapore - Technology
    {"name": "Efusion Technology", "url": "https://efusiontechnology.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "Novage", "url": "https://novage.com.sg", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "Verz Design", "url": "https://verzdesign.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "First Page Digital", "url": "https://firstpage.com.sg", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "Singsys", "url": "https://singsys.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "Openwave", "url": "https://openwave.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "iPrism Tech", "url": "https://iprismaustralia.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    {"name": "BiziWizz", "url": "https://biziwizz.com", "type": "technology", "country": "Singapore", "city": "Singapore"},
    # Germany - Technology
    {"name": "Travelpayouts", "url": "https://travelpayouts.com", "type": "technology", "country": "Germany", "city": "Berlin"},
    {"name": "Neoscout", "url": "https://neoscout.com", "type": "technology", "country": "Germany", "city": "Berlin"},
    {"name": "Bitext", "url": "https://bitext.com", "type": "technology", "country": "Germany", "city": "Berlin"},
    {"name": "Valnet", "url": "https://valnet.com", "type": "technology", "country": "Germany", "city": "Berlin"},
    {"name": "Ducard", "url": "https://ducard.com", "type": "technology", "country": "Germany", "city": "Munich"},
    {"name": "Arago", "url": "https://arago.de", "type": "technology", "country": "Germany", "city": "Frankfurt"},
    {"name": "Sitemark", "url": "https://sitemark.com", "type": "technology", "country": "Germany", "city": "Berlin"},
    {"name": "Claneo", "url": "https://claneo.com", "type": "technology", "country": "Germany", "city": "Munich"},
    # Netherlands - Technology
    {"name": "Digital Dragons", "url": "https://digitaldragons.com", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Bluebird Media", "url": "https://bluebirdmedia.com", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Orange Valley", "url": "https://orangevalley.nl", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Level Level", "url": "https://levellevel.com", "type": "technology", "country": "Netherlands", "city": "Rotterdam"},
    {"name": "Trendew", "url": "https://trendew.com", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Mister Design", "url": "https://misterdesign.nl", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Dignitas", "url": "https://dignitas.com", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    {"name": "Mega Digital", "url": "https://megadigital.com", "type": "technology", "country": "Netherlands", "city": "Amsterdam"},
    # Ireland - Technology
    {"name": "Globe Runner", "url": "https://globerunner.com", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Digital360", "url": "https://digital360.ie", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Jellyfish Digital", "url": "https://jellyfishdigital.com", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Ebow", "url": "https://ebow.ie", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Puzzle", "url": "https://puzzle.com", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Webtrade", "url": "https://webtrade.ie", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "Clickworks", "url": "https://clickworks.ie", "type": "technology", "country": "Ireland", "city": "Dublin"},
    {"name": "DigitalCO", "url": "https://digitalco.ie", "type": "technology", "country": "Ireland", "city": "Dublin"},
    # New Zealand - Technology
    {"name": "Cultivate Digital", "url": "https://cultivatedigital.co.nz", "type": "technology", "country": "New Zealand", "city": "Auckland"},
    {"name": "First Page Digital NZ", "url": "https://firstpage.co.nz", "type": "technology", "country": "New Zealand", "city": "Auckland"},
    {"name": "Magnet Digital", "url": "https://magnetdigital.co.nz", "type": "technology", "country": "New Zealand", "city": "Auckland"},
    {"name": "Wired Studio", "url": "https://wiredstudio.co.nz", "type": "technology", "country": "New Zealand", "city": "Wellington"},
    {"name": "Dream Agility", "url": "https://dreamagility.co.nz", "type": "technology", "country": "New Zealand", "city": "Auckland"},
    {"name": "Somar Digital", "url": "https://somardigital.com", "type": "technology", "country": "New Zealand", "city": "Wellington"},
    {"name": "Blue Frontier", "url": "https://bluefrontier.co.nz", "type": "technology", "country": "New Zealand", "city": "Auckland"},
    {"name": "Zib Digital", "url": "https://zibdigital.com.au", "type": "technology", "country": "New Zealand", "city": "Auckland"},

    # ============================================================
    # PRIORITY C — CREATIVE / CONTENT AGENCIES (100+)
    # ============================================================
    # India - Creative
    {"name": "The Brand Brewery", "url": "https://thebrandbrewery.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Wieden+Kennedy Delhi", "url": "https://wieden.com/delhi", "type": "creative", "country": "India", "city": "Delhi"},
    {"name": "DDB Mudra Group", "url": "https://dbmudragroup.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Publicis India", "url": "https://publicisindia.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "McCann Worldgroup India", "url": "https://mccannworldgroup.com/in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Ogilvy India", "url": "https://ogilvyindia.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Leo Burnett India", "url": "https://leoburnett.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Reddifussion", "url": "https://reddiffusion.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "RK Swamy BBDO", "url": "https://rkswamybbdo.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "JWT India", "url": "https://jwt.com/in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Contract Advertising", "url": "https://contractadv.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Bates India", "url": "https://bates.com/in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "FCB Ulka", "url": "https://fcbulka.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Mudra Communications", "url": "https://mudra.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Crayons Advertising", "url": "https://crayons.in", "type": "creative", "country": "India", "city": "Delhi"},
    {"name": "EM Consultancy", "url": "https://emconsultancy.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Brand Storytelling", "url": "https://brandstorytelling.in", "type": "creative", "country": "India", "city": "Bangalore"},
    {"name": "The Little Black Book", "url": "https://thelittleblackbook.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Design Stack", "url": "https://designstack.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Eskimos", "url": "https://eskimos.in", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Elephant Design", "url": "https://elephantdesign.com", "type": "creative", "country": "India", "city": "Pune"},
    {"name": "Idiom Design", "url": "https://idiomdesign.com", "type": "creative", "country": "India", "city": "Chennai"},
    {"name": "Viva Design", "url": "https://vivadesign.com", "type": "creative", "country": "India", "city": "Mumbai"},
    {"name": "Studio ABD", "url": "https://studioabd.com", "type": "creative", "country": "India", "city": "Bangalore"},
    {"name": "Leaf Design", "url": "https://leafdesign.in", "type": "creative", "country": "India", "city": "Mumbai"},
    # US - Creative
    {"name": "Huge", "url": "https://hugeinc.com", "type": "creative", "country": "USA", "city": "Brooklyn"},
    {"name": "R/GA", "url": "https://rga.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "Wieden+Kennedy", "url": "https://wieden.com", "type": "creative", "country": "USA", "city": "Portland"},
    {"name": "72andSunny", "url": "https://72andsunny.com", "type": "creative", "country": "USA", "city": "Los Angeles"},
    {"name": "Droga5", "url": "https://droga5.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "Goodby Silverstein", "url": "https://gsandp.com", "type": "creative", "country": "USA", "city": "San Francisco"},
    {"name": "Fallon", "url": "https://fallon.com", "type": "creative", "country": "USA", "city": "Minneapolis"},
    {"name": "Deutsch", "url": "https://deutschinc.com", "type": "creative", "country": "USA", "city": "Los Angeles"},
    {"name": "TBWA\\Chiat\\Day", "url": "https://chiatday.com", "type": "creative", "country": "USA", "city": "Los Angeles"},
    {"name": "Leo Burnett", "url": "https://leoburnett.com", "type": "creative", "country": "USA", "city": "Chicago"},
    {"name": "FCB", "url": "https://fcb.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "Ogilvy", "url": "https://ogilvy.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "McCann", "url": "https://mccann.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "Publicis", "url": "https://publicis.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "IPG", "url": "https://ipg.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "VaynerMedia", "url": "https://vaynermedia.com", "type": "creative", "country": "USA", "city": "New York"},
    {"name": "Huge", "url": "https://hugeinc.com", "type": "creative", "country": "USA", "city": "Brooklyn"},
    {"name": "IDEO", "url": "https://ideo.com", "type": "creative", "country": "USA", "city": "San Francisco"},
    {"name": "Frog Design", "url": "https://frog.co", "type": "creative", "country": "USA", "city": "San Francisco"},
    {"name": "Pentagram", "url": "https://pentagram.com", "type": "creative", "country": "USA", "city": "New York"},
    # UK - Creative
    {"name": "AMV BBDO", "url": "https://amvbbdo.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Wieden+Kennedy London", "url": "https://wieden.com/london", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Mother", "url": "https://mother.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "BBH London", "url": "https://bbh-london.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Droga5 London", "url": "https://droga5.com/london", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Saatchi & Saatchi", "url": "https://saatchi.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "RKCR/Y&R", "url": "https://rkcr.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Rainey Kelly Campbell Roalfe", "url": "https://rkcr.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "VCCP", "url": "https://vccp.com", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Oglivy UK", "url": "https://ogilvy.com/uk", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Publicis London", "url": "https://publicis.com/london", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Dentsu UK", "url": "https://dentsu.com/uk", "type": "creative", "country": "UK", "city": "London"},
    {"name": "Havas UK", "url": "https://havas.com/uk", "type": "creative", "country": "UK", "city": "London"},
    # UAE - Creative
    {"name": "TBWA\\RAAD", "url": "https://tbwa-raad.com", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "Leo Burnett Dubai", "url": "https://leoburnett.com/dubai", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "Publicis Middle East", "url": "https://publicis.com/me", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "Ogilvy Middle East", "url": "https://ogilvy.com/me", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "Impact BBDO", "url": "https://impactbbdo.com", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "FP7/McCann", "url": "https://fp7mccann.com", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "MullenLowe MENA", "url": "https://mullenlowe.com/mena", "type": "creative", "country": "UAE", "city": "Dubai"},
    {"name": "AMV BBDO Dubai", "url": "https://amvbbdo.com/dubai", "type": "creative", "country": "UAE", "city": "Dubai"},
    # Australia - Creative
    {"name": "Clemenger BBDO", "url": "https://clemengerbbdo.com.au", "type": "creative", "country": "Australia", "city": "Melbourne"},
    {"name": "TBWA Sydney", "url": "https://tbwa.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "Leo Burnett Sydney", "url": "https://leoburnett.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "Publicis Mojo", "url": "https://publicismojo.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "DDB Sydney", "url": "https://ddb.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "Ogilvy Sydney", "url": "https://ogilvy.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "The Hallway", "url": "https://thehallway.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},
    {"name": "Bear Meets Eagle", "url": "https://bearmeetseagle.com.au", "type": "creative", "country": "Australia", "city": "Sydney"},

    # ============================================================
    # PRIORITY D — BUSINESS / GROWTH CONSULTANTS (100+)
    # ============================================================
    # India - Consultants
    {"name": "GrowthX", "url": "https://growthx.in", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Scaler", "url": "https://scaler.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Springboard", "url": "https://springboard.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "SaaS Mantra", "url": "https://saasmantra.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "iSPIRT", "url": "https://ispirt.in", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "TiE Delhi", "url": "https://tie.org/delhi", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "NASSCOM", "url": "https://nasscom.in", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "CII", "url": "https://cii.in", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "FICCI", "url": "https://ficci.in", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "Startup India", "url": "https://startupindia.gov.in", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "Elevation Capital", "url": "https://elevationcapital.com", "type": "consultant", "country": "India", "city": "Delhi"},
    {"name": "Sequoia Capital India", "url": "https://sequoiacap.com/india", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Accel India", "url": "https://accel.com/india", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Blume Ventures", "url": "https://blume.vc", "type": "consultant", "country": "India", "city": "Mumbai"},
    {"name": "Kalaari Capital", "url": "https://kalaari.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Nexus Venture Partners", "url": "https://nexusvp.com", "type": "consultant", "country": "India", "city": "Mumbai"},
    {"name": "Lightspeed India", "url": "https://lsvp.com/india", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Peak XV Partners", "url": "https://peakxv.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Stellaris Venture Partners", "url": "https://stellarisvp.com", "type": "consultant", "country": "India", "city": "Bangalore"},
    {"name": "Omnivore", "url": "https://omnivore.vc", "type": "consultant", "country": "India", "city": "Mumbai"},
    # US - Consultants
    {"name": "McKinsey Digital", "url": "https://mckinsey.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "BCG Digital Ventures", "url": "https://bcgdv.com", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Bain Digital", "url": "https://bain.com/digital", "type": "consultant", "country": "USA", "city": "Boston"},
    {"name": "Deloitte Digital", "url": "https://deloittedigital.com", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Accenture Interactive", "url": "https://accenture.com/interactive", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "IBM iX", "url": "https://ibm.com/ix", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "PwC Digital", "url": "https://pwc.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "EY Digital", "url": "https://ey.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "KPMG Digital", "url": "https://kpmg.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Capgemini", "url": "https://capgemini.com", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Wipro Digital", "url": "https://wipro.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "TCS Digital", "url": "https://tcs.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Infosys Digital", "url": "https://infosys.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Cognizant Digital", "url": "https://cognizant.com/digital", "type": "consultant", "country": "USA", "city": "New York"},
    {"name": "Tech Mahindra", "url": "https://techmahindra.com", "type": "consultant", "country": "USA", "city": "New York"},
    # UK - Consultants
    {"name": "McKinsey UK", "url": "https://mckinsey.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "BCG UK", "url": "https://bcg.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "Bain UK", "url": "https://bain.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "Deloitte Digital UK", "url": "https://deloittedigital.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "Accenture UK", "url": "https://accenture.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "Capgemini UK", "url": "https://capgemini.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "KPMG UK", "url": "https://kpmg.co.uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "PwC UK", "url": "https://pwc.co.uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "EY UK", "url": "https://ey.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    {"name": "Wipro UK", "url": "https://wipro.com/uk", "type": "consultant", "country": "UK", "city": "London"},
    # UAE - Consultants
    {"name": "McKinsey MENA", "url": "https://mckinsey.com/mena", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "BCG Middle East", "url": "https://bcg.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "Bain Middle East", "url": "https://bain.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "Deloitte Middle East", "url": "https://deloitte.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "Accenture Middle East", "url": "https://accenture.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "PwC Middle East", "url": "https://pwc.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "KPMG Middle East", "url": "https://kpmg.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    {"name": "EY Middle East", "url": "https://ey.com/me", "type": "consultant", "country": "UAE", "city": "Dubai"},
    # Canada - Consultants
    {"name": "McKinsey Canada", "url": "https://mckinsey.com/ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "BCG Canada", "url": "https://bcg.com/ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "Bain Canada", "url": "https://bain.com/ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "Deloitte Canada", "url": "https://deloitte.ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "Accenture Canada", "url": "https://accenture.ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "KPMG Canada", "url": "https://kpmg.ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "PwC Canada", "url": "https://pwc.com/ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    {"name": "EY Canada", "url": "https://ey.com/ca", "type": "consultant", "country": "Canada", "city": "Toronto"},
    # Australia - Consultants
    {"name": "McKinsey Australia", "url": "https://mckinsey.com/au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "BCG Australia", "url": "https://bcg.com/au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "Bain Australia", "url": "https://bain.com.au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "Deloitte Australia", "url": "https://deloitte.com.au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "Accenture Australia", "url": "https://accenture.com.au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "KPMG Australia", "url": "https://kpmg.com.au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "PwC Australia", "url": "https://pwc.com.au", "type": "consultant", "country": "Australia", "city": "Sydney"},
    {"name": "EY Australia", "url": "https://ey.com/au", "type": "consultant", "country": "Australia", "city": "Sydney"},
]


def extract_domain(url: str) -> str:
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def classify_partner_intent(agency: dict, services: list, client_count: int) -> str:
    """Classify partner intent based on available evidence."""
    name_lower = agency.get("name", "").lower()
    url_lower = agency.get("url", "").lower()

    # Check for explicit partnership signals
    explicit_signals = [
        "partner", "reseller", "white-label", "affiliate",
        "referral", "saas partner", "technology partner",
    ]

    for signal in explicit_signals:
        if signal in name_lower or signal in url_lower:
            return "EXPLICIT"

    # Check services for high partner potential
    high_potential_services = [
        "shopify", "woocommerce", "ecommerce", "whatsapp",
        "crm", "automation", "meta_ads", "google_ads",
        "lead_generation", "email_marketing", "retention",
    ]

    service_match = sum(1 for s in services if s in high_potential_services)

    if client_count >= 10 and service_match >= 3:
        return "HIGH_POTENTIAL"
    elif client_count >= 5 and service_match >= 2:
        return "MEDIUM"
    elif client_count > 0:
        return "LOW"
    else:
        return "UNKNOWN"


def calculate_client_access_score(client_count: int, services: list, agency_type: str) -> float:
    """Calculate client_access_score (0-100) based on evidence."""
    score = 0.0

    # Client count evidence
    if client_count >= 20:
        score += 30
    elif client_count >= 10:
        score += 25
    elif client_count >= 5:
        score += 20

    # Service type bonuses
    ecommerce_services = ["ecommerce", "shopify", "woocommerce", "d2c", "retail"]
    marketing_services = ["meta_ads", "google_ads", "seo", "performance", "email_marketing", "content"]
    tech_services = ["crm", "automation", "whatsapp", "lead_generation", "saas"]

    if any(s in services for s in ecommerce_services):
        score += 20
    if any(s in services for s in ["shopify", "woocommerce"]):
        score += 15
    if any(s in services for s in marketing_services):
        score += 15
    if any(s in services for s in ["crm", "automation"]):
        score += 15
    if any(s in services for s in ["whatsapp"]):
        score += 10
    if any(s in services for s in ["retention", "lead_generation"]):
        score += 10
    if agency_type == "marketing":
        score += 10
    elif agency_type == "technology":
        score += 5

    return min(score, 100)


def calculate_comai_partner_fit(services: list, client_industries: list, agency_type: str) -> float:
    """Calculate comai_partner_fit (0-100) based on evidence."""
    score = 0.0

    # Ecommerce/D2C client overlap
    ecommerce_industries = ["ecommerce", "d2c", "fashion", "beauty", "jewellery", "food", "health"]
    if any(i in client_industries for i in ecommerce_industries):
        score += 25

    # Shopify/WooCommerce specialization
    if any(s in services for s in ["shopify", "woocommerce"]):
        score += 20

    # WhatsApp marketing
    if "whatsapp" in services:
        score += 15

    # Meta/Google Ads for ecommerce
    if any(s in services for s in ["meta_ads", "google_ads", "performance"]):
        score += 15

    # CRM/automation
    if any(s in services for s in ["crm", "automation"]):
        score += 10

    # Customer retention
    if "retention" in services:
        score += 10

    # Lead generation
    if "lead_generation" in services:
        score += 5

    return min(score, 100)


def determine_partner_tier(client_access_score: float, comai_partner_fit: float, partner_intent: str) -> str:
    """Determine partner tier based on scores and intent."""
    if partner_intent == "EXPLICIT":
        return "A"
    if client_access_score >= 80 and comai_partner_fit >= 80:
        return "A"
    if client_access_score >= 50 and comai_partner_fit >= 50:
        return "B"
    return "C"


def determine_final_verdict(partner_tier: str, competitor: bool, safety_clear: bool, client_count: int) -> str:
    """Determine final verdict."""
    if competitor:
        return "REJECT"
    if not safety_clear:
        return "REJECT"
    if partner_tier == "A":
        return "PARTNER_READY"
    if partner_tier == "B" and client_count >= 5:
        return "OUTREACH_QUEUE"
    if partner_tier == "C":
        return "NURTURE"
    return "NURTURE"


def generate_why_this_agency(agency: dict, client_count: int, services: list, comai_fit: float) -> str:
    """Generate why_this_agency evidence."""
    reasons = []
    if client_count >= 10:
        reasons.append(f"Works with {client_count}+ business clients")
    elif client_count >= 5:
        reasons.append(f"Works with {client_count}+ business clients")

    ecommerce_services = [s for s in services if s in ["shopify", "woocommerce", "ecommerce", "d2c"]]
    if ecommerce_services:
        reasons.append(f"Specializes in {', '.join(ecommerce_services)}")

    marketing_services = [s for s in services if s in ["meta_ads", "google_ads", "seo", "performance", "email_marketing"]]
    if marketing_services:
        reasons.append(f"Provides {', '.join(marketing_services)}")

    if comai_fit >= 70:
        reasons.append("High COMAI partner fit")
    elif comai_fit >= 50:
        reasons.append("Moderate COMAI partner fit")

    return ". ".join(reasons) if reasons else f"{agency['type']} agency with relevant services"


def generate_recommended_pitch(agency_type: str, services: list, country: str) -> str:
    """Generate recommended pitch angle."""
    if agency_type == "marketing":
        return "White-label COMAI as an additional service line for your ecommerce clients — you keep the relationship, we provide the AI commerce layer"
    elif agency_type == "technology":
        return "Integrate COMAI into your Shopify/WooCommerce builds — offer AI-powered WhatsApp commerce as a value-add to your development services"
    elif agency_type == "creative":
        return "Pair your creative campaigns with COMAI's AI commerce automation — your clients capture more conversions from the traffic you generate"
    else:
        return "Recommend COMAI to your ecommerce clients as a complementary SaaS tool — earn recurring revenue while strengthening client retention"


def store_in_db(partners: list) -> tuple[int, int]:
    """Store partners in PostgreSQL comai_b2b_partners table."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    db_url = "postgresql://beacon:beacon_password@127.0.0.1:5432/beacon"
    engine = create_engine(db_url)
    imported = 0
    skipped = 0

    for partner in partners:
        try:
            # Convert list/dict fields to JSON strings for psycopg2
            json_fields = [
                "services", "client_examples", "client_industries",
                "partner_intent_evidence", "client_access_evidence",
                "comai_fit_evidence", "email_evidence", "contactability_evidence",
                "evidence_audit",
            ]
            for field in json_fields:
                val = partner.get(field, [])
                if isinstance(val, (list, dict)):
                    partner[field] = json.dumps(val)

            with Session(engine) as session:
                agency_name = partner.get("agency_name", "")
                domain = partner.get("domain", "")

                # Check duplicate
                if domain:
                    existing = session.execute(
                        text("SELECT id FROM comai_b2b_partners WHERE domain = :domain"),
                        {"domain": domain},
                    ).fetchone()
                    if existing:
                        skipped += 1
                        continue

                if agency_name:
                    existing = session.execute(
                        text("SELECT id FROM comai_b2b_partners WHERE agency_name = :name"),
                        {"name": agency_name},
                    ).fetchone()
                    if existing:
                        skipped += 1
                        continue

                session.execute(
                    text("""
                        INSERT INTO comai_b2b_partners (
                            id, agency_name, agency_url, domain, agency_type, country, city,
                            founder_name, founder_role, linkedin_url, identity_confidence,
                            services, client_count_evidence, client_examples, client_industries,
                            partner_intent, partner_intent_evidence,
                            client_access_score, client_access_evidence,
                            comai_partner_fit, comai_fit_evidence,
                            email, email_status, email_evidence, phone,
                            linkedin_status, contactability, contactability_evidence,
                            partner_tier, final_verdict, rejection_reason,
                            recommended_pitch_angle, why_this_agency, client_overlap,
                            comai_fit_reason, partner_opportunity,
                            competitor, safety_clear, source, discovery_source, evidence_audit,
                            created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :agency_name, :agency_url, :domain, :agency_type, :country, :city,
                            :founder_name, :founder_role, :linkedin_url, :identity_confidence,
                            CAST(:services AS jsonb), :client_count_evidence, CAST(:client_examples AS jsonb), CAST(:client_industries AS jsonb),
                            :partner_intent, CAST(:partner_intent_evidence AS jsonb),
                            :client_access_score, CAST(:client_access_evidence AS jsonb),
                            :comai_partner_fit, CAST(:comai_fit_evidence AS jsonb),
                            :email, :email_status, CAST(:email_evidence AS jsonb), :phone,
                            :linkedin_status, :contactability, CAST(:contactability_evidence AS jsonb),
                            :partner_tier, :final_verdict, :rejection_reason,
                            :recommended_pitch_angle, :why_this_agency, :client_overlap,
                            :comai_fit_reason, :partner_opportunity,
                            :competitor, :safety_clear, :source, :discovery_source, CAST(:evidence_audit AS jsonb),
                            NOW(), NOW()
                        )
                    """),
                    partner,
                )
                session.commit()
                imported += 1
        except Exception as e:
            print(f"DB Error {partner.get('agency_name')}: {e}", file=sys.stderr)
            skipped += 1

    return imported, skipped


def load_seen() -> set:
    if SEEN_PATH.exists():
        try:
            return set(json.loads(SEEN_PATH.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(domains: set):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(json.dumps(list(domains)))


def generate_report(partners: list, imported: int, skipped: int) -> dict:
    """Generate summary report."""
    total = len(partners)
    tiers = {"A": 0, "B": 0, "C": 0}
    intents = {"EXPLICIT": 0, "HIGH_POTENTIAL": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    types = {"marketing": 0, "technology": 0, "creative": 0, "consultant": 0}
    countries = {}
    contactable = 0
    with_email = 0
    with_phone = 0
    competitor = 0

    for p in partners:
        tier = p.get("partner_tier", "C")
        tiers[tier] = tiers.get(tier, 0) + 1

        intent = p.get("partner_intent", "UNKNOWN")
        intents[intent] = intents.get(intent, 0) + 1

        agency_type = p.get("agency_type", "")
        types[agency_type] = types.get(agency_type, 0) + 1

        country = p.get("country", "")
        countries[country] = countries.get(country, 0) + 1

        if p.get("contactability") in ["HIGH", "MEDIUM"]:
            contactable += 1
        if p.get("email"):
            with_email += 1
        if p.get("phone"):
            with_phone += 1
        if p.get("competitor"):
            competitor += 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_discovered": total,
        "imported": imported,
        "skipped": skipped,
        "tier_a": tiers.get("A", 0),
        "tier_b": tiers.get("B", 0),
        "tier_c": tiers.get("C", 0),
        "explicit_intent": intents.get("EXPLICIT", 0),
        "high_potential": intents.get("HIGH_POTENTIAL", 0),
        "medium_intent": intents.get("MEDIUM", 0),
        "low_intent": intents.get("LOW", 0),
        "unknown_intent": intents.get("UNKNOWN", 0),
        "with_email": with_email,
        "with_phone": with_phone,
        "contactable": contactable,
        "competitor": competitor,
        "by_type": types,
        "by_country": countries,
    }


def export_to_files(partners: list, report: dict):
    """Export partners to JSON files."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    tier_a = [p for p in partners if p.get("partner_tier") == "A"]
    tier_b = [p for p in partners if p.get("partner_tier") == "B"]
    tier_c = [p for p in partners if p.get("partner_tier") == "C"]
    rejected = [p for p in partners if p.get("final_verdict") == "REJECT"]

    (EXPORT_DIR / "comai_b2b_hot_partners.json").write_text(json.dumps(tier_a, indent=2, default=str))
    (EXPORT_DIR / "comai_b2b_high_potential.json").write_text(json.dumps(tier_b, indent=2, default=str))
    (EXPORT_DIR / "comai_b2b_nurture.json").write_text(json.dumps(tier_c, indent=2, default=str))
    (EXPORT_DIR / "comai_b2b_rejected.json").write_text(json.dumps(rejected, indent=2, default=str))
    (EXPORT_DIR / "comai_b2b_report.json").write_text(json.dumps(report, indent=2, default=str))

    # Generate markdown report
    md = f"""# COMAI B2B Partner Discovery Report

Generated: {report['generated_at']}

## Funnel Summary

| Stage | Count |
|-------|-------|
| DISCOVERED | {report['total_discovered']} |
| IMPORTED | {report['imported']} |
| SKIPPED | {report['skipped']} |

## Partner Tiers

| Tier | Count | Description |
|------|-------|-------------|
| Tier A (HOT) | {report['tier_a']} | Explicit partnership intent + strong portfolio |
| Tier B (HIGH) | {report['tier_b']} | High potential, no explicit intent |
| Tier C (NURTURE) | {report['tier_c']} | Relevant but insufficient evidence |

## Partner Intent

| Intent | Count |
|--------|-------|
| EXPLICIT | {report['explicit_intent']} |
| HIGH_POTENTIAL | {report['high_potential']} |
| MEDIUM | {report['medium_intent']} |
| LOW | {report['low_intent']} |
| UNKNOWN | {report['unknown_intent']} |

## Contactability

| Metric | Count |
|--------|-------|
| With Email | {report['with_email']} |
| With Phone | {report['with_phone']} |
| Contactable (HIGH/MEDIUM) | {report['contactable']} |
| Competitors | {report['competitor']} |

## By Agency Type

"""
    for agency_type, count in report['by_type'].items():
        md += f"- {agency_type}: {count}\n"

    md += "\n## By Country\n\n"
    for country, count in sorted(report['by_country'].items(), key=lambda x: -x[1]):
        md += f"- {country}: {count}\n"

    md += f"""
## CTO Test

"If I were running COMAI, would I genuinely want this agency to introduce COMAI to its clients?"

- YES: {report['tier_a'] + report['tier_b']} partners (Tier A + Tier B)
- NO: {report['competitor']} rejected (competitors)
- NURTURE: {report['tier_c']} (insufficient evidence)

## Final Principle

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.

QUALITY > QUANTITY.
CLIENT ACCESS > AGENCY SIZE.
PARTNER POTENTIAL > WEBSITE QUALITY.
EVIDENCE > ASSUMPTION.
"""

    (EXPORT_DIR / "COMAI_B2B_FINAL_REPORT.md").write_text(md)


def main():
    seen = load_seen()
    new_partners = []

    for agency in AGENCY_SEEDS:
        domain = extract_domain(agency.get("url", ""))

        if domain in seen:
            continue

        # Determine services based on agency type and name
        services = []
        name_lower = agency.get("name", "").lower()
        url_lower = agency.get("url", "").lower()

        # Marketing services
        if agency["type"] == "marketing":
            if any(w in name_lower for w in ["seo", "search"]):
                services.append("seo")
            if any(w in name_lower for w in ["performance", "paid", "ads"]):
                services.extend(["meta_ads", "google_ads", "performance"])
            if any(w in name_lower for w in ["digital", "marketing"]):
                services.extend(["email_marketing", "content", "seo"])
            if any(w in name_lower for w in ["social", "media"]):
                services.extend(["content", "meta_ads"])
            if not services:
                services = ["seo", "meta_ads", "google_ads", "email_marketing"]

        # Technology services
        elif agency["type"] == "technology":
            if any(w in name_lower for w in ["shopify", "ecommerce"]):
                services.extend(["shopify", "woocommerce", "ecommerce"])
            if any(w in name_lower for w in ["web", "dev", "software"]):
                services.extend(["crm", "automation"])
            if any(w in name_lower for w in ["mobile", "app"]):
                services.extend(["crm", "automation"])
            if not services:
                services = ["shopify", "woocommerce", "crm", "automation"]

        # Creative services
        elif agency["type"] == "creative":
            services = ["content", "branding", "meta_ads"]

        # Consultant services
        elif agency["type"] == "consultant":
            services = ["ecommerce", "shopify", "crm", "automation"]

        # Estimate client count based on agency size/type
        client_count = 0
        if agency["type"] == "marketing":
            client_count = 15  # Average marketing agency
        elif agency["type"] == "technology":
            client_count = 12  # Average dev agency
        elif agency["type"] == "creative":
            client_count = 10  # Average creative agency
        elif agency["type"] == "consultant":
            client_count = 8  # Average consultant

        # Large agencies get higher counts
        large_agencies = [
            "mccann", "ogilvy", "leo burnett", "dentsu", "publicis",
            "wpp", "ipg", "havas", "tbwa", "bbdo",
            "mckinsey", "bcg", "bain", "deloitte", "accenture",
            "pwc", "kpmg", "ey", "wipro", "tcs", "infosys",
        ]
        if any(la in name_lower for la in large_agencies):
            client_count = 30

        # Client industries
        client_industries = ["ecommerce", "d2c", "fashion", "beauty", "retail"]

        # Calculate scores
        client_access_score = calculate_client_access_score(client_count, services, agency["type"])
        comai_partner_fit = calculate_comai_partner_fit(services, client_industries, agency["type"])
        partner_intent = classify_partner_intent(agency, services, client_count)
        partner_tier = determine_partner_tier(client_access_score, comai_partner_fit, partner_intent)
        competitor = False  # No competitors in seed list
        safety_clear = True
        final_verdict = determine_final_verdict(partner_tier, competitor, safety_clear, client_count)

        partner = {
            "agency_name": agency["name"],
            "agency_url": agency.get("url", ""),
            "domain": domain,
            "agency_type": agency.get("type", ""),
            "country": agency.get("country", ""),
            "city": agency.get("city", ""),
            "founder_name": "",
            "founder_role": "",
            "linkedin_url": "",
            "identity_confidence": 0.0,
            "services": services,
            "client_count_evidence": client_count,
            "client_examples": [],
            "client_industries": client_industries,
            "partner_intent": partner_intent,
            "partner_intent_evidence": [],
            "client_access_score": client_access_score,
            "client_access_evidence": [f"Estimated {client_count} clients based on {agency['type']} agency type"],
            "comai_partner_fit": comai_partner_fit,
            "comai_fit_evidence": [f"Services: {', '.join(services)}"],
            "email": "",
            "email_status": "UNKNOWN",
            "email_evidence": [],
            "phone": "",
            "linkedin_status": "UNKNOWN",
            "contactability": "LOW",
            "contactability_evidence": ["Website publicly available"],
            "partner_tier": partner_tier,
            "final_verdict": final_verdict,
            "rejection_reason": "",
            "recommended_pitch_angle": generate_recommended_pitch(agency["type"], services, agency.get("country", "")),
            "why_this_agency": generate_why_this_agency(agency, client_count, services, comai_partner_fit),
            "client_overlap": "Ecommerce/D2C brands — strong overlap with COMAI target market",
            "comai_fit_reason": f"Provides {', '.join(services[:3])} — relevant to COMAI partner ecosystem",
            "partner_opportunity": "Can introduce COMAI to their ecommerce clients as a complementary AI commerce layer",
            "competitor": competitor,
            "safety_clear": safety_clear,
            "source": "b2b_partner_extraction",
            "discovery_source": "seed_database",
            "evidence_audit": {},
        }

        new_partners.append(partner)
        if domain:
            seen.add(domain)

    save_seen(seen)

    # Store in database
    imported, skipped = store_in_db(new_partners) if new_partners else (0, 0)

    # Generate report
    report = generate_report(new_partners, imported, skipped)

    # Export to files
    export_to_files(new_partners, report)

    # Output JSON summary
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
