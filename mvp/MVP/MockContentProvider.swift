import Foundation

// MARK: - Models

struct ContentCategory: Identifiable {
    let id: String
    let name: String
    let emoji: String
}

struct CommunityPost: Identifiable, Hashable {
    let id: String
    let initials: String
    let name: String
    let title: String
    let preview: String
    let category: String
}

struct LibraryItem: Identifiable, Hashable {
    let id: String
    let emoji: String
    let title: String
    let subtitle: String
    let category: String
}

// MARK: - Content Library

enum MockContentProvider {

    // MARK: Categories

    static let categories: [ContentCategory] = [
        ContentCategory(id: "emotional-wellness", name: "Emotional Wellness", emoji: "🧠"),
        ContentCategory(id: "family-dynamics", name: "Family Dynamics", emoji: "👨‍👩‍👧‍👦"),
        ContentCategory(id: "health-nutrition", name: "Health & Nutrition", emoji: "🥗"),
        ContentCategory(id: "daily-routines", name: "Daily Routines", emoji: "⏰"),
        ContentCategory(id: "childcare-village", name: "Childcare & Village", emoji: "🏘️"),
        ContentCategory(id: "education-growth", name: "Education & Growth", emoji: "📖"),
        ContentCategory(id: "social-skills", name: "Social Skills", emoji: "🤝"),
        ContentCategory(id: "adventures-play", name: "Adventures & Play", emoji: "🌲"),
        ContentCategory(id: "style-gear", name: "Style & Gear", emoji: "👟"),
        ContentCategory(id: "parental-growth", name: "Parental Growth", emoji: "🌱"),
    ]

    // MARK: Community Posts

