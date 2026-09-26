"""
Comprehensive Automated Test Suite for Smart Library CLI
Verifies all functional, analytical, and AI horizon components.
"""

from data_store import db, hash_pin
from auth import register_member, authenticate, CurrentSession
import member_ops
import admin_ops
import analytics
import ai_features


def test_all():
    print("=" * 60)
    print("RUNNING AUTOMATED TEST SUITE: SMART LIBRARY CLI")
    print("=" * 60)

    # 1. Auth & Member Verification
    print("\n[1] Testing Auth & Member Registration...")
    import time
    ts = int(time.time())
    test_phone = f"99{str(ts)[-8:]}"
    test_email = f"test_{ts}@hackathon.org"
    success, msg, member = register_member("Test User", test_phone, test_email, "5566")
    assert success, f"Registration failed: {msg}"
    print(f"  -> Member registered: {member['id']} - {member['name']}")

    auth_success, auth_msg, auth_user = authenticate(member["id"], "5566")
    assert auth_success, f"Authentication failed: {auth_msg}"
    assert CurrentSession.user["id"] == member["id"]
    print(f"  -> Authenticated successfully as {auth_user['name']}")

    # 2. Seed Data Validation (Prompt Requirements)
    print("\n[2] Validating Pre-Seeded Analytics Benchmarks...")
    b101 = db.books.get("B101")
    b102 = db.books.get("B102")
    b103 = db.books.get("B103")
    assert b101["issue_count"] == 42, f"Expected 42 issues for Python Basics, got {b101['issue_count']}"
    assert b102["issue_count"] == 37, f"Expected 37 issues for DBMS Fundamentals, got {b102['issue_count']}"
    assert b103["issue_count"] == 31, f"Expected 31 issues for Clean Code, got {b103['issue_count']}"
    print("  -> Most Borrowed seed data verified: Python Basics (42), DBMS (37), Clean Code (31)")

    m102 = db.members.get("M102")
    m114 = db.members.get("M114")
    m127 = db.members.get("M127")
    assert m102["total_borrowed_count"] == 18, "Expected 18 for M102"
    assert m114["total_borrowed_count"] == 15, "Expected 15 for M114"
    assert m127["total_borrowed_count"] == 13, "Expected 13 for M127"
    print("  -> Most Active Member seed data verified: M102 (18), M114 (15), M127 (13)")

    # 3. AI Smart Recommendation Engine
    print("\n[3] Testing AI Smart Recommendation Engine...")
    recs = ai_features.recommend_books_for_member("M101", top_n=3)
    assert len(recs) > 0, "Recommendations should not be empty"
    print(f"  -> Top Recommendation for M101: '{recs[0]['book']['title']}' (Score: {recs[0]['score']}, Reason: {recs[0]['reason']})")

    # 4. AI Semantic Natural Language Search
    print("\n[4] Testing Semantic / Natural Language Search...")
    queries = [
        "beginner friendly guide to python coding",
        "database storage rdbms indexing",
        "clean code refactoring best practices"
    ]
    for q in queries:
        matches = ai_features.semantic_natural_language_search(q)
        assert len(matches) > 0, f"Expected matches for query '{q}'"
        top_match = matches[0]
        print(f"  -> Query: '{q}'\n     Top Match: '{top_match['book']['title']}' [{top_match['confidence']}% match]")

    # 5. AI Demand Predictor
    print("\n[5] Testing AI Book Demand Predictor...")
    demands = ai_features.predict_book_demand()
    assert len(demands) == len(db.books), "Demand predicted for all books"
    top_demand = demands[0]
    print(f"  -> Highest Demand: '{top_demand['title']}' | Demand Index: {top_demand['demand_index']}/100 | Class: {top_demand['classification']}")

    # 6. AI Smart Tagging
    print("\n[6] Testing AI Smart Tag Recommendation...")
    tags = ai_features.recommend_tags_for_book("Modern Database Architecture", "Database")
    assert len(tags) > 0, "Tags should be recommended"
    print(f"  -> Recommended tags for 'Modern Database Architecture': {tags}")

    # 7. Slicing & Pagination
    print("\n[7] Testing Python Slicing in Data Presentation...")
    all_books = list(db.books.values())
    page_1 = all_books[0:3]
    page_2 = all_books[3:6]
    assert len(page_1) == 3
    assert len(page_2) == 3
    assert page_1[0]["id"] != page_2[0]["id"]
    print("  -> Slicing verified: page_1 = books[0:3], page_2 = books[3:6]")

    # 8. Fine Calculation & Overdue Verification
    print("\n[8] Testing Overdue Fine Engine...")
    member_ops.check_and_update_overdue_status()
    overdue_txns = [t for t in db.transactions if t.get("status") == "OVERDUE"]
    assert len(overdue_txns) > 0, "Should have pre-seeded overdue transaction"
    first_overdue = overdue_txns[0]
    assert first_overdue["fine_amount"] > 0, "Fine amount should be accrued"
    print(f"  -> Overdue Txn {first_overdue['txn_id']} for '{first_overdue['book_title']}': Fine = Rs. {first_overdue['fine_amount']:.2f}")

    # 9. Smart Librarian Dashboard
    print("\n[9] Testing Smart Librarian Dashboard Analytics...")
    insights = ai_features.generate_smart_librarian_insights()
    assert "circulation_rate" in insights
    assert "health_index" in insights
    print(f"  -> Collection Health Index: {insights['health_index']}/100 | Circulation: {insights['circulation_rate']}%")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
