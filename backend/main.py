import os
from datetime import datetime, date

import anthropic
import httpx
import stripe
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from gotrue import SyncGoTrueClient

app = FastAPI(title="LinkedIn Post Generator API", docs_url=None, redoc_url=None)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

claude = anthropic.Anthropic()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

auth_client = SyncGoTrueClient(
    url=f"{SUPABASE_URL}/auth/v1",
    headers={"apikey": SUPABASE_SERVICE_KEY},
)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")

MODEL = "claude-haiku-4-5-20251001"
FREE_DAILY_LIMIT = 3
MAX_TOPIC_LENGTH = 500
MAX_POST_LENGTH = 2000
MAX_ANGLE_LENGTH = 200


def db_request(method: str, table: str, params: dict | None = None, body: dict | None = None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    with httpx.Client() as client:
        if method == "GET":
            res = client.get(url, headers=headers, params=params)
        elif method == "POST":
            res = client.post(url, headers=headers, params=params, json=body)
        elif method == "PATCH":
            res = client.patch(url, headers=headers, params=params, json=body)
        else:
            raise ValueError(f"Unsupported method: {method}")
    res.raise_for_status()
    return res.json() if res.text else None


class AuthRequest(BaseModel):
    email: str
    password: str


class GenerateRequest(BaseModel):
    type: str
    topic: str | None = None
    tone: str = "thought-leader"
    length: str = "medium"
    original_post: str | None = None
    angle: str | None = None


class GenerateResponse(BaseModel):
    text: str
    tokens_used: int
    usage_remaining: int


async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        res = auth_client.get_user(token)
        return res.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


def get_usage_today(user_id: str) -> int:
    today = date.today().isoformat()
    rows = db_request("GET", "usage", params={
        "user_id": f"eq.{user_id}",
        "date": f"eq.{today}",
        "select": "generation_count",
    })
    if rows:
        return rows[0]["generation_count"]
    return 0


def increment_usage(user_id: str):
    today = date.today().isoformat()
    rows = db_request("GET", "usage", params={
        "user_id": f"eq.{user_id}",
        "date": f"eq.{today}",
        "select": "id,generation_count",
    })
    if rows:
        db_request("PATCH", "usage", params={"id": f"eq.{rows[0]['id']}"}, body={
            "generation_count": rows[0]["generation_count"] + 1,
        })
    else:
        db_request("POST", "usage", body={
            "user_id": user_id,
            "date": today,
            "generation_count": 1,
        })


def get_user_plan(user_id: str) -> str:
    rows = db_request("GET", "users", params={
        "id": f"eq.{user_id}",
        "select": "plan",
    })
    if rows:
        return rows[0]["plan"]
    return "free"


@app.post("/auth/signup")
async def signup(req: AuthRequest):
    try:
        res = auth_client.sign_up({"email": req.email, "password": req.password})
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed.")
        db_request("POST", "users", body={
            "id": res.user.id,
            "email": req.email,
            "plan": "free",
        })
        return {
            "access_token": res.session.access_token if res.session else None,
            "user": {"id": res.user.id, "email": req.email, "plan": "free"},
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Signup failed. Email may already be in use.")


@app.post("/auth/login")
async def login(req: AuthRequest):
    try:
        res = auth_client.sign_in_with_password(
            {"email": req.email, "password": req.password}
        )
        plan = get_user_plan(res.user.id)
        usage = get_usage_today(res.user.id)
        return {
            "access_token": res.session.access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "plan": plan,
                "usage_today": usage,
            },
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@app.get("/auth/me")
async def me(user=Depends(get_current_user)):
    plan = get_user_plan(user.id)
    usage = get_usage_today(user.id)
    return {
        "id": user.id,
        "email": user.email,
        "plan": plan,
        "usage_today": usage,
    }


SYSTEM_PROMPT = """You are an expert LinkedIn content writer. You write posts that feel authentic, human, and engaging — never corporate, spammy, or cringe.

Rules:
- Write in first person
- No hashtags unless specifically asked
- No emojis unless the tone calls for casual/fun
- No "I'm excited to announce" or similar LinkedIn cliches
- Keep paragraphs short (1-2 sentences)
- Use line breaks between paragraphs for readability
- Hook the reader in the first line
- End with something that invites engagement (a question, a bold take, a call to reflect)
- Sound like a real person, not a brand
- Match the exact tone and length requested"""

TONE_GUIDES = {
    "thought-leader": "Write with authority and insight. Share a perspective that makes people think. Back up claims with reasoning or experience.",
    "casual": "Write like you're texting a smart friend. Keep it loose, conversational, maybe a bit funny. No jargon.",
    "storytelling": "Open with a specific moment or scene. Pull the reader in with narrative. Deliver the insight through the story.",
    "contrarian": "Challenge conventional wisdom. Take a bold stance. Be respectful but don't hedge — commit to the take.",
    "educational": "Teach something useful. Break down a complex idea simply. Use examples. Make the reader feel smarter.",
    "motivational": "Be genuine, not cheesy. Share a real lesson. Inspire through honesty, not hype.",
    "supportive": "Add genuine value to the conversation. Validate their point and build on it.",
    "add-value": "Share additional insight, a relevant example, or a useful resource that extends the original point.",
    "respectful-disagree": "Acknowledge their perspective, then share a different view with reasoning. Stay classy.",
    "curious": "Ask a thoughtful follow-up question that deepens the conversation. Show genuine interest.",
    "witty": "Be clever and quick. A sharp observation or a well-timed joke. Don't try too hard.",
}

LENGTH_GUIDES = {
    "short": "Keep it under 60 words. Punchy and direct.",
    "medium": "Aim for 100-140 words. Enough room to develop an idea.",
    "long": "Go for 180-220 words. Tell a story or break down a concept fully.",
}


def build_post_prompt(topic: str, tone: str, length: str) -> str:
    tone_guide = TONE_GUIDES.get(tone, TONE_GUIDES["thought-leader"])
    length_guide = LENGTH_GUIDES.get(length, LENGTH_GUIDES["medium"])
    return f"""Write a LinkedIn post about: {topic}

Tone: {tone_guide}

Length: {length_guide}

Write ONLY the post text. No meta-commentary, no "here's your post", no quotation marks around it."""


def build_reply_prompt(original_post: str, tone: str, angle: str | None) -> str:
    tone_guide = TONE_GUIDES.get(tone, TONE_GUIDES["supportive"])
    angle_instruction = f"\nSpecific angle to take: {angle}" if angle else ""
    return f"""Write a LinkedIn reply/comment to this post:

---
{original_post}
---

Tone: {tone_guide}
{angle_instruction}

Keep it concise (2-4 sentences). Sound natural, not like an AI. Write ONLY the reply text."""


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, user=Depends(get_current_user)):
    plan = get_user_plan(user.id)
    usage = get_usage_today(user.id)

    if plan != "pro" and usage >= FREE_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="Daily free limit reached. Upgrade to Pro for unlimited.")

    try:
        if req.type == "post":
            if not req.topic:
                raise HTTPException(status_code=400, detail="Topic is required for post generation.")
            if len(req.topic) > MAX_TOPIC_LENGTH:
                raise HTTPException(status_code=400, detail=f"Topic must be under {MAX_TOPIC_LENGTH} characters.")
            if req.tone not in TONE_GUIDES:
                raise HTTPException(status_code=400, detail="Invalid tone.")
            if req.length not in LENGTH_GUIDES:
                raise HTTPException(status_code=400, detail="Invalid length.")
            user_prompt = build_post_prompt(req.topic, req.tone, req.length)
        elif req.type == "reply":
            if not req.original_post:
                raise HTTPException(status_code=400, detail="Original post text is required for reply generation.")
            if len(req.original_post) > MAX_POST_LENGTH:
                raise HTTPException(status_code=400, detail=f"Post text must be under {MAX_POST_LENGTH} characters.")
            if req.angle and len(req.angle) > MAX_ANGLE_LENGTH:
                raise HTTPException(status_code=400, detail=f"Angle must be under {MAX_ANGLE_LENGTH} characters.")
            if req.tone not in TONE_GUIDES:
                raise HTTPException(status_code=400, detail="Invalid tone.")
            user_prompt = build_reply_prompt(req.original_post, req.tone, req.angle)
        else:
            raise HTTPException(status_code=400, detail="Type must be 'post' or 'reply'.")

        message = claude.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()
        tokens_used = message.usage.input_tokens + message.usage.output_tokens

        increment_usage(user.id)
        new_usage = usage + 1
        remaining = max(0, FREE_DAILY_LIMIT - new_usage) if plan != "pro" else -1

        return GenerateResponse(text=text, tokens_used=tokens_used, usage_remaining=remaining)
    except HTTPException:
        raise
    except anthropic.APIError:
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable. Try again.")
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong. Try again.")


