# P12 — Information Fragmentation and the "Dedicated Forwarding Address" Strategy

Collector P12. Retrieved 2026-08-21. US-focused; global figures flagged inline.

**The question:** parents receive kid-related information across a dozen disconnected channels.
The proposal is to give each family a dedicated inbound address (`name@ourdomain.com`) that the
parent **registers directly with schools and activity providers as a secondary contact** — a
"Trojan horse" into systems with no API, avoiding Gmail OAuth entirely.

**Short answer, stated up front so the rest can be read against it:** the fragmentation is real and
is not being solved upstream, and the CASA-avoidance is worth more than it looks. But the Trojan
horse *as specified* — register our address with the school — **fails on the two largest school
platforms and is contractually hostile on four others**. The thing that actually works is the
mundane sibling of the idea: a per-family inbound address the parent **auto-forwards to from their
own mailbox**. That gets ~100% of email-borne content, needs no platform cooperation, no OAuth, no
CASA, and no district front-office visit. Register-with-the-school survives as a *bonus* path on the
five platforms where it is genuinely self-serve.

---

## Section 1: FINDINGS

| # | Claim (one sentence, with the number) | Value | Cohort/segment | Publisher | Year | Method (n, fielding window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | **The best-sourced tool-count in the category:** US K-12 districts accessed **2,982 distinct edtech tools** in SY2024-25, up 9% YoY, and the series rose every year — 2,591 (SY22-23) → 2,739 (SY23-24) → 2,982 (SY24-25). | 2,982 tools/district/yr | US K-12 districts | LearnPlatform / Instructure, "EdTech Top 40" 8th ed. | 2025 | Passive telemetry via LearnPlatform Inventory Dashboard, Sep 1 2024–May 31 2025; "64 billion interactions from 3.7M students and 546,000 educators." **Self-selecting panel; the number of districts in the panel is never disclosed in any edition. Not a probability sample.** | C (vendor, method disclosed) | https://www.instructure.com/edtech-top40 |
| 2 | The same report's per-*person* figure is far smaller and cuts against the fragmentation story: **individual students and teachers interact with just 4 LTIs on average** (SY2025-26). | 4 LTIs/person | US students + educators | Instructure | 2026 | Canvas LTI launch data only, Sep 1 2025–Apr 30 2026, n=12,672,611 individuals. **METHOD CHANGED — do not chart against the 2,591/2,739/2,982 series.** | C (vendor) | https://www.instructure.com/press-release/new-instructure-data-shows-k-12-districts-are-demanding-evidence-not-just-access |
| 3 | **The one legally-attested reach figure in the whole category:** PowerSchool served **17,000+ customers, 90 of the 100 largest US districts, ~50M students globally / "over 80% of all K-12 students in the U.S."**, and ~20M students on its SIS. | 80% of US K-12 | US K-12 | PowerSchool Holdings, SEC Form 10-K FY2023 | 2024 (filed 2024-03-01) | Audited SEC filing, as of 2023-12-31. **No newer audited figure exists — Bain took PowerSchool private Oct 2024.** | A (SEC filing) | https://www.sec.gov/Archives/edgar/data/1835681/000183568124000016/pwsc-20231231.htm |
| 4 | ParentSquare claims **22 million students at 42,000+ schools, all 50 states, ~40% of US families, 99% district retention.** | 22M students | US K-12 | ParentSquare (vendor); repeated by Santa Barbara Independent 2026-08-12 | 2026 | **Vendor self-report, no method disclosed.** Newspaper repeats the same figures without independent verification. | C (vendor) | https://www.parentsquare.com/company/press/ |
| 5 | Remind claims **~30 million users in 80% of US schools** and 2M+ teachers; at acquisition (Dec 2023) ParentSquare said the combined products "support **20 million students in all 50 states**" and its free classroom service is "used in **80% of US schools**." | 30M users / 80% of schools | US K-12 | Remind / ParentSquare (vendor) | 2023–2026 | **Vendor self-report, no method.** Remind and ParentSquare user bases overlap — **do not add them.** | C (vendor) | https://www.remind.com/ ; https://www.parentsquare.com/blog/parentsquare-remind-a-new-chapter-and-whats-next/ |
| 6 | ClassDojo claims **50 million families globally** and presence in **95% of US schools** (also stated as "90% of all K-8 schools"). | 50M families | **GLOBAL, not US** | ClassDojo (vendor), PR Newswire | 2026 | **Vendor self-report, no method.** The 90–95% denominator counts any school with ≥1 active teacher — a very loose definition of adoption. | C (vendor) | https://www.classdojo.com/press/ |
| 7 | TalkingPoints claims **1 in 4 US schools and 1 in 4 US districts, 24M+ families/educators/students**. | 1 in 4 schools | US K-12 | TalkingPoints (vendor) | 2026 | Vendor self-report, no method. | C (vendor) | https://www.talkingpts.org/ |
| 8 | The sports layer is comparably large and **entirely outside district control**: TeamSnap claims **30M parents/players/coaches, 19,000+ organizations**; SportsEngine claims **16M athletes, 1.2M teams, 45,000 organizations**. | 30M / 16M | US youth sports | TeamSnap, SportsEngine (vendors) | 2025–2026 | Vendor self-report, no method. | C (vendor) | https://www.teamsnap.com/ ; https://www.sportsengine.com/ |
| 9 | **Corrections to the Edsby "App Overload" figure P4 carries:** n=**125 parents** (plus 100+ teachers and 58 curriculum leaders), fielded over five weeks **Dec 2024–Jan 2025**, and **all respondents were North American, not US-only.** Parent split: 14% at 1–3 apps/child, 32% at 4–6, **44% at 7–9, 10% at >10 — i.e. 54% at 7 or more.** | 44% at 7–9 | North American parents | Cornerstone Communications + **Edsby (vendor-sponsored)** | 2025 | n=125, five weeks Dec 2024–Jan 2025, online + in-person, self-described "stratified random," **no MoE, non-probability**, skews to older kids and multi-child homes. | C (vendor, weak n) | https://cornerstonepr.net/wp-content/uploads/2025/03/AppOverloadReport_bg.pdf.pdf |
| 10 | **The district-side count from the same study, which P4 did not surface:** **54% of curriculum leaders said their schools use 10–15 officially sanctioned apps** with a student or parent component; 25% said 5–9; 16% under five; 5% more than 16. | 54% at 10–15 apps | US/Canada curriculum leaders | Cornerstone + Edsby | 2025 | **n=58 curriculum leaders** — very small, same non-probability design. | C (vendor, very weak n) | same as #9 |
| 11 | **A hard federal negative:** the NHES:2023 Parent and Family Involvement questionnaire — the federal instrument that *should* answer "how many platforms does a parent deal with" — asks only whether the school sent notes/emails, newsletters, or phone calls (yes/no). **There is no item counting apps, portals or logins, and no item on missed information.** | 0 items | US parents of K-12 students | NCES, National Household Education Survey | 2023 | Federal survey instrument, fielded through Aug 2023; item 51 reviewed directly. | A | https://nces.ed.gov/nhes/pdf/pfi/2023_pfi.pdf |
| 12 | **Nothing better than the Edsby n=125 exists.** No larger-n, probability-sample, or independent district-side count of *parent-facing* platforms per family was found in the public record. | no data | US parents | — | 2026 | Exhaustive search of NCES, Pew, Gallup, Learning Heroes, EdWeek Research Center, National Parents Union, Common Sense. | — (negative finding) | — |
| 13 | **No independent corroboration of "62% missed something" exists**, and nothing contradicts it either. The nearest evidence is qualitative: a GreatSchools multi-method study across **75+ districts** found "Information overload is real" and "Parents feel there is both too much information coming from districts and not enough relevant information as it pertains to their individual child." | qualitative only | US parents + district leaders | GreatSchools (CEO Jon Deane, in The 74) | 2024 | District-leader interviews + parent surveys/interviews across 75+ districts. **No n, no fielding window, no percentages published — quote the language, never a number.** | C | https://www.the74million.org/article/how-well-do-schools-families-communicate-study-sees-parent-district-disconnect/ |
| 14 | **Demand for the job is near-universal even though nobody has measured the channel problem:** **95%** of K-12 parents say communicating about how their child is doing is important for the school to focus on, and **72% call it "one of the MOST important things"** — statistically tied with academic support as the single highest-rated school priority. | 95% / 72% | US K-12 public school parents | National Parents Union | 2026 | n=**1,527**, fielded **May 28–June 1 2026**, MoE ±2.7pp. **Contains no item on channels or missed information.** | B | https://nationalparentsunion.org/ |
| 15 | **Districts ARE consolidating the comms channel, and one state now mandates it:** Kentucky SB 181 (signed 2025-04-01) requires boards to designate programs as "the **exclusive means** for school district employees and volunteers to communicate electronically with students," with parent notice within the first 10 school days. | statute | Kentucky K-12 | Kentucky General Assembly, 2025 RS, Acts ch. 149 | 2025 | Enacted statute. **Governs employee↔student contact, not the parent's app pile, and permits parents to consent to off-platform contact.** | A | https://apps.legislature.ky.gov/record/25rs/sb181.html |
| 16 | **Correcting a likely assumption: ParentSquare has NOT sunset Remind.** ParentSquare's own FAQ says "ParentSquare is now home to Remind Chat and Remind Hub, **both of which remain available**" and "Remind Chat continues to be free to use and available to new users!" Remind's help center was updated **2026-08-21**; searches for sunset/discontinued/retire return **zero** articles. **No published EOL date exists.** | no EOL | US K-12 | ParentSquare / Remind (primary vendor docs) | 2026 (checked 2026-08-21) | Direct fetch of vendor FAQ + Zendesk help-center API article timestamps. | C (primary vendor doc) | https://www.remind.com/parentsquare ; https://www.parentsquare.com/remind/ |
| 17 | **ParentSquare contact info is SIS-sourced and not parent-editable in the general case.** ParentSquare: "Once a staff member updates the contact information in your SIS, the change will automatically reflect in ParentSquare within 24 hours." A district FAQ states it plainly: "Changes and corrections must be made in the student information system (SIS) records. **Ask your school office to update your information.**" Hart USD, on this exact question: "**Please contact your school office to add an additional email address.**" | blocked | US parents | ParentSquare + district IT pages | 2026 | Primary vendor + district documentation, retrieved 2026-08-21. | C (primary doc) | https://www.parentsquare.com/resources/help-center/ ; https://www.ddouglas.k12.or.us/departments/cfcp/parentsquare/psq-parents-guardians-faq/ ; https://www.hartdistrict.org/apps/pages/ParentSquare |
| 18 | **The single most damaging technical fact for the whole strategy:** three of the largest platforms silently **disable email the moment the parent installs the app.** ClassDojo: "By downloading the app, you'll receive push notifications instead of email notifications. **At this time, it's not possible to receive both.**" Remind: "When you download the app, push notifications are turned on, and your text and email Remind messages are **automatically disabled**." | push/email exclusivity | US parents | ClassDojo, Remind, Seesaw help centers | 2026 | Primary vendor documentation retrieved via public Zendesk APIs, 2026-08-21. | C (primary doc) | https://help.classdojo.com/hc/en-us/articles/360050778411 ; https://help.remind.com/hc/en-us/articles/206430755 |
| 19 | **Three platforms have no usable email channel at all for the content that matters:** TalkingPoints (teacher messages are SMS/app-only; family email exists only for district emergency broadcasts on a paid add-on), BAND (posts/comments/chat have no email path), Infinite Campus (grades/attendance/assignments are **push-only at every configuration**). | 3 of 12 | US parents | TalkingPoints, BAND, Infinite Campus docs | 2026 | Primary vendor documentation. | C (primary doc) | https://talkingpts.org/families/ ; https://help.band.us/help/1205 ; https://kb.infinitecampus.com/help/push-notifications-mobile-portal |
| 20 | **`gmail.readonly` is a RESTRICTED scope and so is every Gmail scope that reads bodies — including `gmail.modify`.** Google's policy defines restricted as "Any Gmail API scope that permits an application to: Read, create, or modify message bodies (including attachments), metadata, or headers." | restricted | developers | Google, Workspace API User Data Developer Policy + Gmail scopes page | 2026 (pages dated 2026-07-22) | Primary vendor documentation. **This kills a widely-circulated workaround claiming `gmail.modify` is merely "sensitive."** | A-adjacent (platform owner's own policy) | https://developers.google.com/workspace/gmail/api/auth/scopes |
| 21 | **Restricted-scope verification: Google's own published estimate is 6 weeks**, versus 10 business days for sensitive and 2–3 days for brand verification; elsewhere Google says verification "might require **several months**." | 6 weeks | developers | Google, OAuth API Verification FAQ | 2026 | Primary vendor documentation. | A-adjacent | https://support.google.com/cloud/answer/13463817 |
| 22 | **The security assessment is mandatory, annual, and a full re-test every year regardless of code changes.** "apps must be reverified for compliance and complete a security assessment **at least every 12 months**"; "We require the annual security reassessment to be a **complete test of your application whether you have made any changes or not**." | annual | developers | Google + App Defense Alliance (CASA) | 2026 (ADA page updated 2026-06-27) | Primary documentation. Tier is assigned by Google, **not chosen by the developer**. | A-adjacent | https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification ; https://appdefensealliance.dev/casa/casa-tiering |
| 23 | **The free CASA self-scan was eliminated in May 2024.** Google's notification email: "**Tier 2 self scan is no longer an option**… you will incur a small cost, paid to an independent assessor." ADA's own pages now carry "**The CASA self scanning process is deprecated**" and both surviving assurance levels are labelled "Lab Tested - Lab Verified." | no free tier | developers | Google (email quoted in public forum) + App Defense Alliance | 2024–2026 | Verbatim Google email posted to Google Apps Script Community 2024-05-03; ADA deprecation banner checked 2026-08-21. | C (verbatim vendor email in public forum) / A-adjacent (ADA) | https://groups.google.com/g/google-apps-script-community/c/XgsHT2Fr7u8 ; https://appdefensealliance.dev/casa/tier-2/tier2-overview |
| 24 | **Published lab pricing from Google's named preferred partner:** CASA **Tier 2 $675** (a second tier at $855; "Tier 2 Unlimited" $3,600), **Tier 3 $4,500**; turnaround 1–3 weeks (T2) and 2–4 weeks (T3). Market spread across other authorized labs runs roughly $800–1,500 (T2) and $5,000–8,000 (T3). | $675–$4,500/yr | developers | TAC Security (Google-named partner) | 2026 (fetched 2026-08-21) | Published price list. The cross-lab spread is from a vendor blog table marked "as of 2024" — directional only. | C (vendor price list) | https://tacsecurity.com/google-casa-cloud-application-security-assessment/ |
| 25 | **The number that actually decides this:** an unverified restricted-scope app is capped at "**100 new users in total**" and "the user cap applies over the **entire lifetime of the project**, and **it cannot be reset or changed**." | 100 lifetime users | developers | Google | 2026 | Primary vendor documentation. **A closed beta fits under it. A launch does not — and burning it permanently kills that GCP project.** | A-adjacent | https://support.google.com/cloud/answer/7454865 ; https://support.google.com/cloud/answer/13463817 |
| 26 | **Tier 3 costs more than money:** "the assessor will need **read-only access to the cloud system where Google production data will be stored**" — i.e. annual third-party auditor access to production. | prod access | developers | Google | 2026 | Primary vendor documentation. | A-adjacent | https://support.google.com/cloud/answer/13463817 |
| 27 | **A separate Google policy risk that may bind harder than CASA:** "Google User Data may not be used to train or improve foundational or frontier models **or be stored in conjunction with such models**," and "Don't allow humans to read the data, unless: You first obtained the user's affirmative agreement to view specific messages." | policy constraint | developers | Google | 2026 | Primary vendor documentation. **An LLM pipeline over Gmail content sits in genuinely ambiguous territory here — unresolved, not settled.** | A-adjacent | https://support.google.com/cloud/answer/13463817 |
| 28 | **Microsoft is dramatically cheaper: consumer Outlook.com mail via Graph `Mail.Read` requires NO admin consent and NO CASA-equivalent audit**, and publisher verification is free: "**Microsoft doesn't charge developers for publisher verification. No license is required.**" Microsoft 365 Certification (the annual-pen-test analogue) applies only to marketplace add-ins for Teams/Office/Outlook/SharePoint — not a standalone consumer app calling Graph. | free | developers | Microsoft Learn | 2024–2025 (pages last updated 2024-08-13 and 2025-10-30) | Primary vendor documentation. | A-adjacent | https://learn.microsoft.com/en-us/graph/permissions-reference ; https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview |
| 29 | **There is no iCloud Mail API. The only Apple path is IMAP with an app-specific password** (`imap.mail.me.com`, port 993, 2FA required, max 25 active app-specific passwords) — technically possible, product-hostile, and it hands your app a long-lived credential to the user's entire Apple mail. | no API | developers | Apple Support | 2026 | Primary vendor documentation (IMAP settings). **The absence of a mail API is evidenced by absence — developer.apple.com serves a JS shell to scripted fetches.** | C (primary doc for IMAP; negative uncited) | https://support.apple.com/en-us/102525 ; https://support.apple.com/en-us/102654 |
| 30 | **Receiving mail at your own domain has NO gatekeeper — no Google review, no Apple review, no audit — and costs $0–20/month.** Cloudflare Email Routing inbound is "**Unlimited**" on both Free and Paid; AWS SES inbound is **$0.10 per 1,000 emails received**; Postmark from $15/mo; Mailgun Free includes 1 inbound route. | $0–20/mo | developers | Cloudflare, AWS, Postmark, Mailgun price pages | 2026 (fetched 2026-08-21) | Published pricing. **Scaling trap: every provider caps routing rules (Cloudflare 200/domain, Mailgun 1–5 by plan) — a per-family-rule design does not scale; use a catch-all → single handler.** | C (vendor price list) | https://developers.cloudflare.com/email-service/platform/pricing/ ; https://aws.amazon.com/ses/pricing/ |
| 31 | **Gmail auto-forward setup is desktop-web only and requires a verification link sent to the destination address** — "On your computer, open Gmail… A verification message is sent to the forwarding email address." Filters can scope which mail forwards. | desktop-only | US parents | Google Gmail Help | 2026 | Primary vendor documentation. **Because we own the destination inbox, we can auto-click the verification link — collapsing the hardest step. This is a design unlock, not a blocker.** | A-adjacent | https://support.google.com/mail/answer/10957 |
| 32 | **Auto-forwarding is disabled by default on Microsoft 365 and one toggle away on Google Workspace** — Defender for Office 365: "In 2021, the value changed to **Off - Forwarding is disabled** for new organizations," bouncing with `5.7.520 Access denied, Your organization does not allow external forwarding.` | off by default (M365) | school/work-issued accounts | Microsoft Learn | 2026 (ms.date 2026-08-18) | Primary vendor documentation. **Matters because many parents read school mail on a work account.** | A-adjacent | https://learn.microsoft.com/en-us/defender-office-365/ |
| 33 | **Forwarding breaks DMARC by design, and the RFC says so:** "Without Authenticated Identifiers aligned with the Author's RFC5322.From header field domain, the new Recipient **has no way to achieve a passing DMARC evaluation**." | protocol fact | — | IETF RFC 7960 §3.2.2 | 2016 | Standards-track RFC (dated but definitive). **Product requirement: publish SPF/DKIM/DMARC on the ingest domain, implement ARC, and DO NOT reject inbound on DMARC failure — or you silently drop the school mail you exist to parse.** | A | https://www.rfc-editor.org/rfc/rfc7960 |
| 34 | **A2P 10DLC registration is a SENDER obligation — inbound-only needs none.** Twilio: "**If you do NOT Send Messages to US Numbers** — US A2P 10DLC registration is not required." Inbound long-code is **$0.0083/segment** and AT&T, Verizon and US Cellular are **free to receive**. | $0 registration | developers | Twilio Help Center | 2026 | Primary vendor documentation. **Answers by negation — there is no article scoped to inbound-only. Get it in writing if load-bearing.** | C (primary vendor doc) | https://help.twilio.com/articles/1260800720410-What-is-A2P-10DLC- |
| 35 | **An iPhone cannot auto-forward SMS to an email address or a third-party number.** iOS Text Message Forwarding delivers only to the user's *own* Apple devices signed into the same Apple Account: messages "can also appear on your **Mac, iPad, and Apple Vision Pro**." There is no arbitrary destination and no API. | not possible | iOS parents | Apple Support | 2026 | Primary vendor documentation. | A-adjacent | https://support.apple.com/en-us/102545 |
| 36 | **Android SMS reading is gated to default-handler apps**, and Google Play states: "Apps must be **actively registered as the default SMS, Phone, or Assistant handler** before prompting users to accept any of SMS or Call Log permissions… **Apps that fail to meet policy requirements… may be removed from Google Play.**" | blocked | Android parents | Google Play developer policy | 2026 | Primary platform policy. | A-adjacent | https://support.google.com/googleplay/android-developer/answer/10208820 |
| 37 | **A parent's Twilio number cannot text in to a short code** (e.g. Remind's 81010): "**Twilio numbers cannot send to Short Codes.**" This closes the obvious "give the school our phone number" workaround for the largest SMS-based school platform. | not possible | developers | Twilio Help Center | 2026 | Primary vendor documentation. | C (primary vendor doc) | https://help.twilio.com/hc/en-us/articles/223181828 |
| 38 | **The strategy is already in market:** Schoolcase ($9/mo, $60/yr, 14-day trial) sells a per-family vanity address and names all three modes explicitly — "**Hand it out to schools, coaches, and directories.** / Auto-forward from Gmail, Outlook, or iCloud. / Forward as you go, one email at a time," pitched as "your school never has your real email." | live competitor | US parents | Schoolcase (vendor site) | 2026 (retrieved 2026-08-21) | Primary vendor site. | C (primary vendor doc) | https://schoolcase.app/ |
| 39 | **Ohai gates the same feature behind Premium ($9.99/mo) and ships the design detail that neutralizes the main objection:** "**Give this email to schools, clubs, sports teams, or memberships** that send frequent updates… no manual forwarding needed," and — critically — "**Every message scanned by Ohai is also forwarded to your regular inbox.**" | live competitor | US parents | Ohai.ai (vendor) | 2026 | Primary vendor site. | C (primary vendor doc) | https://ohai.ai/ |
| 40 | **Sense's architecture cannot do the Trojan horse at all**, and this is the design lesson: a **single shared** address (`share@getsense.ai`) routes by sender identity, so a school emailing it has no family to route to. Sense's own guidance is "turn on email notifications in each app, then forward" — it never proposes registering its address. | architecture | — | Sense (vendor) | 2026 | Primary vendor site. **A shared address supports forwarding only; only a per-family address supports registration.** | C (primary vendor doc) | https://getsense.ai/school-email-organizer |
| 41 | **Mass-consumer proof that people will register a proxy address with a third party:** Apple Hide My Email, Firefox Relay and SimpleLogin are exactly this pattern at scale — Firefox Relay's pitch is "any time a website, app, store, or restaurant asks for your information." | precedent | US consumers | Apple, Mozilla | 2025 | Primary vendor documentation. **Neither Apple nor Mozilla publishes any adoption number** — only SimpleLogin's unverified "1,000,000+ users." | C (primary doc) | https://support.apple.com/en-us/105078 ; https://relay.firefox.com/ |
| 42 | **Own analysis, 4,193 App Store/Play reviews captured 2026-08-21 — the pattern's adoption is bimodal.** Share of reviews spontaneously naming email-in: **Jam 8/88 = 9.1% (all 5★)**; Skylight 4/638 = 0.6%; Ohai 4/~130; Hearth 0/117; **Cozi 0/1,917; Todoist 0/1,000; Evernote 0/1,000.** | 9.1% vs 0% | US app reviewers | Own analysis of iTunes/Play review APIs | 2026 | **Own-analysis proxy, not a vendor statistic. Non-probability (reviewers self-select).** When the address is the front door and the parse works, ~1 in 11 reviewers names it unprompted as their favourite thing; when it is a settings-screen utility, **0 of 3,917** mainstream consumers ever mention it. | C (own analysis) | — |
| 43 | **Verbatim, from a self-identified non-technical user — the pattern IS comprehensible to normal consumers:** "One of the things I love the most is the way I can forward an invitation to the jam email address, and it is automatically added CORRECTLY to our shared calendar… And truly, **I am not all that tech savvy**, and it was so simple signing up and getting going." | verbatim | US parent | Jam, App Store US, 5★ | 2024-03-25 | Single review. Corroborated by Jam 5★ 2024-07-09: "I have 3 kids at 3 different schools (!!!!)… Literally all you do is forward the emails… I use this all the time now." | C (verbatim) | App Store US |
| 44 | **The verbatim that should govern the whole product design — silent failure is catastrophic and invisible:** "As someone with ADHD that feature was invaluable… **Once I forwarded an email to Skylight, it was out of my head.** Then without realizing it, email forwarding [stopped]. I kept forwarding emails, assuming everything was being added… **About a year and a half later… After missing multiple important appointments and events**, I discovered [the change]." | verbatim | US parent | Skylight, App Store, 3★ | 2026-07-30 | Single review; corroborated by Skylight 1★ 2026-05-11 and 1★ 2024-09-11. **Skylight DOES send a confirmation email with an Undo button and this user still went 18 months — confirmation emails are not a sufficient feedback loop.** | C (verbatim) | App Store US |
| 45 | **The verbatim that explains why forwarding beats OAuth even when OAuth is available:** "My job has our calendars locked down and can't be shared or joined so I've struggled to remember things on 2 calendars. **I love that I can just forward calendar invites** and it adds them to a single calendar." And the objection it answers: "**giving full inbox access with no granular control over what's shared** makes me cautious about privacy. My Gmail inbox is a treasure chest of personal data." | verbatim | US parents | Ohai.ai, App Store, 4★ and 3★ | 2026 | Single reviews. | C (verbatim) | App Store US |
| 46 | **You cannot have both unguessable and memorable, and the vendors admit it.** Evernote: the address `username.5199b42@m.evernote.com` is "designed to **prevent unauthorized people from easily remembering** and using it," the only fix offered is "save it in your contacts," and it cannot be customised. Readwise: "using a non-random string **may increase the chance** of your Reader email receiving spam." | design tradeoff | — | Evernote (help updated 2026-08-11), Readwise | 2026 | Primary vendor documentation. | C (primary doc) | https://help.evernote.com/ ; https://readwise.io/ |
| 47 | **The explicit counter-precedent — read before designing.** Trello: "Your unique board and card email addresses are **only visible to you. If you share them, other people can create cards or comments as you.**" An inbound address that can write to shared family state, handed to a district, is an unauthenticated write endpoint for everyone that district CCs. | security | — | Atlassian/Trello | 2026 | Primary vendor documentation. | C (primary doc) | https://support.atlassian.com/trello/ |
| 48 | **Corporate mail security silently breaks forwarding, and the incumbent ships a FAQ about it:** Expensify — "If your company uses **Proofpoint Hosted Email Security**, you may be unable to forward receipts to receipts@expensify.com." Its fallbacks are in-app upload and SMS. | breakage | US consumers | Expensify | 2026 | Primary vendor documentation. **Any serious forwarding product needs a non-email ingest path.** | C (primary doc) | https://help.expensify.com/ |
| 49 | **Parent trust decays with institutional distance, and the instrument never even reaches "a company":** teachers **91%** → principals 83% → counselors 79% → superintendents **61%** → state DOE **59%**. A 32-point drop occurs entirely *within* the education system. | 91% → 59% | US parents of children 5–17 | Data Quality Campaign / The Harris Poll | 2015 (**DATED — 11 years old**) | n=**1,093** US parents, fielded Nov 2015. **The questionnaire contains no "third-party company/app" category at all.** | B (dated) | https://dataqualitycampaign.org/resource/parents-want-childrens-data/ |
| 50 | **Concern about commercial handling of kids' data is near-universal and non-partisan:** **84%** of parents are concerned about kids' personal data being **misused** by AI; **81%** about AI **collecting kids' info without their knowledge**; **68%** want strong laws forcing companies to make AI safe vs **24%** who would trust self-regulation (68% D / 70% R). | 84% / 81% / 68% | US parents | Common Sense Media (Lake Research + Echelon Insights) | 2025 | n=**843 parents** base, fielded **Nov 17–26 2025**. | B | https://www.commonsensemedia.org/research |
| 51 | **No Tier A/B US survey measures either target construct** — parents' comfort granting a consumer app OAuth inbox access, or comfort with a third party receiving their child's school communications. P10 independently found the same for OAuth: "**NO DATA EXISTS at any age.**" | no data | US parents | — | 2026 | Exhaustive search across Pew, Common Sense, DQC, Learning Heroes, NPU, FPF, Gallup-Walton, PDK. | — (negative finding) | — |
| 52 | **FERPA does not regulate a parent-side app in either architecture.** 34 CFR §99.1(a) applies "to an **educational agency or institution** to which funds have been made available under any program administered by the Secretary"; §99.3 "education records" requires the record be "**Maintained by** an educational agency… **or by a party acting for** the agency." A copy held for the parent is neither. | not regulated | — | 34 CFR Part 99 | current | Regulation text read directly via eCFR. **Also: "school official" is NOT defined in §99.3 — it is operative only in §99.31(a)(1). Any brief citing "§99.3 school official" cites something that does not exist.** | A | https://www.ecfr.gov/current/title-34/subtitle-A/part-99 |
| 53 | **But the two architectures diverge sharply on residual exposure.** Registering our address (A): §99.33(c) exempts only §§99.31(a)(8),(9),(11),(12),(14),(15),(16) — a §99.30 consent disclosure is **not** on that list, so **§99.33(a)'s redisclosure restriction plausibly binds the company**, SPPO can investigate it directly (§99.64(b)), and §99.67(e) allows a **five-year** access ban. OAuth-reading the parent's inbox (B): §99.31(a)(12) makes school→parent a **no-consent-required** disclosure and **§99.33(c) expressly strips the redisclosure condition** — the chain terminates at the parent. | A riskier than B | — | 34 CFR Part 99 | current | Regulation text. **Note the brief's five-year cite is §99.67(e), not §99.33(e) — current §99.33 has only (a)–(d).** | A | https://www.ecfr.gov/current/title-34/subtitle-A/part-99 |
| 54 | **State student-privacy laws do not attach — and the trigger is marketing, not contracting.** California SOPIPA §22584(a)(7) requires actual knowledge the site "**is used primarily for K–12 school purposes and was designed and marketed for K–12 school purposes**," and §22584(j) says it "**does not apply to general audience** internet websites." **Illinois SOPPA's operator definition is word-for-word identical** with the same carve-out at §30(3). New York Ed. Law §2-d(1)(k) requires receipt "**from an educational agency pursuant to a contract or other written agreement**" — both elements fail. | no attachment | — | Cal. B&P §22584; 105 ILCS 85; NY Ed. Law §2-d | current | Statutory text. **Your marketing copy is the compliance surface: "manage your child's school communications" invites the argument; general-audience family positioning avoids it.** | A | https://leginfo.legislature.ca.gov/ ; https://www.ilga.gov/legislation/ilcs/ |
| 55 | **One state does bite Architecture A specifically:** Illinois SOPPA §26(2) bars a school from sharing covered information with anyone "**other than the student's parent**" absent a written agreement — so registering a third-party address in Illinois arguably forces a school contract, the exact burden the strategy exists to avoid. §27(b): a non-compliant agreement "is **void and unenforceable as against public policy**." | IL blocker | Illinois | 105 ILCS 85 | current | Statutory text. | A | https://www.ilga.gov/legislation/ilcs/ |

