# =============================================================================
# AI News Aggregator — Configuration
# =============================================================================

TIMEZONE_OFFSET = -6  # Costa Rica (UTC-6)

# ---------------------------------------------------------------------------
# LLM Classification
# ---------------------------------------------------------------------------
LLM_CLASSIFY = True  # Use Claude Haiku for classification (keywords as fallback)
LLM_MODEL = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# RSS Feed Sources
# ---------------------------------------------------------------------------

FEEDS = {
    # --- Tier 0: Official Company Blogs (straight from the source) ---
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Google Research": "https://research.google/blog/rss/",
    "NVIDIA Blog": "https://blogs.nvidia.com/feed/",
    "Meta Research": "https://research.facebook.com/feed/",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/feed/",
    "Apple ML Research": "https://machinelearning.apple.com/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Stability AI": "https://stability.ai/news/rss.xml",
    "Databricks": "https://www.databricks.com/feed",
    "Palantir": "https://blog.palantir.com/feed",
    "Shield AI": "https://shield.ai/feed/",

    # --- Tier 1: AI-Focused News Sites (always relevant) ---
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "The Register AI": "https://www.theregister.com/software/ai_ml/headlines.atom",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "AI News": "https://www.artificialintelligence-news.com/feed/",
    "InfoQ AI/ML": "https://feed.infoq.com/ai-ml-data-eng/",
    "The Decoder": "https://the-decoder.com/feed/",
    "Futurism AI": "https://futurism.com/categories/ai-artificial-intelligence/feed",
    "ZDNet AI": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "Import AI": "https://importai.substack.com/feed",
    "The Gradient": "https://thegradient.pub/rss/",

    # --- Tier 1.5: AI Leaders & Influential Newsletters ---
    "Sam Altman": "https://blog.samaltman.com/posts.atom",
    "Andrej Karpathy": "https://karpathy.bearblog.dev/feed/",
    "One Useful Thing": "https://www.oneusefulthing.org/feed",
    "Interconnects": "https://www.interconnects.ai/feed",
    "Ahead of AI": "https://magazine.sebastianraschka.com/feed",
    "Exponential View": "https://www.exponentialview.co/feed",
    "Benedict Evans": "https://www.ben-evans.com/benedictevans?format=rss",
    "Simon Willison": "https://simonwillison.net/atom/everything/",

    # --- Tier 1.6: Universities & Research Labs ---
    "MIT News AI": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
    "BAIR Blog": "https://bair.berkeley.edu/blog/feed.xml",
    "CMU SCS": "https://www.cs.cmu.edu/news/feed",
    "Oxford Internet Institute": "https://www.oii.ox.ac.uk/feed/",
    "UW Allen School": "https://news.cs.washington.edu/feed/",
    "Cambridge CST": "https://www.cst.cam.ac.uk/news/feed",
    "Vector Institute": "https://vectorinstitute.ai/feed/",

    # --- Tier 1.7: Scientific Journals & Media ---
    "Nature": "https://www.nature.com/nature.rss",
    "Nature Machine Intelligence": "https://www.nature.com/natmachintell.rss",
    "Science": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "Scientific American": "http://rss.sciam.com/ScientificAmerican-Global",
    "New Scientist": "https://www.newscientist.com/feed/home/",
    "IEEE Spectrum": "https://spectrum.ieee.org/feeds/feed.rss",

    # --- Tier 1.8: Defense & Consulting ---
    "McKinsey": "https://www.mckinsey.com/insights/rss.aspx",
    "Lockheed Martin": "https://news.lockheedmartin.com/news-releases?pagetemplate=rss",
    "Northrop Grumman": "https://investor.northropgrumman.com/rss/news-releases.xml",
    "RTX": "https://www.rtx.com/rss-feeds/news",
    "L3Harris": "https://www.l3harris.com/feeds/newsroom/rss.xml",
    "Leidos": "https://investors.leidos.com/rss/news-releases.xml",
    "SAIC": "https://investors.saic.com/rss/news-releases.xml",
    "Boeing": "https://boeing.mediaroom.com/news-releases-statements?pagetemplate=rss",

    # --- Tier 2: Traditional Media & Finance (filtered for AI keywords) ---
    "Axios": "https://api.axios.com/feed/",
    "NYT Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "WSJ Tech": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
    "BBC Tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "CNN Tech": "http://rss.cnn.com/rss/money_technology.rss",
    "Washington Post": "https://feeds.washingtonpost.com/rss/business/technology",
    "Financial Times": "https://www.ft.com/technology?format=rss",
    "Guardian Tech": "https://www.theguardian.com/technology/rss",
    "Fortune": "https://fortune.com/feed/fortune-feeds/?id=3230629",
    "Bloomberg Tech": "https://feeds.bloomberg.com/technology/news.rss",
    "CNBC Tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",

    # --- Tier 3: Community & Aggregators ---
    "Hacker News AI": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+Anthropic&points=10",
    "Google News AI": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    "Google News Vibe Coding": "https://news.google.com/rss/search?q=%22vibe+coding%22+OR+%22vibecoding%22+OR+%22generative+coding%22&hl=en-US&gl=US&ceid=US:en",
    "Google News Anthropic": "https://news.google.com/rss/search?q=Anthropic+OR+%22Claude+AI%22+OR+%22Claude+Code%22&hl=en-US&gl=US&ceid=US:en",
    "Google News OpenAI": "https://news.google.com/rss/search?q=OpenAI+OR+ChatGPT+OR+%22GPT-5%22&hl=en-US&gl=US&ceid=US:en",
}

