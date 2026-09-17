import os
import re
import datetime
import hashlib
from typing import Any, Dict, List

from curl_cffi import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def clean(s: str) -> str:
    return re.sub(r'\s+', ' ', str(s)).strip()

def parse_number(val: Any) -> float:
    try:
        if val is None: return 0.0
        n = float(str(val).replace(",", ""))
        return n if n == n else 0.0
    except ValueError:
        return 0.0

def parse_duration_to_seconds(val: Any) -> int:
    try:
        n = float(val)
        return int(round(n * 3600)) if n == n else 0
    except (ValueError, TypeError):
        return 0

def parse_wishnet_date(val: Any) -> datetime.datetime | None:
    input_str = clean(val)
    if not input_str: return None
    
    match = re.match(r"^(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s*(AM|PM)$", input_str, re.IGNORECASE)
    if not match: return None
        
    dd, mm, yyyy, hh0, min_val, sec, ap = match.groups()
    hh = int(hh0)
    if ap.upper() == "PM" and hh != 12: hh += 12
    if ap.upper() == "AM" and hh == 12: hh = 0
    
    dt = datetime.datetime(int(yyyy), int(mm), int(dd), hh, int(min_val), int(sec), tzinfo=datetime.timezone.utc)
    dt = dt - datetime.timedelta(hours=5, minutes=30)
    return dt

def stable_session_key(row: Dict[str, Any]) -> str:
    data = f"{row['planName']}|{row['ipAddress']}|{row['loginTime']}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def to_stored_row(row: Dict[str, Any]) -> Dict[str, Any]:
    logout = parse_wishnet_date(row.get("logoutTime"))
    return {
        "sessionKey": stable_session_key(row),
        "planName": row["planName"],
        "ipAddress": row["ipAddress"],
        "loginTime": parse_wishnet_date(row["loginTime"]),
        "logoutTime": logout,
        "sessionSeconds": row["sessionSeconds"],
        "downloadMB": row["downloadMB"],
        "uploadMB": row["uploadMB"],
        "source": "wishnet",
        "scrapedAt": datetime.datetime.now(datetime.timezone.utc)
    }

def scrape_wishnet() -> List[Dict[str, Any]]:
    login_url = os.getenv("WISHNET_LOGIN_URL", "https://www.wishnet.in/login")
    usage_url = os.getenv("WISHNET_USAGE_URL", "https://www.wishnet.in/portal/usage")
    usage_get_url = "https://www.wishnet.in/portal/usage/get"
    username = os.getenv("WISHNET_USERNAME")
    password = os.getenv("WISHNET_PASSWORD")
    
    if not username or not password:
        raise Exception("WISHNET_USERNAME and WISHNET_PASSWORD must be set in .env")

    session = requests.Session(impersonate="chrome120")
    session.headers.update({"Referer": login_url})

    res1 = session.get(login_url)
    match = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', res1.text)
    csrf_token = match.group(1) if match else ""
    
    if not csrf_token:
        raise Exception("Could not find CSRF token on login page")

    data = {
        "csrf_token": csrf_token,
        "customer_no": username,
        "password": password,
        "submit": "Sign in"
    }

    res2 = session.post(login_url, data=data, allow_redirects=False)
    
    if res2.status_code == 302:
        loc = res2.headers.get("Location", "")
        if "portal" in loc:
            res3 = session.get(loc)
            res4 = session.get(
                f"{usage_get_url}?_={int(datetime.datetime.now().timestamp() * 1000)}", 
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": usage_url,
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                }
            )
            try:
                payload = res4.json()
                if not isinstance(payload, list):
                    raise Exception(f"Unexpected Wishnet usage response shape")
                
                output = []
                for row in payload:
                    login = row.get("logged_in_at")
                    if not login: continue
                    output.append({
                        "planName": clean(row.get("plan", "Unknown")),
                        "ipAddress": clean(row.get("ip_address", "")),
                        "loginTime": login,
                        "logoutTime": row.get("logged_out_at"),
                        "sessionSeconds": parse_duration_to_seconds(row.get("used_for_hrs")),
                        "downloadMB": parse_number(row.get("downloaded_mbs")),
                        "uploadMB": parse_number(row.get("uploaded_mbs"))
                    })
                return output
            except Exception as e:
                raise Exception(f"Wishnet API fetch error: {e}")
        else:
            raise Exception("Login failed (redirected to another location)")
    else:
        raise Exception(f"Login failed with status {res2.status_code}")

def run_sync():
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB")
    if not uri or not db_name:
        raise Exception("MongoDB URI and DB name must be set")
        
    client = MongoClient(uri)
    db = client[db_name]
    usage_col = db["usage"]
    logs_col = db["logs"]
    
    started_at = datetime.datetime.now(datetime.timezone.utc)
    log_id = logs_col.insert_one({
        "startedAt": started_at,
        "status": "running",
        "recordsFound": 0, "recordsInserted": 0, "recordsUpdated": 0, "error": None
    }).inserted_id
    
    try:
        scraped = scrape_wishnet()
        inserted = 0; updated = 0
        
        for row in scraped:
            doc = to_stored_row(row)
            session_key = doc["sessionKey"]
            result = usage_col.update_one(
                {"sessionKey": session_key},
                {"$set": doc, "$setOnInsert": {"firstSeenAt": datetime.datetime.now(datetime.timezone.utc)}},
                upsert=True
            )
            if result.upserted_id is not None: inserted += 1
            elif result.modified_count > 0: updated += 1
                
        finished_at = datetime.datetime.now(datetime.timezone.utc)
        duplicates = max(0, len(scraped) - inserted)
        
        logs_col.update_one({"_id": log_id}, {"$set": {
            "finishedAt": finished_at, "status": "success",
            "recordsFound": len(scraped), "recordsInserted": inserted,
            "recordsUpdated": updated, "duplicates": duplicates, "error": None
        }})
        
        return {"status": "success", "recordsFound": len(scraped), "recordsInserted": inserted, "recordsUpdated": updated, "duplicates": duplicates}
        
    except Exception as e:
        logs_col.update_one({"_id": log_id}, {"$set": {
            "finishedAt": datetime.datetime.now(datetime.timezone.utc), "status": "error", "error": str(e)
        }})
        raise e