@app.post("/create-checkout-session")
async def create_checkout_session(user=Depends(get_current_user)):
    rows = db_request("GET", "users", params={
        "id": f"eq.{user.id}",
        "select": "stripe_customer_id",
    })
    customer_id = rows[0]["stripe_customer_id"] if rows and rows[0].get("stripe_customer_id") else None

    if not customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
        customer_id = customer.id
        db_request("PATCH", "users", params={"id": f"eq.{user.id}"}, body={
            "stripe_customer_id": customer_id,
        })

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=os.environ.get("STRIPE_SUCCESS_URL", "https://linkedin-post-gen.com/success"),
        cancel_url=os.environ.get("STRIPE_CANCEL_URL", "https://linkedin-post-gen.com/cancel"),
        metadata={"user_id": user.id},
    )
    return {"checkout_url": session.url}


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        rows = db_request("GET", "users", params={
            "stripe_customer_id": f"eq.{customer_id}",
            "select": "id",
        })
        if rows:
            db_request("PATCH", "users", params={"id": f"eq.{rows[0]['id']}"}, body={
                "plan": "pro",
            })

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        rows = db_request("GET", "users", params={
            "stripe_customer_id": f"eq.{customer_id}",
            "select": "id",
        })
        if rows:
            is_active = subscription.get("status") in ("active", "trialing")
            db_request("PATCH", "users", params={"id": f"eq.{rows[0]['id']}"}, body={
                "plan": "pro" if is_active else "free",
            })

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        attempt_count = invoice.get("attempt_count", 0)
        if attempt_count >= 3:
            rows = db_request("GET", "users", params={
                "stripe_customer_id": f"eq.{customer_id}",
                "select": "id",
            })
            if rows:
                db_request("PATCH", "users", params={"id": f"eq.{rows[0]['id']}"}, body={
                    "plan": "free",
                })

    return JSONResponse(content={"received": True})


CONFIRM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Email Confirmed</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh;
background:#f5f5f5;color:#1a1a1a}
.card{text-align:center;background:#fff;padding:48px 40px;border-radius:12px;
box-shadow:0 2px 12px rgba(0,0,0,0.08);max-width:420px}
.check{width:56px;height:56px;background:#e8f5e9;border-radius:50%;
display:inline-flex;align-items:center;justify-content:center;margin-bottom:20px}
.check svg{width:28px;height:28px;color:#2e7d32}
h1{font-size:22px;font-weight:600;margin-bottom:8px}
p{font-size:14px;color:#666;line-height:1.5}
</style>
</head>
<body>
<div class="card">
<div class="check">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
<polyline points="20 6 9 17 4 12"></polyline>
</svg>
</div>
<h1>Email confirmed!</h1>
<p>You can close this tab and go back to the extension to log in.</p>
</div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return CONFIRM_HTML


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
