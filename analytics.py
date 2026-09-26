"""
Analytics & Reporting Module
Implements:
1. Leaderboards: Most Borrowed Books & Most Active Members (built-ins sorted, slicing, zip)
2. Inventory Alert: Low-stock & zero-stock triggers
3. Overdue Management: In-depth audit with contact details and penalties
4. Category Analytics: Volume and circulation distribution
5. Smart Librarian Dashboard: AI collection insights and predictive forecasts
"""

from data_store import db
from ui import Colors, print_header, print_alert, print_table
from member_ops import check_and_update_overdue_status, TODAY_STR, parse_date
from ai_features import predict_book_demand, generate_smart_librarian_insights


def show_most_borrowed_books(top_n: int = 5):
    """
    Renders leaderboard of most borrowed books.
    Demonstrates Python built-in sorted() with custom lambda key and list slicing.
    """
    books_list = list(db.books.values())
    # Sort descending by issue_count
    sorted_books = sorted(books_list, key=lambda b: b.get("issue_count", 0), reverse=True)
    # Slicing: take top N
    top_books = sorted_books[:top_n]

    print_header(f"MOST BORROWED BOOKS LEADERBOARD (Top {len(top_books)})")
    headers = ["Rank", "Book Title", "Author", "Category", "Total Issues"]
    rows = []
    medals = ["[1st]", "[2nd]", "[3rd]", "[4th]", "[5th]", "[6th]", "[7th]"]

    for idx, b in enumerate(top_books):
        rank_badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
        issues_str = f"{b.get('issue_count', 0)} issues"
        rows.append([rank_badge, b["title"], b["author"], b["category"], issues_str])

    print_table(headers, rows)


def show_most_active_members(top_n: int = 5):
    """
    Renders leaderboard of most active members.
    Uses built-in sorted and dictionary manipulation.
    """
    # Exclude admins
    members_list = [m for m in db.members.values() if m.get("role") != "admin"]
    sorted_members = sorted(members_list, key=lambda m: m.get("total_borrowed_count", 0), reverse=True)
    top_members = sorted_members[:top_n]

    print_header(f"MOST ACTIVE MEMBERS LEADERBOARD (Top {len(top_members)})")
    headers = ["Rank", "Member ID", "Name", "Email", "Books Borrowed"]
    rows = []
    medals = ["[1st]", "[2nd]", "[3rd]", "[4th]", "[5th]"]

    for idx, m in enumerate(top_members):
        rank_badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
        count_str = f"{m.get('total_borrowed_count', 0)} books"
        rows.append([rank_badge, m["id"], m["name"], m["email"], count_str])

    print_table(headers, rows)


def show_inventory_alerts(threshold: int = 2):
    """
    Displays real-time inventory warnings for books with low or zero stock.
    Demonstrates list comprehensions and filtering.
    """
    out_of_stock = [b for b in db.books.values() if b.get("available_copies", 0) == 0]
    low_stock = [b for b in db.books.values() if 0 < b.get("available_copies", 0) <= threshold]

    print_header("Inventory Alerts & Stock Depletion Warnings")

    if not out_of_stock and not low_stock:
        print_alert("All books have adequate stock levels! No immediate shortages.", "success")
        return

    if out_of_stock:
        print(f"\n{Colors.RED}{Colors.BOLD}[CRITICAL SHORTAGE: OUT OF STOCK (0 Copies)]{Colors.RESET}")
        headers = ["Book ID", "Title", "Category", "Total Copies", "Pending Reservations"]
        rows = []
        for b in out_of_stock:
            res_cnt = sum(1 for r in db.reservations if r["book_id"] == b["id"] and r["status"] == "PENDING")
            rows.append([b["id"], b["title"], b["category"], str(b["total_copies"]), str(res_cnt)])
        print_table(headers, rows)

    if low_stock:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[LOW STOCK WARNING (<= {threshold} Copies Remaining)]{Colors.RESET}")
        headers = ["Book ID", "Title", "Category", "Available", "Total Copies"]
        rows = [[b["id"], b["title"], b["category"], str(b["available_copies"]), str(b["total_copies"])] for b in low_stock]
        print_table(headers, rows)