# Sources that require AI keyword match in title to be included
# (they publish lots of non-AI content)
TIER2_SOURCES = {
    # Traditional media
    "Axios", "NYT Tech", "WSJ Tech", "BBC Tech", "CNN Tech",
    "Washington Post", "Financial Times",
    "Guardian Tech", "Fortune",
    "Bloomberg Tech", "CNBC Tech",
    # Mixed-content tech sites
    "Meta Research", "ZDNet AI", "MIT Tech Review", "Ars Technica",
    "Google Research", "Apple ML Research", "Databricks",
    # Defense & consulting (publish mostly non-AI)
    "McKinsey", "Palantir", "Shield AI",
    "Lockheed Martin", "Northrop Grumman", "RTX", "L3Harris",
    "Leidos", "SAIC", "Boeing",
    # Scientific journals (broad science, filter for AI)
    "Nature", "Science", "Scientific American", "New Scientist",
    "IEEE Spectrum",
    # Universities (general CS/dept news)
    "MIT News AI", "CMU SCS", "Oxford Internet Institute",
    "UW Allen School", "Cambridge CST", "Vector Institute",
    # Community
    "Hacker News AI", "Google News AI", "Google News Vibe Coding",
}

# Keywords for Tier 2 filtering. These must match as whole words (word boundaries).
# Kept specific to avoid pulling in generic tech articles that mention "AI" in passing.
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "llama",
    "neural network", "chatbot", "openai", "anthropic", "deepmind",
    "copilot", "grok", "generative ai", "diffusion model", "agi",
    "superintelligence", "reinforcement learning", "computer vision",
    "natural language processing", "nlp", "ai model", "ai agent",
    "ai tool", "ai safety", "ai regulation", "ai chip",
    "vibe coding", "vibecoding", "generative coding",
    "autonomous", "robotics", "robot", "drone",
    "data science", "predictive model", "transformer",
]

# ---------------------------------------------------------------------------
# Topic Categories — Ordered from most actionable to most background
# ---------------------------------------------------------------------------
#
# CLASSIFICATION RULES:
#   - Each headline is scored against every category
#   - strong keyword match = +3, weak = +1, exclude = -5
#   - Highest score wins; ties go to the earlier (more relevant) category
#   - Score of 0 = "Industry" catch-all
#
# DUPLICATE HANDLING:
#   - URL-based dedup removes exact duplicates
#   - Title similarity dedup catches the same story from multiple outlets
#     (e.g., 5 outlets covering the same Anthropic funding round)
#   - When duplicates are found, the earliest published one is kept
#
# ---------------------------------------------------------------------------