---

## FEASIBILITY MATRIX

Verdicts are for the **Trojan-horse path specifically** (parent registers our address directly with the
platform). The final column of the analysis — whether the platform can be captured by *auto-forwarding
from the parent's own mailbox* — is treated separately below the table, and it is much more forgiving.

| Platform | Secondary / arbitrary email? | Content in body or link-only? | SMS/push-only risk? | Verdict | Source |
|---|---|---|---|---|---|
| **ParentSquare** | **No — SIS-gated.** "Please contact your school office to add an additional email address"; nightly SIS sync is source of truth and overwrites parent edits. A minority of districts unlock "Edit Account." | **Body**, but Digest is the default for new accounts (daily 6pm summary); instant is opt-in. | Urgent alerts are SMS-inescapable by ToS. | **BLOCKED** (front-office visit per district; overwritten nightly) | hartdistrict.org/apps/pages/ParentSquare ; parentsquare.com/resources/help-center/ |
| **Remind** (ParentSquare-owned; **not sunset**) | **YES — best in the set.** "Click on the **+ Add device** button to add an additional email or phone number," confirmed by a 4-digit code. | **Full content, two-way by email.** Voice clips/surveys are link-only. | **Yes, silently:** installing the app "automatically disables" text and email. | **WORKS — with the app-install trap** | help.remind.com/hc/en-us/articles/206430755 |
| **ClassDojo** | **No secondary.** Email is the login and must be globally unique. A second parent account is **teacher-initiated** and sees class content only, not DMs. | Announcements carry "the **full text**… with images displayed in-line." Private chat body: **undetermined**. | **Yes, hard:** "By downloading the app, you'll receive push notifications instead of email… **it's not possible to receive both**." Parent Chat: "All messages happen within ClassDojo." | **BLOCKED** (and worst ToS — see below) | help.classdojo.com/hc/en-us/articles/205647195 ; /360050778411 |
| **Seesaw** | **No.** "Seesaw accounts can only use one email address at a time and cannot be merged." Only route is an 11th-slot family account (cap 10); teachers can see and remove any connected account. | **Digest is explicitly contentless:** "will receive an email summary with the number of new posts… but **will not see message content**." Per-event email body: **undetermined**. | SMS is contentless and mutually exclusive with push. | **BLOCKED** | help.seesaw.me/hc/en-us/articles/115005566243 ; /206528005 |
| **TalkingPoints** | **Impossible.** Login is a phone number; email is a marketing opt-in. Self-editable fields are "phone number, name, preferred language, and profile photo" — email is not among them. | Where email exists: "Email body uses the same text as the Text Message." | **Yes, total.** Family email exists ONLY for district emergency broadcasts on a paid add-on. **A parent cannot cause a single TalkingPoints email to reach an address of their choosing.** | **BLOCKED** | intercom.help/talkingpoints/en/articles/10073818 ; talkingpts.org/families/ |
| **PowerSchool** | **YES — the cleanest legitimate door.** "**Additional Notification Emails**: If you have authorized the delivery of email notifications to another person, enter the other person's email. **Separate multiple email addresses with commas.**" Parent-controlled, arbitrary, plural, no school action. | **Real content** — grades, assignments, attendance, announcements, balances. | Real-time changes are push-only to the mobile app. | **WORKS — but cadence caps at "Daily… except Saturday and Sunday."** No real-time email. | ps.powerschool-docs.com/pssis-student-parent/latest/email-notifications |
| **Infinite Campus** | **Effectively no.** The parent-editable "Account Security Email" receives **no notifications** (password recovery only). The notification address is district-gated: "**If your school has turned on certain options**, you may be able to modify your phone numbers and email addresses," and edits route through an approval queue. Census stores a Secondary Email; **parent-UI exposure unproven.** | Email channel carries body; the Inbox channel "places a note in the parent's inbox that a new message is available." | **Yes:** grades/attendance/assignments are **push-only at every configuration**. | **BLOCKED** (biggest install base, weakest fit) | kb.infinitecampus.com/help/campus-parent-portal ; /push-notifications-mobile-portal |
| **Blackbaud** | **Partial.** A native **CC Email** field exists — "Whenever Pushpages (Newsletters) are sent to the primary email address, a duplicate is also automatically sent to the CC email" — but it reaches **Newsletters only**, notifications follow primary, and edit rights are school-gated ("By default, **No** is selected to prevent access"). Parent self-edit: **undetermined**. | **Weakest content of the set.** Blackbaud instructs schools that templates "should be **generic**… Placeholders are used." | Inbox Messages is a walled internal messenger that "cannot be disabled for an individual role." | **PARTIAL — low value even when it works** | webfiles-sc1.blackbaud.com/.../bb-core-subscribe-to-notifications.html |
| **TeamSnap** | **YES, self-serve** — main roster contact clicks "+ Add Family Member" with any email; multiple emails per profile with a per-email "Receive emails" toggle. | Body. | No. | **WORKS — but per team.** Must be repeated for every team, every season; added contacts get **full account access** to that roster. | helpme.teamsnap.com/article/108 ; /article/125 |
| **SportsEngine** | **YES, self-serve, two ways** — account-level "Add Email" (verified), and per-athlete "Below the **Secondary** heading, enter the additional email address." | Body. | No. | **WORKS.** Caveat: "**You can not have two SportsEngine accounts with the same email address (primary or secondary)**" — so addresses must be unique per family, which a per-family design satisfies. | help.sportsengine.com/en/articles/6311527 ; /6304756 |
| **Sawyer** | **YES, fully self-serve**, and providers are locked out: "providers do **not** have access to update email addresses on a customer's behalf." | **Best content fidelity of the set** — activity, participant, date/time, location, instructor; no character limit on provider messages. | Provider SMS may have no email counterpart (**undetermined**). | **WORKS — but only by becoming the primary login.** Sawyer: "providers will use the **primary** email on your account for correspondence even if there are multiple contacts." | support.hisawyer.com/en/articles/11326156 |
| **Jumbula** | **UNDETERMINED — a real gap.** No KB article documents a parent adding or changing their own email; the Family Dashboard "lets you add or edit profiles," but whether an added profile receives mail is unconfirmed. | **Email-native, full content** — org-authored bodies with merge tags; reminders carry agenda and details. | No push/in-app silo. Some orgs send text-only campaigns. | **UNKNOWN — likely works; also the only genuinely permissive ToS in the set** | kb.jumbula.com/portal/en/kb/articles/the-new-family-dashboard |
| **BAND** | **No.** One email per account. The "Accounts" screen is a login-method list, not a recipient list. | **Undetermined** — BAND publishes nothing on email body content. | **Yes, total.** Posts/comments/chat have **no email path**; email exists only via two manual admin actions, one capped at 100 people. | **BLOCKED** | help.band.us/help/1171 ; /1205 ; /1097 |
| **GameChanger** | **No.** Cannot reuse an email already in use; player-follower invites cap at 5; the add-contact button "will not appear for teams that are 13U or lower." | Body on the fallback path — "The email notification will contain the event details, and the team member can RSVP… directly from that email." | **Yes, and it is actively revoked:** email flows only to addresses that have **never registered a GameChanger account**; registering flips you to push. Messaging: "Users must download the app." | **BLOCKED** | help.gc.com/hc/en-us/articles/360041839871 |
| **Brightwheel** | **No self-serve.** Email **is** the username; "Providers are unable to edit a student contact's email… once the guardian account has been created." A new address must be added by the **provider**, or by another parent contact if the provider permits. | Body (daily reports, calendar, billing). | SMS notifications are opt-in, not exclusive. | **PROVIDER-GATED** — one request per centre, not per district; the easiest of the "gated" set | help.mybrightwheel.com/en/articles/9362776 ; /11817047 |

