# beta-v1 — Design Sprint 2 spec (+ the sprint-1 gap)

Extracted **once** from Figma `Wb072IjTsBT7Ooqc41UFbK`, pages
`754:4311` (*Design sprint 2 - exprience (wip)*, Aug 5) and `754:4310` (*Design sprint1*),
via the REST API. **This file is the source of truth for the build — do not re-read Figma.**
The Figma MCP under-reports this file (it lists 2 of 12 pages); use REST if it must be re-read.

Copy strings below are verbatim from the frames, typos included. Every frame carries the same
five-item tab bar (HOME · COACH · PLANNER · CIRCLE · SETTINGS), noted as `[Tab Bar]` and not
otherwise repeated. Status bars and decorative vectors are omitted.


---

## Circle

### Circle-000 — no circle yet — `754:5810`  (440×792)

- <Vector>
- TEXT: "Gather your circle"
- TEXT: "Your circle are the people who show up for Ben & Lily — grandparents, sitters, close friends. bring them into one place."
- <button>
- TEXT: "Invite someone"
- [Tab Bar]

### Circle-001 — no conversations — `754:5882`  (440×792)

- TEXT: "Start the conversation"
- TEXT: "Ask your circle for advice, share a win, or just check in."
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>
- [Tab Bar]

### Circle-002 — new conversation composer — `754:5898`  (440×841)

- [Tab Bar]
- TEXT: "New conversation"
- TEXT: "Dinner with Ben & Lily"
- TEXT: "I need dinner ideas for the kids tonight. What’s on your plates?"
- TEXT: "Invite to the conversation"
- TEXT: "M"
- TEXT: "Contact name"
- <menu - dots>
- dots
- TEXT: "H"
- TEXT: "Contact name"
- <menu - dots>
- dots
- TEXT: "T"
- TEXT: "Contact name"
- <menu - dots>
- dots
- TEXT: "Add circle members"
- <add>
- group
- <Global Button>
- <Star>
- TEXT: "Start a discussion"
- <X>
- <Global Button>
- <Star>
- TEXT: "Cancel"
- <X>
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>

### Circle-003 — thread, one reply — `754:5827`  (440×792)

- <chatinput>
- <icon.attach>
- input
  - TEXT: "I need help with dinner ideas for Ben & Lily"
  - <icon.microphone>
- TEXT: "I need help with dinner ideas for Ben & Lily"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "T"
- TEXT: "I’m making crispy brussel sprouts with cheesy noodles tonight!"
- reactions
  - Frame
  - Frame
  - Frame
  - Frame
  - TEXT: "Reply"
- [Tab Bar]
- <back>
- TEXT: "Dinner plans for the kids"
- <back>
- <menu-dots>

### Circle-004 — thread, full — `754:5693`  (440×792)

- TEXT: "I need help with dinner ideas for Ben & Lily"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "T"
- TEXT: "I’m making crispy brussel sprouts with cheesy noodles tonight!"
- reactions
  - Frame
  - Frame
  - Frame
  - Frame
  - TEXT: "Reply"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "M"
- TEXT: "Thursdays are waffle nights for us"
- reactions
  - Frame
  - Frame
  - Frame
  - Frame
  - TEXT: "Reply"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "H"
- TEXT: "Can’t go wrong with a veggie pizza"
- reactions
  - Frame
  - Frame
  - Frame
  - Frame
  - TEXT: "Reply"
- TEXT: "Thanks for all you ideas!"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- <chatinput>
- <icon.attach>
- input
  - TEXT: "I need help with dinner ideas for Ben & Lily"
  - <icon.microphone>
- [Tab Bar]
- <back>
- TEXT: "Dinner plans for the kids"
- <back>
- <menu-dots>

### Circle-005 — conversation list — `754:5947`  (440×792)

- <menu - dots>
- dots
- TEXT: "Dinner plans for the kids"
- TEXT: "3 replies · last from Teri"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "T"
- directions_run_FILL0_wght400_GRAD0_opsz48 2
  - TEXT: "M"
