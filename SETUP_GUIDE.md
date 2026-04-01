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

## Step 1: Supabase Setup (15 min) — FREE

Supabase is the database that stores your users and tracks how many generations they've used each day.

### 1a. Create an Account
1. Go to **https://supabase.com** in your browser
2. Click **"Start your project"** (top right)
3. Sign up with your GitHub account (easiest) — click "Continue with GitHub" and authorize it
4. You're now on the Supabase dashboard

### 1b. Create a New Project
1. Click the **"New project"** button
2. You'll see a form:
   - **Organization**: Pick your default org (it was auto-created when you signed up)
   - **Name**: Type `linkedin-post-gen`
   - **Database Password**: Click "Generate a password" and **copy it somewhere safe** (you won't need it in the code, but save it anyway in case you need to connect to the DB directly later)
   - **Region**: Pick the one closest to you. If you're in the US, `US East (N. Virginia)` or `US West (Oregon)` are fine
3. Click **"Create new project"**
4. Wait 1-2 minutes while it provisions. You'll see a loading screen — don't close the tab

### 1c. Create the Database Tables
1. Once your project is ready, look at the **left sidebar**
2. Click **"SQL Editor"** (it has a terminal/code icon)
3. You'll see a blank editor. Click **"New query"** in the top left
4. Now open the file `backend/supabase_schema.sql` from this repo on your computer
5. **Copy the entire contents** of that file
6. **Paste it** into the SQL Editor in your browser
7. Click the green **"Run"** button (bottom right of the editor, or Ctrl+Enter)
8. You should see a green message: **"Success. No rows returned"** — this is correct! It created the tables but tables don't return rows when created
9. To verify: click **"Table Editor"** in the left sidebar. You should see two tables listed: `users` and `usage`

### 1d. Copy Your API Keys
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

### 1e. Disable Email Confirmation
By default, Supabase sends a confirmation email when someone signs up. For development and testing, turn this off so you can sign up and immediately use the app.

1. In the left sidebar, click **"Authentication"** (the key icon)
2. Click **"Providers"** in the submenu
3. Click on **"Email"** to expand it
4. Find **"Confirm email"** and toggle it **OFF**
5. Click **"Save"**

Later, before real launch, you can turn this back on if you want users to verify their email.

---

## Step 2: Stripe Setup (20 min) — FREE

Stripe handles payments. You won't be charged anything to set it up — Stripe only takes a cut when someone actually pays you.

### 2a. Create an Account
1. Go to **https://stripe.com** in your browser
2. Click **"Start now"** or **"Create account"**
3. Enter your email, full name, and a password
4. Verify your email (check your inbox, click the link)
5. You'll land on the Stripe Dashboard

### 2b. Stay in Test Mode
1. Look at the **top-right** of the Stripe dashboard
2. You should see a toggle that says **"Test mode"** — make sure it's **ON** (it should be orange/highlighted)
3. Test mode lets you simulate payments with fake credit cards — no real money involved
4. You'll switch to Live mode later when you're ready for real payments

### 2c. Create Your Product
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

### 2d. Get Your Secret API Key
1. In the left sidebar, click **"Developers"** (near the bottom)
2. Click **"API keys"**
3. You'll see two keys:
   - **Publishable key** — starts with `pk_test_` (you don't need this one)
   - **Secret key** — starts with `sk_test_`. Click **"Reveal test key"** to see it
4. **Copy the Secret key** and save it as `STRIPE_SECRET_KEY`
5. **Never share this key or commit it to GitHub** — it gives full access to your Stripe account

### 2e. Set Up Webhook (do this AFTER Step 3)
You'll come back to this step after deploying to Railway, because you need your backend URL first. Skip ahead to Step 3, then come back here.

1. In Stripe, go to **"Developers"** > **"Webhooks"** (in the left sidebar)
2. Click **"+ Add endpoint"**
3. In the **"Endpoint URL"** field, paste: `https://YOUR-RAILWAY-URL/webhook` (replace with your actual Railway URL from Step 3c)
4. Click **"+ Select events"** under "Listen to"
5. Search for and check these 4 events:
   - `checkout.session.completed` (search "checkout")
   - `customer.subscription.updated` (search "subscription")
   - `customer.subscription.deleted` (search "subscription")
   - `invoice.payment_failed` (search "invoice")
6. Click **"Add events"**, then **"Add endpoint"**
7. You'll be taken to the webhook detail page
8. Find **"Signing secret"** — click **"Reveal"** to see it. It starts with `whsec_`
9. **Copy this** and save it as `STRIPE_WEBHOOK_SECRET`

---

## Step 3: Deploy Backend to Railway (15 min) — Free 30-day trial, then **$5/month**

Railway hosts your Python backend so it's accessible from the internet. The Trial plan lasts 30 days for free. After that, you need the Hobby plan at **$5/month** to keep it running. You'll need to add a credit card when signing up, but you won't be charged until the trial ends.

### 3a. Create an Account
1. Go to **https://railway.com** in your browser
2. Click **"Login"** (top right), then **"Login with GitHub"**
3. Authorize Railway to access your GitHub account

### 3b. Create a New Project
1. Once logged in, click **"+ New Project"** (top right)
2. Click **"Deploy from GitHub Repo"**
3. You'll see a list of your GitHub repos — find and click **`linkedin-post-gen`**
4. **IMPORTANT — Set the Root Directory:**
   - Railway will show a configuration panel before deploying
   - Look for a **"Root Directory"** field (or click "Settings" on the service)
   - Type **`backend`** in the Root Directory field
   - This tells Railway to only look at the `backend/` folder (where the Python code is), not the whole repo
   - **If you skip this, the deploy WILL fail** (Railway won't know it's a Python app)
5. Click **"Deploy"**
6. The build will start — you can watch the logs. It will probably fail at first because environment variables aren't set yet. That's normal — keep going.

### 3c. Generate a Public URL
1. Click on your service (the purple box that appeared)
2. Go to the **"Settings"** tab
3. Scroll down to **"Networking"** > **"Public Networking"**
4. Click **"Generate Domain"**
5. Railway will give you a URL like: `https://linkedin-post-gen-production.up.railway.app`
6. **Copy this URL** — you need it for the webhook (Step 2e) and the extension (Step 4)

### 3d. Add Environment Variables
1. Click on your service, then go to the **"Variables"** tab
2. Click **"+ New Variable"** for each of these (copy-paste the names exactly):

| Variable Name | What to paste | Where you got it |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Your Anthropic account (console.anthropic.com > API Keys) |
| `SUPABASE_URL` | `https://abcdefgh.supabase.co` | Step 1d |
| `SUPABASE_SERVICE_KEY` | `eyJhbGci...` (long key) | Step 1d |
| `STRIPE_SECRET_KEY` | `sk_test_...` | Step 2d |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Step 2e (come back and add this after you create the webhook) |
| `STRIPE_PRICE_ID` | `price_...` | Step 2c |
| `STRIPE_SUCCESS_URL` | `https://your-landing-page.com/success` | Use any URL for now, update after Step 6 |
| `STRIPE_CANCEL_URL` | `https://your-landing-page.com` | Use any URL for now, update after Step 6 |

3. After adding each variable, Railway will auto-redeploy. Wait for the last redeploy to finish (green "Active" status).

### 3e. Go Back and Finish Step 2e
Now that you have your Railway URL, go back to Step 2e and create the Stripe webhook. Then come back and add `STRIPE_WEBHOOK_SECRET` to Railway variables.

### 3f. Verify It Works
1. Open your browser and go to: `https://YOUR-RAILWAY-URL/health` (replace with your actual URL)
2. You should see: `{"status":"ok","timestamp":"2026-04-01T..."}`
3. If you see this, your backend is live and working

**If the deploy fails:**
- Click on the failed deployment to see the build logs
- Make sure Root Directory is set to `backend`
- Make sure all environment variables are added (even with placeholder values)
- Check that the build log shows "Python" being detected

---

## Step 4: Update Extension for Production (2 min) — FREE

1. Open the file `extension/popup/popup.js` on your computer
2. Find line 3 which says:
   ```js
   const API_BASE = "http://localhost:8000";
   ```
3. Change it to your Railway URL:
   ```js
   const API_BASE = "https://your-actual-railway-url.up.railway.app";
   ```
4. Save the file
5. If you already loaded the extension in Chrome, go to `chrome://extensions`, find "LinkedIn Post Generator", and click the refresh icon to reload it

---

## Step 5: Publish to Chrome Web Store (15 min) — **$5 one-time fee**

This is the only step that costs money upfront. Google charges a one-time $5 fee to become a Chrome Web Store developer.

### 5a. Create Developer Account
1. Go to **https://chrome.google.com/webstore/devconsole** in your browser
2. Sign in with your Google account
3. You'll be asked to **pay a $5 one-time registration fee** — pay with a credit/debit card
4. Fill in the developer information (name, email, etc.)
5. You may need to verify your identity — follow the prompts

### 5b. Create Extension Icons
The extension currently has placeholder blue squares as icons. You need real icons before publishing.

1. Go to **https://www.canva.com** (free) or use any image editor
2. Create 3 images — they should all be the same design, just different sizes:
   - `icon16.png` — 16x16 pixels
   - `icon48.png` — 48x48 pixels
   - `icon128.png` — 128x128 pixels
3. Design suggestion: a simple "LI" text or a pen/writing icon on a LinkedIn-blue (#0a66c2) background
4. Download them as PNG files
5. Replace the files in `extension/icons/` with your new icons (same filenames)

### 5c. Take Screenshots
Chrome Web Store requires at least 1 screenshot. Take 2-3 for a better listing.

1. Load the extension locally first:
   - Open Chrome, go to `chrome://extensions`
   - Toggle **"Developer mode"** ON (top right)
   - Click **"Load unpacked"** and select the `extension/` folder
2. Click the extension icon to open the popup
3. Take a screenshot of the popup (you can use Windows Snipping Tool: `Win + Shift + S`)
4. Recommended screenshots:
   - The popup with "New post" tab open (showing the form)
   - The popup with a generated post in the output area (use localhost backend to generate a real one)
   - The popup with "Smart reply" tab open
5. Screenshots must be **1280x800** or **640x400** pixels — resize if needed

### 5d. Zip the Extension
1. Navigate to the `extension/` folder on your computer
2. Select ALL files and folders inside it (`manifest.json`, `popup/`, `content/`, `background/`, `icons/`)
3. Right-click > **"Compress to ZIP file"** (or "Send to > Compressed folder" on Windows)
4. **Important**: The ZIP should contain `manifest.json` at the root level, NOT inside an `extension/` subfolder
   - Correct: `your.zip/manifest.json`
   - Wrong: `your.zip/extension/manifest.json`

### 5e. Upload and Submit
1. Go back to the Chrome Web Store Developer Dashboard
2. Click **"+ New Item"** (top right)
3. Upload your ZIP file
4. Fill in the listing (use `store-listing.md` in the repo for all the copy):
   - **Name**: LinkedIn Post Generator — AI Writer & Smart Replies
   - **Summary**: Copy the short description from `store-listing.md`
   - **Description**: Copy the detailed description from `store-listing.md`
   - **Category**: Productivity
   - **Language**: English
5. Upload your screenshots
6. You'll also need to fill in:
   - **Privacy policy**: You can use a free generator like https://www.freeprivacypolicy.com — or write a simple one stating you collect email for auth and don't sell data
   - **Single purpose description**: "Generates LinkedIn posts and replies using AI"
7. Click **"Submit for review"**
8. Review takes **1-3 business days**. You'll get an email when it's approved (or if they need changes).

---

## Step 6: Build Landing Page — FREE

Use Bolt AI to generate and deploy a landing page for free.

1. Go to **https://bolt.new** in your browser
2. Paste this prompt:

> Build a simple landing page for a Chrome extension called "LinkedIn Post Generator." It generates LinkedIn posts and smart replies using AI. Pricing: Free (3/day) or Pro ($7.99/mo unlimited). Include: hero section with headline + CTA button linking to the Chrome Web Store listing, feature list (6 tones, smart reply, copy to clipboard), pricing section (Free vs Pro), and a footer. Use LinkedIn blue (#0a66c2) as the primary color. Make it clean and modern, single page, mobile responsive.

3. Bolt will generate the page — review it and make any tweaks
4. Click **"Deploy"** in Bolt — it will deploy to Netlify for free
5. You'll get a URL like `https://your-site.netlify.app`
6. Go back to **Railway > Variables** and update:
   - `STRIPE_SUCCESS_URL` → `https://your-site.netlify.app/success`
   - `STRIPE_CANCEL_URL` → `https://your-site.netlify.app`
7. After the Chrome Web Store listing is live, update the CTA button link on the landing page to point to it

---

## Step 7: Go Live Checklist

Go through each item and check it off:

- [ ] Supabase project created and schema SQL run
- [ ] Supabase email confirmation disabled (for testing)
- [ ] Stripe account created
- [ ] Stripe product created ($7.99/mo recurring)
- [ ] Backend deployed to Railway with Root Directory set to `backend`
- [ ] All 8 environment variables added to Railway
- [ ] `/health` endpoint returns OK in browser
- [ ] Stripe webhook created with your Railway URL + all 4 events
- [ ] `STRIPE_WEBHOOK_SECRET` added to Railway variables
- [ ] `API_BASE` in popup.js updated to Railway URL
- [ ] Placeholder icons replaced with real icons
- [ ] Extension zipped correctly (manifest.json at zip root)
- [ ] Extension uploaded to Chrome Web Store
- [ ] Store listing filled out with screenshots + privacy policy
- [ ] Landing page built and deployed
- [ ] `STRIPE_SUCCESS_URL` and `STRIPE_CANCEL_URL` updated in Railway

### When You're Ready for Real Payments
1. In Stripe, switch from **Test mode** to **Live mode** (toggle in top-right)
2. Go to **Developers > API keys** and copy the **live** secret key (`sk_live_...`)
3. In Railway, update `STRIPE_SECRET_KEY` to the live key
4. In Stripe, create a **new webhook** in Live mode with the same endpoint URL and events
5. Update `STRIPE_WEBHOOK_SECRET` in Railway with the new live webhook secret
6. Create a new Product/Price in Live mode and update `STRIPE_PRICE_ID` in Railway

---

## Testing Payments (Before Going Live)

While in Stripe Test mode, use these fake credit card numbers — no real money is charged:

| Card Number | Result |
|---|---|
| `4242 4242 4242 4242` | Payment succeeds |
| `4000 0000 0000 0002` | Payment is declined |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |

For all test cards: use any future expiry date (e.g., `12/30`), any 3-digit CVC (e.g., `123`), and any billing ZIP.

### Test the Full Flow
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
