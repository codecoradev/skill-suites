---
name: copywriting
version: 1.4.0
description: |
  Copywriting techniques for AI-generated text to sound natural, persuasive, 
  and human. Covers 7 frameworks (AIDA, PAS, BAB, FAB, 4Ps, 4Cs, STAR-S), 
  Cialdini's 7 principles (including Unity), emotional copywriting, 
  storytelling, voice development, platform-specific patterns, and 
  Bahasa Indonesia-specific copywriting. Complements humanizer skills.
license: MIT
metadata:
  hermes:
    tags: [copywriting, writing, persuasion, content, frameworks, aida, storytelling]
compatibility: claude-code opencode
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Copywriting: Natural, Persuasive Writing for AI Output

Copywriting is not just about selling — it's about **writing that compels action or attention**. This skill covers techniques to make AI-generated text persuasive, engaging, and indistinguishable from good human writing.

**Pair with:** `creative/humanizer` (remove AI patterns) + `creative/humanizer-improve` (advanced patterns). This skill focuses on **what to write**; the humanizer skills focus on **what not to write**.

## When to Use This Skill

- Newsletter opening hooks
- Blog post introductions
- WhatsApp/business outreach messages
- Social media captions
- Product descriptions
- Landing page copy
- Email subject lines and bodies
- Any content where engagement matters

## Core Frameworks

### AIDA (Attention → Interest → Desire → Action)

The classic. Still works when done right.

| Stage | Purpose | AI Mistake |
|-------|---------|-----------|
| **Attention** | Stop the scroll | "In today's rapidly evolving..." — boring, generic |
| **Interest** | Make them want to read more | Data dump without narrative |
| **Desire** | Make them want the outcome | Feature lists instead of benefits |
| **Action** | Tell them what to do | "Contact us for more information" — too vague |

**Example (Newsletter Indo):**
- **Attention:** "Stripe baru naikin fee buat marketplace Indo. Dampaknya?"
- **Interest:** "Mulai 1 Agustus, fee naik 0.5% untuk semua marketplace transaction. Ini ngaruh ke seluruh ecosystem — dari Midtrans sampe Xendit."
- **Desire:** "Tapi ada workaround yang bisa tetep optimalin margin kamu tanpa pindah payment gateway."
- **Action:** "Baca breakdown-nya di bawah, atau langsung cek flow alternatifnya di sini."

### PAS (Problem → Agitation → Solution)

Most effective for technical content and B2B.

1. **Problem:** State the reader's problem clearly and specifically
2. **Agitation:** Make it hurt — show consequences of not solving it
3. **Solution:** Your answer, positioned as relief

**Example (Blog post):**
- **Problem:** "Your CI pipeline takes 45 minutes. Nobody wants to wait that long."
- **Agitation:** "While you wait, context-switching kills focus. By the time tests pass, you've forgotten what you were fixing."
- **Solution:** "Parallel test execution with `pytest-xdist` cuts that to 8 minutes. Here's the setup."

### BAB (Before → After → Bridge)

Effective for transformation stories and product demos.

1. **Before:** The pain point / current state
2. **After:** The ideal outcome / future state
3. **Bridge:** How to get there (your product/method)

**Example:**
- **Before:** "Mengirim invoice manual? Copy-paste dari spreadsheet, format beda-beda tiap client, lupa follow up."
- **After:** "Bayangin semua invoice jalan otomatis. Template rapi, reminder otomatis, pelacakan real-time."
- **Bridge:** "Nggak perlu tools mahal. Google Sheets + n8n bisa handle ini dalam 2 jam setup."

## Hook Techniques

### 1. The Surprising Fact
> "90% startup AI di Indonesia mati dalam 18 bulan pertama. Yang survive punya satu kesamaan."

### 2. The Controversial Take
> "TypeScript overrated buat project kecil. Di situ. Fight me."

### 3. The Specific Scenario
> "Kamu lagi debugging error 500 yang cuma muncul di production, bukan di local. Nggak keliatan di log."

### 4. The Direct Question
> "Terakhir kali kamu cek berapa biaya API OpenAI per bulan?"

### 5. The Contrarian
> "Stop pakai Docker buat development lokal. EC2 lebih cepat setup-nya."