- directions_run_FILL0_wght400_GRAD0_opsz48 3
  - TEXT: "H"
- <menu - dots>
- dots
- TEXT: "Gifts for the party this weekend"
- TEXT: "M started this — 4 replies"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 2
  - TEXT: "S"
- directions_run_FILL0_wght400_GRAD0_opsz48 3
  - TEXT: "M"
- [Tab Bar]
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>

### contacts — `754:6023`  (440×874)

- TEXT: "Contacts"
- TEXT: "Add"
- <add>
- group
- content
  - all contacts
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
    - contatct
      - avatar - default
        - TEXT: "CN"
      - TEXT: "Contact name"
      - <menu - dots>
      - dots
  - quick nav
    - TEXT: "A / B C D E F G H I J K L M N O P Q R S T U V W X Y Z"
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>
- [Tab Bar]

### invite preview A — `754:6094`  (440×874)

- <Global Button>
- <Star>
- TEXT: "Invite selected"
- <X>
- TEXT: "Add contacts"
- <Contacts>
- TEXT: "add contact"
- <import>
- Group
- TEXT: "Import CSV"
- <linkedin>
- Group
- TEXT: "Connect to LinkedIn"
- <copy link>
- TEXT: "Copy link to invite"
- Frame
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>

### invite preview B — `754:5987`  (440×874)

- <Global Button>
- <Star>
- TEXT: "Invite selected"
- <X>
- TEXT: "Contacts"
- <Contacts>
- TEXT: "add contact"
- <copy link>
- TEXT: "Copy link to invite"
- Frame
- TEXT: "https://share.mvparent.ai/invite"
- TEXT: "share.mvparent.ai"
- TEXT: "Greg and Teri invited you to their circle on MVP"
- TEXT: "Heather wants you in their circle — a place to share what works for Ben & Lily.""
- TEXT: "MVP"
- <back>
- <Vector>
- TEXT: "Circle"
- <back>
- <menu-dots>

### row context menu — `754:6705`  (145×111)

- TEXT: "Edit / Delete Send message / add to team"

---

## Coach

### coach-000 — first run — `754:5568`  (440×813)

- <coach>
- Layer_1
- TEXT: "Meet your coach"
- TEXT: "Sleep, tantrums, dinner, the days that feel like too much. your coach knows Ben and Llly and remembers what you've already tried."
- <button>
- TEXT: "Easy dinner ideas for tonight"
- <button>
- TEXT: "Bedtime is a fight right now"
- <button>
- TEXT: "How do I talk to Lily about..."
- <chatinput>
- <icon.attach>
- input
  - TEXT: "Ask the coach for help"
  - <icon.microphone>
- [Tab Bar]

### coach-001 — chat — `1008:4717`  (440×1145)

- user
  - TEXT: "I need help with dinner ideas for Ben & Lily"
- coach
  - TEXT: "Got it. quick question — are they picky, or open to trying new things tonight?""
- user
  - TEXT: "Ben will eat anything. Lily's going through a beige-food phase."
- coach
  - TEXT: "classic. here's one that usually works for both — deconstructed, so Lily can keep things separate and Ben can pile it on."
- coach
  - Frame
    - <favorites>
  - TEXT: "Sheet-pan chicken and veggie tacos Serves 4, 25 minutes / 500g chicken thighs, cut into strips / 1 bell pepper, sliced / 1 zucchini, sliced / 2 tsp cumin / 1 tsp paprika / olive oil, salt / 8 small tortillas / toppings on the side: shredded cheese, sour cream, lime / toss chicken and veggies with oil and spices, spread on a sheet pan, roast at 220°C for 18–20 minutes. serve everything separately so Lily can build a plain tortilla with just chicken and cheese, and Ben can load his up. / Want me to save this one, or find a few more like it?"
- <back>
- TEXT: "Dinner plans for the kids"
- <chatinput>
- <icon.attach>
- input
  - TEXT: "I need help with dinner ideas for Ben & Lily"
  - <icon.microphone>
- Frame
- Frame
- [Tab Bar]

### coach-002 — history — `754:5520`  (440×813)

