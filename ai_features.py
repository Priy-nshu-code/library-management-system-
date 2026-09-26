"""
AI Features Module: Next-Gen Horizons
Includes:
1. Smart Recommendation Engine (Hybrid: Content-Based + Collaborative Filtering + Live API)
2. Semantic / Natural Language Search (Intent extraction, tokenization, concept mapping)
3. Book Demand Predictor (Predictive Analytics with circulation velocity & reservation pressure)
4. Smart Tag Recommendation (Rule-based NLP entity extractor)
5. Smart Librarian Dashboard (AI collection health & risk analyzer)

Zero external database or pip package dependencies; uses standard library math, json, and urllib.
"""

import math
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from data_store import db
from ui import Colors, print_header, print_alert, print_table


# -------------------------------------------------------------
# 1. SMART RECOMMENDATION ENGINE
# -------------------------------------------------------------

COMMON_STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for",
    "with", "by", "of", "about", "as", "into", "like", "through",
    "after", "over", "between", "out", "against", "during", "without",
    "before", "under", "around", "among", "is", "are", "was", "were",
    "i", "me", "my", "we", "our", "you", "your", "they", "them", "he", "she",
    "want", "need", "looking", "learn", "find", "good", "best", "give", "book", "books"
}


def get_user_borrowing_profile(member_id: str) -> dict:
    """
    Extracts category affinities and tag interests from a member's
    active transactions, history, and wishlist.
    """
    category_counts = {}
    tag_counts = {}
    read_book_ids = set()

    # Past and active transactions
    for txn in db.transactions:
        if txn.get("member_id") == member_id:
            book_id = txn.get("book_id")
            read_book_ids.add(book_id)
            if book_id in db.books:
                book = db.books[book_id]
                cat = book.get("category", "General")
                category_counts[cat] = category_counts.get(cat, 0) + 1
                for tag in book.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Wishlist books
    member_wishlist = db.wishlists.get(member_id, [])
    for b_id in member_wishlist:
        if b_id in db.books:
            b = db.books[b_id]
            cat = b.get("category", "General")
            category_counts[cat] = category_counts.get(cat, 0) + 0.5
            for tag in b.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 0.5

    return {
        "categories": category_counts,
        "tags": tag_counts,
        "read_book_ids": read_book_ids
    }


def find_similar_members(target_member_id: str) -> list:
    """
    Collaborative filtering heuristic:
    Finds members who borrowed at least one book in common with target_member.
    Returns list of tuples: (member_id, similarity_score)
    """
    target_books = {t["book_id"] for t in db.transactions if t.get("member_id") == target_member_id}
    if not target_books:
        return []

    member_overlap = {}
    for txn in db.transactions:
        m_id = txn.get("member_id")
        if m_id != target_member_id:
            b_id = txn.get("book_id")
            if b_id in target_books:
                member_overlap[m_id] = member_overlap.get(m_id, 0) + 1

    # Sort descending by overlap score
    return sorted(member_overlap.items(), key=lambda item: item[1], reverse=True)


def calculate_average_rating(book_id: str) -> float:
    """Calculates average 5-star rating for a book from reviews list."""
    relevant_reviews = [r["rating"] for r in db.reviews if r.get("book_id") == book_id]
    if not relevant_reviews:
        return 4.0  # default baseline
    return sum(relevant_reviews) / len(relevant_reviews)


