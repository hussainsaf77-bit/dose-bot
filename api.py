import os, json, hmac, hashlib, uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx, jwt, bcrypt
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://finwslipvvasokmuxdla.supabase.co")
SUPABASE_ANON = os.getenv("SUPABASE_KEY", "sb_publishable_7g9H8VEBGrgGcF9CEfLrNg_Bu6xlorY")
SUPABASE_SERVICE = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_ANON)
JWT_SECRET = os.getenv("JWT_SECRET", "dosebot2026supersecretkey!xK9mQp")
JWT_ALGO = "HS256"
BOT_SECRET = os.getenv("BOT_SECRET", "bot-secret-key-123")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://hussainsaf77-bit.github.io/dose-web")
PADDLE_API_KEY = os.getenv("PADDLE_API_KEY", "")
PADDLE_WEBHOOK_SECRET = os.getenv("PADDLE_WEBHOOK_SECRET", "")
PADDLE_SANDBOX = os.getenv("PADDLE_SANDBOX", "true").lower() == "true"
PADDLE_BASE = "https://sandbox-api.paddle.com" if PADDLE_SANDBOX else "https://api.paddle.com"

class DB:
    def _h(self, write=False):
        key = SUPABASE_SERVICE if write else SUPABASE_ANON
        return {"apikey": key, "Authorization": f"Bearer {key}",
                "Content-Type": "application/json", "Prefer": "return=representation"}

    async def select(self, table, query="", limit=100):
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}?{query}&limit={limit}", headers=self._h())
        return r.json() if r.status_code == 200 else []

    async def select_one(self, table, query):
        rows = await self.select(table, query, limit=1)
        return rows[0] if rows else None

    async def insert(self, table, data):
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=self._h(True), json=data)
        if r.status_code in (200, 201):
            d = r.json(); return d[0] if isinstance(d, list) else d
        raise HTTPException(500, f"DB error: {r.text[:100]}")

    async def update(self, table, query, data):
        async with httpx.AsyncClient() as c:
            r = await c.patch(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=self._h(True), json=data)
        return r.status_code in (200, 204)

    async def delete(self, table, query):
        async with httpx.AsyncClient() as c:
            r = await c.delete(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=self._h(True))
        return r.status_code in (200, 204)

db = DB()

