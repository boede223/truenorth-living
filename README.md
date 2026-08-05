# TrueNorth Living — website

Everything you need is in this folder. No accounts, servers, or subscriptions
are required to work on it locally.

---

## The 30-second version

- **To change words, photos, prices, or bed counts:** go to `yoursite.com/admin/`.
  Never touch code.
- **To see it on your own machine:** run `python3 build.py --serve`, open
  <http://localhost:8000>.
- **To publish:** save in the admin panel. It goes live by itself in ~1 minute.

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

### Through the admin panel (normal way)

Go to `yoursite.com/admin/`. You'll see four sections:

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

### Directly in the files (if you'd rather)

Open any file in `content/` in a text editor and change the text between the
quotation marks. Then run `python3 build.py`. Don't delete commas or braces.

---

## Running it locally

You need Python 3, which is already on every Mac.

```bash
python3 build.py --serve
```

Then open <http://localhost:8000>. Edit a file in `content/`, run
`python3 build.py` in a second terminal, and refresh the browser. The preview
server keeps running through rebuilds.

To build without serving:

```bash
python3 build.py
```

---

## Putting it online

### One-time setup

1. **Put this folder on GitHub.** Create a free account at github.com, make a
   new repository (call it `truenorth-living`), and follow the "push an
   existing repository" instructions it gives you.

2. **Connect Netlify.** Sign up free at netlify.com → *Add new site* →
   *Import an existing project* → pick your GitHub repo. Netlify reads
   `netlify.toml` and configures itself — build command and publish directory
   are already set. Click deploy.

3. **Point the editor at your repo.** Open `admin/config.yml`, find this line
   near the top:

   ```yaml
   repo: YOUR-GITHUB-USERNAME/truenorth-living   # ← CHANGE THIS
   ```

   Replace it with your actual GitHub username and repo name. Save, commit,
   push.

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
- [ ] **TROHN / NARR status** — About page. State whether you're certified,
      in process, or aligned with the standards. Do not claim a certification
      you don't hold.
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

## Known trade-off

Adding a page means editing `build.py`, not just the admin panel. That's the
cost of having no framework — worth it at this size, and worth revisiting if
you ever get past a dozen pages or start a blog.