def recommend_books_for_member(member_id: str, top_n: int = 4) -> list:
    """
    Hybrid recommendation algorithm combining:
    1. Content-based category & tag affinity
    2. Collaborative filtering from similar peers
    3. Rating and popularity weighting
    """
    profile = get_user_borrowing_profile(member_id)
    user_cats = profile["categories"]
    user_tags = profile["tags"]
    already_read = profile["read_book_ids"]

    similar_members = find_similar_members(member_id)
    collab_boost_books = {}
    for peer_id, overlap_score in similar_members[:3]:
        peer_books = [t["book_id"] for t in db.transactions if t.get("member_id") == peer_id]
        for b_id in peer_books:
            if b_id not in already_read:
                collab_boost_books[b_id] = collab_boost_books.get(b_id, 0) + overlap_score

    scores = []
    for book_id, book in db.books.items():
        if book_id in already_read:
            continue

        score = 0.0
        reasons = []

        # Category match
        b_cat = book.get("category", "")
        if b_cat in user_cats:
            cat_affinity = user_cats[b_cat]
            score += cat_affinity * 3.5
            reasons.append(f"Favorite category: '{b_cat}'")

        # Tag overlap
        b_tags = book.get("tags", [])
        shared_tags = [t for t in b_tags if t in user_tags]
        if shared_tags:
            score += len(shared_tags) * 2.0
            reasons.append(f"Matches topics: {', '.join(shared_tags[:2])}")

        # Collaborative boost
        if book_id in collab_boost_books:
            collab_weight = collab_boost_books[book_id] * 4.0
            score += collab_weight
            reasons.append("Read by users with similar taste")

        # Global popularity & rating
        avg_rating = calculate_average_rating(book_id)
        score += avg_rating * 1.5
        score += math.log(max(book.get("issue_count", 0), 1)) * 0.8

        if not reasons:
            reasons.append(f"High community rating ({avg_rating:.1f}★)")

        scores.append({
            "book": book,
            "score": round(score, 2),
            "reason": reasons[0] if reasons else "Trending in library",
            "available": book.get("available_copies", 0) > 0
        })

    # Sort descending by score
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_n]


def fetch_external_openlibrary_recommendations(query: str) -> list:
    """
    Live API Call: Fetches book recommendations and related topics from Open Library API.
    Zero 3rd party dependencies: Uses standard library urllib.request.
    Falls back gracefully if offline.
    """
    encoded_query = urllib.parse.quote(query)
    api_url = f"https://openlibrary.org/search.json?q={encoded_query}&limit=5"
    try:
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": "SmartLibraryCLI-Hackathon/1.0 (academic-demo)"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                docs = data.get("docs", [])
                results = []
                for doc in docs[:4]:
                    title = doc.get("title", "Unknown Title")
                    authors = ", ".join(doc.get("author_name", ["Unknown Author"])[:2])
                    first_publish = doc.get("first_publish_year", "N/A")
                    results.append({
                        "title": title,
                        "author": authors,
                        "year": str(first_publish),
                        "source": "Open Library Public API"
                    })
                return results
    except Exception:
        pass  # Graceful fallback on network timeout/offline
    return []


# -------------------------------------------------------------
# 2. SEMANTIC / NATURAL LANGUAGE SEARCH
# -------------------------------------------------------------

SEMANTIC_CONCEPT_MAP = {
    "code": ["programming", "python", "software", "clean code", "syntax"],
    "coding": ["programming", "python", "software", "dsa", "algorithms"],
    "beginner": ["basics", "fundamentals", "introduction", "beginner"],
    "start": ["basics", "fundamentals", "introduction", "beginner"],
    "database": ["dbms", "sql", "data", "rdbms", "distributed systems", "indexing"],
    "db": ["dbms", "sql", "database", "acid"],
    "storage": ["database", "dbms", "sql", "data-intensive"],
    "web": ["networks", "protocols", "tcp/ip", "security"],
    "internet": ["networks", "protocols", "tcp/ip", "routing"],
    "clean": ["clean code", "refactoring", "software engineering", "best practices"],
    "architect": ["software engineering", "designing data-intensive", "clean code"],
    "ai": ["artificial intelligence", "machine learning", "agents", "nlp", "search"],
    "intelligence": ["artificial intelligence", "machine learning", "agents"],
    "dsa": ["data structures", "algorithms", "arrays", "trees", "graphs"],
    "speed": ["algorithms", "scalability", "distributed systems"],
    "system": ["operating system", "networks", "distributed systems", "processes"],
    "os": ["operating system", "memory management", "threads", "virtualization"]
}