- <menu - dots>
- dots
- TEXT: "Dinner plans for the kids"
- TEXT: "sheet-pan tacos worked for both kids — saved for next week"
- Frame
  - <favorites>
- <menu - dots>
- dots
- TEXT: "Kelsy's birthday party"
- TEXT: "Gift ideas for 5-year old girls"
- <menu - dots>
- dots
- TEXT: "Dinner advice"
- TEXT: "3 dinner ideas, no beige-food fights"
- <menu - dots>
- dots
- TEXT: "Bedtime battles"
- TEXT: "talked through Lily's bedtime pushback"
- [Tab Bar]

---

## Planner

### planner 01 — empty — `1026:10476`  (440×792)

- <planner-xl>
- TEXT: "MPV Planner"
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "Plan"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Ask the coach"
- TEXT: "Nothing planned yet? / Find a few options — nothing is booked or shared until you say so."
- <seach large>
- TEXT: "Find activities"
- TEXT: "Where to:"
- TEXT: "Zip code..."
- TEXT: "25 mi"
- <arrow>
- <tag item>
- <camp>
- TEXT: "Camp"
- <tag item>
- <camp>
- TEXT: "Activity"
- <tag item>
- <location>
- TEXT: "Trip"
- <tag item>
- <schoolwork>
- TEXT: "Classes"
- <tag item>
- <camp>
- TEXT: "Find activities"
- [Tab Bar]
- <camera>
- TEXT: "Paste a camp email or snap a flyer —  I'll pull out the details and track it."
- TEXT: "Planning for Ben & Lily"
- TEXT: "Edit kids and interests"

### planner 02 — ask the coach — `1026:10520`  (440×792)

- [Tab Bar]
- <planner-xl>
- TEXT: "MPV Planner"
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "Plan"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Ask the coach"
- TEXT: "Ask the coach / Find camps, sort out coverage gaps, or decide between options. I see the whole family plan."
- <button>
- TEXT: "Camps & school breaks"
- <button>
- TEXT: "Classes & sports"
- <button>
- TEXT: "Weekend outings"
- <button>
- TEXT: "Family trips — dates, packing, not bookings"
- <chatinput>
- <icon.attach>
- input
  - TEXT: "Just ask if you already have an idea"
  - <icon.microphone>

### planner 3 — board — `1026:10543`  (440×863)

- [Tab Bar]
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "Plan"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Ask the coach"
- TEXT: "2 next steps this week / $0 confirmed · 1 cost TBD · 2 tracked"
- TEXT: "View"
- <back arrow>
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "List"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Timeline"
- <tag choice>
- <check>
- TEXT: "All"
- <tag choice>
- <check>
- TEXT: "New"
- <tag choice>
- <check>
- TEXT: "Deciding (3)"
- <tag choice>
- <check>
- TEXT: "Needs action (1)"
- <seach large>
- TEXT: "Find more activities"
- TEXT: "98332 · 25 mi · camps, classes & more"
- <arrow>
- TEXT: "Lily & Ben"
- TEXT: "Deciding"
- TEXT: "University Place 3-Day Sports Mini Camps"
- TEXT: "75%"
- TEXT: "Camp · YMCA / City of University Place"
- TEXT: "Gig Harbor · Jun 22 – Aug 28"
- <tag choice>
- <check>
- TEXT: "Planned"
- <tag choice>
- <check>
- TEXT: "Ask the coach"
- <button>
- <addcircle>
- TEXT: "Plan something new"
- <back>
- <planner-xl>
- TEXT: "MPV Planner"
- <back>
- <menu-dots>

### planner 4 — activity detail — `1026:10608`  (440×1342)