**Rules untuk hooks:**
- Spesifik, bukan generik. "Startup AI di Indonesia" > "startup"
- Bisa dibaca dalam 3 detik
- Hindari clickbait — janji di hook harus ada di konten
- Untuk Indo: pakai bahasa sehari-hari, bukan bahasa formal
- Max 2 kalimat

## Structure Patterns

### Newsletter Structure
```
1. Hook (1-2 sentences)
2. Context/Setup (2-3 sentences) — why this matters NOW
3. Key Points (3-5 items, each 2-4 sentences)
4. Takeaway/Closing (1-2 sentences + CTA)
```

### Blog Post Introduction
```
1. Hook — grab attention
2. Problem statement — what's the pain
3. Stakes — why it matters
4. Promise — what this post will deliver
5. Transition — into the body
```

### WhatsApp Outreach
```
1. Name/personal greeting (1 line)
2. One relevant observation (1 line) — shows you know them
3. One pain point or opportunity (1-2 lines)
4. Soft question/CTA (1 line)
```

**Max 5-6 lines total.** Never more.

## Persuasion Principles

### Reciprocity
Give something valuable before asking. "Nih breakdown fee-nya dulu, gratis."

### Social Proof
Specific numbers, not vague claims. "2,000 developer Indo udah pake" > "banyak developer"

### Authority
Cite sources, show credentials. "Menurut laporan Stripe 2025..." not "Menurut beberapa sumber..."

### Scarcity
Real urgency, not fake. "Early bird sampai 31 Juli" > "Terbatas!" (unless truly limited)

### Specificity
Specific beats vague every time. "Potensi hemat Rp 2.5 juta/bulan" > "Bisa hemat biaya"

## Voice Development

### Finding Your Voice
Good copywriting sounds like a specific person, not a brand.