def semantic_natural_language_search(query: str) -> list:
    """
    Processes natural conversational search queries:
    - Normalizes text & eliminates conversational stop words
    - Expands domain query concepts using semantic dictionary
    - Scores library books based on token overlap & semantic relevance
    """
    clean_query = re.sub(r"[^\w\s]", " ", query.lower())
    tokens = [w for w in clean_query.split() if w and w not in COMMON_STOP_WORDS]

    if not tokens:
        tokens = query.lower().split()

    expanded_terms = set(tokens)
    for token in tokens:
        if token in SEMANTIC_CONCEPT_MAP:
            for related in SEMANTIC_CONCEPT_MAP[token]:
                expanded_terms.add(related)

    scored_results = []
    for b_id, book in db.books.items():
        score = 0
        matches = []

        title_lower = book["title"].lower()
        cat_lower = book["category"].lower()
        author_lower = book["author"].lower()
        tags_lower = [t.lower() for t in book.get("tags", [])]

        for term in expanded_terms:
            # Direct title match (high weight)
            if term in title_lower:
                score += 15
                matches.append(f"Title contains '{term}'")
            # Category match (medium weight)
            if term in cat_lower:
                score += 10
                matches.append(f"Category matches '{term}'")
            # Tag match (high precision)
            if any(term in t for t in tags_lower):
                score += 12
                matches.append(f"Tag matched '{term}'")
            # Author match
            if term in author_lower:
                score += 8
                matches.append(f"Author matches '{term}'")

        if score > 0:
            # Match confidence percentage
            confidence = min(round((score / 35.0) * 100), 98)
            scored_results.append({
                "book": book,
                "score": score,
                "confidence": confidence,
                "reason": ", ".join(matches[:2])
            })

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results


# -------------------------------------------------------------
# 3. BOOK DEMAND PREDICTOR (Predictive Analytics)
# -------------------------------------------------------------

def predict_book_demand() -> list:
    """
    Calculates demand forecast for all catalog books:
    - Borrow velocity (issue count)
    - Utilization rate ((total - available) / total)
    - Reservation queue pressure
    Returns categorized demand metrics and replenishment recommendations.
    """
    forecasts = []

    # Count pending reservations per book
    res_counts = {}
    for res in db.reservations:
        if res.get("status") == "PENDING":
            b_id = res.get("book_id")
            res_counts[b_id] = res_counts.get(b_id, 0) + 1

    for b_id, book in db.books.items():
        total = max(book.get("total_copies", 1), 1)
        avail = book.get("available_copies", 0)
        borrowed = total - avail
        issue_cnt = book.get("issue_count", 0)
        reservations = res_counts.get(b_id, 0)

        # 1. Utilization Rate (0 to 100)
        util_rate = (borrowed / total) * 100

        # 2. Circulation Velocity factor (normalized)
        velocity_score = min(issue_cnt * 1.5, 40)

        # 3. Reservation Pressure
        res_score = reservations * 20

        # Combined Demand Index (0 - 100)
        demand_index = min(round((util_rate * 0.4) + velocity_score + res_score), 99)

        # Demand Classification & Actionable Insights
        if demand_index >= 75 or (avail == 0 and reservations > 0):
            classification = "CRITICAL SURGE"
            action = f"Restock +{max(3, reservations * 2)} copies immediately"
            status_color = Colors.RED
        elif demand_index >= 50:
            classification = "HIGH DEMAND"
            action = "Monitor stock; restock +2 copies"
            status_color = Colors.YELLOW
        elif demand_index >= 25:
            classification = "STABLE"
            action = "Inventory adequate"
            status_color = Colors.GREEN
        else:
            classification = "LOW CIRCULATION"
            action = "Consider promotional display"
            status_color = Colors.DIM

        forecasts.append({
            "book_id": b_id,
            "title": book["title"],
            "total": total,
            "available": avail,
            "issues": issue_cnt,
            "reservations": reservations,
            "demand_index": demand_index,
            "classification": classification,
            "action": action,
            "color": status_color
        })

    # Sort by demand index descending
    forecasts.sort(key=lambda x: x["demand_index"], reverse=True)
    return forecasts