- [Tab Bar]
- TEXT: "CAMP FOR LILY & BENJAMIN"
- TEXT: "Tom Taylor YMCA Summer Day Camp"
- TEXT: "YMCA of Pierce and Kitsap Counties"
- TEXT: "Lily & Ben"
- TEXT: "Registered, needs action"
- TEXT: "75% Match"
- TEXT: "FOR"
- TEXT: "Lily · fits ages 7–12"
- TEXT: "DATES"
- TEXT: "Jun 22 – Aug 28, 2026 / ⚠ Overlaps Rialto Beach trip, Aug 15–17"
- TEXT: "SCHEDULE"
- TEXT: "All Week Camp, Mon–Fri; weekly themes, age 7+ specialty add-ons. Registration open through August."
- TEXT: "LOCATION"
- TEXT: "Tom Taylor Family YMCA 10550 Harbor Hill Dr, Gig Harbor · 6 mi"
- TEXT: "COST"
- TEXT: "TBD — I'll track it once you register"
- <tag choice>
- <check>
- TEXT: "Planned"
- <tag choice>
- <check>
- TEXT: "Ask the coach"
- TEXT: "Why it matched"
- TEXT: "Weekly drop-in fits your flexible-weeks preference, Lily's age band, and it's the closest full-day option to home."
- TEXT: "Still to do"
- TEXT: "75%"
- <check circle>
- Frame
- TEXT: "Register Ben"
- <check circle>
- Frame
- TEXT: "Register Lily"
- <check circle>
- TEXT: "Forward the confirmation email"
- <button>
- <check>
- TEXT: "Mark next step done"
- TEXT: "Moves to All set once nothing is left."
- <back>
- TEXT: "Activity"
- <back>
- <menu-dots>

### planner 5 — coach adds to calendar — `1026:10766`  (440×1209)

- [Tab Bar]
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "Plan"
  - chip
    - TEXT: "2"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Ask the coach"
- user
  - TEXT: "What can we do with the kids this weekend?"
- coach
  - TEXT: "Got it. quick question — How much time do you have?"
- user
  - TEXT: "All day"
- coach
  - Frame
    - <favorites>
  - TEXT: "Weekend outing with the kids"
  - TEXT: "3 family-friendly ideas near 98332:"
  - TEXT: "Children's Museum of Tacoma — indoor, sensory-friendly; great rain backup. / Briscot Farm outing — simple outdoor animal time. / Salmon run at Ballard Locks — free, low-pressure."
  - TEXT: "My pick: the museum if weather turns."
  - <button>
  - <addcircle>
  - TEXT: "Add Museum to  calendadr"
- coach
  - TEXT: "Added Children's Museum of Tacoma to the plan for Lily — Saturday, Aug 8 at 11:00 AM, set as a 2-hour outing."
  - <button>
  - <addcircle>
  - TEXT: "View plan"
- Frame
- Frame
- <back>
- <planner-xl>
- TEXT: "MPV Planner"
- <back>
- <menu-dots>
- <chatinput>
- <icon.attach>
- input
  - TEXT: "What can we do with the kids the weekend?"
  - <icon.microphone>
- <tag choice>
- <check>
- TEXT: "Camps"
- <tag choice>
- <check>
- TEXT: "Classes"
- <tag choice>
- <check>
- TEXT: "Outings"
- <tag choice>
- <check>
- TEXT: "Trips"

### planner 6 — board, two cards — `1026:10680`  (440×1159)

- [Tab Bar]
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "Plan"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Ask the coach"
- TEXT: "2 next steps this week / $0 confirmed · 1 cost TBD · 2 tracked"
- TEXT: "View"
- <back arrow>
- <Segmented control>
- Button 1
  - <planner edit>
  - TEXT: "List"
- Button 3
  - <coach>
  - Layer_1
  - TEXT: "Timeline"