**Questions to answer:**
1. Formal or casual? (Newsletter: semi-casual. WA: casual. Blog: depends on topic)
2. Long sentences or short? (Mix both — see humanizer skill for burstiness rules)
3. Opinionated or neutral? (For content marketing: opinionated. For docs: neutral)
4. Funny or serious? (Pick one per piece, don't alternate randomly)

### Indonesian Voice Guide

**Bahasa gaul natural (casual content):**
- "Udah", "nggak", "banget", "sih", "dong", "kok", "kan", "deh", "ya" — natural connector
- "Kayak", "kayaknya" — common in casual writing
- "Cek", "liat", "buka" — action verbs
- "Nggak perlu", "gak usah" — dismissive but friendly
- "Btw", "oh iya" — transition
- "Keren", "mantap", "gas" — positive reactions

**Bahasa semi-formal (newsletter/blog):**
- Mix formal + casual: "Menurut data terbaru dari [sumber], tren ini naik signifikan. Nggak heran sih, soalnya..."
- Avoid: "Saya", "Anda" (use "kamu" or omit pronoun)
- Tech terms in English OK: API, deployment, workflow (don't force Indonesian translation)

**Bahasa formal (docs, technical):**
- Full words, proper grammar
- "Anda" / "pengguna" OK
- No abbreviations
- Still avoid AI patterns (landscape, testament, etc.)

## Copywriting for AI Output: Specific Rules

### Rule 1: Lead with the So-What
Don't describe what something is. Describe why the reader should care.

**Before (AI):** "React 19 introduces a new compiler that optimizes rendering performance."
**After (copywriting):** "React 19 bisa bikin app kamu 2x lebih cepat tanpa ngubah kode. Ini caranya."

### Rule 2: One Idea Per Paragraph
AI tends to pack multiple ideas into one paragraph. Human writing gives each idea breathing room.

### Rule 3: Active Voice Default
Not a ban on passive — sometimes passive is the right call. But default to active.

### Rule 4: Front-Load Value
The most important information goes first. Don't bury the lede.

### Rule 5: Cut ruthlessly
If removing a sentence doesn't change the meaning, remove it. AI writes fluffy filler; humans cut it.

### Rule 6: End with Momentum
The last sentence should propel the reader forward — to the next section, to action, to thought. Never end on a weak summary.

## Common Copywriting Mistakes by AI

| Mistake | Example | Fix |
|---------|---------|-----|
| Feature-dumping | "Our product has X, Y, Z features" | Lead with benefit, mention features as proof |
| Hedging too much | "This might potentially help some users" | Commit. "This will save you 3 hours/week" |
| Fake urgency | "Limited time offer!" (always on) | Real deadlines or remove urgency |
| Buried CTA | Action buried at end of wall of text | CTA early and repeated naturally |
| Generic claims | "Industry-leading solution" | "Used by 500+ companies in Indonesia" |
| Academic tone | "Research indicates that..." | "Data shows..." or "Here's what happened..." |
| Preaching | "It is important to note that..." | Delete. If it's important, it's already in the text |
| Summary endings | "In conclusion, the future looks bright." | End with the next step or a provocative thought |
| **Unnecessary English in Indo content** | "Expected: Agent menjawab..." | "Hasilnya: Agent menjawab..." |
| **Formal copula "adalah"** | "VPS adalah komputer yang..." | Rewrite without "adalah" or use "=" |
| **Vague quantifiers** | "Beberapa pilihan provider" | Give the number, or drop "beberapa" |

## Templates

### Scripts
| File | Purpose |
|------|---------|
| `scripts/humanize_tiptap.py` | Programmatic humanizer for Tiptap JSON (LearnHouse). Recursively walks doc structure, applies humanizer rules to all text nodes. CLI: `python humanize_tiptap.py input.json output.json`. Library: `humanize_tiptap(doc)`. Used in bulk course pipeline for CodeCora LMS. |

### Templates

### Newsletter Item (Indo)
```
**[Judul singkat, 5-8 kata]**

[1 kalimat hook — kenapa ini penting sekarang]

[2-3 kalimat detail — apa yang terjadi, impact-nya apa]

🔗 [Sumber](url)
```

### Product/Tool Announcement (Indo)
```
**[Nama tool] baru rilis [versi/fitur].**

[1 kalimat: masalah apa yang di-solve]

[1-2 kalimat: cara kerja / highlight fitur]

Mau coba? → [link]
```

### WhatsApp Cold Message (Indo)
```
Hai [Nama], [Aji/Kai] dari [perusahaan]. [1 kalimat personal observation — "dapet nama kamu dari..." / "liat kamu lagi kerja di..."]. [1 kalimat value prop / pain point]. [1 kalimat soft CTA — "Mau jelasin lebih detail?" / "Boleh reply sini"]
```

## Advanced Frameworks

### FAB (Feature → Advantage → Benefit)

Best for product descriptions and tool announcements. Translates technical specs into user value.

| Layer | Question | AI Mistake |
|-------|----------|-----------|
| **Feature** | What does it do? | Lists 10 features without context |
| **Advantage** | What does that mean in practice? | Skips this entirely |
| **Benefit** | What does the user get? | Confuses advantage with benefit |

**Example (Tool Announcement Indo):**
- **Feature:** "TensorRT optimization support di v2.4"
- **Advantage:** "Inference jadi 3x lebih cepat di GPU yang sama"
- **Benefit:** "Cost API turun 60% buat produksi"

**Template:**
```
[Tool] punya [feature]. Artinya [advantage — concrete].
Buat kamu, ini berarti [benefit — user outcome].
```

### 4Ps (Picture → Promise → Prove → Push)

Best for landing pages and long-form sales copy. Narrative-driven.

1. **Picture:** Paint the ideal scenario — "Bayangin..."
2. **Promise:** What they'll achieve — "Dengan [method], kamu bisa..."
3. **Prove:** Evidence — data, testimonials, case study
4. **Push:** CTA — "Mulai sekarang", "Coba gratis"

**Example:**
- **Picture:** "Bayangin deploy ke production cuma butuh 30 detik, bukan 30 menit."
- **Promise:** "Dengan CI/CD pipeline yang bener, setiap push ke main langsung live."
- **Prove:** "Tim X di Jakarta ngurangi deploy time dari 45 menit jadi 28 detik. Error rate turun 80%."
- **Push:** "Setup-nya cuma 3 command. Mau cek panduannya?"

### 4C Framework (Clear → Concise → Compelling → Credible)

Quality checklist untuk setiap copy. Gunakan sebagai final pass sebelum publish.

| C | Question | Red Flag |
|---|----------|----------|
| **Clear** | Bisakah dibaca 1x dan paham? | Jargon tanpa penjelasan, kalimat ambigu |
| **Concise** | Ada kata yang bisa dihapus tanpa ngubah makna? | Filler, hedging, repetition |
| **Compelling** | Ada alasan buat terus baca? | Flat opening, no hook, boring middle |
| **Credible** | Klaim punya backing? | Vague claims, no numbers, no sources |

### Storytelling Framework (STAR-S)

Best for blog posts, case studies, dan newsletter yang engaging.

1. **Situation:** Set the scene — who, where, when
2. **Task:** The challenge or goal
3. **Action:** What was done (specific steps)
4. **Result:** The outcome (with numbers)
5. **So What:** Why it matters to the reader

**Example:**
- **Situation:** "Startup fintech di Jakarta dengan 50k user tiba-tiba kena spike transaction 10x saat promo."
- **Task:** "Payment gateway mulai throttling. Transaction gagal 23%. User komplain banjir."
- **Action:** "Tim switch ke payment routing — fallback ke 3 provider, retry logic, dan circuit breaker."
- **Result:** "Success rate recovery ke 99.7% dalam 4 jam. Zero downtime setelah itu."
- **So What:** "Kalau kamu pakai single payment provider, ini risiko yang sama. Multi-routing itu bukan luxury, itu keharusan."

## Cialdini's 7 Principles of Persuasion (Updated)

The 6 original + the 7th (Unity, added 2016). Each with AI copywriting application.

### 1. Reciprocity
**Mechanism:** Give before you ask. People feel obligated to return favors.
**AI Application:** Lead with value — free template, data, insight. Never open with a pitch.
**Example:** "Nih breakdown fee-nya dulu, gratis. Ya buat referensi aja."

### 2. Commitment & Consistency
**Mechanism:** People align with their past commitments.
**AI Application:** Start with a small ask (reply, bookmark), then bigger (try, buy). Micro-commitments.
**Example:** "Setuju nggak kalau CI/CD itu wajib? Reply aja."

### 3. Social Proof
**Mechanism:** People follow the crowd.
**AI Application:** Specific numbers, real names. Not "banyak user" — "2,347 developer Indo".
**Red Flag:** Fake or vague social proof = instant distrust.

### 4. Authority
**Mechanism:** People trust experts.
**AI Application:** Cite real sources. "Menurut laporan Stripe 2025..." not "Menurut para ahli..."
**Red Flag:** AI loves "experts say" without naming the expert.

### 5. Liking
**Mechanism:** People say yes to people they like.
**AI Application:** Conversational tone, shared identity, humor. Sound like a person, not a brand.
**Indo:** "Kita" (we), shared experience — "Sama kayak waktu aku juga bingung..."

### 6. Scarcity
**Mechanism:** People want what's rare.
**AI Application:** Real deadlines only. "Early bird sampai 31 Juli" > "Terbatas!" (unless truly limited)
**Red Flag:** AI generates fake urgency. Avoid unless 100% real.

### 7. Unity (NEW — Cialdini, 2016)
**Mechanism:** Shared identity — "we are the same", not just "we are similar". The most powerful principle.
**Application:** Connect through shared values, community, tribe. "Kita developer Indo" > "Developer di Indonesia"
**Indo Examples:**
- "Buat kita yang coding di Indonesia, latency ke US server itu masalah sehari-hari."
- "Kita semua udah pernah ngalamin ini — push ke production jam Jumat sore."
- "Developer Indo punya keuntungan yang developer Silicon Valley nggak punya: kita serba bisa."

**Unity vs Liking:** Liking = "they're like me" (similar interests). Unity = "they're one of us" (shared identity). Unity is deeper and more persuasive.

## Emotional Copywriting

### The Emotional Hierarchy
People decide emotionally, then justify rationally. Structure copy accordingly.

1. **Feel** — Hook the emotion (frustration, excitement, curiosity, fear)
2. **Think** — Provide the logic (data, features, reasoning)
3. **Do** — Clear action (CTA)

**Example:**
- **Feel:** "Lagi nunggu CI pass sambil nge-buka Twitter buat kill time? We know that feeling."
- **Think:** "Parallel testing dengan `pytest-xdist` bisa potong wait time dari 45 menit jadi 8 menit. Setup-nya cuma 1 flag."
- **Do:** `pytest -n auto` — coba sekarang, README-nya di sini.

### Emotional Triggers for Tech Content

| Emotion | When to Use | Hook Pattern |
|---------|-------------|--------------|
| **Frustration** | Pain point content | "Again?" / "Serious?" / "Why is this still..." |
| **Curiosity** | Educational content | "Ternyata..." / "Nggak semua orang tau..." |
| **Relief** | Solution content | "Akhirnya..." / "Gini caranya..." |
| **FOMO** | Trend/update content | "Udah pada tau belum..." / "Baru aja..." |
| **Validation** | Opinion pieces | "Bener kan..." / "Aku juga dulu mikir gitu..." |

## Advanced AI-Specific Copywriting Rules

### Rule 7: The Specificity Cascade
AI defaults to generic statements. Counter with a specificity cascade — each paragraph should be more specific than the last.

**Before (AI):**
> AI tools are transforming how developers work. Many companies have adopted AI for various tasks. The results have been impressive.

**After:**
> Developer di Jakarta mulai pake AI copilot buat code review. Hasilnya? PR merge time turun 40% di tim engineering Tokopedia. Dari rata-rata 3 hari jadi 1.8 hari per PR.

### Rule 8: The Anti-Summary
AI loves summarizing at the end. Never summarize what you just said. Instead:
- End with a question
- End with a challenge
- End with a next step
- End with an unexpected thought

**Before (AI):** "In summary, AI has significantly impacted the technology landscape."
**After:** "Jadi, pertanyaannya bukan 'apakah AI ngaruh' — tapi 'kamu udah optimize workflow kamu belum?'"

### Rule 9: Conversational Friction
Perfect text feels AI-generated. Add small imperfections:
- Occasional sentence fragments: "Tapi ya." "Nggak juga sih."
- Self-corrections: "Atau lebih tepatnya..." "Well, sebenarnya..."
- Asides in parentheses: "(ini yang sering kelupaan)"
- Colloquialisms at transitions: "Nah, di sininya..." "Terus..." "Jadi gini..."

**Use sparingly** — 1-2 per article max. Too many = affected.

### Rule 10: The Micro-Story
Instead of a general statement, tell a 1-sentence story.

**Before (AI):** "Payment failures can significantly impact user retention."
**After:** "Satra, founder SaaS kecil di Bandung, kehilangan 30% customer-nya karena payment gateway error selama 2 hari. Dia nggak punya monitoring."

### Rule 11: Data with Context
Numbers without context = AI tell. Always anchor data to something relatable.

**Before (AI):** "The model achieves 95% accuracy."
**After:** "95% accuracy — artinya dari 100 transaction, cuma 5 yang perlu review manual. Buat tim dengan 500 transaction/hari, itu turun dari 25 review jadi 25."

## Platform-Specific Copywriting

### Newsletter (Discord/Beehiiv)
- Hook: 1-2 kalimat, langsung ke topik
- Body: 3-5 items, masing-masing 2-4 kalimat
- CTA: 1 link, natural positioning
- Tone: Semi-casual, opinionated, informative
- Max: 800-1500 words total

### WhatsApp/Chat
- Max 5-6 lines per message
- Buka dengan nama, bukan "Halo"
- 1 pain point per pesan
- Soft CTA: tanya, bukan perintah
- No signature blocks

### Blog Post (Ghost/Website)
- Intro: Hook → Problem → Stakes → Promise → Transition (max 150 words)
- Body: H2 per major point, H3 for sub-points
- Conclusion: Takeaway + CTA (no "in conclusion")
- Length: 500-1000 words for standard, 1500+ for deep dive

### Social Media (Threads/LinkedIn)
- Hook: 1 line punchy
- Body: 3-5 lines max
- CTA: last line
- Format: No emoji spam, max 1-2 emoji total

## Quick Reference Card

**Framework picker:**
| Situation | Framework |
|-----------|-----------|
| New product/feature launch | AIDA |
| Solving a specific pain | PAS |
| Transformation story | BAB or 4Ps |
| Product description | FAB |
| Quality check | 4Cs |
| Case study | STAR-S |
| Community/tribe content | Unity |

**Cialdini quick check:**
| Principle | Trigger |
|-----------|---------|
| Reciprocity | Give value first |
| Commitment | Small ask → big ask |
| Social Proof | Specific numbers |
| Authority | Named sources |
| Liking | Conversational, relatable |
| Scarcity | Real deadlines only |
| Unity | Shared identity, "we/us" |

## Reference

Based on established copywriting principles: AIDA (Strong, 1898), PAS framework, FAB (feature-advantage-benefit), 4Ps, 4Cs, STAR-S, Robert Cialdini's Influence (1984) + Pre-suasion (2016, Unity principle), and 2025-2026 AI copywriting research.

### AI Tells in Indonesian Educational/Course Content

When writing or reviewing Indonesian course materials (LMS, ebooks, tutorials), the AI tells are different from marketing copy. These are the patterns that make course content feel "irrelevant" or AI-generated to Indonesian readers.

**Category 1: Unnecessary English Jargon (most common signal)**

Indonesian courses for Indonesian audiences should use Indonesian terms, not English borrowed jargon. AI defaults to English because training data skews English-heavy.

| English Term | Frequency | Indonesian Replacement |
|-------------|-----------|----------------------|
| "Expected" | Very high | "Hasilnya", "Output-nya", "Yang harus terjadi" |
| "Use case" | High | "Contoh penerapan", "Contoh", "Kasus pemakaian", "Skenario" |
| "Best practice" | Medium | "Tips", "Langkah praktis", "Cara terbaik", "Rekomendasi" |
| "Pattern" | Medium | "Cara", "Pola", "Format" (context-dependent) |
| "Deliver" | Low | "Kirim ke", "Sampaikan ke" |

**Rule:** If the course targets Indonesian beginners, translate ALL non-tech English terms. Tech terms (API, webhook, cron) are fine. Business/educational jargon ("use case", "best practice", "expected") must be in Indonesian.

**Category 2: Formal Copula "adalah"**

The word "adalah" is grammatically correct but creates a formal, textbook-like tone. In casual/conversational course content, it feels stiff.

| Before (stiff) | After (natural) |
|----------------|-----------------|
| "VPS adalah komputer yang menyala 24 jam" | "VPS itu komputer yang menyala 24 jam" |
| "Browser tool adalah yang paling powerful" | "Browser tool yang paling powerful" |
| "Skill adalah procedural memory" | "Skill itu kayak SOP kerja agent" |
| "SOUL.md adalah file konfigurasi" | "SOUL.md itu file konfigurasi" |

**Fix:** Replace "adalah" with "itu" or rewrite the sentence to avoid needing a copula. In some cases, just drop it entirely.

**Category 3: Vague Quantifiers**

AI loves vague quantifiers instead of specific numbers or concrete descriptions.

| Vague | Better |
|-------|--------|
| "Beberapa pilihan provider" | "4 pilihan provider" or just "Pilihan provider:" |
| "Berbagai tools" | Name the tools or say "tools yang sudah disebut di atas" |
| "Masing-masing" | "Tiap-tiap" or restructure the sentence |

**Category 4: Headings as Summary Headers**

AI-generated educational content often uses "Ringkasan" (summary) or "Rangkuman" headings that restate what was just said. Per copywriting Rule 8 (Anti-Summary), these should be replaced with forward-looking headings or removed entirely.

**Detection pattern:** `grep -i "ringkasan\|rangkuman" content.json` — if found in heading blocks, flag for removal.

**Review Checklist for Indonesian Course Content:**
1. Scan for English jargon (expected, use case, best practice, pattern) → replace with Indonesian
2. Count "adalah" occurrences → replace with "itu" or rewrite
3. Check for vague quantifiers (beberapa, berbagai, masing-masing) → be specific or drop
4. Check for "Ringkasan"/"Rangkuman" headings → remove or replace with forward-looking text
5. Verify the overall tone matches the target audience level (beginner → casual, expert → can be formal)

### Validation & Testing Methodology

When testing whether copywriting output reads as human-written (not AI), use this methodology:

**3-Sample Test:**
1. Select 3 sample texts from different registers: Newsletter Indo (semi-casual), Technical English (neutral), WhatsApp Indo (casual)
2. For each sample:
   - Identify ALL AI patterns present (reference `creative/humanizer` §1-33 and `creative/humanizer-improve` §34-39)
   - Draft rewrite applying copywriting rules + humanizer rules
   - Audit remaining AI tells
   - Final rewrite (fix remaining tells)
   - Score 1-10

**Scoring Rubric:**
| Score | Verdict | Action |
|-------|---------|--------|
| 9-10 | Clean | No AI tells remain, natural voice |
| 7-8 | Minor | 1-2 minor tells, acceptable |
| 5-6 | Needs work | Multiple tells, requires rewrite |
| <5 | AI-detected | Full rewrite needed |

**Perplexity/Burstiness Check:**
- Mix 5-word and 25-word sentences within paragraphs
- Check for at least 3 clearly different sentence lengths per paragraph
- Verify concrete specifics (names, numbers, dates) — not just abstractions
- Ensure opinion/take present in non-technical content

Sources: SEOAuthori AI Copywriting Guide 2026, Gracker.ai 2026 Copywriting Trends, ContentGenics Copywriting 2025, CXL Cialdini Unity, Leading Expert Unity Principle.

Designed to complement `creative/humanizer` and `creative/humanizer-improve` skills.

## i18n / UI Microcopy Audit

When auditing PR i18n keys (localization files like `id.ts`/`en.ts`), apply copywriting + humanizer rules to short UI strings. This is different from long-form copy — the patterns are tighter and more specific.

### Common AI Tells in UI Microcopy

| Tell | Example | Fix |
|------|---------|-----|
| Emoji in headings (§18) | `"🌟 Popular Games"` | Strip emoji, text-only |
| "Jelajahi" as AI vocabulary (§7 Indo) | `"Jelajahi game berdasarkan pelajaran"` | Use concrete subject list: `"Matematika, membaca, logika, dan lainnya"` |
| Vague marketing fluff | `"Pilihan terbaik untuk mulai belajar"` | Concrete social proof: `"Game yang sering dimainkan"` |
| Over-formal Indonesian | `"Pilih jenjang kelas anak kamu"` | Simplify: `"Pilih kelas anak"` |
| Corporate tagline repetition | `"Game edukasi gratis untuk anak Indonesia"` (when brand already says "edukasi") | Distinct voice: `"Belajar sambil main, gratis."` |
| Bald empty-state text | `"Tidak ada game"` | Contextual: `"Tidak ada game yang cocok"` |
| Redundant browse/explore | `"Browse by Subject" / "Explore games by school subject"` | Keep title, make subtitle concrete: `"Math, reading, logic, and more"` |

### Audit Workflow

1. Pull the i18n diff (`gh pr diff -- <files>`)
2. Scan all new/changed keys for AI tells above
3. Apply fixes to BOTH locale files (id + en) in parallel
4. Validate: svelte-check + tests (i18n changes shouldn't break logic)
5. Commit with descriptive message, push to PR branch

### Pitfalls

- **Don't touch emoji that are intentional UX elements** (e.g., `🎮 Pilihan Minggu Ini` as a section label is fine — it's a section marker, not a heading). Target emoji ON heading/title keys.
- **Keep functional keys unchanged**: `games.clearFilter: 'Reset'` is fine. Don't over-edit utility text.
- **Subtitle = opportunity, title = keep simple**: When fixing a title/subtitle pair, the title stays short/factual. The subtitle is where you inject voice/concreteness.
- **Match id ↔ en semantics**: Don't just translate — rewrite both to sound natural in their language. The fix for "jelajahi" in Indo might be a concrete list, while the English fix might be a different concrete framing.

### Real Audit Example (Hompimpah PR #85)

6 fixes per locale applied:
- Emoji stripped from featured game heading
- "Pilihan terbaik untuk mulai belajar" → "Game yang sering dimainkan" (social proof)
- "Pilih jenjang kelas anak kamu" → "Pilih kelas anak" (simpler)
- "Jelajahi game berdasarkan pelajaran" → "Matematika, membaca, logika, dan lainnya" (concrete)
- "Tidak ada game" → "Tidak ada game yang cocok" (contextual)
- Footer tagline: corporate → human voice

## Companion Skills

- `oss-readme-marketing` — GitHub README optimization specifically (structure, badges, comparison tables, FAQ for SEO, star-growth tactics). Load it when the task is about repo adoption/stars rather than general copywriting.