def show_overdue_management():
    """
    Comprehensive overdue report with member contact details,
    days overdue, and calculated fine balances.
    """
    check_and_update_overdue_status()
    overdue_txns = [t for t in db.transactions if t.get("status") == "OVERDUE" and not t.get("return_date")]

    print_header("Overdue Compliance & Penalty Audit")
    if not overdue_txns:
        print_alert("Zero overdue loans recorded across all members!", "success")
        return

    total_fine_due = sum(t.get("fine_amount", 0.0) for t in overdue_txns)
    print(f" {Colors.BOLD}Total Overdue Loans  :{Colors.RESET} {Colors.RED}{len(overdue_txns)}{Colors.RESET}")
    print(f" {Colors.BOLD}Total Accrued Penalty:{Colors.RESET} {Colors.RED}Rs. {total_fine_due:.2f}{Colors.RESET}\n")

    headers = ["Txn ID", "Book Title", "Member", "Phone", "Due Date", "Days Late", "Fine (Rs.)"]
    rows = []
    today = parse_date(TODAY_STR)

    for t in overdue_txns:
        mem = db.members.get(t["member_id"], {})
        phone = mem.get("phone", "N/A")
        due = parse_date(t["due_date"])
        days_late = max((today - due).days, 0)
        rows.append([
            t["txn_id"],
            t["book_title"],
            t["member_name"],
            phone,
            t["due_date"],
            str(days_late),
            f"Rs. {t['fine_amount']:.2f}"
        ])

    print_table(headers, rows)


def show_category_analytics():
    """
    Computes statistical distribution of books and circulation by category.
    Demonstrates dict counting and percentage calculations.
    """
    cat_stats = {}
    for b in db.books.values():
        cat = b.get("category", "General")
        if cat not in cat_stats:
            cat_stats[cat] = {"titles": 0, "total_copies": 0, "issues": 0}
        cat_stats[cat]["titles"] += 1
        cat_stats[cat]["total_copies"] += b.get("total_copies", 0)
        cat_stats[cat]["issues"] += b.get("issue_count", 0)

    total_issues_all = sum(s["issues"] for s in cat_stats.values()) or 1

    print_header("Category Analytics & Circulation Distribution")
    headers = ["Category", "Titles", "Total Stock", "Total Issues", "Share of Circulation"]
    rows = []

    # Sort descending by issues
    sorted_cats = sorted(cat_stats.items(), key=lambda item: item[1]["issues"], reverse=True)
    for cat, stats in sorted_cats:
        share_pct = (stats["issues"] / total_issues_all) * 100
        # Text-based mini progress bar using string multiplication
        bar = "=" * int(share_pct / 5)
        share_str = f"{share_pct:.1f}% {bar}"
        rows.append([cat, str(stats["titles"]), str(stats["total_copies"]), str(stats["issues"]), share_str])

    print_table(headers, rows)


def show_smart_librarian_dashboard():
    """
    AI-powered Smart Librarian Dashboard:
    Synthesizes real-time metrics, demand predictions, collection health index,
    and automated replenishment recommendations.
    """
    print_header("Smart Librarian AI Dashboard", "Holistic Operational & Predictive Intelligence")

    insights = generate_smart_librarian_insights()

    # High-level Metrics Cards
    circ_val = f"{insights['circulation_rate']}%"
    health_val = f"{insights['health_index']}/100"
    print(f" {Colors.CYAN}┌─────────────────────────┬─────────────────────────┬─────────────────────────┐{Colors.RESET}")
    print(f" {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Catalog Titles:{Colors.RESET} {str(insights['total_books_titles']).ljust(8)} {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Physical Copies:{Colors.RESET} {str(insights['total_physical_copies']).ljust(7)} {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Circulation Rate:{Colors.RESET} {circ_val.ljust(6)} {Colors.CYAN}│{Colors.RESET}")
    print(f" {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Active Borrows:{Colors.RESET} {str(insights['active_borrows']).ljust(8)} {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Overdue Loans  :{Colors.RESET} {str(insights['overdue_count']).ljust(7)} {Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Collection Health:{Colors.RESET} {health_val.ljust(5)} {Colors.CYAN}│{Colors.RESET}")
    print(f" {Colors.CYAN}└─────────────────────────┴─────────────────────────┴─────────────────────────┘{Colors.RESET}\n")

    print_alert(f"Top Trending Category: {Colors.BOLD}{insights['top_category']}{Colors.RESET} ({insights['top_category_issues']} issues)", "ai")
    print_alert(f"Immediate Restock Priority: {Colors.BOLD}{insights['top_critical_book']}{Colors.RESET}", "ai")

    # Predictive Demand Forecast Table
    print(f"\n{Colors.BOLD}{Colors.HEADER}--- AI Book Demand Forecasts ---{Colors.RESET}")
    predictions = predict_book_demand()
    headers = ["Book Title", "Total/Avail", "Issues", "Waitlist", "Demand Index", "Classification", "AI Recommended Action"]
    rows = []
    # Slicing top 5 demand items
    for p in predictions[:5]:
        stock_ratio = f"{p['total']}/{p['available']}"
        rows.append([
            p["title"],
            stock_ratio,
            str(p["issues"]),
            str(p["reservations"]),
            f"{p['demand_index']}/100",
            p["classification"],
            p["action"]
        ])
    print_table(headers, rows)