- <tag choice>
- <check>
- TEXT: "All"
- <tag choice>
- <check>
- TEXT: "New"
- <tag choice>
- <check>
- TEXT: "Deciding (3)"
- <tag choice>
- <check>
- TEXT: "Needs action (1)"
- <seach large>
- TEXT: "Find more activities"
- TEXT: "98332 · 25 mi · camps, classes & more"
- <arrow>
- TEXT: "Lily & Ben"
- TEXT: "Deciding"
- TEXT: "University Place 3-Day Sports Mini Camps"
- TEXT: "75%"
- TEXT: "Camp · YMCA / City of University Place"
- TEXT: "Gig Harbor · Jun 22 – Aug 28"
- <tag choice>
- <check>
- TEXT: "Planned"
- <tag choice>
- <check>
- TEXT: "Ask the coach"
- TEXT: "Lily & Ben"
- TEXT: "Needs action"
- TEXT: "Rialto Beach family trip"
- TEXT: "75%"
- TEXT: "Trip · Jun 22 – Aug 28"
- <check circle>
- Frame
- TEXT: "Pack toys"
- <check circle>
- Frame
- TEXT: "Meds & documents"
- <check circle>
- Frame
- TEXT: "Book room"
- <check circle>
- TEXT: "Download maps"
- <button>
- <addcircle>
- TEXT: "Plan something new"
- <back>
- <planner-xl>
- TEXT: "MPV Planner"
- <back>
- <menu-dots>

---

## Article

### artcile 01 — reader — `1007:3914`  (440×2515)

- Frame
  - <favorites>
- TEXT: "WE TRIED IT · Ages 3–7 · 4 min"
- TEXT: "A rainy Saturday, nothing bought"
- TEXT: "Four things to do with tape, a bedsheet, and whatever's in the recycling."
- TEXT: "It's 9:40am, it's raining, and you have maybe seven hours to fill. These four are in order of how long they last."
- TEXT: "1. tape roads"
- TEXT: "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."
- TEXT: "2. The box that becomes something"
- TEXT: "You need:  one large cardboard box, a marker. Buys you: thirty minutes, plus a week of it living in your hallway.  Don't tell them what it is. Ask them. A four-year-old will make a decision faster than you will. Where it goes wrong: if you cut the windows yourself, it becomes your project. Let it be ugly."
- TEXT: "3. bedsheet fort, with a rule"
- TEXT: "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."
- TEXT: "4. floor is lava, timed"
- TEXT: "You need: painter's tape. Buys you: forty minutes, sometimes two hours. Lay roads across the floor — around the couch, under the table, up one wall. Then hand over the cars and leave. The building is the activity; the driving is the bonus. Where it goes wrong: regular masking tape pulls up finish on wood floors. Painter's tape only."
- TEXT: "Miguel Alvarado · tested on an actual rainy Saturday with his two little ones in San Francisco"
- [Tab Bar]
- <back>
- <stamp>
- TEXT: "MVP Recommends"
- <back>
- <menu-dots>

---

## Sprint-1 gap — the avatar / account sheet

These are Home with the Page-4 `profile` component overlaid as a sheet, in its three variants.

### account01 — profile sheet, default (no activity) — `870:1234`  (440×1714)

- Icon Container
  - TEXT: "G"
- TEXT: "YOUR KIDS"
- Card Container
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Benjamin"
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Lily"
- <coach>
- Layer_1
- TEXT: "COACH  •  This morning"
- TEXT: "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."
- small button
  - TEXT: "Try this with Ben"
- For You
  - Title Container
    - <For You Icon>
    - TEXT: "FOR YOU"
  - Articles Container
    - Article
      - TEXT: "Care · 2 min"
      - Article Content
        - TEXT: "When bedtime becomes a negotiation"
        - TEXT: "What to do when the third glass of water isn't about water"
    - Article
      - TEXT: "This week"
      - TEXT: "Tips on surviving the day"
      - TEXT: "The big birthday parting is coming in 3 days"
      - Action Container
        - small button
          - TEXT: "See all"
- Section Title
  - <Section Icon>
  - TEXT: "COMING UP"
- Card Container
  - Card
    - TEXT: "Soccer camp starts on Friday"
    - TEXT: "Get Ben ready! Camp begins on Aug 8, 7am."
  - Card
    - TEXT: "Lily and Ben birthday outing"
    - TEXT: "Going to the zoo with the kids. Aug 4, 2pm."
    - Card
      - small button
        - TEXT: "See all"
- [Tab Bar]
- <profile>
- <Vector>
- TEXT: "Hi Greg!"
- TEXT: "No recent activity. Your history and saved articles can be found here."
- small button
  - <favorites>
  - TEXT: "Saved"
