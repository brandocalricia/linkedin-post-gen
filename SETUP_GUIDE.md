# Full Setup Guide

Everything you need to do manually to get this live. All the code is already written — this guide covers the dashboard/account setup steps that can't be automated.

---

## Step 1: Supabase Setup (15 min)

### 1a. Create Project
1. Go to supabase.com and sign up / log in
2. Click "New project"
3. Name it `linkedin-post-gen`
4. Set a database password (save it somewhere)
5. Choose the closest region to your users
6. Click "Create new project" and wait for it to provision

### 1b. Run the Schema SQL
1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click "New query"
3. Paste the entire contents of `backend/supabase_schema.sql`
4. Click "Run"
5. You should see "Success. No rows returned" — that means the tables were created

### 1c. Grab Your Keys
1. Go to **Settings > API** in the Supabase dashboard
2. Copy these two values:
   - **Project URL** — looks like `https://abcdefgh.supabase.co`
   - **service_role key** (under "Project API keys") — the long one labeled "secret", NOT the anon key
3. Save both for Step 4

### 1d. Disable Email Confirmation (for dev/testing)
1. Go to **Authentication > Providers > Email**
2. Toggle OFF "Confirm email"
3. This lets users sign up and immediately use the app without checking their inbox
4. You can re-enable this before launch if you want email verification

---

## Step 2: Stripe Setup (20 min)

### 2a. Create Account
1. Go to stripe.com and create an account
2. You can stay in **Test mode** while developing (toggle in top-right)

### 2b. Create Product + Price
1. Go to **Products** in the Stripe dashboard
2. Click "Add product"
3. Name: `LinkedIn Post Generator Pro`
4. Pricing: **Recurring**, $7.99/month
5. Click "Save product"
6. On the product page, find the **Price ID** — it starts with `price_` (e.g., `price_1Abc123...`)
7. Copy that Price ID for Step 4

### 2c. Get API Keys
1. Go to **Developers > API keys**
2. Copy the **Secret key** — starts with `sk_test_` (test mode) or `sk_live_` (production)
3. Save it for Step 4