**Score: 5 clean WORKS (Remind, PowerSchool, TeamSnap, SportsEngine, Sawyer), 1 PARTIAL (Blackbaud),
1 UNKNOWN (Jumbula), 1 provider-gated (Brightwheel), 6 BLOCKED (ParentSquare, ClassDojo, Seesaw,
TalkingPoints, Infinite Campus, BAND, GameChanger — 7 including GameChanger).** The five that work
skew to **sports and one SIS**. The blocked set contains **the two platforms with the largest school
install bases.**

### Terms of Service — the picture is not "no rule found"

This is worse than the strategy assumes, and it varies enormously by platform.

- **ParentSquare** — no anti-bot or anti-third-party clause; nearest are a ban on redistributing page content and on "harvest or otherwise collect information about others, including email addresses." Crucially, **the contract runs against the district, not the parent** ("Your District can set other permissions applicable to your access or use"). A violation notice lands on the parent's school. That is a *worse* failure mode than a notice landing on us.
- **Blackbaud** — same structure: the AUP's "You" is the school.
- **Seesaw** — the hardest legal fact in the set. §2.2 prohibits using Service content "for any **machine learning and/or artificial intelligence training or development purposes**." That is a flat AI ban, not a rate limit, and it points straight at an LLM extraction pipeline.
- **ClassDojo** — most hostile overall: bans "automated means, including spiders, robots, crawlers, data mining tools"; bans sharing account credentials; restricts to "personal, noncommercial use"; and explicitly forbids building or supporting "products or services **in competition with ClassDojo**."
- **GameChanger** — names the pattern directly: you "may not **share it with a third party service so they can access your Account**," plus bans on automated agents and scraping, with stated escalation to legal action.
- **BAND** — a clause that reads as if drafted for this case: "Accounts with temporary phone numbers or e-mails that are **not means for continuous contact** may be determined unusual and service may be restricted."
- **Sawyer** — licence is "personal… non-assignable and non-transferable"; "Your accounts are not transferable"; "It's not OK to use false information."
- **PowerSchool** — "Usernames and passwords are personal… may not be shared or transferred"; personal non-commercial use; no scraping. **Note the asymmetry: the Additional Notification Emails field is an official product feature, so using it is not credential sharing.** This is the cleanest legitimate path in the entire matrix.
- **Jumbula** — the only genuinely permissive ToS: ~15 sentences, no anti-bot, anti-automation or anti-scraping clause at all.
- **Infinite Campus** — **no parent-facing ToS exists.** The governing document is a different district AUP per user, unknowable at scale. That is not permission; it is unquantifiable risk.