- small button
  - <history>
  - TEXT: "History"
- TEXT: "Account"
- TEXT: "Username: / MVP Email: / Password: Plan / Billing"
- TEXT: "MVPDad_GregH / MVP_GregH@mvp.com / ****** / Family / Annual"
- small button
  - TEXT: "Cancel"
- small button
  - TEXT: "Sign out"

### account 02 — profile sheet, full — `1006:2517`  (440×2216)

- Icon Container
  - TEXT: "G"
- TEXT: "YOUR KIDS"
- Card Container
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Benjamin"
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Lily"
- <coach>
- Layer_1
- TEXT: "COACH  •  This morning"
- TEXT: "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."
- small button
  - TEXT: "Try this with Ben"
- For You
  - Title Container
    - <For You Icon>
    - TEXT: "FOR YOU"
  - Articles Container
    - Article
      - TEXT: "Care · 2 min"
      - Article Content
        - TEXT: "When bedtime becomes a negotiation"
        - TEXT: "What to do when the third glass of water isn't about water"
    - Article
      - TEXT: "This week"
      - TEXT: "Tips on surviving the day"
      - TEXT: "The big birthday parting is coming in 3 days"
      - Action Container
        - small button
          - TEXT: "See all"
- Section Title
  - <Section Icon>
  - TEXT: "COMING UP"
- Card Container
  - Card
    - TEXT: "Soccer camp starts on Friday"
    - TEXT: "Get Ben ready! Camp begins on Aug 8, 7am."
  - Card
    - TEXT: "Lily and Ben birthday outing"
    - TEXT: "Going to the zoo with the kids. Aug 4, 2pm."
    - Card
      - small button
        - TEXT: "See all"
- [Tab Bar]
- <profile>
- <Vector>
- TEXT: "Hi Greg!"
- TEXT: "Browse your recent activity"
- small button
  - <favorites>
  - TEXT: "Saved"
- small button
  - <history>
  - TEXT: "History"
- Article
  - <Vector>
  - TEXT: "Care · 2 min"
  - <favorites>
  - TEXT: "When bedtime becomes a negotiation"
  - TEXT: "What to do when the third glass of water isn't about water"
- Article
  - <Vector>
  - TEXT: "Adventure · 5 min"
  - <favorites>
  - TEXT: "How to plan the perfect nature outing"
  - TEXT: "What to do when the third glass of water isn't about water"
- Article
  - <Vector>
  - TEXT: "Swim camp · Aug. 2, 2026"
  - <favorites>
  - TEXT: "Summer Swim camp 2026"
  - TEXT: "Camp is only one month away - are the kids ready?"
- Article
  - <camp>
  - TEXT: "Summer camps · 5 min"
  - <favorites>
  - TEXT: "The best camps near you"
  - TEXT: "A list of the the best camps for your family"
- TEXT: "Family interests"
- TEXT: "See all"
- <brush>
- TEXT: "Arts & crafts"
- <addcircle>
- <library>
- TEXT: "Museums"
- <hike>
- TEXT: "Hiking"
- <addcircle>
- <garden>
- TEXT: "Gardens"
- <nature>
- TEXT: "Nature"
- <park>
- TEXT: "Parks"
- <robot>
- TEXT: "Science"
- <addcircle>
- <swimming>
- TEXT: "Nature"
- <rocket>
- TEXT: "Parks"
- TEXT: "Account"
- TEXT: "Username: / MVP Email: / Password: Plan / Billing"
- TEXT: "MVPDad_GregH / MVP_GregH@mvp.com / ****** / Family / Annual"
- small button
  - TEXT: "Cancel"
- small button
  - TEXT: "Sign out"

### account 03 — profile sheet, variant 3 — `1008:5111`  (440×2216)

- Icon Container
  - TEXT: "G"
- TEXT: "YOUR KIDS"
- Card Container
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Benjamin"
  - Kid Card
    - Kid Image
      - Kid Card Divider
        - <Kid Card Settings>
      - TEXT: "Lily"
