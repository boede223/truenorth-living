# TrueNorth Living — website

Everything you need is in this folder. No accounts, servers, or subscriptions
are required to work on it locally.

---

## The 30-second version

**Right now, on this Mac, with no accounts:**

```bash
python3 build.py --serve
```

Open <http://localhost:8000/admin/> in Chrome → click **Work with Local
Repository** → choose the `TrueNorth` folder. You get the full visual editor,
and the site refreshes itself as you save.

**After you deploy** (see below), the same editor lives at
`yoursite.com/admin/` and publishes to the real site.

---

## How the site is put together

```
content/*.json   ← all your words, prices, photos. This is the only thing that changes day to day.
      │
      ▼
  build.py       ← reads the JSON, writes finished HTML
      │
      ▼
   _site/        ← the actual website that gets published
```

`assets/` holds the stylesheet, the JavaScript, and uploaded images.
`admin/` is the editor. `templates/` is unused — the page structure lives in
`build.py`.

Why a build step instead of a normal database-driven site: Google indexes
plain HTML instantly and reliably. For a local business where most of your
traffic will come from someone typing "sober living near me" into a phone,
that matters more than anything else on this page.

---

## Editing the site

There are three ways in. They all change the same files, so you can mix them
freely.

### 1. The visual editor on your own Mac — works today, no accounts

This is the one to start with. Nothing to sign up for, and nothing you do here
is public until you deploy.

1. Open Terminal, and run:

   ```bash
   cd ~/TrueNorth && python3 build.py --serve
   ```

2. Open **Chrome** (this needs Chrome or Edge — Safari and Firefox don't
   support the folder-access feature yet) and go to
   <http://localhost:8000/admin/>.

3. Click **Work with Local Repository** and select your `TrueNorth` folder
   when the picker appears. Grant access.

You now have the full editor. Change something, hit Save, and the site at
<http://localhost:8000> **refreshes itself** — no rebuilding, no reloading.
Leave the site open in one tab and the editor in another and you can watch
your changes land.

Terminal stays running the whole time. Press `Ctrl+C` when you're done.

If you break something (delete a comma in a file, say), the terminal prints the
error and keeps serving the last version that worked. Fix it and it recovers on
its own. You cannot get the site into a broken state this way.

### 2. The visual editor on the live site — after you deploy

Once the site is on Netlify, go to `yoursite.com/admin/` from anywhere,
including your phone. Same editor, except Save publishes to the real site in
about a minute.

Either way, you'll see four sections:

| Section | What's in it |
| --- | --- |
| **Houses & Availability** | Add/remove houses, change bed counts, upload house photos, set weekly rates |
| **Pages** | The words on the home, about, cost, FAQ, and application pages |
| **Contact & Settings** | Phone number, address, and the crisis bar at the top of every page |

Click something, change it, press **Save**. The site rebuilds and republishes
on its own, usually within a minute. It works fine on a phone.

**The thing you'll do most often** is Houses & Availability → change
`Beds open right now`. That number drives the "4 beds open tonight" pill on the
homepage and the coloured dot on each house card.

### Adding a house

Admin → **Houses & Availability** → scroll to the Houses list → **Add House**.
Fill in the form, and it appears on the site everywhere houses are shown:
the homepage grid, the Houses page, the Cost page rates table, the footer,
and the dropdown on the application form. You never edit more than one place.

Each house has a **Show on website** switch:

- **Off** — the house is invisible to visitors. Use this while you're still
  setting it up, negotiating the lease, or waiting on a certificate of
  occupancy. You can fill in everything in advance and flip it on later.
- **On** — it's live.

**Before your first house is live**, the site doesn't show empty shelves. It
switches to a pre-launch mode: the Houses page shows an "opening soon" notice
with a call-to-action, the homepage badge reads "Now taking applications for
our first house" instead of a bed count, the Cost page explains rates are being
set, and the empty Houses column drops out of the footer. All of that copy is
editable under Houses & Availability → *Before your first house opens*.

The moment you switch one house on, everything reverts to normal availability
mode by itself. Nothing to remember.

### 3. Directly in the files

Open any file in `content/` in a text editor and change the text between the
quotation marks. Don't delete commas, braces, or quotes. If `--serve` is
running, the site updates as soon as you save. Otherwise run `python3 build.py`.

---

## The two commands

```bash
python3 build.py --serve
```

Builds the site, serves it at <http://localhost:8000>, watches for changes, and
auto-refreshes your browser. This is the one you want while working.

```bash
python3 build.py
```

Builds once and stops. You rarely need this — Netlify runs it for you on every
deploy.

Python 3 is already on every Mac; there is nothing to install.

---

## Putting it online

### One-time setup

The editor is already pointed at `boede223/truenorth-living`, and the git
remote is already set. Steps 1 and 2 are what's left.

1. **Create the repository.** On github.com, *New repository* → name it exactly
   `truenorth-living` → **don't** add a README, .gitignore, or licence
   (this folder already has them). Create.

2. **Push this folder up:**

   ```bash
   cd ~/TrueNorth && git push -u origin main
   ```

   GitHub will ask you to sign in the first time.

3. **Connect Netlify.** Sign up free at netlify.com → *Add new site* →
   *Import an existing project* → pick `truenorth-living`. Netlify reads
   `netlify.toml` and configures itself — build command and publish directory
   are already set. Click deploy.

