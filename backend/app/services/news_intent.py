"""Cheap news routing and public query construction; no account data is sent."""
import re

NEWS_INTENTS = {"NEWS_CURRENT", "NEWS_SUMMARY", "COMPANY_NEWS", "MARKET_NEWS_IMPACT"}
TOPICS = {
    "rbi": ("Reserve Bank of India RBI", ["rbi", "reserve bank"]),
    "reliance": ("Reliance Industries", ["reliance"]),
    "infosys": ("Infosys", ["infosys"]),
    "infy": ("Infosys", ["infosys", "infy"]),
    "tcs": ("Tata Consultancy Services TCS", ["tcs", "tata consultancy"]),
    "hdfc": ("HDFC Bank", ["hdfc"]),
    "hdfcbank": ("HDFC Bank", ["hdfc", "hdfcbank"]),
    "icici": ("ICICI Bank", ["icici"]),
    "nifty": ("NIFTY Indian stock market", ["nifty"]),
    "banknifty": ("Bank NIFTY Indian banking", ["bank nifty", "banknifty", "banking"]),
    "sensex": ("Sensex Indian stock market", ["sensex"]),
    "global": ("global financial markets", ["global", "world", "international"]),
    "bank": ("Indian banking stocks", ["bank", "banking"]),
}
COMPANIES = {"reliance", "infosys", "infy", "tcs", "hdfc", "hdfcbank", "icici"}


def is_followup(message: str) -> bool:
    return bool(re.search(r"\b(this news|that news|these headlines|intha news|indha news|this announcement|that announcement)\b", message.lower()))


def detect_news_intent(message: str) -> str | None:
    q = message.lower()
    current = bool(re.search(r"\b(latest|recent|today|current|now|innaiku|ippo)\b", q))
    news = bool(re.search(r"\b(news|headlines|announcement|announcements)\b", q))
    impact = bool(re.search(r"\b(affect|impact|implications|influence|pannum)\b", q))
    if is_followup(q):
        return "MARKET_NEWS_IMPACT" if impact else "NEWS_SUMMARY"
    if news and (current or not re.search(r"\b(what is|define|how does|how do|meaning|na enna)\b", q)):
        if impact:
            return "MARKET_NEWS_IMPACT"
        if any(re.search(r"\b" + company + r"\b", q) for company in COMPANIES):
            return "COMPANY_NEWS"
        if re.search(r"\b(summarize|summary|explain)\b", q):
            return "NEWS_SUMMARY"
        return "NEWS_CURRENT"
    if re.search(r"\b(today|innaiku)\b", q) and re.search(r"\b(what.?s happening|what is happening|enna nadakk)\b", q) and not re.search(r"\b(rsi|macd|indicator|price|strategy|portfolio)\b", q):
        return "NEWS_CURRENT"
    return None


def public_topic(message: str) -> tuple[str, list[str]]:
    q = message.lower()
    for key, (topic, terms) in TOPICS.items():
        if re.search(r"\b" + key + r"\b", q):
            return topic, terms
    # An explicit unknown company is a clarification, rather than broad news.
    if re.search(r"\b(company|about)\b", q) and not re.search(r"\b(market|stock|financial|economy|india|indian)\b", q):
        return "", []
    if not re.search(r"\b(market|markets|stock|stocks|financial|finance|economy|india|indian)\b", q):
        generic = {"what", "is", "the", "any", "latest", "recent", "news", "headlines", "today", "current", "now", "please", "show", "me", "tell", "summarize", "summary", "explain", "announcement", "announcements", "innaiku", "ippo", "sollunga", "enna"}
        if any(word not in generic for word in re.findall(r"[a-z]+", q)):
            return "", []
    return "Indian stock market financial news", ["market", "stocks", "nifty", "sensex", "rbi", "economy"]
