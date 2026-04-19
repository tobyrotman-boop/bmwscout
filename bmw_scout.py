import requests
import re
import json
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "diamondnightsdues@gmail.com" 
SENDER_PASSWORD = "zbvc slvi ehea jmsh"
RECIPIENTS = ["tobyrotman@gmail.com"]

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

def save_json(listings):
    preferred_colors = ['black', 'white', 'gray', 'grey', 'silver']
    now = datetime.datetime.now().isoformat()
    
    output = []
    for l in listings:
        color = l.get('exteriorColor', 'Not listed')
        output.append({
            'year': l['year'],
            'trim': l.get('trim', ''),
            'price': l['price'],
            'mileage': l['mileage'],
            'exteriorColor': color,
            'preferredColor': any(c in color.lower() for c in preferred_colors),
            'location': l.get('cityRegion', 'Not listed'),
            'deal': l.get('dealFinderRating', 'N/A'),
            'vin': l.get('vin', 'N/A'),
            'listingId': l.get('listingId', ''),
            'url': make_url(l.get('listingId', '')),
            'imageUrl': l.get('imageUrl', ''),
            'lastUpdated': now
        })
    
    with open('listings.json', 'w') as f:
        json.dump({'lastUpdated': now, 'listings': output}, f, indent=2)
    
    print(f"Saved {len(output)} listings to listings.json")

def format_email(listings):
    preferred_colors = ['black', 'white', 'gray', 'grey', 'silver']
    body = f"BMW X5 Scout — {len(listings)} AWD listings found today\n\n"
    
    for l in listings:
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

listings = search_cargurus()
print(f"Found {len(listings)} listings")
save_json(listings)
body = format_email(listings)
send_email(body)