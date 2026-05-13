import json
import os
import time
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

EMAIL_ADDRESS = os.getenv("MY_GMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

with open("config.json", "r") as f:
    config = json.load(f)

CHECK_INTERVAL = config["settings"]["check_interval_seconds"]
RESET_EVERY_CYCLE = config["settings"]["reset_seenproducts_every_cycle"]
BUDGET = config["budget"]
WATCHLIST = config.get("watchlist", [])
SEEN_FILE = "seen_products.json"

# Load in as dictionary
if os.path.exists(SEEN_FILE):
    seen = json.load(open(SEEN_FILE))
else:
    seen = {}

def saveSeen():
    json.dump(seen, open(SEEN_FILE, "w"), indent=2)

def getGrade(text):
    text = text.upper()
    if "HG" in text:
        return "HG"
    if "MG" in text:
        return "MG"
    if "RG" in text:
        return "RG"
    if "PG " in text:
        return "PG"
    if "ENTRY GRADE" in text:
        return "Entry Grade"
    return None

def sendEmail(watchlist_items, deal_items):
    if not watchlist_items and not deal_items:
        return

    msg = MIMEMultipart()
    total = len(watchlist_items) + len(deal_items)
    msg["Subject"] = f"{total} Deals Found"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    html = ""

    if watchlist_items:
        html += "<h2>From Watchlist </h2><ul>"
        for i in watchlist_items:
            html += f"""
            <li>
                <b>{i['title']}</b>
                <br>
                Site: {i['site']}
                <br>
                Price: <b>${i['price']}</b> (MSRP: ${i['compare_at']})
                <br>
                <a href="{i['url']}">Link</a>
                <br><br>
            </li>
            """
        html += "</ul>"

    if deal_items:
        html += "<h2>Items on Sale</h2><ul>"
        for i in deal_items:
            if i.get("price_drop"):
                label = f"Price drop from ${i['seen_price']}"
            else:
                label = "New deal"
            html += f"""
            <li>
                <b>{i['title']}</b>
                <br>
                Site: {i['site']}
                <br>
                Price: <b>${i['price']}</b> (MSRP: ${i['compare_at']}) — {label}
                <br>
                Grade: {i['grade']}
                <br>
                <a href="{i['url']}">Link</a>
                <br><br>
            </li>
            """
        html += "</ul>"

    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        error = smtp.send_message(msg)
            
        if not error:
            print("Email sent")
        else:
            print(f"Failed to send email")
        
def checkWatchlist():
    results = []

    for item in WATCHLIST:
        url = item["url"]
        site = item["site"]

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        product = r.json().get("product", {})

        title = product.get("title", "")
        variants = product.get("variants", [])
        if not variants:
            continue

        variant = variants[0]
        price = float(variant["price"])
        compare_at = variant.get("compare_at_price")

        if not compare_at or float(compare_at) <= price:
            continue

        handle = product.get("handle", "")
        if "usagundam" in url:
            product_url = f"https://www.usagundamstore.com/products/{handle}"
        else:
            product_url = f"https://www.gundamplanet.com/products/{handle}"

        print(f"[watchlist] On Sale: {title}")
        results.append({
            "title": title,
            "price": price,
            "compare_at": float(compare_at),
            "site": site,
            "url": product_url
        })

    return results

def gundamPlanet():
    results = []
    site = config["gundamplanet"]
    base_url = site["base_url"]
    limit = site["limit"]
    page = 1

    while True:
        print(f"[gundamplanet] Checking page {page}")
        params = {"limit": limit, "page": page, "sort_by": "created-descending"}

        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        products = response.json().get("products", [])

        if not products:
            print("[gundamplanet] No more products")
            break


        for product in products:
            title = product.get("title", "")
            variants = product.get("variants", [])
            if not variants:
                continue

            variant = variants[0]
            # Only items in stock
            if not variant.get("available"):
                continue
            
            # Only if item is on sale
            price = float(variant["price"])
            compare_at = variant.get("compare_at_price")
            if not compare_at or float(compare_at) <= price:
                continue

            grade = getGrade(title)
            if not grade or grade not in BUDGET:
                continue
            
            # Checks if item is within the budget
            rule = BUDGET[grade]
            if not (rule["min"] <= price <= rule["max"]):
                continue
            
            # Checks if item is already seen
            uid = f"gundamplanet::{product['id']}"
            entry = seen.get(uid)
            if entry and price >= entry["price"]:
                continue

            # Continues if not seen or price is goes even lower than last seen
            if entry is not None and price < entry["price"]:
                price_drop = True
            else:
                price_drop = False
            seen[uid] = {"price": price, "title": title}

            results.append({
                "title": title,
                "price": price,
                "compare_at": float(compare_at),
                "grade": grade,
                "site": "Gundam Planet",
                "url": f"https://www.gundamplanet.com/products/{product['handle']}",
                "price_drop": price_drop,
                "seen_price": entry["price"] if price_drop else None
            })
            message = f"[gundamplanet] MATCH: {title} ${price}"
            if price_drop:
                message += " (price drop)"
            print(message)

        page += 1
        time.sleep(1)

    return results

def usaGundam():
    results = []

    for base_url in config["usagundam"]["collections"]:
        page = 1

        while True:
            print(f"[usagundam] Checking page {page}")
            r = requests.get(base_url, params={"page": page}, timeout=30)
            r.raise_for_status()
            data = r.json()

            results_list = data.get("results", [])
            if not results_list:
                print("[usagundam] No more products")
                break

            for product in results_list:
                title = product.get("name", "")
                # Only items in stock
                if product.get("ss_available") != "1":
                    continue
                
                # Only if item is on sale
                price = float(product.get("price", 0))
                compare_at = product.get("msrp")
                if not compare_at or float(compare_at) <= price:
                    continue
                
                grade = getGrade(title)
                if not grade or grade not in BUDGET:
                    continue
                
                # Checks if item is within the budget
                rule = BUDGET[grade]
                if not (rule["min"] <= price <= rule["max"]):
                    continue
                
                # Checks if item is already seen
                uid = f"usagundam::{product['uid']}"
                entry = seen.get(uid)
                if entry and price >= entry["price"]:
                    continue
                
                # Continues if not seen or price is goes even lower than last seen
                if entry is not None and price < entry["price"]:
                    price_drop = True
                else:
                    price_drop = False

                seen[uid] = {"price": price, "title": title}

                results.append({
                    "title": title,
                    "price": price,
                    "compare_at": float(compare_at),
                    "grade": grade,
                    "site": "USA Gundam Store",
                    "url": f"https://www.usagundamstore.com{product['url']}",
                    "price_drop": price_drop,
                    "seen_price": entry["price"] if price_drop else None
                })
                message = f"[usagundam] MATCH: {title} ${price}"
                if price_drop:
                    message += " (price drop)"
                print(message)

            page += 1

    return results

def main():
    print("Running")

    while True:
        if RESET_EVERY_CYCLE:
            seen.clear()
        watchlist_items = checkWatchlist()
        deal_items = gundamPlanet() + usaGundam()

        if watchlist_items or deal_items:
            sendEmail(watchlist_items, deal_items)
            saveSeen()
        else:
            print("No matches")

        print("SLEEPING")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()