    static let communityPosts: [CommunityPost] = [
        // Family Dynamics
        CommunityPost(id: "cp-annie-holidays", initials: "AQ", name: "Annie Q", title: "First holidays divorced",
                       preview: "Hey there — this is my first holiday season divorced. Any tips for making it feel okay for the kids when they're splitting time?",
                       category: "family-dynamics"),
        CommunityPost(id: "cp-lynsey-meltdowns", initials: "LP", name: "Lynsey Park", title: "Managing meltdowns when Dad's away",
                       preview: "My husband is gone on a work trip, and I'm solo with 3 kids under 7. Bedtime has been a disaster. What's your survival-mode routine?",
                       category: "family-dynamics"),
        CommunityPost(id: "cp-james-newbaby", initials: "JT", name: "James T", title: "Sibling rivalry after new baby",
                       preview: "Our oldest (4) has been acting out since we brought the baby home — hitting, regressing on potty training, saying 'take the baby back.'",
                       category: "family-dynamics"),
        CommunityPost(id: "cp-david-single-dad", initials: "DM", name: "David M", title: "Single dad doing hair — help!",
                       preview: "My daughter's mom isn't in the picture and I have NO idea how to do her hair. Every morning is tears. What products and styles are easiest?",
                       category: "family-dynamics"),
        CommunityPost(id: "cp-nina-marriage", initials: "NP", name: "Nina P", title: "Kids killed our marriage",
                       preview: "We love our kids. We're great co-parents. But we're basically roommates now. No intimacy, no real conversation beyond logistics.",
                       category: "family-dynamics"),

        // Emotional Wellness
        CommunityPost(id: "cp-sarah-perimenopause", initials: "SK", name: "Sarah K", title: "Perimenopause rage + parenting",
                       preview: "I never used to yell. Now I snap at my kids over nothing and then cry in the bathroom. I'm 43 and my doctor says it's hormonal. Anyone else?",
                       category: "emotional-wellness"),
        CommunityPost(id: "cp-emma-triggers", initials: "EH", name: "Emma H", title: "I parent exactly like my mother",
                       preview: "I swore I'd never be like her. But when I'm stressed, I hear her words coming out of my mouth — the criticism, the guilt trips.",
                       category: "emotional-wellness"),
        CommunityPost(id: "cp-mike-midlife", initials: "MK", name: "Mike K", title: "Dad's midlife identity crisis",
                       preview: "I'm 41, two amazing kids, a good job... and I feel completely lost. Like I built someone else's life. Anyone else going through this?",
                       category: "emotional-wellness"),

        // Daily Routines
        CommunityPost(id: "cp-maria-daycare", initials: "MR", name: "Maria R", title: "Toddler won't let go at daycare",
                       preview: "Every morning is a battle. My 3-year-old clings to me and cries when I try to leave. I've tried everything. I'm starting to dread drop-off.",
                       category: "daily-routines"),
        CommunityPost(id: "cp-rachel-sleep", initials: "RB", name: "Rachel B", title: "4-year-old won't stay in bed",
                       preview: "We switched to a toddler bed 3 months ago and every night she's up 10-15 times. I've tried everything gentle. Is sleep training at 4 a thing?",
                       category: "daily-routines"),
        CommunityPost(id: "cp-tom-screen-time", initials: "TL", name: "Tom L", title: "Screen time guilt is eating me alive",
                       preview: "I work from home and my 5-year-old gets way more tablet time than I'd like. The guilt is constant but I literally can't be in two places.",
                       category: "daily-routines"),
        CommunityPost(id: "cp-sam-separation", initials: "SJ", name: "Sam J", title: "Post-holiday separation tears",
                       preview: "After winter break, my kindergartener is back to clinging and crying at drop-off like it's September again. How long does re-adjustment take?",
                       category: "daily-routines"),

        // Health & Nutrition
        CommunityPost(id: "cp-priya-picky", initials: "PS", name: "Priya S", title: "My kid only eats 5 foods",
                       preview: "Pasta, chicken nuggets, plain rice, bananas, and goldfish crackers. That's it. She's 6. Has anyone expanded a picky eater's range?",
                       category: "health-nutrition"),

        // Childcare & Village
        CommunityPost(id: "cp-michelle-nanny", initials: "MW", name: "Michelle W", title: "How much should I pay my nanny?",
                       preview: "We're in a MCOL area and I keep getting wildly different numbers. $18/hr? $25/hr? Does it change for 2 kids vs 1? I want to be fair.",
                       category: "childcare-village"),
        CommunityPost(id: "cp-lisa-village", initials: "LT", name: "Lisa T", title: "Moved to new city — no village",
                       preview: "We relocated for my husband's job and I know literally no one. I have a 2-year-old and a newborn. How did you build your village from scratch?",
                       category: "childcare-village"),

        // Education & Growth
        CommunityPost(id: "cp-carlos-school", initials: "CG", name: "Carlos G", title: "Public vs. private school anxiety",
                       preview: "We can technically afford private school but it would be tight. Our public school is 'okay' rated. For those who chose — do you regret it?",
                       category: "education-growth"),
        CommunityPost(id: "cp-alex-adhd", initials: "AT", name: "Alex T", title: "Navigating school with an ADHD kid",
                       preview: "My son just got diagnosed at 8 and suddenly everything makes sense. But the school seems clueless. Do I push for a 504 or an IEP?",
                       category: "education-growth"),

        // Social Skills
        CommunityPost(id: "cp-jason-bullying", initials: "JR", name: "Jason R", title: "My 7-year-old is being excluded",
                       preview: "He comes home saying 'nobody wants to play with me' and it's gutting. Teacher says he's fine in class but recess is a different story.",
                       category: "social-skills"),

        // Adventures & Play
        CommunityPost(id: "cp-amanda-travel", initials: "AF", name: "Amanda F", title: "Flying solo with a toddler — tips?",
                       preview: "I have a 5-hour flight next month with my 2-year-old. No other adult. What snacks, toys, and strategies got you through a long flight?",
                       category: "adventures-play"),

        // Style & Gear
        CommunityPost(id: "cp-jen-upcycle", initials: "JD", name: "Jen D", title: "Best consignment apps for kids' clothes?",
                       preview: "My kids grow out of everything in 2 months and I'm done buying new. What apps or local swaps do you use?",
                       category: "style-gear"),
    ]

    // MARK: Library Items

