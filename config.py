# =============================================================================
# AI News Aggregator — Configuration
# =============================================================================

TIMEZONE_OFFSET = -6  # Costa Rica (UTC-6)

# ---------------------------------------------------------------------------
# RSS Feed Sources
# ---------------------------------------------------------------------------

FEEDS = {
    # --- Tier 0: Official Company Blogs (straight from the source) ---
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "NVIDIA Blog": "https://blogs.nvidia.com/feed/",
    "Meta Research": "https://research.facebook.com/feed/",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/feed/",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",

    # --- Tier 1: AI-Focused News Sites (always relevant) ---
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
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

    # --- Tier 2: Traditional Media & Finance (filtered for AI keywords) ---
    "NYT Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "WSJ Tech": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
    "BBC Tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "CNN Tech": "http://rss.cnn.com/rss/money_technology.rss",
    "Guardian Tech": "https://www.theguardian.com/technology/rss",
    "Fortune": "https://fortune.com/feed/fortune-feeds/?id=3230629",
    "Bloomberg Tech": "https://feeds.bloomberg.com/technology/news.rss",
    "CNBC Tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",

    # --- Tier 3: Community & Aggregators ---
    "Hacker News AI": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+Anthropic&points=10",
    "Google News AI": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    "Google News Vibe Coding": "https://news.google.com/rss/search?q=%22vibe+coding%22+OR+%22vibecoding%22+OR+%22generative+coding%22&hl=en-US&gl=US&ceid=US:en",
}

# Sources that require AI keyword match in title to be included
# (they publish lots of non-AI content)
TIER2_SOURCES = {
    # Traditional media
    "NYT Tech", "WSJ Tech", "BBC Tech", "CNN Tech",
    "Guardian Tech", "Fortune",
    "Bloomberg Tech", "CNBC Tech",
    # Mixed-content tech sites
    "Meta Research", "ZDNet AI", "MIT Tech Review", "Ars Technica",
    # Community
    "Hacker News AI", "Google News AI", "Google News Vibe Coding",
}

