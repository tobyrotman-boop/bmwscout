import requests
import re
import json
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'diamondnightsdues@gmail.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '')
RECIPIENTS = ["tobyrotman@gmail.com","lindsey.leggett@gmail.com"]

def load_previous_ids():
    try:
        with open('listings.json', 'r') as f:
            data = json.load(f)
            return {l['listingId'] for l in data.get('listings', [])}
    except:
        return set()

def search_cargurus():
    url = "https://www.cargurus.com/search?sourceContext=carGurusHomePageModel&makeModelTrimPaths=m3%2Fd393%2Cm3%2Fd2120&newUsed=2&startYear=2024&endYear=2025&maxPrice=60000&isDeliveryEnabled=false&priceDropsOnly=false&maxMileage=35000&hideNationwideShipping=true&distance=200&nonShippableBaseline=15&sortDirection=ASC&sortType=BEST_MATCH&zip=94939"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    pattern = r'\[(\{"listingId".*?)\]\)'
    match = re.search(pattern, response.text, re.DOTALL)
    if not match:
        print("Could not find listing data")
        return []
    
    raw = '[' + match.group(1) + ']'
    listings = json.loads(raw)
    return [l for l in listings if 'sDrive' not in l.get('trim', '')]

def make_url(listing_id):
    return f"https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId={listing_id}#listing={listing_id}"

def save_json(listings, previous_ids):
    preferred_colors = ['black', 'white', 'gray', 'grey', 'silver']
    now = datetime.datetime.now().isoformat()
    
    output = []
    for l in listings:
        color = l.get('exteriorColor', 'Not listed')
        listing_id = l.get('listingId', '')
        is_new = listing_id not in previous_ids
        output.append({
            'year': l['year'],
            'trim': l.get('trim', ''),
            'price': l['price'],
            'mileage': l['mileage'],
            'exteriorColor': color,
            'preferredColor': any(c in color.lower() for c in preferred_colors),
            'isNew': is_new,
            'location': l.get('cityRegion', 'Not listed'),
            'deal': l.get('dealFinderRating', 'N/A'),
            'vin': l.get('vin', 'N/A'),
            'listingId': listing_id,
            'url': make_url(listing_id),
            'imageUrl': l.get('imageUrl', ''),
            'lastUpdated': now
        })
    
    # Sort: new first, then by price
    output.sort(key=lambda x: (not x['isNew'], x['price']))
    
    with open('listings.json', 'w') as f:
        json.dump({'lastUpdated': now, 'listings': output}, f, indent=2)
    
    print(f"Saved {len(output)} listings to listings.json ({sum(1 for l in output if l['isNew'])} new)")

def format_email(listings, previous_ids):
    preferred_colors = ['black', 'white', 'gray', 'grey', 'silver']
    new_listings = [l for l in listings if l.get('listingId', '') not in previous_ids]
    body = f"BMW X5 Scout — {len(listings)} total listings, {len(new_listings)} new today\n\n"
    
    if new_listings:
        body += "🆕 NEW LISTINGS\n"
        body += "=" * 40 + "\n\n"
        for l in new_listings:
            color = l.get('exteriorColor', 'Not listed')
            color_flag = " ✓" if any(c in color.lower() for c in preferred_colors) else ""
            body += f"{l['year']} {l.get('model', 'X5')} {l.get('trim', '')}\n"
            body += f"  Price:    ${l['price']:,}\n"
            body += f"  Mileage:  {l['mileage']:,} miles\n"
            body += f"  Color:    {color}{color_flag}\n"
            body += f"  Location: {l.get('cityRegion', 'Not listed')}\n"
            body += f"  Deal:     {l.get('dealFinderRating', 'N/A')}\n"
            body += f"  VIN:      {l.get('vin', 'N/A')}\n"
            body += f"  Link:     {make_url(l.get('listingId', ''))}\n\n"
    
    body += "ALL LISTINGS\n"
    body += "=" * 40 + "\n\n"
    for l in listings:
        color = l.get('exteriorColor', 'Not listed')
        color_flag = " ✓" if any(c in color.lower() for c in preferred_colors) else ""
        new_flag = "🆕 " if l.get('listingId', '') not in previous_ids else ""
        body += f"{new_flag}{l['year']} {l.get('model', 'X5')} {l.get('trim', '')}\n"
        body += f"  Price:    ${l['price']:,}\n"
        body += f"  Mileage:  {l['mileage']:,} miles\n"
        body += f"  Color:    {color}{color_flag}\n"
        body += f"  Location: {l.get('cityRegion', 'Not listed')}\n"
        body += f"  Deal:     {l.get('dealFinderRating', 'N/A')}\n"
        body += f"  VIN:      {l.get('vin', 'N/A')}\n"
        body += f"  Link:     {make_url(l.get('listingId', ''))}\n\n"
    
    return body

def send_email(body):
    if not RECIPIENTS:
        print("No recipients set, skipping email.")
        return
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECIPIENTS)
    msg['Subject'] = "Daily BMW X5 Scout Results"
    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
    
    print("Email sent successfully!")

previous_ids = load_previous_ids()
listings = search_cargurus()
print(f"Found {len(listings)} listings")
save_json(listings, previous_ids)
new_listings = [l for l in listings if l.get('listingId', '') not in previous_ids]
if new_listings:
    body = format_email(new_listings, previous_ids)
    send_email(body)
else:
    print("No new listings, skipping email.")