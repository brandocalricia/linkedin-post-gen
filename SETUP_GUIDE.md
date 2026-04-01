# Full Setup Guide

Everything you need to do manually to get this live. All the code is already written — this guide covers the dashboard/account setup steps.

**Total cost to launch:**
- Anthropic API: **$5 minimum credit purchase** (required to get an API key — pays for AI generations, lasts a long time with Haiku)
- Supabase: FREE (free tier, no time limit)
- Stripe: FREE to create (they take 2.9% + $0.30 per transaction only when you get paid)
- Railway: Free 30-day trial, then **$5/month** (Hobby plan — required to keep your backend running)
- Chrome Web Store: **$5 one-time fee** (required to publish)
- Landing page (Bolt + Netlify): FREE

**Upfront cost: $15** — $5 Anthropic API credits + $5 Chrome Web Store (one-time) + $5 Railway (monthly, starts after 30-day trial). Stripe and Supabase are free.

---

## Step 1: Supabase Setup (15 min) — FREE --- DONE

Supabase is the database that stores your users and tracks how many generations they've used each day.

### 1a. Create an Account --- DONE
1. Go to **https://supabase.com** in your browser
2. Click **"Start your project"** (top right)
3. Sign up with your GitHub account (easiest) — click "Continue with GitHub" and authorize it
4. You're now on the Supabase dashboard

