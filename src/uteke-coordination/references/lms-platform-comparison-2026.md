# LMS Platform Comparison — Skool vs LearnHouse vs Mayar.id (Jul 2026)

Research compiled for CodeCora strategic evaluation. Data verified against official sites and independent reviews.

## Quick Comparison

| Aspect | Skool | LearnHouse | Mayar.id |
|--------|-------|------------|----------|
| Type | Proprietary SaaS | Open Source (MIT) | Proprietary SaaS |
| Pricing | $9-99/mo + 2.9-10% fee | Free/$49/$149 (0% fee) | Rp 0/Rp 349K (1-4% fee) |
| Market | Global (US-centric) | Global | Indonesia (150K+ users) |
| Community | Core feature (feed, DMs) | Basic (discussions) | None |
| Courses | Basic (video, PDF) | Advanced (block editor, quiz, SCORM, versioning) | Basic (DRM, quiz, certificate) |
| Gamification | Best (XP, levels, leaderboard, gated content) | None | None |
| AI Features | None | Full suite (RAG, course planning, code gen) | None |
| Payments | Built-in (Skool Payments) | BYO Stripe | All Indonesian (QRIS, VA, e-wallet) |
| Self-host | No | Yes | No |
| Email/Marketing | No | No | Blast email, bundling, upsell |
| Certifications | Unknown | N/A | ISO 27001, SOC2 |
| Multi-language | English only | Yes | Indonesia only |
| Mobile App | Yes (iOS + Android) | Yes | Yes |

## Skool — Community-First Platform

- Founder: Sam Ovens, backed by Alex Hormozi
- Model: Community = product. Courses support the community.
- Pricing: Hobby $9/mo (10% fee, 1 admin) | Pro $99/mo (2.9% fee, unlimited admins)
- Per community — multiple communities = multiple subscriptions
- Break-even: Pro cheaper than Hobby at ~$900-1,150/mo revenue
- Strengths: Simplicity (<1hr setup), gamification, community-course integration, mobile app, Skool Call (webinar up to 10K), discovery algorithm
- Weaknesses: No email, no funnels, no advanced LMS (no quiz/assignment/certificate), limited branding, English only, no self-hosting, no AI

## LearnHouse — Feature-Complete Open Source LMS

- Stack: Next.js (frontend) + FastAPI (backend) + PostgreSQL + Redis + Hocuspocus (collab)
- License: MIT
- Pricing: Free (self-host) | Standard $49/mo | Pro $149/mo (0% fee)
- Activity types: Dynamic (Page/Markdown/Embed), Video (YouTube/Hosted), Document (PDF/Doc), Assignment (quiz/code/short answer/number/file/form), SCORM
- Unique features: Real-time collaborative boards (Yjs), AI suite (RAG chat, course planning, magic blocks), code playgrounds (Judge0), activity versioning/rollback, RBAC with custom roles, multi-tenant orgs
- Strengths: Most complete LMS, AI-native, self-hostable, 0% fee, white-label, multi-language
- Weaknesses: Complex deployment (3 services), Python+Node hybrid, smaller community, no gamification, BYO Stripe, steep learning curve
- Rebuild estimate: 30-43 weeks solo dev, 15-22 weeks duo (Rust+Svelte)

## Mayar.id — Indonesian Super Commerce Platform

- Pricing: Starter Rp 0 | Business Rp 349K/mo | Enterprise custom
- Users: 150K+ businesses registered
- Product types: 17+ types (online classes, bootcamp, membership, webinar, event, digital products, physical products, SaaS, license, credit-based, galang dana, etc.)
- Class features: DRM protection, curriculum, quiz, certificates, student dashboard, discussion
- Marketing: Blast email, bundling, upsell, cross-sell, discount, affiliate management
- Analytics: Meta Pixel, TikTok Pixel, UTM, GA, GTM
- Integrations: WA, Telegram, API, webhooks, Zapier, MCP
- Certifications: ISO 27001, SOC2
- Platform fees: 1% (payment link) to 4% (classes, membership, SaaS) + channel fees
- Channel fees: QRIS 0.7%, E-wallet 1.5-2%, VA Rp 4K, CC 2.6%+Rp 2K, Minimarket Rp 5-7.5K
- Strengths: Indonesia-native, all payment methods, ISO certified, free starter, API+MCP available
- Weaknesses: No community, no gamification, no AI, no self-hosting, Indonesia-focused, course features basic vs LearnHouse

## Unit Economics Summary

For Rp 750jt/year revenue (~$50K):

| Platform | Cost | Net Margin |
|----------|------|------------|
| Skool Pro | ~Rp 42jt ($2.8K) | ~94% |
| LearnHouse (self-host) | ~Rp 3.6jt ($240 infra) | ~99.5% |
| Mayar Business | ~Rp 18jt ($1.2K) | ~97.6% |

## Key Strategic Questions

1. Build vs buy — can CodeCora differentiate enough to justify 30+ weeks of dev?
2. Indonesia vs global — Mayar dominates ID market, Skool dominates global community space
3. Niche opportunity — AI-native LMS with gamification for Indonesian market? (No platform combines both)
4. Revenue vs cost — LearnHouse has best unit economics but highest complexity; Mayar has lowest barrier to entry

## Sources

- https://marksinsights.com/skool-review/ (comprehensive Skool review)
- https://skoolco.com/skool-pricing-i/ (Skool pricing breakdown)
- https://www.learnhouse.app/compare/closed-source/skool (LearnHouse official comparison)
- https://skoolprep.com/skool-community-guide (Skool community guide)
- https://mayar.id/features (Mayar full feature list)
- https://mayar.id/pricing (Mayar pricing details)
- https://mayar.id/kelas-online (Mayar online class features)
- GitHub: learnhouse/learnhouse (architecture analysis)