def hash_pw(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_pw(pw, h): return bcrypt.checkpw(pw.encode(), h.encode())
def make_token(uid, email):
    return jwt.encode({"sub": uid, "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)}, JWT_SECRET, algorithm=JWT_ALGO)

security = HTTPBearer(auto_error=False)

async def get_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    if not cred: raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALGO])
        uid = payload["sub"]
    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError: raise HTTPException(401, "Invalid token")
    user = await db.select_one("users", f"uid=eq.{uid}")
    if not user: raise HTTPException(401, "User not found")
    return user

def require_bot(x_bot_secret: str = Header(None)):
    if x_bot_secret != BOT_SECRET: raise HTTPException(401, "Unauthorized")

async def get_active_sub(uid):
    return await db.select_one("subscriptions", f"uid=eq.{uid}&status=eq.active")

async def get_user_plan(uid):
    sub = await get_active_sub(uid)
    if sub:
        pm = {"1w":"Basic","1m":"Basic","3m":"Pro","6m":"Pro","1y":"Pro Annual","yearly":"Pro Annual"}
        pn = pm.get(sub.get("plan",""), sub.get("plan",""))
        plan = await db.select_one("plans", f"name=eq.{pn}")
        if plan: return plan
    return await db.select_one("plans", "name=eq.Free") or {
        "name":"Free","name_ar":"مجاني","search_limit":5,"reminder_limit":0,
        "has_pdf":False,"has_interactions":False,"price":0,"interval":"free"}

async def check_limit(uid, action):
    plan = await get_user_plan(uid)
    limit = plan.get("search_limit" if action=="search" else "reminder_limit", 5)
    if limit == -1: return True, 0, -1
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log = await db.select_one("usage_logs", f"uid=eq.{uid}&action=eq.{action}&date=eq.{today}")
    used = log.get("count", 0) if log else 0
    return used < limit, used, limit

async def inc_usage(uid, action):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log = await db.select_one("usage_logs", f"uid=eq.{uid}&action=eq.{action}&date=eq.{today}")
    if log:
        await db.update("usage_logs", f"uid=eq.{uid}&action=eq.{action}&date=eq.{today}",
                        {"count": log["count"]+1})
    else:
        await db.insert("usage_logs", {"uid":uid,"action":action,"date":today,"count":1})

app = FastAPI(title="DoseBot API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

class RegisterBody(BaseModel):
    email: str; password: str; name: Optional[str] = None

class LoginBody(BaseModel):
    email: str; password: str

class LinkTgBody(BaseModel):
    telegram_id: str

class ChangePwBody(BaseModel):
    current_password: str; new_password: str

class ReminderBody(BaseModel):
    drug_name: str; dose: Optional[str]=None; times: list
    days: Optional[list]=[]; email_notify: bool=False

@app.get("/")
async def root(): return {"status":"ok","service":"dose-web-api","version":"2.0.0"}

@app.get("/health")
async def health(): return {"status":"ok","timestamp":datetime.utcnow().isoformat()}

@app.get("/test123")
async def test(): return {"status":"ok","version":"2.0.0"}

@app.post("/auth/register")
@app.post("/api/register")
async def register(data: RegisterBody):
    email = data.email.lower().strip()
    if await db.select_one("users", f"email=eq.{email}"):
        raise HTTPException(400, "البريد الإلكتروني مسجّل مسبقاً")
    if len(data.password) < 8: raise HTTPException(400, "كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    uid = f"w_{uuid.uuid4().hex[:12]}"
    name = data.name or email.split("@")[0]
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/users",
            headers=db._h(True),
            json={"uid":uid,"email":email,"password_hash":hash_pw(data.password),
                  "name":name,"lang":"ar","level":"registered"})
    return {"token":make_token(uid,email),"user":{"uid":uid,"email":email,"name":name}}

@app.post("/auth/login")
async def login(data: LoginBody):
    email = data.email.lower().strip()
    user = await db.select_one("users", f"email=eq.{email}")
    if not user or not verify_pw(data.password, user.get("password_hash","")):
        raise HTTPException(401, "البريد أو كلمة المرور غير صحيحة")
    uid = user["uid"]
    return {"token":make_token(uid,email),"user":{"uid":uid,"email":email,"name":user.get("name","")}}

@app.get("/auth/me")
async def me(user: dict = Depends(get_user)):
    uid = user["uid"]
    plan = await get_user_plan(uid)
    sub = await get_active_sub(uid)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log = await db.select_one("usage_logs", f"uid=eq.{uid}&action=eq.search&date=eq.{today}")
    return {"uid":uid,"email":user.get("email"),"name":user.get("name"),
            "telegram_linked":bool(user.get("telegram_id")),
            "telegram_id":user.get("telegram_id"),
            "plan":{"name":plan.get("name"),"name_ar":plan.get("name_ar"),
                    "interval":plan.get("interval"),"search_limit":plan.get("search_limit"),
                    "reminder_limit":plan.get("reminder_limit"),"has_pdf":plan.get("has_pdf",False),
                    "has_interactions":plan.get("has_interactions",False)},
            "subscription":{"status":sub["status"] if sub else "free",
                            "expires":sub.get("end_date") if sub else None},
            "usage_today":{"searches":log.get("count",0) if log else 0,
                           "search_limit":plan.get("search_limit",5)}}

@app.post("/auth/link-telegram")
async def link_tg(data: LinkTgBody, user: dict = Depends(get_user)):
    ex = await db.select_one("users", f"telegram_id=eq.{data.telegram_id}")
    if ex and ex["uid"] != user["uid"]: raise HTTPException(400, "مرتبط بمستخدم آخر")
    await db.update("users", f"uid=eq.{user['uid']}", {"telegram_id":data.telegram_id})
    return {"message":"تم ربط Telegram بنجاح ✅"}

@app.post("/auth/change-password")
async def change_pw(data: ChangePwBody, user: dict = Depends(get_user)):
    if not verify_pw(data.current_password, user.get("password_hash","")):
        raise HTTPException(400, "كلمة المرور الحالية غير صحيحة")
    await db.update("users", f"uid=eq.{user['uid']}", {"password_hash":hash_pw(data.new_password)})
    return {"message":"تم تغيير كلمة المرور ✅"}

@app.get("/plans")
async def get_plans():
    plans = await db.select("plans", "is_active=eq.true&order=sort_order.asc")
    return [{"id":p.get("id"),"name":p.get("name"),"name_ar":p.get("name_ar"),
             "paddle_price_id":p.get("paddle_price_id"),"price":p.get("price"),
             "interval":p.get("interval"),"search_limit":p.get("search_limit"),
             "reminder_limit":p.get("reminder_limit"),"has_pdf":p.get("has_pdf",False),
             "has_interactions":p.get("has_interactions",False),
             "features":p.get("features") or []} for p in plans]

@app.get("/subscription/status")
async def sub_status(user: dict = Depends(get_user)):
    uid = user["uid"]
    plan = await get_user_plan(uid)
    sub = await get_active_sub(uid)
    return {"plan":plan.get("name"),"plan_ar":plan.get("name_ar"),
            "status":sub["status"] if sub else "free",
            "expires":sub.get("end_date") if sub else None,
            "search_limit":plan.get("search_limit"),"reminder_limit":plan.get("reminder_limit")}

@app.post("/subscription/cancel")
async def cancel_sub(user: dict = Depends(get_user)):
    sub = await get_active_sub(user["uid"])
    if not sub: raise HTTPException(404, "لا يوجد اشتراك نشط")
    await db.update("subscriptions", f"uid=eq.{user['uid']}&status=eq.active", {"status":"cancelled"})
    return {"message":"تم إلغاء الاشتراك ✅"}

@app.post("/paddle/webhook")
@app.post("/api/paddle/webhook")
async def paddle_webhook(request: Request):
    raw = await request.body()
    data = json.loads(raw)
    event = data.get("event_type","")
    ev = data.get("data",{})
    sub_id = ev.get("id")
    if event == "subscription.created":
        email = ev.get("customer",{}).get("email","")
        user = await db.select_one("users", f"email=eq.{email.lower()}")
        if user:
            items = ev.get("items",[])
            price_id = items[0]["price"]["id"] if items else None
            plan = await db.select_one("plans", f"paddle_price_id=eq.{price_id}")
            if plan:
                await db.update("subscriptions", f"uid=eq.{user['uid']}&status=eq.active",
                                {"status":"superseded"})
                await db.insert("subscriptions", {
                    "uid":user["uid"],"plan":plan["name"],
                    "start_date":datetime.utcnow().strftime("%Y-%m-%d"),
                    "end_date":ev.get("next_billed_at","")[:10],
                    "status":"active","amount":plan.get("price",0),
                    "paddle_subscription_id":sub_id})
    elif event in ("subscription.cancelled","subscription.canceled"):
        await db.update("subscriptions", f"paddle_subscription_id=eq.{sub_id}", {"status":"cancelled"})
    elif event == "subscription.past_due":
        await db.update("subscriptions", f"paddle_subscription_id=eq.{sub_id}", {"status":"past_due"})
    return {"status":"ok"}

@app.get("/bot/verify/{telegram_id}")
async def bot_verify(telegram_id: str, _=Depends(require_bot)):
    user = await db.select_one("users", f"telegram_id=eq.{telegram_id}")
    if not user: user = await db.select_one("users", f"uid=eq.{telegram_id}")
    if not user:
        return {"linked":False,"has_sub":False,"plan":"Free","search_limit":5,
                "reminder_limit":0,"register_url":f"{FRONTEND_URL}/auth.html"}
    uid = user["uid"]
    plan = await get_user_plan(uid)
    sub = await get_active_sub(uid)
    return {"linked":True,"has_sub":sub is not None,"uid":uid,"email":user.get("email"),
            "plan":plan.get("name"),"plan_ar":plan.get("name_ar"),
            "status":sub["status"] if sub else "free",
            "expires":sub.get("end_date") if sub else None,
            "search_limit":plan.get("search_limit"),"reminder_limit":plan.get("reminder_limit"),
            "upgrade_url":f"{FRONTEND_URL}/pricing.html"}

@app.post("/bot/track/{telegram_id}")
async def bot_track(telegram_id: str, action: str = "search", _=Depends(require_bot)):
    user = await db.select_one("users", f"telegram_id=eq.{telegram_id}")
    if not user: user = await db.select_one("users", f"uid=eq.{telegram_id}")
    if not user: return {"allowed":True,"used":0,"limit":5}
    uid = user["uid"]
    allowed, used, limit = await check_limit(uid, action)
    if allowed: await inc_usage(uid, action)
    return {"allowed":allowed,"used":used+(1 if allowed else 0),"limit":limit}

@app.get("/reminders")
async def list_rem(user: dict = Depends(get_user)):
    rows = await db.select("reminders", f"uid=eq.{user['uid']}&is_active=eq.true")
    return [{"id":r.get("id"),"drug_name":r.get("drug_name"),"dose":r.get("dose"),
             "times":r.get("times") or [],"days":r.get("days") or [],
             "email_notify":r.get("email_notify",False)} for r in rows]

@app.post("/reminders")
async def create_rem(data: ReminderBody, user: dict = Depends(get_user)):
    uid = user["uid"]
    plan = await get_user_plan(uid)
    limit = plan.get("reminder_limit",0)
    if limit == 0: raise HTTPException(403, "التذكيرات تتطلب خطة مدفوعة")
    if limit != -1:
        ex = await db.select("reminders", f"uid=eq.{uid}&is_active=eq.true")
        if len(ex) >= limit: raise HTTPException(403, f"الحد الأقصى {limit} تذكيرات")
    r = await db.insert("reminders", {"uid":uid,"drug_name":data.drug_name,"dose":data.dose,
                                       "times":data.times,"days":data.days or [],
                                       "email_notify":data.email_notify,"is_active":True})
    return {"id":r.get("id"),"message":"تم إنشاء التذكير ✅"}

@app.delete("/reminders/{rid}")
async def del_rem(rid: int, user: dict = Depends(get_user)):
    await db.update("reminders", f"id=eq.{rid}&uid=eq.{user['uid']}", {"is_active":False})
    return {"message":"تم الحذف ✅"}

@app.get("/usage/today")
async def usage_today(user: dict = Depends(get_user)):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logs = await db.select("usage_logs", f"uid=eq.{user['uid']}&date=eq.{today}")
    return {l["action"]:l["count"] for l in logs}

@app.post("/usage/track")
async def track(action: str="search", user: dict = Depends(get_user)):
    uid = user["uid"]
    allowed, used, limit = await check_limit(uid, action)
    if allowed: await inc_usage(uid, action)
    return {"allowed":allowed,"used":used+(1 if allowed else 0),"limit":limit}

@app.get("/history")
async def history(limit: int=20, user: dict = Depends(get_user)):
    return await db.select("drug_history", f"uid=eq.{user['uid']}&order=searched_at.desc", limit=limit)

@app.post("/history/add")
async def add_history(drug_name: str, drug_id: Optional[int]=None, user: dict = Depends(get_user)):
    await db.insert("drug_history", {"uid":user["uid"],"drug_name":drug_name,"drug_id":drug_id})
    return {"ok":True}

@app.post("/api/chat")
async def api_chat(request: Request):
    return {"reply":"API v2.0 - use /auth endpoints"}

@app.post("/api/create-checkout")
async def api_checkout(request: Request):
    return {"message":"Use Paddle.js directly from frontend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT",8000)))