### 1b. Create a New Project --- DONE
1. Click the **"New project"** button
2. You'll see a form:
   - **Organization**: Pick your default org (it was auto-created when you signed up)
   - **Name**: Type `linkedin-post-gen`
   - **Database Password**: Click "Generate a password" and **copy it somewhere safe** (you won't need it in the code, but save it anyway in case you need to connect to the DB directly later)
   - **Region**: Pick the one closest to you. If you're in the US, `US East (N. Virginia)` or `US West (Oregon)` are fine
3. Click **"Create new project"**
4. Wait 1-2 minutes while it provisions. You'll see a loading screen — don't close the tab

### 1c. Create the Database Tables --- DONE
1. Once your project is ready, look at the **left sidebar**
2. Click **"SQL Editor"** (it has a terminal/code icon)
3. You'll see a blank editor. Click **"New query"** in the top left
4. Now open the file `backend/supabase_schema.sql` from this repo on your computer
5. **Copy the entire contents** of that file
6. **Paste it** into the SQL Editor in your browser
7. Click the green **"Run"** button (bottom right of the editor, or Ctrl+Enter)
8. You should see a green message: **"Success. No rows returned"** — this is correct! It created the tables but tables don't return rows when created
9. To verify: click **"Table Editor"** in the left sidebar. You should see two tables listed: `users` and `usage`

### 1d. Copy Your API Keys --- DONE
1. In the left sidebar, click **"Settings"** (the gear icon at the very bottom)
2. Click **"API"** in the Settings submenu
3. You'll see a section called **"Project URL"**:
   - Copy the URL — it looks like `https://abcdefgh.supabase.co`
   - **Save this as `SUPABASE_URL`** (paste it in a notes app or text file for now)
4. Scroll down to **"Project API keys"**:
   - You'll see two keys: `anon` (public) and `service_role` (secret)
   - Copy the **`service_role`** key — it's the longer one. It will say "This key has the ability to bypass Row Level Security" — that's the one you want
   - **Save this as `SUPABASE_SERVICE_KEY`**
   - **DO NOT** use the `anon` key — that one doesn't have permission to manage users

### 1e. Email Confirmation --- DONE
Supabase email confirmation is working. The `/` route on your backend serves a confirmation page that tells users to close the tab and log in via the extension.

---

## Step 2: Stripe Setup (20 min) — FREE --- DONE

Stripe handles payments. You won't be charged anything to set it up — Stripe only takes a cut when someone actually pays you.

### 2a. Create an Account --- DONE
1. Go to **https://stripe.com** in your browser
2. Click **"Start now"** or **"Create account"**
3. Enter your email, full name, and a password
4. Verify your email (check your inbox, click the link)
5. You'll land on the Stripe Dashboard

### 2b. Stay in Test Mode --- DONE (currently using test keys)
1. Look at the **top-right** of the Stripe dashboard
2. You should see a toggle that says **"Test mode"** — make sure it's **ON** (it should be orange/highlighted)
3. Test mode lets you simulate payments with fake credit cards — no real money involved
4. You'll switch to Live mode later when you're ready for real payments

### 2c. Create Your Product --- DONE
1. In the left sidebar, click **"Product catalog"** (or **"Products"** on some layouts)
2. Click the **"+ Add product"** button (top right)
3. Fill in the form:
   - **Name**: `LinkedIn Post Generator Pro`
   - **Description** (optional): `Unlimited LinkedIn post and reply generation`
4. Under **Pricing**:
   - Click **"Add price"** if it's not already showing a price form
   - **Pricing model**: "Standard pricing" (default)
   - **Price**: Type `7.99`
   - **Currency**: USD (should be default)
   - **Billing period**: Select **"Recurring"**, then **"Monthly"**
5. Click **"Save product"**
6. You'll be taken to the product detail page
7. Under the **"Pricing"** section, you'll see your price listed. It has an ID that starts with **`price_`** (like `price_1Abc123XYZ...`)
   - Click on the price row to expand it, or hover to find a "copy" icon
   - **Copy this Price ID** and save it as `STRIPE_PRICE_ID`

### 2d. Get Your Secret API Key --- DONE
1. In the left sidebar, click **"Developers"** (near the bottom)
2. Click **"API keys"**
3. You'll see two keys:
   - **Publishable key** — starts with `pk_test_` (you don't need this one)
   - **Secret key** — starts with `sk_test_`. Click **"Reveal test key"** to see it
4. **Copy the Secret key** and save it as `STRIPE_SECRET_KEY`
5. **Never share this key or commit it to GitHub** — it gives full access to your Stripe account

### 2e. Set Up Webhook --- DONE
Webhook endpoint is live at `https://linkedin-post-gen-production-a8f4.up.railway.app/webhook` with all 4 events configured. Test payment with `checkout.session.completed` webhook confirmed working (200 OK, plan updates to Pro).

---

## Step 3: Deploy Backend to Railway (15 min) — Free 30-day trial, then **$5/month** --- DONE

Railway hosts your Python backend so it's accessible from the internet.

### 3a. Create an Account --- DONE

### 3b. Create a New Project --- DONE
- Deployed from GitHub repo `linkedin-post-gen`
- Root Directory set to `backend`
- Auto-deploys on every `git push`

### 3c. Generate a Public URL --- DONE
- URL: `https://linkedin-post-gen-production-a8f4.up.railway.app`

### 3d. Add Environment Variables --- DONE
All 8 environment variables configured in Railway:

| Variable Name | Status |
|---|---|
| `ANTHROPIC_API_KEY` | Set |
| `SUPABASE_URL` | Set |
| `SUPABASE_SERVICE_KEY` | Set |
| `STRIPE_SECRET_KEY` | Set (test key: `sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Set (`whsec_...`) |
| `STRIPE_PRICE_ID` | Set (`price_...`) |
| `STRIPE_SUCCESS_URL` | **NEEDS UPDATE** — see Remaining Tasks |
| `STRIPE_CANCEL_URL` | **NEEDS UPDATE** — see Remaining Tasks |
| `ALLOWED_ORIGINS` | Set to `chrome-extension://ggcgoadbnnclgdibigejighpdafgfpdo` |

### 3e. Verify It Works --- DONE
- `/health` endpoint returns `{"status":"ok"}`
- Email confirmation page working at `/`
- Generation endpoint working
- Webhook receiving and processing Stripe events

---

## Step 4: Update Extension for Production (2 min) — FREE --- DONE

- `API_BASE` in `popup.js` set to `https://linkedin-post-gen-production-a8f4.up.railway.app`
- `manifest.json` updated with Railway URL in `host_permissions`
- `ALLOWED_ORIGINS` in Railway set to `chrome-extension://ggcgoadbnnclgdibigejighpdafgfpdo`
- Extension loaded locally and tested — post generation, signup, login, upgrade all working

---

## Step 5: Publish to Chrome Web Store (15 min) — **$5 one-time fee** --- IN PROGRESS

### 5a. Create Developer Account --- DONE
- $5 fee paid
- Developer verification submitted (waiting for approval — takes a few days)

### 5b. Create Extension Icons --- DONE

### 5c. Take Screenshots --- DONE

### 5d. Zip the Extension --- DONE
- `linkedin-post-gen-extension.zip` created at repo root

### 5e. Upload and Submit --- IN PROGRESS
- Extension draft saved in Chrome Web Store Developer Dashboard
- Listing info, screenshots, and promo tiles uploaded
- **Waiting on developer identity verification** before you can submit for review
- Once verified, go to the Developer Dashboard, open your draft, and click **"Submit for review"**
- Review takes **1-3 business days** after submission

---

## Step 6: Build Landing Page — FREE --- NOT STARTED

Use Bolt AI to generate and deploy a landing page for free.

1. Go to **https://bolt.new** in your browser
2. Paste this prompt:

> Build a simple landing page for a Chrome extension called "LinkedIn Post Generator." It generates LinkedIn posts and smart replies using AI. Pricing: Free (3/day) or Pro ($7.99/mo unlimited). Include: hero section with headline + CTA button linking to the Chrome Web Store listing, feature list (6 tones, smart reply, copy to clipboard), pricing section (Free vs Pro), and a footer. Use LinkedIn blue (#0a66c2) as the primary color. Make it clean and modern, single page, mobile responsive.

3. Bolt will generate the page — review it and make any tweaks
4. Click **"Deploy"** in Bolt — it will deploy to Netlify for free
5. You'll get a URL like `https://your-site.netlify.app`
6. Go back to **Railway > Variables** and update:
   - `STRIPE_SUCCESS_URL` → `https://your-site.netlify.app`
   - `STRIPE_CANCEL_URL` → `https://your-site.netlify.app`
7. After the Chrome Web Store listing is live, update the CTA button link on the landing page to point to it

---

## Step 7: Switch to Stripe Live Mode --- NOT STARTED

Do this when you're ready for real payments (after Chrome Web Store listing is approved).

1. In Stripe, switch from **Test mode** to **Live mode** (toggle in top-right)
2. Create a **new product** in Live mode:
   - Same as before: `LinkedIn Post Generator Pro`, $7.99/mo recurring
   - Copy the new `price_...` ID
3. Go to **Developers > API keys** in Live mode and copy the **live** secret key (`sk_live_...`)
4. Create a **new webhook** in Live mode:
   - Endpoint URL: `https://linkedin-post-gen-production-a8f4.up.railway.app/webhook`
   - Same 4 events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
   - Copy the new signing secret (`whsec_...`)
5. In **Railway > Variables**, update these 3 values:
   - `STRIPE_SECRET_KEY` → your live key (`sk_live_...`)
   - `STRIPE_WEBHOOK_SECRET` → your new live webhook secret (`whsec_...`)
   - `STRIPE_PRICE_ID` → your new live price ID (`price_...`)
6. Railway will auto-redeploy — real payments are now active

---

## Remaining Tasks (in order)

### 1. Update Stripe redirect URLs in Railway (2 min)
Go to Railway > Variables and update:
- `STRIPE_SUCCESS_URL` → `https://linkedin-post-gen-production-a8f4.up.railway.app` (temporary until you have a landing page)
- `STRIPE_CANCEL_URL` → `https://linkedin-post-gen-production-a8f4.up.railway.app` (temporary until you have a landing page)

### 2. Wait for Chrome Web Store developer verification
- You've already submitted for verification — this takes a few days
- Once approved, go to Developer Dashboard, open your draft, and click **"Submit for review"**
- Review takes 1-3 business days after that

### 3. Build landing page with Bolt (Step 6 above)
- You can do this while waiting for verification
- Once deployed, update `STRIPE_SUCCESS_URL` and `STRIPE_CANCEL_URL` in Railway to your landing page URL

### 4. Switch to Stripe Live mode (Step 7 above)
- Do this after the Chrome Web Store listing is approved and you're ready for real users
- Create new product, webhook, and API keys in Live mode
- Update 3 Railway env vars

### 5. Optional: Re-enable Supabase email confirmation
- If you want users to verify their email before using the app
- Go to Supabase > Authentication > Providers > Email > toggle "Confirm email" ON
- The confirmation flow already works (the `/` route serves a confirmation page)

---

## Testing Payments (Before Going Live)

While in Stripe Test mode, use these fake credit card numbers — no real money is charged:

| Card Number | Result |
|---|---|
| `4242 4242 4242 4242` | Payment succeeds |
| `4000 0000 0000 0002` | Payment is declined |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |

For all test cards: use any future expiry date (e.g., `12/30`), any 3-digit CVC (e.g., `123`), and any billing ZIP.

### Test the Full Flow --- DONE
1. Open the extension popup and create a new account (sign up)
2. Generate 3 posts to use up free generations
3. Click **"Upgrade to Pro"**
4. A Stripe Checkout page opens — enter test card `4242 4242 4242 4242`
5. Complete checkout
6. Close and reopen the extension popup
7. The badge should now show **"Pro"** and the footer should show **"Pro plan"**
8. Generate unlimited posts to confirm it works

### Test Cancellation
1. Go to **Stripe Dashboard > Customers**
2. Find the test customer and click on them
3. Under their subscription, click **"Cancel subscription"**
4. Close and reopen the extension popup
5. Should show **"Free plan"** again with 3/3 generations
