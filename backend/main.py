import os
from datetime import datetime

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="LinkedIn Post Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5-20251001"


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
async def generate(req: GenerateRequest):
    try:
        if req.type == "post":
            if not req.topic:
                raise HTTPException(status_code=400, detail="Topic is required for post generation.")
            user_prompt = build_post_prompt(req.topic, req.tone, req.length)
        elif req.type == "reply":
            if not req.original_post:
                raise HTTPException(status_code=400, detail="Original post text is required for reply generation.")
            user_prompt = build_reply_prompt(req.original_post, req.tone, req.angle)
        else:
            raise HTTPException(status_code=400, detail="Type must be 'post' or 'reply'.")

        message = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()
        tokens_used = message.usage.input_tokens + message.usage.output_tokens
        return GenerateResponse(text=text, tokens_used=tokens_used)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