# Keywords for Tier 2 filtering. These must match as whole words (word boundaries).
# Kept specific to avoid pulling in generic tech articles that mention "AI" in passing.
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "claude", "gemini", "llama",
    "neural network", "chatbot", "openai", "anthropic", "deepmind",
    "copilot", "generative ai", "diffusion model", "agi",
    "superintelligence", "reinforcement learning", "computer vision",
    "natural language processing", "nlp", "ai model", "ai agent",
    "ai tool", "ai safety", "ai regulation", "ai chip",
    "vibe coding", "vibecoding", "generative coding",
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
    #   "GPT-5 benchmarks show improvement" (→ Research),
    #   "Claude Code popularity surprises CEO" (→ Industry)
    # -----------------------------------------------------------------
    {
        "name": "Releases",
        "strong": [
            "releases new", "released new", "releasing new", "now available",
            "rolling out", "rolls out", "generally available", "public beta",
            "early access", "ships new", "shipped new",
            "introduces new", "introducing new", "debuts new",
            "we're excited to", "is now open source", "open-sources",
            "new version of", "v2 ", "v3 ", "v4 ", "v5 ",
        ],
        "weak": [
            "release", "deploy", "open source", "open-source",
            "launched", "available",
        ],
        "exclude": [
            "rumor", "reportedly", "expected to", "might", "could soon",
            "leak", "may release", "planning to", "accus", "stock",
            "billion", "million", "lawsuit",
        ],
    },

    # -----------------------------------------------------------------
    # 2. PRODUCTS & TOOLS — Things you can use
    # -----------------------------------------------------------------
    # DEFINITION: Coverage of AI products, apps, APIs, developer tools,
    # and platforms. Practical, hands-on. Either reviewing a product,
    # announcing a feature, or discussing how to use something.
    #
    # IS products: "ChatGPT adds voice mode", "How to use Claude Code",
    #   "Copilot gets new IDE features", "New AI coding assistant reviewed"
    # NOT products: "OpenAI raises $10B" (→ Business), "AI agents will
    #   destroy jobs" (→ Industry), "SDK benchmark paper" (→ Research)
    # -----------------------------------------------------------------
    {
        "name": "Products & Tools",
        "strong": [
            "chatgpt", "copilot", "coding assistant", "claude code",
            "ai assistant", "ai app", "ai tool", "ai platform",
            "ai-powered", "ai search", "api access",
            "sdk", "plugin", "new feature",
            "free tier", "pricing update", "subscription",
            "reverse-engineering", "foundation tool",
            "agent gateway", "sandbox agent", "agent sdk",
            "ai news app", "ai payment",
        ],
        "weak": [
            "developer tool", "enterprise", "integration",
            "workspace", "extension", "infrastructure",
            "cybersecurity", "firewall", "cloud ai",
        ],
        "exclude": [
            "rumor", "stock", "billion", "funding", "valuation",
            "lawsuit", "regulation",
        ],
    },

    # -----------------------------------------------------------------
    # 3. RUMORS & SPECULATION — Not confirmed yet
    # -----------------------------------------------------------------
    # DEFINITION: Leaks, unconfirmed reports, speculation about future
    # products, upcoming announcements. The headline uses hedging
    # language ("reportedly", "may", "could", "sources say").
    #
    # IS rumor: "OpenAI reportedly working on GPT-6", "Apple may launch
    #   AI device next year", "Sources: Google considering Anthropic bid"
    # NOT rumor: "OpenAI launches GPT-5" (→ Releases, it happened)
    # -----------------------------------------------------------------
    {
        "name": "Rumors & Speculation",
        "strong": [
            "rumor", "rumour", "reportedly", "report says",
            "sources say", "according to sources", "leaked",
            "leak suggests", "upcoming", "expected to",
            "planning to", "set to announce", "may soon",
            "could soon", "in talks to", "in the works",
            "under development", "preparing to", "considering",
        ],
        "weak": [
            "may ", "might ", "could ", "plans to", "working on",
            "aims to", "looking to", "exploring",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 4. FUN & WEIRD — The lighter side of AI
    # -----------------------------------------------------------------
    # DEFINITION: Quirky, humorous, absurd, or culturally interesting
    # AI stories. The pope vs AI, robots doing silly things, AI art
    # controversies, AI dating, unusual applications.
    #
    # IS fun: "Pope tells priests not to use AI for homilies",
    #   "AI generates 10,000 cats nobody asked for",
    #   "Man marries AI chatbot", "AI writes a Christmas album"
    # NOT fun: "OpenAI releases GPT-5" (→ Releases)
    # -----------------------------------------------------------------
    {
        "name": "Fun & Weird",
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
    # 5. BUSINESS & MONEY — Follow the money
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
    # 6. POLICY & REGULATION — AI meets government
    # -----------------------------------------------------------------
    # DEFINITION: Government regulation, legislation, lawsuits, bans,
    # export controls, copyright disputes, safety mandates, ethics
    # enforcement. Where AI intersects with law and the state.
    #
    # IS policy: "EU passes AI Act", "OpenAI sued for copyright",
    #   "Congress holds AI safety hearing", "AI chip export ban"
    # NOT policy: "Anthropic CEO discusses safety" (→ Industry),
    #   "AI safety research paper" (→ Research)
    # -----------------------------------------------------------------
    {
        "name": "Policy & Regulation",
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
            "policy", "govern", "privacy", "surveillance",
            "probe", "investigat", "oversight", "scrutiny",
            "advertising claims", "law review",
        ],
        "exclude": [],
    },

    # -----------------------------------------------------------------
    # 7. RESEARCH — From the labs
    # -----------------------------------------------------------------
    # DEFINITION: Academic papers, scientific studies, benchmarks,
    # technical breakthroughs, and fundamental research. Content that
    # advances understanding rather than ships a product.
    #
    # IS research: "New paper on scaling laws", "Researchers find...",
    #   "Benchmark shows...", "Study: LLMs can reason about..."
    # NOT research: "Anthropic releases Claude 4" (→ Releases),
    #   "AI researcher quits Google" (→ Industry)
    # -----------------------------------------------------------------
    {
        "name": "Research",
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
    # 8. VIBE CODING — Non-coders building software with AI
    # -----------------------------------------------------------------
    # DEFINITION: The practice of describing what you want to an AI
    # and having it generate the code, without necessarily understanding
    # the code yourself. Coined by Andrej Karpathy in 2025. Covers
    # non-programmers building apps, prompt-to-app workflows, the
    # cultural movement, and concerns about code quality/accountability.
    #
    # IS vibe coding: "Vibe coding is changing who can build software",
    #   "Non-programmer builds SaaS app with AI in a weekend",
    #   "Andrej Karpathy on the future of vibe coding",
    #   "The security risks of vibe-coded applications"
    # NOT vibe coding: "GitHub Copilot adds new features" (→ Products),
    #   "SWE-bench benchmark results" (→ Research),
    #   "Will AI replace programmers?" (→ Ethics)
    # -----------------------------------------------------------------
    {
        "name": "Vibe Coding",
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
    # 9. ETHICS & PHILOSOPHY — The big questions
    # -----------------------------------------------------------------
    # DEFINITION: Moral, philosophical, and societal debates about AI.
    # Consciousness, sentience, existential risk, alignment philosophy,
    # bias and fairness, labor displacement ethics, human dignity,
    # the future of work, AI rights, responsible AI.
    #
    # IS ethics: "Will AI make human workers obsolete?",
    #   "AI consciousness debate heats up", "The ethics of deepfakes",
    #   "Who decides who gets to eat if AI replaces labor?"
    # NOT ethics: "EU passes AI Act" (→ Policy, that's law not ethics),
    #   "AI safety benchmark" (→ Research)
    # -----------------------------------------------------------------
    {
        "name": "Ethics & Philosophy",
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
]

# Catch-all for headlines that don't score in any category
DEFAULT_CATEGORY = "Other"

# Maximum items to show in the catch-all category (drop low-signal noise)
MAX_OTHER_ITEMS = 25

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
]

# Entity aliases: different forms that refer to the same entity.
# Used to normalize entity extraction for dedup.
DEDUP_ENTITY_ALIASES = {
    "chinese": "china",
    "chinas": "china",
}

# ---------------------------------------------------------------------------
# Display Settings
# ---------------------------------------------------------------------------

MAX_HEADLINE_AGE_DAYS = 7
REQUEST_TIMEOUT = 15