None of these prohibit a parent **auto-forwarding their own received mail from their own mailbox** —
which is the strongest argument for making forwarding, not registration, the primary architecture.

---

## Interpretation

**1. The fragmentation is real, it is not shrinking, and the honest number is a district-side one, not
a parent-side one.** The best-sourced figure in the category — LearnPlatform's 2,591 → 2,739 → 2,982
distinct tools per district per year — **rose every year** through the stable-method period (#1). But
it measures district *access*, not parent *logins*, and the same report's per-person figure is **4
LTIs** (#2). Using 2,982 as "apps a parent deals with" would be a misuse that a reviewer will catch.
The parent-side number remains the Edsby n=125 (#9) — and I looked hard for something better and
**found nothing** (#12). Worse, the federal instrument that should answer it, NHES:2023, **contains no
item counting apps or portals and no item on missed information** (#11). That absence is itself the
most defensible thing I can say about parent-side fragmentation: nobody has measured it. Two
corrections to how P4 carries the Edsby figure: n is 125 parents (not 50) and the population is
**North American, not US** — flag it every time.

**2. Districts are consolidating the channel; the parent's surface area is not shrinking, and the
biggest "consolidation" did not remove a product.** ParentSquare at 22M students (#4), ClassDojo
launching a district product in Jan 2026, Kentucky mandating an exclusive communication system by
statute (#15) — the district-side consolidation is genuine and will continue. But **ParentSquare has
not sunset Remind** (#16): both Hub and Chat "remain available," Remind's help centre was updated the
day before this research, and there is no published EOL. Meanwhile district consolidation
announcements almost never *forbid* teachers from using other tools, Kentucky's law governs
employee↔student contact rather than the parent's app pile, and **the entire sports and activity
layer — 30M TeamSnap users, 16M SportsEngine athletes (#8) — is outside any district's jurisdiction
and is consolidating on its own separate axis** (PlayMetrics/SportsEngine, LeagueApps/NCSI, both 2026).
The fragmentation that actually hurts a parent is *cross-institutional*: school + district + sports +
camp + music + scouts + PTA + medical. No district platform has authority over any of it. So: anyone
claiming this is being solved upstream is wrong; anyone claiming districts aren't consolidating is
also wrong. The wedge survives, but its centre of gravity is **outside the school**, not inside it.

**3. The Trojan horse as literally specified is a leaky workaround, and the leak is in the worst
place.** Five platforms genuinely support a self-serve additional address — Remind, PowerSchool,
TeamSnap, SportsEngine, Sawyer — and PowerSchool's is a purpose-built product feature ("Separate
multiple email addresses with commas") that raises no ToS question at all. But **ParentSquare and
Infinite Campus, the two largest school-side install bases, both require a district front-office
request and both re-sync nightly over anything the parent enters** (#17). ClassDojo and Seesaw make
email the login and cannot hold a second address. TalkingPoints, BAND and Infinite Campus have **no
email path at all** for the content that matters (#19). And the single most damaging fact is #18:
ClassDojo, Remind and Seesaw **silently disable email the moment the parent installs the app** — which
is how essentially every parent uses them. GameChanger inverts it, mailing only addresses that have
*never* registered. So even where registration is mechanically possible, the platform's default
notification state is working against you.

**4. But the sibling idea — auto-forward from the parent's own mailbox — is much stronger, and it is
what the incumbents actually ship.** Every platform in the matrix that has any email channel can be
captured this way, because we are receiving mail the parent already receives; no platform cooperation
is required and no ToS in the set forbids it. Gmail's setup is desktop-web-only with a verification
handshake (#31) — but **we own the destination inbox, so we can auto-click the confirmation link and
collapse the hardest step.** That is a genuine design unlock hiding in a documentation footnote. The
constraints are real but bounded: Microsoft 365 disables external forwarding by default (#32), which
matters for parents reading school mail on a work account; forwarding breaks DMARC by protocol
(#33), so we must publish SPF/DKIM/DMARC on the ingest domain, implement ARC, and **never reject
inbound on DMARC failure** — or we will silently drop exactly the school mail we exist to parse.
Note that Sense, the most focused competitor in this wedge, uses a **single shared address** that
structurally *cannot* be registered with a school (#40), and its own published guidance is "turn on
email in each app, then forward." It never proposes the Trojan horse. That is a competitor with
every incentive to find the shortcut, declining to take it.

**5. The CASA avoidance is worth more than it looks, and the decisive number is 100.** Dropping
`gmail.readonly` removes: a restricted-scope classification that **no Gmail body-reading scope
escapes** (#20, killing the circulating "use gmail.modify instead" workaround); a 6-week-to-several-
months verification (#21); a **mandatory, annual, full-re-test-every-year** third-party security
assessment (#22) that has had **no free tier since May 2024** (#23) at $675–$4,500/yr (#24); annual
read-only auditor access to production at Tier 3 (#26); and an unresolved policy question about
whether an LLM pipeline over Gmail content complies with Limited Use at all (#27) — which for an
AI-first parenting app is arguably the scariest item on the list. Replacing all of that is a
**$0–20/month inbound mail service that nobody reviews or approves** (#30). But the number that
actually forces the decision is #25: an unverified restricted-scope app is capped at **100 users over
the entire lifetime of the GCP project, and the cap cannot be reset.** Today's closed beta fits
underneath it. Any launch does not — and launching without clearing verification permanently burns
that project. The Gmail integration is not "working"; it is running out a clock. One asymmetry worth
banking: **Microsoft is cheap.** Consumer Outlook.com via Graph `Mail.Read` needs no admin consent
and no CASA analogue, and publisher verification is explicitly free (#28). Apple is a flat no —
there is no iCloud Mail API, only IMAP with an app-specific password (#29), which is product-hostile.

**6. SMS and push are mostly a wall, and the wall is on the ingest side, not the cost side.**
Inbound-only numbers need **no A2P 10DLC registration** and cost fractions of a cent, with AT&T,
Verizon and US Cellular free to receive (#34) — cost is not the blocker. The blockers are absolute:
an iPhone **cannot** forward SMS anywhere except the user's own Apple devices (#35); Android SMS
reading is gated to default-handler apps under threat of Play removal (#36); a third-party iOS app
cannot read other apps' push notifications; and a Twilio number **cannot text a short code** (#37),
which closes the "just give the school our number" idea for Remind's 81010 specifically. The one
genuinely open question is empirical, not legal: whether carriers and platforms silently reject
A2P-to-A2P long-code traffic or run undocumented line-type checks against VoIP numbers. **That is
answerable for about $1.15 — buy one Twilio number, register it with a live Remind or TeamSnap
account, and watch.** It is cheaper than any further desk research and I recommend it over more reading.

**7. Consumers do understand a forwarding address — but only when it is the front door, and the
failure mode is brutal.** My own count across 4,193 reviews is bimodal (#42): where the address *is*
the product, ~1 in 11 reviewers names it unprompted as their favourite feature, all five-star; where
it is a settings-screen utility, **0 of 3,917** mainstream Cozi/Todoist/Evernote reviewers mention it
once. A self-identified non-technical parent describes it as trivially easy (#43). It also survives
conditions where OAuth cannot: locked-down work accounts, and parents who explicitly refuse inbox
access (#45). But #44 should govern the design. The property that makes forwarding delightful — "once
I forwarded it, **it was out of my head**" — is precisely what makes silent failure invisible, and a
Skylight user went **eighteen months and multiple missed events** before noticing, *despite* Skylight
sending confirmation emails with an Undo button. Confirmation emails are not a sufficient feedback
loop. Whatever we ship needs positive liveness signalling — a visible "last message received N hours
ago," a nag when a family's stream goes quiet, and a non-email fallback (Expensify ships one because
Proofpoint silently eats forwarded mail, #48). Ohai's design detail is the one to copy: **"every
message scanned is also forwarded to your regular inbox"** (#39), which removes the "will I stop
seeing my own mail?" objection at a stroke.

**8. Privacy is the unmeasured risk, and FERPA points the opposite way from intuition.** No Tier A/B
survey has ever asked a US parent either question we need (#51) — P10 found the same independently.
The proxies are not encouraging: parent trust decays 32 points *within* the education system before a
company is even mentioned (#49, though 11 years old), and 84% of parents are concerned about misuse of
kids' data by AI (#50). We will have to field this ourselves; DQC's 2015 trust ladder is the right
instrument to borrow, with "a private company's app" added as a rung. On the law, the counterintuitive
result is that **the Trojan horse is the riskier architecture, not the safer one.** Neither approach
makes us a FERPA-regulated entity (#52). But OAuth-reading the parent's inbox has FERPA's chain
**expressly severed** at the parent by §99.31(a)(12) and §99.33(c), whereas registering our address as
a recipient plausibly attaches §99.33(a)'s redisclosure restriction to us, exposes us to direct SPPO
investigation, and carries a five-year district access ban as a sanction (#53). Illinois SOPPA
§26(2) arguably forces a school contract for the registration path specifically (#55). And the state
student-privacy trigger is **marketing, not contracting** (#54) — "manage your child's school
communications" invites the argument; general-audience family positioning avoids it. That is a
copywriting decision with legal consequences, and it should be made deliberately.

**9. The contradiction worth naming.** Findings #1 and #2 come from the same report and point opposite
ways: districts touch ~3,000 tools while individuals touch 4. Both are true — the district number is an
inventory, the individual number is usage — and the honest reading is that **institutional sprawl does
not automatically become parent-experienced sprawl.** Similarly, #4/#5/#15 (real, accelerating district
consolidation) contradicts #8/#9 (persistent cross-institutional sprawl), and the resolution is that
they operate on different axes. Anyone building a pitch deck off "parents juggle 3,000 apps" will be
caught. The defensible claim is narrower and still sufficient: **a US family's kid-related information
arrives through school, district, multiple activity providers, and other parents, and no single
platform — including the consolidators — has jurisdiction over more than one of those.**

---

## Section 2: WEAK SIGNAL (not citable — do not promote into Section 1)

- **"add@cozi.com."** Could not confirm this address exists. It appears nowhere on Cozi's live site,
  FAQ, or help sitemap, in Wayback FAQ snapshots from 2014/2017/2020/2023, or in **any of 1,917 Cozi
  reviews.** Cozi's current AI ingestion is "Cozi Max" ($79.99/yr), mechanism undocumented. **Do not
  cite add@cozi.com.**
- **"Digital Promise 2017: 74% of US districts use more than 26 different technology products, only
  33% have integrated the majority."** Quoted inside PowerSchool's SEC 10-K, which makes it tempting.
  Digital Promise is Tier B, but **the original was not traced**, and the figure is 9 years old. Do
  not cite until traced to the Digital Promise publication.
- **"CASA costs $15,000+."** Circulates in Reddit thread titles. **Unverified and far above every
  published lab price I could confirm** ($675–$8,000). Reddit blocked every fetch path this session.
  Historical Google language is citable *as historical only*: a Wayback capture of 2020-06-01 said
  "$15,000 and $75,000 (or more)… payable whether or not your app passes," and 2022-06-01 said
  "$10,000 - $75,000… smaller applications may see costs at a lower threshold of $4,500." **Google
  removed all fee language between the 2022-06 and 2023-06 snapshots.** The live prices are the
  labs' own.
- **Google's own FAQ still contains the phrase "free tier 2 assessment,"** contradicting both ADA's
  deprecation banner and Google's own May-2024 notification email. Could not resolve whether this is
  stale text or a live low-risk carve-out. **Plan for paid; ask in the verification thread.**
- **Any funnel comparison of email-forwarding onboarding vs. OAuth inbox connection** — conversion,
  activation, drop-off. Searched startup blogs, Lenny's, Reforge, First Round, YC, Mixpanel, Amplitude.
  **Does not exist in public. Put no number on this.** Same for activation rates on inbound addresses
  at Evernote, Todoist, Trello, Slack, Expensify or Readwise — **no vendor publishes one.**
- **The Orbis engineering blog claim that `gmail.modify` is "sensitive (Tier 2), not restricted"**
  (2026-02-10) is **factually wrong** per Google's own scope page. Their pre-scan methodology (OWASP
  ZAP baseline, Fluid Attacks DAST, SSL Labs, securityheaders.com **before** engaging the lab; passed
  Tier 2 for $540 with only 4 low-severity findings) is still worth copying. Do not copy the scope claim.
- **Child Trends, "Parents Trust School Communications About Education Far More Than AI, Social Media,
  or News," 2026-07-28.** Tier B, plausibly the single best source in existence for the "missed
  information / channel trust" question. **childtrends.org is a client-rendered SPA that defeated every
  fetch method.** Highest-value manual retrieval on this list.
- **Center for Democracy & Technology's annual paired parent/student/teacher student-privacy survey
  series** ("Hidden Harms" / "Off Task" / "Hand in Hand"). Asks parents directly about school data
  sharing. **cdt.org returns 403 to all automated access; Wayback rate-limited.** Second-highest-value
  manual retrieval — most likely source of a directly on-point privacy number.
- **PowerSchool "2026 K-12 EdTech Pulse"** (Business Wire 2026-02-03) — exists, fetch timed out.
- **National Parents Union Feb 2026** (n=1,511; only 37% say their school shared AI policy info;
  ~two-thirds want stronger data protections) — **fielding window not disclosed.** Hold until toplines.
- **Talker Research/SWNS "why parents dread this time of year" (May 2025), Life360 "Back-to-School
  Stress Hits New High" (Aug 2025), NY Post "parents lose 48 nights of sleep."** PR-survey mill and
  vendor content marketing, no method. **Killed.** Also note: **GovTech and eSchool News coverage of
  "App Overload" are re-reports of the same Edsby press release** — citing them alongside Edsby fakes
  corroboration, and they render the satisfaction figure inconsistently (42% vs 85%). Use the primary PDF.
- **FCC one-to-one consent rule status.** Believed vacated by the Eleventh Circuit in *Insurance
  Marketing Coalition v. FCC* (Jan 2025), but **fcc.gov returned Access Denied** — do not publish
  without checking. Similarly, *Gonzaga Univ. v. Doe*, 536 U.S. 273 (2002) (no FERPA private right of
  action) was not re-verified from the opinion this session.
- **Whether a §99.30 consent authorizing onward use displaces §99.33(a)'s redisclosure restriction.**
  No text, no SPPO guidance, and no case found. **This is the single most consequential open legal
  question for the registration architecture**, and it turns on whether the mailbox is characterized as
  "the parent's" or "the app's" — an architecture decision, not a legal one.
- **Adoption numbers for Apple Hide My Email and Firefox Relay.** Neither publishes any. Only
  SimpleLogin's unverified vendor claim of "1,000,000+ users."
- **Reach numbers for Bloomz, Seesaw, Brightwheel, and Blackbaud K-12.** None published anywhere.
- **All Reddit, Trustpilot and G2 evidence.** reddit.com is blocked at the tool level, its JSON/RSS
  endpoints 403, every Redlib mirror was down or walled; Trustpilot and G2 403. **Zero quotes from
  those platforms appear in this report** — a real coverage gap for verbatim user language.

### Explicitly undetermined on the feasibility matrix

Seesaw per-event email body content; ClassDojo private-chat email body; BAND email body content and
the location of its "email alerts for events" toggle; GameChanger Announcement email delivery;
**Jumbula parent self-serve email edit** (the whole Jumbula row hinges on this); Infinite Campus
Secondary Email exposure in the parent UI; Blackbaud parent self-edit of their own CC Email; Sawyer's
provider-SMS email counterpart; PowerSchool SchoolMessenger/Communications parent contact behaviour;
whether carriers systematically filter A2P→A2P long-code traffic; and whether Remind, ParentSquare,
TeamSnap, SportsEngine, SchoolMessenger or Blackboard/Finalsite silently reject VoIP/CPaaS line types.

### Method notes

- **The WebSearch budget was exhausted before this collector began.** All research was conducted via
  `curl` against Brave, plus direct fetches of constructed URLs. Brave, DuckDuckGo, Bing, Ecosia,
  Startpage, Mojeek and public SearXNG instances were all bot-blocked or rate-limited at various points.
- **What worked and is worth remembering:** vendor `sitemap.xml` grepping; **Zendesk help-center public
  APIs** (`/api/v2/help_center/articles/search.json` and `/api/v2/help_center/en-us/articles/{id}.json`),
  which bypass the Cloudflare 403 on Remind, ClassDojo and Seesaw; **Intercom help-center search**
  (`https://help.X.com/en/?q=…` returns server-rendered article links) for Brightwheel, SportsEngine,
  Sawyer and TalkingPoints; HelpScout search for TeamSnap; Wayback CDX; `data.sec.gov`; `ecfr.gov`;
  and Google News RSS.
- **ParentSquare's help center is now login-gated** (all Wayback captures 302 to signin; the Zendesk
  API returns an auth error). Its row in the matrix therefore rests on district IT pages plus
  ParentSquare's own public FAQ, terms and privacy policy. I regard the finding as solid — three
  independent sources say the same thing — but it is not from the vendor's own help center.