### 2d. Set Up Webhook
1. Go to **Developers > Webhooks**
2. Click "Add endpoint"
3. Endpoint URL: `https://YOUR-BACKEND-URL/webhook` (you'll get this URL after deploying in Step 3)
4. Select these events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click "Add endpoint"
6. On the webhook page, click "Reveal" under **Signing secret** — starts with `whsec_`
7. Copy that for Step 4

---

## Step 3: Deploy Backend to Railway (10 min)

### 3a. Deploy
1. Go to railway.com and sign up with GitHub
2. Click "New Project" > "Deploy from GitHub repo"
3. Select the `linkedin-post-gen` repo
4. Railway will auto-detect the code — set the **Root directory** to `backend`
5. Click "Deploy"

### 3b. Add Environment Variables
1. In Railway, go to your service > **Variables**
2. Add each of these:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (`sk-ant-...`) |
| `SUPABASE_URL` | From Step 1c (e.g., `https://abcdefgh.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | From Step 1c (the service_role key) |
| `STRIPE_SECRET_KEY` | From Step 2c (`sk_test_...` or `sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | From Step 2d (`whsec_...`) |
| `STRIPE_PRICE_ID` | From Step 2b (`price_...`) |
| `STRIPE_SUCCESS_URL` | `https://your-landing-page.com/success` (or any URL) |
| `STRIPE_CANCEL_URL` | `https://your-landing-page.com` (or any URL) |

3. Railway will auto-redeploy after adding variables

### 3c. Get Your Production URL
1. In Railway, go to your service > **Settings > Networking**
2. Click "Generate Domain" to get a public URL
3. It'll look like: `https://linkedin-post-gen-production.up.railway.app`
4. Copy this URL — you need it for Step 2d (webhook URL) and Step 5

### 3d. Update Stripe Webhook URL
1. Go back to **Stripe > Developers > Webhooks**
2. Update the endpoint URL to: `https://YOUR-RAILWAY-URL/webhook`

### 3e. Verify It Works
Open your browser and go to: `https://YOUR-RAILWAY-URL/health`
You should see: `{"status":"ok","timestamp":"..."}`

---

## Step 4: Update Extension for Production (2 min)

1. Open `extension/popup/popup.js`
2. Change the `API_BASE` line to your Railway URL:
   ```js
   const API_BASE = "https://linkedin-post-gen-production.up.railway.app";
   ```
3. Save the file

---

## Step 5: Publish to Chrome Web Store (15 min)

### 5a. Developer Account
1. Go to the Chrome Web Store Developer Dashboard: https://chrome.google.com/webstore/devconsole
2. Pay the one-time $5 registration fee
3. Complete the developer verification

### 5b. Prepare Extension Files
1. Replace the placeholder icons in `extension/icons/` with real icons:
   - `icon16.png` — 16x16 px
   - `icon48.png` — 48x48 px
   - `icon128.png` — 128x128 px
   - Use a simple logo (the LinkedIn blue color #0a66c2 works well)
   - Canva, Figma, or any icon generator works for this
2. Zip the entire `extension/` folder (not the parent — the zip should contain `manifest.json` at the root level)

### 5c. Upload & Submit
1. In the Developer Dashboard, click "New Item"
2. Upload the zip file
3. Fill in the listing details (use `store-listing.md` in the repo for copy):
   - Name, short description, detailed description
   - Category: Productivity
   - Language: English
4. Upload screenshots (at least 1 required, 1280x800 or 640x400):
   - Take a screenshot of the popup in action (Chrome DevTools > toggle device toolbar can help size it)
   - Take a screenshot showing a generated post
5. Submit for review — takes 1-3 business days

---

## Step 6: Build Landing Page

Use Bolt AI (bolt.new) to generate a landing page. Give it this prompt:

> Build a simple landing page for a Chrome extension called "LinkedIn Post Generator." It generates LinkedIn posts and smart replies using AI. Pricing: Free (3/day) or Pro ($7.99/mo unlimited). Include: hero section with headline + CTA button linking to the Chrome Web Store listing, feature list (6 tones, smart reply, copy to clipboard), pricing section (Free vs Pro), and a footer. Use LinkedIn blue (#0a66c2) as the primary color. Make it clean and modern, single page, mobile responsive.

After Bolt generates it, deploy it (Bolt can deploy to Netlify for free).

Update `STRIPE_SUCCESS_URL` and `STRIPE_CANCEL_URL` in Railway to point to your landing page URL.

---

## Step 7: Go Live Checklist

- [ ] Supabase project created and schema SQL run
- [ ] Email confirmation disabled (or enabled if you want verification)
- [ ] Stripe product created ($7.99/mo)
- [ ] Stripe webhook configured with all 4 events
- [ ] Backend deployed to Railway with all env vars set
- [ ] `/health` endpoint returns OK
- [ ] Stripe webhook URL updated to Railway URL
- [ ] `API_BASE` in popup.js updated to Railway URL
- [ ] Placeholder icons replaced with real icons
- [ ] Extension zipped and uploaded to Chrome Web Store
- [ ] Store listing filled out with screenshots
- [ ] Landing page built and deployed
- [ ] Stripe switched from Test to Live mode (when ready for real payments)
- [ ] Update `STRIPE_SECRET_KEY` in Railway to the live key

---

## Testing Payments (Before Going Live)

While in Stripe Test mode, use these test card numbers:
- **Success**: `4242 4242 4242 4242` (any future expiry, any CVC)
- **Decline**: `4000 0000 0000 0002`
- **Requires auth**: `4000 0025 0000 3155`

1. Sign up in the extension
2. Use all 3 free generations
3. Click "Upgrade to Pro"
4. Use test card `4242 4242 4242 4242`
5. After checkout completes, close and reopen the popup
6. Badge should show "Pro" and plan should show "Pro plan"
7. Generate unlimited posts to confirm

To test cancellation:
1. Go to Stripe dashboard > Customers > find the test customer
2. Cancel their subscription
3. Close and reopen the popup — should show "Free plan" again