    static let libraryItems: [LibraryItem] = [
        // Emotional Wellness
        LibraryItem(id: "ew-shadow-triggers", emoji: "🪞", title: "Your Trigger Is Your Teacher", subtitle: "Shadow Work for the Everyday Parent", category: "emotional-wellness"),
        LibraryItem(id: "ew-perimenopause-parenting", emoji: "🔥", title: "Parenting Through Perimenopause", subtitle: "When Your Body Rewrites the Rules", category: "emotional-wellness"),
        LibraryItem(id: "ew-midlife-identity", emoji: "🦋", title: "The Midlife Unraveling", subtitle: "Finding Yourself Again Inside the Parent Role", category: "emotional-wellness"),
        LibraryItem(id: "ew-anxiety-spiral", emoji: "🌀", title: "Breaking the Anxiety Spiral", subtitle: "When Your Worry Becomes Their Worry", category: "emotional-wellness"),
        LibraryItem(id: "ew-rage-repair", emoji: "💔", title: "After You've Lost It", subtitle: "The Repair Playbook for Parental Rage", category: "emotional-wellness"),

        // Family Dynamics
        LibraryItem(id: "fd-sibling-rivalry", emoji: "⚡", title: "The Sibling Rivalry Reset", subtitle: "Why 'Be Nice to Your Sister' Never Works", category: "family-dynamics"),
        LibraryItem(id: "fd-divorce-kids", emoji: "🏠", title: "Two Homes, One Heart", subtitle: "Helping Kids Thrive After Separation", category: "family-dynamics"),
        LibraryItem(id: "fd-single-parent", emoji: "💪", title: "The Single Parent's Superpower", subtitle: "You Are Enough — Here's the Proof", category: "family-dynamics"),
        LibraryItem(id: "fd-marriage-dates", emoji: "❤️", title: "Date Night Is Not Optional", subtitle: "Your Marriage Needs You to Show Up", category: "family-dynamics"),
        LibraryItem(id: "fd-blended-family", emoji: "🧩", title: "Blending Without Breaking", subtitle: "Stepparenting with Grace and Boundaries", category: "family-dynamics"),

        // Health & Nutrition
        LibraryItem(id: "hn-kid-nutrition", emoji: "🥦", title: "The No-Stress Feeding Playbook", subtitle: "Ending the Dinner Table Power Struggle", category: "health-nutrition"),
        LibraryItem(id: "hn-hydration-kids", emoji: "💧", title: "The Hydration Cheat Sheet", subtitle: "How Much Water Kids Actually Need", category: "health-nutrition"),
        LibraryItem(id: "hn-sick-kid-guide", emoji: "🤒", title: "When to Worry, When to Wait", subtitle: "Guide to Common Childhood Illnesses", category: "health-nutrition"),
        LibraryItem(id: "hn-meal-prep-families", emoji: "🍳", title: "30-Minute Family Meals", subtitle: "12 Recipes Kids Will Actually Eat", category: "health-nutrition"),
        LibraryItem(id: "hn-kids-meds-guide", emoji: "💊", title: "The Parents' Medicine Cabinet", subtitle: "Dosing Charts and What You Actually Need", category: "health-nutrition"),

        // Daily Routines
        LibraryItem(id: "dr-sleep-science", emoji: "🌙", title: "The Sleep Reset", subtitle: "Strategies That Don't Involve Crying It Out", category: "daily-routines"),
        LibraryItem(id: "dr-morning-routine", emoji: "☀️", title: "Mornings Without Meltdowns", subtitle: "The System That Gets Everyone Out the Door", category: "daily-routines"),
        LibraryItem(id: "dr-bedtime-battles", emoji: "📖", title: "Bedtime Battles: A Field Guide", subtitle: "When 'One More Story' Becomes a Negotiation", category: "daily-routines"),
        LibraryItem(id: "dr-screen-time", emoji: "📱", title: "The Screen Time Truce", subtitle: "Realistic Limits That Don't Start a War", category: "daily-routines"),
        LibraryItem(id: "dr-schedules-autonomy", emoji: "📋", title: "Structure That Feels Like Freedom", subtitle: "Building Schedules Kids Actually Follow", category: "daily-routines"),

        // Childcare & Village
        LibraryItem(id: "cv-finding-nanny", emoji: "👶", title: "Finding Your Right-Fit Nanny", subtitle: "Interview Questions, Red Flags, Fair Pay", category: "childcare-village"),
        LibraryItem(id: "cv-babysitter-prep", emoji: "📝", title: "The Babysitter Briefing Sheet", subtitle: "Everything They Need on One Page", category: "childcare-village"),
        LibraryItem(id: "cv-playdate-survival", emoji: "🎈", title: "The Play Date Playbook", subtitle: "Hosting, Boundaries, and When to Intervene", category: "childcare-village"),
        LibraryItem(id: "cv-building-village", emoji: "🏘️", title: "It Takes a Village", subtitle: "Creating Support in the Age of Isolation", category: "childcare-village"),
        LibraryItem(id: "cv-livein-nanny", emoji: "🏡", title: "Live-In vs. Live-Out", subtitle: "Making the Childcare Decision That Fits", category: "childcare-village"),

        // Education & Growth
        LibraryItem(id: "eg-school-choice", emoji: "🏫", title: "Public vs. Private", subtitle: "The School Choice Decision Framework", category: "education-growth"),
        LibraryItem(id: "eg-first-time-parents", emoji: "🍼", title: "The First-Time Parent Survival Kit", subtitle: "What Nobody Tells You But Everyone Should", category: "education-growth"),
        LibraryItem(id: "eg-clubs-activities", emoji: "⚽", title: "The Overscheduling Trap", subtitle: "How Many Activities Is Too Many?", category: "education-growth"),
        LibraryItem(id: "eg-crafts-connection", emoji: "🎨", title: "Crafts as Connection", subtitle: "15 Low-Mess Projects That Build More Than Art", category: "education-growth"),

        // Adventures & Play
        LibraryItem(id: "ap-nature-reset", emoji: "🌲", title: "The 20-Minute Nature Reset", subtitle: "Why Outside Time Is the Best Medicine", category: "adventures-play"),
        LibraryItem(id: "ap-travel-kids", emoji: "✈️", title: "Traveling With Kids", subtitle: "Packing Lists, Plane Strategies, Expectations", category: "adventures-play"),
        LibraryItem(id: "ap-music-development", emoji: "🎵", title: "Why Music Matters", subtitle: "Neuroscience of Rhythm, Bonding, and Regulation", category: "adventures-play"),
        LibraryItem(id: "ap-weekend-outings", emoji: "🗺️", title: "50 Weekend Outings Under $20", subtitle: "Adventure Doesn't Require a Budget", category: "adventures-play"),

        // Style & Gear
        LibraryItem(id: "sg-kids-clothes", emoji: "👗", title: "Dressing Kids Without the Drama", subtitle: "Autonomy, Weather, and Letting Go", category: "style-gear"),
        LibraryItem(id: "sg-upcycled-kids", emoji: "♻️", title: "The Upcycled Kids' Wardrobe", subtitle: "Sustainable Style on a Real-Life Budget", category: "style-gear"),
        LibraryItem(id: "sg-car-safety", emoji: "🚗", title: "Car Seat Safety", subtitle: "What You're Probably Getting Wrong", category: "style-gear"),
        LibraryItem(id: "sg-shoes-kids", emoji: "👟", title: "Kids' Shoes That Actually Last", subtitle: "A Podiatrist-Approved Buying Guide", category: "style-gear"),

        // Social Skills
        LibraryItem(id: "ss-bullying-scripts", emoji: "🛡️", title: "When Your Kid Is Being Bullied", subtitle: "Scripts for Them, Scripts for You", category: "social-skills"),
        LibraryItem(id: "ss-etiquette-modern", emoji: "🎩", title: "Modern Manners for Little Humans", subtitle: "Teaching Etiquette Without Shaming", category: "social-skills"),
        LibraryItem(id: "ss-friendship-skills", emoji: "🌟", title: "Helping the Shy Kid Make Friends", subtitle: "Connection Without Forcing It", category: "social-skills"),
        LibraryItem(id: "ss-relationship-modeling", emoji: "👀", title: "They're Watching How You Fight", subtitle: "Modeling Healthy Conflict for Kids", category: "social-skills"),

        // Parental Growth
        LibraryItem(id: "pg-parental-longevity", emoji: "🏃", title: "Parenting Is a Long Game", subtitle: "Investing in Your Health for All of It", category: "parental-growth"),
        LibraryItem(id: "pg-advocacy", emoji: "📢", title: "Becoming Your Child's Best Advocate", subtitle: "Navigating Schools, Doctors, and Systems", category: "parental-growth"),
        LibraryItem(id: "pg-best-resources", emoji: "📚", title: "The MVP Resource Guide", subtitle: "Curated Blogs, Books, and Accounts", category: "parental-growth"),
        LibraryItem(id: "pg-inner-child", emoji: "🔑", title: "Reparenting Your Inner Child", subtitle: "Breaking Generational Patterns", category: "parental-growth"),
    ]

    /// Returns a random subset of community posts (2 items).
    static func randomCommunityPosts() -> [CommunityPost] {
        Array(communityPosts.shuffled().prefix(2))
    }

    /// Returns a random subset of library items (3 items).
    static func randomLibraryItems() -> [LibraryItem] {
        Array(libraryItems.shuffled().prefix(3))
    }

    /// Returns library items filtered by category.
    static func libraryItems(for category: String) -> [LibraryItem] {
        libraryItems.filter { $0.category == category }
    }

    /// Returns community posts filtered by category.
    static func communityPosts(for category: String) -> [CommunityPost] {
        communityPosts.filter { $0.category == category }
    }

    /// Returns a featured library item (first one from emotional-wellness).
    static var featuredItem: LibraryItem {
        libraryItems.first { $0.category == "emotional-wellness" }!
    }
}