- <coach>
- Layer_1
- TEXT: "COACH  •  This morning"
- TEXT: "Ben's been practicing taking turns. Tonight, try trading who picks the bedtime book — small wins build the muscle."
- small button
  - TEXT: "Try this with Ben"
- For You
  - Title Container
    - <For You Icon>
    - TEXT: "FOR YOU"
  - Articles Container
    - Article
      - TEXT: "Care · 2 min"
      - Article Content
        - TEXT: "When bedtime becomes a negotiation"
        - TEXT: "What to do when the third glass of water isn't about water"
    - Article
      - TEXT: "This week"
      - TEXT: "Tips on surviving the day"
      - TEXT: "The big birthday parting is coming in 3 days"
      - Action Container
        - small button
          - TEXT: "See all"
- Section Title
  - <Section Icon>
  - TEXT: "COMING UP"
- Card Container
  - Card
    - TEXT: "Soccer camp starts on Friday"
    - TEXT: "Get Ben ready! Camp begins on Aug 8, 7am."
  - Card
    - TEXT: "Lily and Ben birthday outing"
    - TEXT: "Going to the zoo with the kids. Aug 4, 2pm."
    - Card
      - small button
        - TEXT: "See all"
- [Tab Bar]
- <profile>
- <Vector>
- TEXT: "Hi Greg!"
- TEXT: "Browse your recent activity"
- small button
  - <favorites>
  - TEXT: "Saved"
- small button
  - <history>
  - TEXT: "History"
- TEXT: "In your Circle"
- TEXT: "Go to Circle"
- <menu - dots>
- dots
- TEXT: "Gifts for the party this weekend"
- TEXT: "M started this — 4 replies"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 2
  - TEXT: "S"
- directions_run_FILL0_wght400_GRAD0_opsz48 3
  - TEXT: "M"
- <menu - dots>
- dots
- TEXT: "Gifts for the party this weekend"
- TEXT: "M started this — 4 replies"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 2
  - TEXT: "S"
- directions_run_FILL0_wght400_GRAD0_opsz48 3
  - TEXT: "M"
- <menu - dots>
- dots
- TEXT: "Gifts for the party this weekend"
- TEXT: "M started this — 4 replies"
- directions_run_FILL0_wght400_GRAD0_opsz48 1
  - TEXT: "G"
- directions_run_FILL0_wght400_GRAD0_opsz48 2
  - TEXT: "S"
- directions_run_FILL0_wght400_GRAD0_opsz48 3
  - TEXT: "M"
- TEXT: "Coach advice"
- TEXT: "Chat with the coach"
- <menu - dots>
- dots
- TEXT: "Dinner plans for the kids"
- TEXT: "sheet-pan tacos worked for both kids — saved for next week"
- Frame
  - <favorites>
- <menu - dots>
- dots
- TEXT: "Kelsy's birthday party"
- TEXT: "Gift ideas for 5-year old girls"
- TEXT: "Family interests"
- TEXT: "See all"
- <brush>
- TEXT: "Arts & crafts"
- <addcircle>
- <library>
- TEXT: "Museums"
- <hike>
- TEXT: "Hiking"
- <addcircle>
- <garden>
- TEXT: "Gardens"
- <nature>
- TEXT: "Nature"
- <park>
- TEXT: "Parks"
- <robot>
- TEXT: "Science"
- <addcircle>
- <swimming>
- TEXT: "Nature"
- <rocket>
- TEXT: "Parks"
- TEXT: "Account"
- TEXT: "Username: / MVP Email: / Password: Plan / Billing"
- TEXT: "MVPDad_GregH / MVP_GregH@mvp.com / ****** / Family / Annual"
- small button
  - TEXT: "Cancel"
- small button
  - TEXT: "Sign out"

---

## Sprint-1 gap — For You per-card feedback (floating annotation by Dashboard 2)

- TEXT: "What we chose for you this week..."  `907:3089`
- TEXT: "Show more like this"  `907:3081`
- TEXT: "Don’t show me this"  `907:3082`