4. **Turn on form submissions.** In Netlify: *Site configuration* → *Forms* →
   enable form detection. Then *Forms* → *Form notifications* → add an email
   notification so applications land in your inbox. **Do this before you
   advertise the site** — until it's on, applications go nowhere.

5. **Connect your domain.** Netlify → *Domain management* → *Add a domain* →
   `thetruenorthliving.com`. Netlify walks you through the DNS records and
   issues the HTTPS certificate free.

### Logging in to the editor

Go to `yoursite.com/admin/` and click **Sign in with Token**. GitHub opens with
the right permissions pre-selected; generate the token, paste it back. It's
saved in your browser, so you do this once per device.

If you'd rather have a plain "Sign in with GitHub" button, deploy
[sveltia-cms-auth](https://github.com/sveltia/sveltia-cms-auth) (a free
Cloudflare Worker) and add its URL as `base_url:` under `backend:` in
`admin/config.yml`. Not required.

---

## Before you launch — the actual checklist

The site is fully built, but it currently describes a fictional version of your
organization. **26 spots hold placeholder text.** They're outlined in orange on
the live site so you can't miss them, and `python3 build.py` prints the count
every time it runs.

Highest impact first:

- [ ] **Phone number** — `content/site.json`. Currently `(214) 555-0134`, which
      is not your number. This appears about a dozen times across the site.
- [ ] **Street address** — same file. Used for Google's local business listing.
- [ ] **Your story** — About page. This paragraph does more work than anything
      else on the site. People are deciding whether to trust you with someone
      they love.
- [ ] **Relapse policy** — FAQ. The single most-read answer on any sober living
      site. Vagueness here costs you residents.
- [ ] **MAT policy** — FAQ. Say plainly whether you accept Suboxone, methadone,
      and Vivitrol. People search for this specifically.
- [ ] **Your first house**, once you have it — there's one template house
      already in the admin with Show on website switched off. Fill it in and
      switch it on. Until then the site runs in pre-launch mode on its own.
- [ ] **House photos** — the biggest single trust signal on the site. Real
      photos of real porches beat any stock image. Until you upload them,
      cards show deliberate placeholder art rather than looking broken.
- [ ] **Certification, if you ever get it** — nothing on the site claims any
      today, which is correct while you don't hold one. If you later certify
      with TROHN (the Texas affiliate of NARR, and the recognised certifying
      body here), add it under About → Standards. It's a genuine advantage
      with referral sources, and it's also required if you ever want state
      funding. Never list it before it's granted.
- [ ] **Testimonials** — replace with real, consented quotes, or delete the
      section. Attribute by role, not full name, unless you have written
      permission.
- [ ] **Team** — About page.
- [ ] **Scholarship and payment-plan details** — Cost page. Only promise what
      you'll honor.

### A note on the claims already in the copy

The homepage says calls are answered by a person and that move-in is usually
within 48 hours. The footer says calls are answered 24/7. Those are good,
concrete promises — which is exactly why you should only keep them if they're
true. Change them in `content/home.json` and `content/site.json` if they're not.

The "path north" timeline on the homepage and the "what happens next" steps on
the application page both describe a process that isn't running yet. They read
fine as a description of how things *will* work, but re-read them the week you
open and make sure they match what actually happens.

---

## Adding a hero video

Admin → Pages → Home page → **Background video**. Upload an MP4.

Keep it under about 8 MB or phones on cell data will see a blank hero while it
loads. It plays muted and looped, so it should work with no sound. Also upload
a **Background photo** — it's the first frame, and it's what shows on
connections too slow for the video. If you set only a photo, the site does a
slow Ken Burns drift over it. If you set neither, it paints its own night sky.

Footage that works: a porch light coming on at dusk, a front door opening,
hands doing dishes, a kitchen table with more than one chair pulled out.
Footage that doesn't: stock drone shots of city skylines, sunsets, or anyone
staring meaningfully into the middle distance.

---

## What's already handled

- Mobile-first, with a permanent tap-to-call bar at the bottom of every screen
- Crisis banner with 988 and the SAMHSA helpline on every page
- Full keyboard navigation, screen-reader landmarks, correct heading order,
  and a skip link
- `prefers-reduced-motion` respected throughout — every animation stops for
  users who ask for it
- LocalBusiness and FAQ structured data for Google
- `sitemap.xml` and `robots.txt`, regenerated on each build
- Spam honeypot on the application form
- Works with JavaScript disabled: every page reads, navigates, and the form
  still submits

## How the site is laid out

It's a **one-page site**. Everything lives on `/` as one scroll, with the nav
jumping between sections:

```
/            hero → the path north → how we run a house →
             #houses → #cost → #about → testimonials → #faq
/apply/      the application form (its own page)
/404.html    when a link is wrong
```

The application form keeps its own page on purpose: it's the thing you want
people to reach, worth linking directly in an email or an ad, and a long form
buried under a long page is a bad combination.

The site used to be five separate pages. Those URLs (`/homes/`, `/costs/`,
`/about/`, `/faq/`) now redirect to the matching section, so any link already
out in the world still works.

## Known trade-offs

**One page means less search surface.** Five separate pages could each rank for
different searches — "sober living cost dallas" had its own page to win with.
Now the homepage has to rank for everything. For a business your size the
homepage does most of the work anyway, but if you ever find you're not showing
up for cost or FAQ searches specifically, splitting those back out is the fix.
Everything needed to do that is still in the git history.

**Adding a page means editing `build.py`**, not just the admin panel. That's
the cost of having no framework — worth it at this size, and worth revisiting
if you ever start a blog.