CATEGORIES = [
    # -----------------------------------------------------------------
    # 1. RELEASES — Something concrete shipped today
    # -----------------------------------------------------------------
    # DEFINITION: A company or project has made something new publicly
    # available. This is a concrete announcement: a new model, a new
    # product version, a new API, a new open-source release.
    #
    # IS a release: "OpenAI releases GPT-5", "Anthropic launches Claude 4",
    #   "Meta open-sources Llama 4", "New version of TensorFlow available"
    # NOT a release: "OpenAI reportedly working on GPT-5" (→ Rumors),
    #   "GPT-5 benchmarks show improvement" (→ Research)
    # -----------------------------------------------------------------
    {
        "name": "Releases",
        "description": "A company shipped something new today — a new model, product version, API, or open-source release. NOT policy papers, press releases, or reports.",
        "strong": [
            "releases new", "released new", "releasing new", "now available",
            "rolling out", "rolls out", "generally available", "general availability",
            "ga release", "public beta",
            "early access", "ships new", "shipped new",
            "introduces new", "introducing new", "debuts new",
            "we're excited to", "is now open source", "open-sources",
            "new version of", "v2 ", "v3 ", "v4 ", "v5 ",
            "just released", "just launched", "announces new",
            "unveils new", "reveals new",
            "now supports", "adds support", "new capability", "new capabilities",
            "stable release", "production ready", "production-ready",
        ],
        "weak": [
            "release", "released", "deploy", "open source", "open-source",
            "unveiled", "reveals", "introduces",
            "new mode", "new feature", "adds new",
        ],
        "exclude": [
            "rumor", "reportedly", "expected to", "could soon",
            "leak", "may release", "planning to", "accus", "stock",
            "billion", "million", "lawsuit",
            "nuke", "missile", "weapon", "combat", "military",
            "simulated", "war game",
        ],
    },

    # -----------------------------------------------------------------
    # 2. PEOPLE — Key personnel moves across AI
    # -----------------------------------------------------------------
    # DEFINITION: Individual people joining, leaving, or moving between
    # AI companies and ventures. Leadership changes, high-profile hires,
    # departures, founders starting new companies.
    #
    # IS people: "Amazon's AGI lab leader is leaving",
    #   "Former OpenAI researcher joins Anthropic",
    #   "Dario Amodei steps down as CEO"
    # NOT people: "Google lays off 500 AI engineers" (→ Business),
    #   "EU summons tech CEOs" (→ Policy)
    # -----------------------------------------------------------------
    {
        "name": "People",
        "description": "Key personnel joining, leaving, or moving between AI companies. Leadership changes, high-profile hires, departures, founders starting new ventures.",
        "strong": [
            # Departures
            "leaves", "leaving", "departs", "departure", "departing",
            "steps down", "stepping down", "step down",
            "resigns", "resigned", "resignation",
            "exits company", "exiting",
            "fired", "ousted", "let go",
            # Arrivals
            "joins", "joining", "joined",
            "appointed", "appointment",
            "named ceo", "named cto", "named chief",
            "new ceo", "new cto", "new chief",
            "taps ", "tapped to lead", "tapped as",
            "hires", "hired",
            # Transitions
            "replaces", "succeeds", "successor",
            "promoted to", "promotion",
            "poached", "recruited from",
            "starts new venture", "launches startup",
        ],
        "weak": [
            "leader", "leadership change",
            "chief", "officer",
            "head of", "director of", "vp of",
            "executive", "founder", "co-founder", "cofounder",
            "veteran", "pioneer",
            "recruit", "talent war",
        ],
        "exclude": [
            "stock", "billion", "million", "funding", "valuation",
            "layoff", "layoffs", "laid off",
            "regulation", "legislation",
        ],
    },

    # -----------------------------------------------------------------
    # 3. VIBE CODING — Non-coders building software with AI
    # -----------------------------------------------------------------
    # DEFINITION: The practice of describing what you want to an AI
    # and having it generate the code, without necessarily understanding
    # the code yourself. Coined by Andrej Karpathy in 2025. Covers
    # non-programmers building apps, prompt-to-app workflows, the
    # cultural movement, and concerns about code quality/accountability.
    #
    # IS vibe coding: "Vibe coding is changing who can build software",
    #   "Non-programmer builds SaaS app with AI in a weekend",
    #   "Andrej Karpathy on the future of vibe coding"
    # NOT vibe coding: "SWE-bench benchmark results" (→ Research),
    #   "Will AI replace programmers?" (→ Ethics)
    # -----------------------------------------------------------------
    {
        "name": "Vibe Coding",
        "description": "Non-coders building software with AI. The prompt-to-app movement, AI code generation tools, and debates about AI-written code quality.",
        "strong": [
            # Core terms
            "vibe coding", "vibe-coding", "vibecoding", "vibe code",
            "vibe coder", "vibe coded", "generative coding",
            # The movement
            "prompt to app", "prompt-to-app",
            "no-code ai", "no code ai", "low-code ai",
            "build apps without cod", "build app without cod",
            "anyone can build", "everyone can code",
            "ai-generated app", "ai-generated software",
            "natural language programming",
            "non-programmer build", "non-coder build",
            # Platforms & tools specific to vibe coding
            "emergent.sh", "bolt.new",
            "lovable ai", "loveable ai", "coderick",
            "code metal",
            # Consequences & debates
            "ai-generated code", "ai-written code", "ai writes code",
            "killing open source", "technical debt ai",
            "ai code quality", "ai code vulnerab",
        ],
        "weak": [
            "karpathy", "replit", "windsurf", "cursor ai",
            "v0.dev", "lovable", "loveable",
            "built with ai", "built entirely",
            "citizen developer", "democratiz",
            "spec-driven", "ai orchestrat",
            "ai pair program", "ai-pair program",
            "code generation", "ai-assisted cod",
            "machine-written code",
        ],
        "exclude": [
            "stock", "billion", "funding", "valuation",
            "lawsuit", "regulation",
        ],
    },

    # -----------------------------------------------------------------
    # 3. RUMORS & SPECULATION — Not confirmed yet
    # -----------------------------------------------------------------
    # DEFINITION: Leaks, unconfirmed reports, speculation about future
    # products, upcoming announcements. The headline uses explicit
    # hedging language ("reportedly", "sources say", "planning to").
    #
    # NOTE: Generic words like "could", "may", "might" are NOT used
    # as keywords — they appear in all kinds of stories. Only phrases
    # that clearly signal unconfirmed information are matched.
    #
    # IS rumor: "OpenAI reportedly working on GPT-6", "Sources say
    #   Google considering Anthropic bid", "Leaked docs reveal..."
    # NOT rumor: "AI could transform healthcare" (→ that's commentary)
    # -----------------------------------------------------------------
    {
        "name": "Rumors & Speculation",
        "description": "Leaks, unconfirmed reports, and speculation about future products or announcements. Uses hedging language like 'reportedly', 'sources say', 'planning to'.",
        "strong": [
            "rumor", "rumour", "reportedly", "report says",
            "sources say", "according to sources", "leaked",
            "leak suggests", "upcoming", "expected to",
            "planning to", "set to announce", "may soon",
            "could soon", "in talks to", "in the works",
            "under development", "preparing to", "considering",
            "scoop:", "exclusive:",
        ],
        "weak": [
            "plans to", "working on",
            "aims to", "looking to", "exploring",
            "teases", "hints at", "signals",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 4. BUSINESS & MONEY — Follow the money
    # -----------------------------------------------------------------
    # DEFINITION: Funding rounds, valuations, M&A, revenue, earnings,
    # stock price moves, IPOs, hiring/layoffs, data center investments.
    # The financial and corporate side of AI.
    #
    # IS business: "Anthropic raises $5B", "NVIDIA stock hits record",
    #   "OpenAI acquires startup", "Google lays off AI team"
    # NOT business: "Anthropic releases Claude 4" (→ Releases),
    #   "EU regulates AI companies" (→ Policy)
    # -----------------------------------------------------------------
    {
        "name": "Business & Money",
        "description": "Funding rounds, valuations, M&A, revenue, earnings, stock moves, IPOs, hiring/layoffs, data center investments. The financial side of AI.",
        "strong": [
            "funding", "raises", "raised", "valuation", "valued at",
            "billion", "million", "ipo", "acquisition", "acquires",
            "acquired", "revenue", "series a", "series b", "series c",
            "series d", "share sale", "stock", "shares", "earnings",
            "profit", "market cap", "investment", "investor",
            "layoff", "layoffs", "laid off", "data center", "data centre",
            "sinks", "plunges", "tanks", "soars", "surges",
            "economic growth", "gdp", "goldman sachs", "morgan stanley",
            "wall street", "market", "bullish", "bearish",
            "consolidation", "enterprise ai", "consulting firms",
        ],
        "weak": [
            "startup", "venture", "deal", "merger", "partnership",
            "hire", "hiring", "spend", "spending",
            "ceo", "executive", "founder", "enterprise",
            "growth", "economy", "tariff",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 5. POLICY & REGULATION — AI meets government
    # -----------------------------------------------------------------
    {
        "name": "Policy & Regulation",
        "description": "Government regulation, lawsuits, legislation, export controls, antitrust, copyright disputes, and legal battles involving AI.",
        "strong": [
            "regulation", "regulated", "ai act", "executive order",
            "legislation", "compliance", "export control",
            "lawsuit", "sued", "suing", "sues",
            "ban ", "bans ", "banned", "antitrust",
            "congressional", "senate hearing", "eu ai",
            "ai safety bill", "ai governance", "regulators",
            "guardrail", "summon", "subpoena",
            "accus", "theft", "steal", "stolen", "ripping off",
            "harvesting", "scraping data", "data theft",
            "military use", "defense secretary",
            "export ban", "chip ban", "chip export",
        ],
        "weak": [
            "congress", "senate", "copyright",
            "policy", "govern",
            "probe", "investigat", "oversight", "scrutiny",
            "advertising claims", "law review",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 6. SECURITY & PRIVACY — Threats, breaches, and surveillance
    # -----------------------------------------------------------------
    {
        "name": "Security & Privacy",
        "description": "Cybersecurity threats, data breaches, vulnerabilities, prompt injection, jailbreaks, surveillance, and AI safety/security risks.",
        "strong": [
            "hack", "hacker", "hackers", "hacking", "hacked",
            "breach", "breaches", "data breach",
            "vulnerability", "vulnerabilities", "security flaw", "security flaws",
            "exploit", "exploits", "exploited", "zero-day", "0-day",
            "malware", "ransomware", "phishing", "spyware",
            "cybersecurity", "cyber attack", "cyberattack", "cyber threat",
            "remote code execution", "code execution", "code injection",
            "exfiltration", "data leak", "data leaked", "data exposure",
            "attack vector", "attack surface",
            "prompt injection", "jailbreak", "jailbreaking", "jailbroken",
            "security risk", "security concern", "security panic",
            "privacy violation", "privacy breach",
            "surveillance", "spy", "spying", "espionage",
            "credential theft", "credential stuffing", "identity theft",
            "botnet", "ddos", "trojan", "backdoor",
            "infosec", "cybercrime",
            "at risk", "sparks panic",
        ],
        "weak": [
            "security", "privacy", "threat", "threats",
            "protect", "defense", "encryption", "decrypt",
            "authentication", "firewall", "sandbox",
            "data protection", "insecure",
            "pentest", "penetration test", "red team",
            "incident", "compromise", "compromised",
        ],
        "exclude": [
            "stock", "billion", "funding", "valuation",
            "regulation", "legislation",
        ],
    },

    # -----------------------------------------------------------------
    # 7. RESEARCH — From the labs
    # -----------------------------------------------------------------
    {
        "name": "Research",
        "description": "Scientific papers, benchmark results, studies, and technical breakthroughs from labs and universities. NOT product announcements that mention research.",
        "strong": [
            "paper", "arxiv", "preprint", "peer review",
            "study finds", "study shows", "researchers found",
            "researchers demonstrate", "breakthrough",
            "scaling law", "benchmark results", "state-of-the-art",
            "novel approach", "outperforms", "distill",
            "interpretable", "fluency index", "swe-bench",
            "evaluate", "benchmark",
        ],
        "weak": [
            "research", "researchers", "dataset", "training data",
            "alignment", "rlhf", "reinforcement learning",
            "tokeniz", "attention mechanism", "fine-tun",
            "study", "experiment", "findings",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 8. ETHICS & PHILOSOPHY — The big questions
    # -----------------------------------------------------------------
    {
        "name": "Ethics & Philosophy",
        "description": "Existential questions about AI — consciousness, job displacement, bias, fairness, societal impact, responsible AI, and the future of work.",
        "strong": [
            "obsolete", "replace human", "replacing humans",
            "consciousness", "sentient", "sentience", "alive",
            "existential risk", "existential threat", "superintelligence",
            "alignment", "ai rights", "robot rights",
            "bias", "fairness", "discrimination",
            "deepfake ethics", "responsible ai",
            "who decides", "who gets to eat", "what it means",
            "future of work", "end of work", "jobs crisis",
            "human dignity", "human-ai", "pro-worker",
            "harmful", "helpful or harmful",
        ],
        "weak": [
            "ethics", "ethical", "moral", "philosophy",
            "dilemma", "should we", "society", "humanity",
            "displacement", "fear", "worry", "concern",
            "trust", "accountability", "transparency",
            "literacy", "education",
        ],
        "exclude": [
            "regulation", "legislation", "lawsuit", "compliance",
        ],
    },

    # -----------------------------------------------------------------
    # 9. FUN & WEIRD — The lighter side of AI
    # -----------------------------------------------------------------
    {
        "name": "Fun & Weird",
        "description": "The lighter, stranger, or more unexpected side of AI — bizarre use cases, memes, dating, art controversies, school bans, robot fails.",
        "strong": [
            "pope", "church", "priest", "homil",
            "weird", "bizarre", "absurd", "hilarious", "funny",
            "dating", "marry", "marriage", "love",
            "cat ", "cats ", "dog ", "dogs ",
            "meme", "parody", "satire", "prank",
            "art controversy", "deepfake", "onlyfans",
            "homework", "cheat", "school ban",
            "robot dance", "robot fail",
            "fumes", "rant", "wooden box into space",
        ],
        "weak": [
            "strange", "unusual", "surprising", "unexpected",
            "creative", "wild", "crazy",
            "hidden", "vanished", "quietly",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 10. OTHER — Catch-all for uncategorized AI news
    # -----------------------------------------------------------------
    {
        "name": "Other",
        "description": "AI news that doesn't fit neatly into the above categories. General industry commentary, analysis, trends, and miscellaneous AI content.",
        "strong": [],
        "weak": [],
        "exclude": [],
    },
]

# Headlines that don't score in any category go to Other.
DEFAULT_CATEGORY = "Other"

# Minimum score required for classification. Articles scoring below this
# are treated as unclassifiable and dropped. Prevents weak description-only
# matches (0.5) from pulling irrelevant articles into categories.
# A score of 1.0 requires at least a weak keyword in the title, OR a strong
# keyword in the description, OR two weak keywords in the description.
MIN_CLASSIFICATION_SCORE = 1.0

# Maximum items per category — keeps the feed focused on the best stories.
# Ranked by: multi-source coverage first, then source tier, then recency.
MAX_ITEMS_PER_CATEGORY = 12

# ---------------------------------------------------------------------------
# Top News — Editorially promoted stories
# ---------------------------------------------------------------------------
# Stories that are breaking or viral (3+ sources covering the same story)
# are promoted to a "Top News" section that appears BEFORE all categories.
# These stories are REMOVED from their original category to avoid duplication.
TOP_NEWS_COVERAGE_THRESHOLD = 3  # min _also_covered_by count to qualify
TOP_NEWS_MAX_ITEMS = 10

# ---------------------------------------------------------------------------
# Breaking News Detection
# ---------------------------------------------------------------------------
# Headlines matching these signals are marked as "breaking" and shown bold.
# A headline is breaking if it scores >= 2 points from these signals.
#
# Signals:
#   - Multiple outlets covering the same story (dedup cluster size >= 3)
#   - Source is a major Tier 0 company blog (official announcements)
#   - Title contains breaking-news language
# ---------------------------------------------------------------------------

BREAKING_TITLE_SIGNALS = [
    "breaking:", "breaking news", "just announced", "just released",
    "exclusive:", "first look:", "officially",
]

# ---------------------------------------------------------------------------
# Company Tags
# ---------------------------------------------------------------------------

COMPANIES = {
    "anthropic": ["anthropic", "claude"],
    "openai": ["openai", "chatgpt", "gpt-4", "gpt-5", "dall-e", "sam altman"],
    "google": ["google", "deepmind", "gemini", "bard"],
    "meta": ["meta ai", "llama", "meta research", "zuckerberg"],
    "microsoft": ["microsoft", "copilot", "bing ai", "azure ai", "satya nadella"],
    "apple": ["apple intelligence", "apple ai", "apple machine learning"],
    "amazon": ["amazon ai", "aws ai", "bedrock", "alexa ai", "amazon sagemaker"],
    "nvidia": ["nvidia", "jensen huang", "cuda", "tensorrt"],
    "deepseek": ["deepseek"],
    "perplexity": ["perplexity"],
    "mistral": ["mistral"],
    "xai": ["xai", "grok"],
    "cohere": ["cohere"],
    "stability": ["stability ai", "stable diffusion"],
    "huggingface": ["hugging face", "huggingface"],
    "ibm": ["ibm", "watson"],
    "samsung": ["samsung ai", "samsung galaxy ai"],
    "baidu": ["baidu", "ernie bot"],
    "alibaba": ["alibaba", "qwen", "tongyi"],
}

# NOTE: Review and update COMPANIES list monthly as the AI landscape shifts.
# Last updated: 2026-02-23

# ---------------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------------
# Similarity threshold for title-based dedup (0.0 to 1.0).
# Headlines with similarity above this are considered duplicates.
# When duplicates are found, the one from the higher-tier source is kept.
DEDUP_SIMILARITY_THRESHOLD = 0.35

# Known entities for entity-aware dedup. If two headlines share 2+ entities,
# they're likely the same story even if other words differ.
DEDUP_ENTITIES = [
    "anthropic", "openai", "google", "meta", "microsoft", "apple", "amazon",
    "nvidia", "deepseek", "mistral", "xai", "stability", "hugging face",
    "perplexity", "cohere", "ibm", "baidu", "alibaba", "samsung",
    "claude", "chatgpt", "gemini", "gpt", "llama", "copilot", "grok",
    "sam altman", "elon musk", "jensen huang", "zuckerberg", "satya nadella",
    "dario amodei", "amodei", "ilya sutskever",
    "stargate", "eu", "congress", "china",
    "pentagon", "dorsey", "block ", "square",
]

# Entity aliases: different forms that refer to the same entity.
# Used to normalize entity extraction for dedup.
DEDUP_ENTITY_ALIASES = {
    "chinese": "china",
    "chinas": "china",
    "department of defense": "pentagon",
    "defense department": "pentagon",
    "dod": "pentagon",
}

# ---------------------------------------------------------------------------
# Paywall Filter
# ---------------------------------------------------------------------------
# Articles from these publishers are skipped entirely. Readers can't access
# them without a subscription, so there's no point listing them.
#
# For direct RSS feeds (e.g., "Bloomberg Tech"), match by feed source name.
# For Google News articles, the publisher is parsed from the title suffix
# (e.g., "Some Headline - Bloomberg" → "bloomberg").

PAYWALLED_PUBLISHERS = {
    # Hard paywalls
    "bloomberg", "wall street journal", "wsj", "financial times", "ft",
    "the information", "barron's", "barrons", "nikkei", "nikkei asia",
    "the athletic", "the economist",
    # Metered / soft paywalls (most readers will hit the wall)
    "new york times", "nyt", "washington post", "business insider",
    "the atlantic", "wired", "fortune", "vanity fair",
    "seeking alpha", "motley fool",
}

# Direct RSS feed sources to skip entirely (they're all paywalled)
PAYWALLED_FEEDS = {
    "Bloomberg Tech", "Financial Times", "WSJ Tech",
    "NYT Tech", "Washington Post",
}

# ---------------------------------------------------------------------------
# Google News Quality Filter
# ---------------------------------------------------------------------------
# Google News aggregates from thousands of publishers. Many are low-quality
# local newspapers, SEO farms, or niche blogs. Block the worst offenders.

GOOGLE_NEWS_BLOCKED_PUBLISHERS = {
    # Local/regional newspapers (not relevant for AI news)
    "gabber", "simpsonian", "utd mercury", "mississippi today",
    "audacy", "statestatescoop", "kansas health",
    "american legislative exchange", "eurasia review",
    "manila times", "latin times", "american bazaar",
    "national cio review", "cpa practice advisor",
    "crain", "hotel online", "bikerumor",
    "1851 franchise", "fox news", "tradingview",
    "govtech", "tipranks", "investmentnews",
    # SEO / content farms
    "pymnts", "mashable",
}

# ---------------------------------------------------------------------------
# Research Source Gating
# ---------------------------------------------------------------------------
# Only these RSS feed sources can contribute articles to the Research category.
# An article from any other source that scores Research will be recategorized
# to its next-best category (or dropped if no other category scores).

RESEARCH_QUALITY_SOURCES = {
    # Universities & labs
    "MIT News AI", "BAIR Blog", "CMU SCS", "Oxford Internet Institute",
    "UW Allen School", "Cambridge CST", "Vector Institute",
    # Company research blogs
    "Google DeepMind", "Google Research", "Meta Research",
    "Microsoft Research", "Apple ML Research",
    # Scientific journals
    "Nature", "Nature Machine Intelligence", "Science",
    "Scientific American", "New Scientist", "IEEE Spectrum",
    # AI-focused (when they publish actual research coverage)
    "The Gradient", "Import AI", "Ahead of AI", "Interconnects",
    "BAIR Blog",
    # Consultancies with research arms
    "McKinsey",
}

# ---------------------------------------------------------------------------
# Display Settings
# ---------------------------------------------------------------------------

MAX_HEADLINE_AGE_DAYS = 7
REQUEST_TIMEOUT = 15