# -------------------------------------------------------------
# 4. SMART TAG RECOMMENDATION (NLP Rule-Based)
# -------------------------------------------------------------

TAG_LEXICON = {
    "python": ["python", "scripting", "backend", "django", "data-science"],
    "dbms": ["sql", "rdbms", "database", "schema-design", "queries"],
    "database": ["storage", "indexing", "acid", "replication", "nosql"],
    "clean": ["best-practices", "refactoring", "design-patterns", "maintainability"],
    "code": ["software-engineering", "programming", "craftsmanship"],
    "intelligence": ["ai", "machine-learning", "neural-networks", "heuristics"],
    "algorithms": ["data-structures", "problem-solving", "time-complexity", "trees"],
    "network": ["networking", "tcp-ip", "sockets", "protocols", "osi"],
    "system": ["operating-systems", "memory", "concurrency", "threads"]
}


def recommend_tags_for_book(title: str, category: str) -> list:
    """
    Extracts NLP keywords from book title and category to recommend semantic tags.
    """
    text = f"{title.lower()} {category.lower()}"
    suggested = set()

    for keyword, tags in TAG_LEXICON.items():
        if keyword in text:
            for t in tags:
                suggested.add(t)

    # Add normalized tokens as fallback
    words = [w for w in text.split() if len(w) > 3 and w not in COMMON_STOP_WORDS]
    for w in words[:3]:
        suggested.add(w)

    return list(suggested)[:5]


# -------------------------------------------------------------
# 5. SMART LIBRARIAN DASHBOARD (AI Executive Synthesis)
# -------------------------------------------------------------

def generate_smart_librarian_insights() -> dict:
    """
    Synthesizes overall library health, circulation velocity,
    risk analysis, and restocking recommendations for the Admin.
    """
    total_books_count = sum(b.get("total_copies", 0) for b in db.books.values())
    total_available = sum(b.get("available_copies", 0) for b in db.books.values())
    total_issued = total_books_count - total_available
    overall_circulation_rate = (total_issued / max(total_books_count, 1)) * 100

    # Overdue risk tracking
    overdue_txns = [t for t in db.transactions if t.get("status") == "OVERDUE"]
    total_outstanding_fine = sum(t.get("fine_amount", 0.0) for t in overdue_txns if not t.get("fine_paid", False))

    # Top demand items
    demand_predictions = predict_book_demand()
    critical_items = [d for d in demand_predictions if d["classification"] == "CRITICAL SURGE"]

    # Category demand breakdown
    cat_distribution = {}
    for b in db.books.values():
        c = b.get("category", "General")
        cat_distribution[c] = cat_distribution.get(c, 0) + b.get("issue_count", 0)

    top_category = max(cat_distribution.items(), key=lambda x: x[1]) if cat_distribution else ("None", 0)

    # Health Index (0 - 100)
    health_index = max(100 - (len(overdue_txns) * 8) - (len(critical_items) * 5), 45)

    return {
        "total_books_titles": len(db.books),
        "total_physical_copies": total_books_count,
        "active_borrows": total_issued,
        "circulation_rate": round(overall_circulation_rate, 1),
        "health_index": health_index,
        "overdue_count": len(overdue_txns),
        "outstanding_fines": total_outstanding_fine,
        "critical_restock_needed": len(critical_items),
        "top_category": top_category[0],
        "top_category_issues": top_category[1],
        "top_critical_book": critical_items[0]["title"] if critical_items else "All inventory well-stocked"
    }
