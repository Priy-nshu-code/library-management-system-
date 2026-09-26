"""
Member Operations Module
Implements user-facing workflows:
- Catalog viewing with pagination (slicing)
- Multi-field Search and Book Details
- Book Issue & Return (with overdue calculation & reservation hand-off)
- Active Loans & Borrowing History
- Fine Management
- Book Reservation & Renewal
- Wishlist / Favourites
- Ratings & Reviews
- Digital Library Card & Notifications
- AI Recommendation & Semantic Search interface
"""

from datetime import datetime, timedelta
from data_store import db
from auth import CurrentSession
from ui import Colors, print_header, print_alert, print_table, paginate_and_display, render_digital_card
from ai_features import (
    recommend_books_for_member,
    semantic_natural_language_search,
    fetch_external_openlibrary_recommendations,
    calculate_average_rating
)

# Reference date for consistent hackathon demo calculations
TODAY_STR = "2026-09-26"
DAILY_FINE_RATE = 5.0  # Rs. 5 or $5 per day overdue
MAX_ACTIVE_BORROWS = 3


def parse_date(date_str: str) -> datetime:
    """Parses standard YYYY-MM-DD string into datetime."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def check_and_update_overdue_status():
    """
    Scans active transactions and updates status to OVERDUE if current date > due_date,
    computing the calculated fine dynamically.
    """
    today = parse_date(TODAY_STR)
    for txn in db.transactions:
        if txn.get("status") in ("ISSUED", "OVERDUE") and not txn.get("return_date"):
            due = parse_date(txn["due_date"])
            if today > due:
                overdue_days = (today - due).days
                txn["status"] = "OVERDUE"
                txn["fine_amount"] = float(overdue_days * DAILY_FINE_RATE)


# -------------------------------------------------------------
# 1. CATALOG & SEARCH
# -------------------------------------------------------------

def view_catalogue():
    """Displays entire book catalog in paginated view using list slicing."""
    check_and_update_overdue_status()
    books_list = list(db.books.values())
    if not books_list:
        print_alert("The library catalogue is currently empty.", "warning")
        return

    def catalog_formatter(page_items):
        headers = ["ID", "Title", "Author", "Category", "Available", "Total", "Rating"]
        rows = []
        for b in page_items:
            avail_str = f"{b['available_copies']} in stock" if b['available_copies'] > 0 else "OUT OF STOCK"
            rating = f"{calculate_average_rating(b['id']):.1f}★"
            rows.append([
                b["id"],
                b["title"],
                b["author"],
                b["category"],
                avail_str,
                str(b["total_copies"]),
                rating
            ])
        print_table(headers, rows)

    paginate_and_display(books_list, page_size=5, display_title="Book Catalogue", formatter_fn=catalog_formatter)


def search_books():
    """Search book catalogue by Title, Author, Category, or Book ID."""
    print_header("Search Book Catalogue", "Filter by Title, Author, Category, or Book ID")
    print(f" {Colors.CYAN}[1]{Colors.RESET} Search by Title")
    print(f" {Colors.CYAN}[2]{Colors.RESET} Search by Author")
    print(f" {Colors.CYAN}[3]{Colors.RESET} Search by Category")
    print(f" {Colors.CYAN}[4]{Colors.RESET} Search by Book ID")
    print(f" {Colors.RED}[B]{Colors.RESET} Back")

    choice = input(f"\n{Colors.BOLD}Select search criteria: {Colors.RESET}").strip()
    if choice.upper() == "B" or not choice:
        return

    query = input(f"{Colors.BOLD}Enter search query: {Colors.RESET}").strip().lower()
    if not query:
        print_alert("Search query cannot be empty.", "warning")
        return

    results = []
    for b_id, book in db.books.items():
        if choice == "1" and query in book["title"].lower():
            results.append(book)
        elif choice == "2" and query in book["author"].lower():
            results.append(book)
        elif choice == "3" and query in book["category"].lower():
            results.append(book)
        elif choice == "4" and query == b_id.lower():
            results.append(book)

    if not results:
        print_alert(f"No books found matching '{query}'.", "warning")
        return

    print_header(f"Search Results ({len(results)} matches found)")
    headers = ["ID", "Title", "Author", "Category", "Available / Total"]
    rows = [[b["id"], b["title"], b["author"], b["category"], f"{b['available_copies']}/{b['total_copies']}"] for b in results]
    print_table(headers, rows)

    view_detail_choice = input(f"\n{Colors.BOLD}Enter Book ID for full details (or press Enter to return): {Colors.RESET}").strip().upper()
    if view_detail_choice and view_detail_choice in db.books:
        view_book_details(view_detail_choice)


def view_book_details(book_id: str = None):
    """Displays comprehensive book details, inventory, tags, and reviews."""
    if not book_id:
        book_id = input(f"{Colors.BOLD}Enter Book ID (e.g., B101): {Colors.RESET}").strip().upper()

    if book_id not in db.books:
        print_alert(f"Book ID '{book_id}' does not exist.", "error")
        return

    book = db.books[book_id]
    avail_status = f"{Colors.GREEN}AVAILABLE ({book['available_copies']} copies){Colors.RESET}" if book["available_copies"] > 0 else f"{Colors.RED}OUT OF STOCK (0 copies){Colors.RESET}"
    avg_rating = calculate_average_rating(book_id)

    print_header(f"Book Details: {book['title']}")
    print(f" {Colors.BOLD}Book ID        :{Colors.RESET} {book['id']}")
    print(f" {Colors.BOLD}Title          :{Colors.RESET} {Colors.CYAN}{book['title']}{Colors.RESET}")
    print(f" {Colors.BOLD}Author         :{Colors.RESET} {book['author']}")
    print(f" {Colors.BOLD}Category       :{Colors.RESET} {book['category']}")
    print(f" {Colors.BOLD}Availability   :{Colors.RESET} {avail_status}")
    print(f" {Colors.BOLD}Total Copies   :{Colors.RESET} {book['total_copies']}")
    print(f" {Colors.BOLD}Available      :{Colors.RESET} {book['available_copies']}")
    print(f" {Colors.BOLD}Issue Count    :{Colors.RESET} {book.get('issue_count', 0)} times borrowed")
    print(f" {Colors.BOLD}Average Rating :{Colors.RESET} {Colors.YELLOW}{avg_rating:.1f} / 5.0 ★{Colors.RESET}")
    print(f" {Colors.BOLD}Topics / Tags  :{Colors.RESET} {', '.join(book.get('tags', []))}")

    # Display Reviews (slicing latest 3 reviews)
    book_reviews = [r for r in db.reviews if r.get("book_id") == book_id]
    print(f"\n {Colors.BOLD}{Colors.HEADER}--- Member Reviews & Ratings ({len(book_reviews)}) ---{Colors.RESET}")
    if not book_reviews:
        print(f"  {Colors.DIM}No member reviews yet. Be the first to review!{Colors.RESET}")
    else:
        # Slicing: show up to 3 most recent reviews
        for rev in book_reviews[-3:]:
            stars = "★" * rev["rating"] + "☆" * (5 - rev["rating"])
            print(f"  • {Colors.YELLOW}{stars}{Colors.RESET} by {Colors.BOLD}{rev['member_name']}{Colors.RESET} ({rev['date']}):")
            print(f"    \"{rev['comment']}\"")


# -------------------------------------------------------------
# 2. BORROW / ISSUE & RETURN
# -------------------------------------------------------------

def issue_book():
    """Member borrows an available book."""
    member = CurrentSession.user
    if not member:
        print_alert("Please log in to borrow books.", "error")
        return

    check_and_update_overdue_status()

    # Check active loans count
    active_loans = [t for t in db.transactions if t.get("member_id") == member["id"] and not t.get("return_date")]
    if len(active_loans) >= MAX_ACTIVE_BORROWS:
        print_alert(f"Borrow limit reached! You already have {len(active_loans)} active books (Max: {MAX_ACTIVE_BORROWS}).", "warning")
        return

    # Check if user has overdue books with unpaid fines
    overdue_loans = [t for t in active_loans if t.get("status") == "OVERDUE"]
    if overdue_loans:
        print_alert("You have overdue books! Please return overdue books before borrowing new ones.", "warning")
        return

    book_id = input(f"{Colors.BOLD}Enter Book ID to borrow (e.g., B101): {Colors.RESET}").strip().upper()
    if book_id not in db.books:
        print_alert("Invalid Book ID. Please check the catalogue.", "error")
        return

    # Check if member already has this active book
    if any(t["book_id"] == book_id for t in active_loans):
        print_alert("You already have an active loan for this book.", "warning")
        return

    book = db.books[book_id]
    if book["available_copies"] <= 0:
        print_alert(f"'{book['title']}' is currently out of stock!", "warning")
        res_choice = input(f"{Colors.BOLD}Would you like to reserve this book? (y/n): {Colors.RESET}").strip().lower()
        if res_choice == "y":
            reserve_book(book_id)
        return

    # Proceed with checkout
    book["available_copies"] -= 1
    book["issue_count"] = book.get("issue_count", 0) + 1
    member["total_borrowed_count"] = member.get("total_borrowed_count", 0) + 1

    issue_date = parse_date(TODAY_STR)
    due_date = issue_date + timedelta(days=14)

    new_txn = {
        "txn_id": db.generate_txn_id(),
        "book_id": book_id,
        "book_title": book["title"],
        "member_id": member["id"],
        "member_name": member["name"],
        "issue_date": TODAY_STR,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "return_date": None,
        "status": "ISSUED",
        "fine_amount": 0.0,
        "fine_paid": False
    }

    db.transactions.append(new_txn)
    db.save()

    print_alert(f"Book '{book['title']}' issued successfully! Due Date: {new_txn['due_date']}", "success")


def return_book():
    """Member returns a borrowed book and calculates fine if overdue."""
    member = CurrentSession.user
    if not member:
        return

    check_and_update_overdue_status()

    # Active loans for current member
    active_loans = [t for t in db.transactions if t.get("member_id") == member["id"] and not t.get("return_date")]
    if not active_loans:
        print_alert("You do not have any active borrowed books to return.", "info")
        return

    print_header("Select Book to Return")
    headers = ["#", "Txn ID", "Book ID", "Title", "Due Date", "Status", "Fine"]
    rows = []
    for idx, t in enumerate(active_loans, start=1):
        fine_str = f"Rs. {t['fine_amount']:.2f}" if t['fine_amount'] > 0 else "Rs. 0.00"
        rows.append([str(idx), t["txn_id"], t["book_id"], t["book_title"], t["due_date"], t["status"], fine_str])
    print_table(headers, rows)

    choice = input(f"\n{Colors.BOLD}Enter number of the book to return (or 'B' to cancel): {Colors.RESET}").strip()
    if choice.upper() == "B" or not choice.isdigit():
        return

    selected_idx = int(choice) - 1
    if selected_idx < 0 or selected_idx >= len(active_loans):
        print_alert("Invalid selection number.", "error")
        return

    txn = active_loans[selected_idx]
    book_id = txn["book_id"]

    # Mark as returned
    txn["return_date"] = TODAY_STR
    txn["status"] = "RETURNED"

    # Restock copy
    if book_id in db.books:
        db.books[book_id]["available_copies"] += 1

    # Overdue fine handling
    if txn["fine_amount"] > 0 and not txn["fine_paid"]:
        print_alert(f"This book was returned late! Outstanding fine: Rs. {txn['fine_amount']:.2f}", "warning")
        pay = input(f"{Colors.BOLD}Would you like to pay the fine now? (y/n): {Colors.RESET}").strip().lower()
        if pay == "y":
            txn["fine_paid"] = True
            print_alert(f"Payment of Rs. {txn['fine_amount']:.2f} received. Fine cleared!", "success")
        else:
            print_alert("Fine recorded in your account. Please clear it soon.", "info")
    else:
        print_alert("Book returned on time! Thank you.", "success")

    # Check for waiting reservations
    pending_reservations = [r for r in db.reservations if r["book_id"] == book_id and r["status"] == "PENDING"]
    if pending_reservations:
        next_reservation = pending_reservations[0]
        next_reservation["status"] = "FULFILLED"
        notif_msg = f"Good news! '{txn['book_title']}' reserved by you is now available for borrowing."
        db.notifications.setdefault(next_reservation["member_id"], []).append({
            "id": f"NOTIF_RES_{next_reservation['res_id']}",
            "message": notif_msg,
            "date": TODAY_STR,
            "read": False,
            "type": "RESERVATION_READY"
        })
        print_alert(f"Notification triggered for Member ID {next_reservation['member_id']} (Reservation fulfilled)!", "ai")

    db.save()

    # Prompt for optional review
    rev_choice = input(f"\n{Colors.BOLD}Would you like to leave a review & rating for this book? (y/n): {Colors.RESET}").strip().lower()
    if rev_choice == "y":
        add_book_review(book_id)


# -------------------------------------------------------------
# 3. MY BORROWED BOOKS & HISTORY
# -------------------------------------------------------------

def view_my_borrowed_books():
    """Displays active borrowed books for current member."""
    member = CurrentSession.user
    check_and_update_overdue_status()

    active_loans = [t for t in db.transactions if t.get("member_id") == member["id"] and not t.get("return_date")]
    print_header(f"My Borrowed Books ({len(active_loans)} active)")

    if not active_loans:
        print_alert("You have no active borrowed books.", "info")
        return

    headers = ["Book ID", "Title", "Issue Date", "Due Date", "Status", "Fine"]
    rows = []
    for t in active_loans:
        status_disp = f"{Colors.RED}OVERDUE{Colors.RESET}" if t["status"] == "OVERDUE" else f"{Colors.GREEN}ACTIVE{Colors.RESET}"
        rows.append([
            t["book_id"],
            t["book_title"],
            t["issue_date"],
            t["due_date"],
            status_disp,
            f"Rs. {t['fine_amount']:.2f}"
        ])
    print_table(headers, rows)


def view_borrowing_history():
    """Displays past returned loans using list slicing."""
    member = CurrentSession.user
    history = [t for t in db.transactions if t.get("member_id") == member["id"] and t.get("return_date")]

    print_header(f"Borrowing History ({len(history)} books returned)")
    if not history:
        print_alert("No past borrowing history found.", "info")
        return

    # Slicing: show history in reverse chronological order
    reversed_history = history[::-1]

    def history_formatter(page_items):
        headers = ["Txn ID", "Book ID", "Title", "Issue Date", "Return Date", "Fine Status"]
        rows = []
        for t in page_items:
            fine_status = "Cleared" if t.get("fine_paid", True) else f"Pending Rs. {t['fine_amount']:.2f}"
            rows.append([
                t["txn_id"],
                t["book_id"],
                t["book_title"],
                t["issue_date"],
                t["return_date"],
                fine_status
            ])
        print_table(headers, rows)

    paginate_and_display(reversed_history, page_size=5, display_title="Past Borrowing History", formatter_fn=history_formatter)


def view_and_pay_fines():
    """Displays member's outstanding fines with payment simulation."""
    member = CurrentSession.user
    check_and_update_overdue_status()

    unpaid_txns = [t for t in db.transactions if t.get("member_id") == member["id"] and t.get("fine_amount", 0) > 0 and not t.get("fine_paid", False)]
    total_unpaid = sum(t["fine_amount"] for t in unpaid_txns)

    print_header("Fines & Penalties Account")
    print(f" {Colors.BOLD}Total Outstanding Fine:{Colors.RESET} {Colors.RED}Rs. {total_unpaid:.2f}{Colors.RESET}\n")

    if not unpaid_txns:
        print_alert("You have no pending fines! Your account is in good standing.", "success")
        return

    headers = ["Txn ID", "Book Title", "Due Date", "Days Late", "Fine Amount"]
    rows = []
    for t in unpaid_txns:
        due = parse_date(t["due_date"])
        ref_date = parse_date(t["return_date"]) if t.get("return_date") else parse_date(TODAY_STR)
        days_late = max((ref_date - due).days, 0)
        rows.append([t["txn_id"], t["book_title"], t["due_date"], str(days_late), f"Rs. {t['fine_amount']:.2f}"])
    print_table(headers, rows)

    pay_choice = input(f"\n{Colors.BOLD}Would you like to pay all outstanding fines now? (y/n): {Colors.RESET}").strip().lower()
    if pay_choice == "y":
        for t in unpaid_txns:
            t["fine_paid"] = True
        db.save()
        print_alert(f"Payment of Rs. {total_unpaid:.2f} successfully processed! All fines cleared.", "success")


# -------------------------------------------------------------
# 4. BONUS USER FEATURES
# -------------------------------------------------------------

def reserve_book(book_id: str = None):
    """Reserves an out-of-stock book for the member."""
    member = CurrentSession.user
    if not book_id:
        book_id = input(f"{Colors.BOLD}Enter Book ID to reserve: {Colors.RESET}").strip().upper()

    if book_id not in db.books:
        print_alert("Book ID not found.", "error")
        return

    book = db.books[book_id]
    if book["available_copies"] > 0:
        print_alert(f"'{book['title']}' currently has {book['available_copies']} copies available. You can borrow it directly!", "info")
        return

    # Check existing active reservation
    existing = any(r["book_id"] == book_id and r["member_id"] == member["id"] and r["status"] == "PENDING" for r in db.reservations)
    if existing:
        print_alert("You already have an active pending reservation for this book.", "warning")
        return

    new_res = {
        "res_id": db.generate_res_id(),
        "book_id": book_id,
        "member_id": member["id"],
        "reserved_at": TODAY_STR,
        "status": "PENDING"
    }
    db.reservations.append(new_res)
    db.save()
    print_alert(f"Reservation placed successfully for '{book['title']}'. You will be notified when a copy is returned!", "success")


def renew_borrowed_book():
    """Renews a borrowed book by extending due date by 7 days."""
    member = CurrentSession.user
    check_and_update_overdue_status()

    active_loans = [t for t in db.transactions if t.get("member_id") == member["id"] and not t.get("return_date")]
    if not active_loans:
        print_alert("You have no active loans to renew.", "info")
        return

    print_header("Select Book to Renew (+7 Days Extension)")
    headers = ["#", "Book ID", "Title", "Current Due Date", "Status"]
    rows = [[str(i), t["book_id"], t["book_title"], t["due_date"], t["status"]] for i, t in enumerate(active_loans, start=1)]
    print_table(headers, rows)

    choice = input(f"\n{Colors.BOLD}Enter number to renew (or 'B' to back): {Colors.RESET}").strip()
    if choice.upper() == "B" or not choice.isdigit():
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(active_loans):
        print_alert("Invalid selection.", "error")
        return

    txn = active_loans[idx]
    if txn["status"] == "OVERDUE":
        print_alert("Cannot renew an overdue book! Please return it and settle the fine.", "error")
        return

    # Check if someone else reserved it
    has_reservation = any(r["book_id"] == txn["book_id"] and r["status"] == "PENDING" and r["member_id"] != member["id"] for r in db.reservations)
    if has_reservation:
        print_alert("Cannot renew: Another member has reserved this book. Please return it on time.", "warning")
        return

    curr_due = parse_date(txn["due_date"])
    new_due = curr_due + timedelta(days=7)
    txn["due_date"] = new_due.strftime("%Y-%m-%d")
    db.save()
    print_alert(f"Book '{txn['book_title']}' renewed! New Due Date: {txn['due_date']}", "success")


def manage_wishlist():
    """Manage wishlist / favourite books."""
    member = CurrentSession.user
    mem_id = member["id"]
    wishlist = db.wishlists.setdefault(mem_id, [])

    while True:
        print_header("My Favourites / Wishlist", f"{len(wishlist)} saved books")
        if not wishlist:
            print_alert("Your wishlist is currently empty.", "info")
        else:
            headers = ["#", "Book ID", "Title", "Category", "Availability"]
            rows = []
            for idx, b_id in enumerate(wishlist, start=1):
                b = db.books.get(b_id, {})
                avail = f"{b.get('available_copies', 0)} in stock" if b.get('available_copies', 0) > 0 else "Out of Stock"
                rows.append([str(idx), b_id, b.get("title", "Unknown"), b.get("category", "General"), avail])
            print_table(headers, rows)

        print(f"\n {Colors.CYAN}[1]{Colors.RESET} Add Book to Wishlist")
        print(f" {Colors.CYAN}[2]{Colors.RESET} Remove Book from Wishlist")
        print(f" {Colors.RED}[B]{Colors.RESET} Back")

        choice = input(f"\n{Colors.BOLD}Enter choice: {Colors.RESET}").strip().upper()
        if choice == "1":
            b_id = input(f"{Colors.BOLD}Enter Book ID to add: {Colors.RESET}").strip().upper()
            if b_id not in db.books:
                print_alert("Book ID not found.", "error")
            elif b_id in wishlist:
                print_alert("Book is already in your wishlist.", "warning")
            else:
                wishlist.append(b_id)
                db.save()
                print_alert(f"Added '{db.books[b_id]['title']}' to your wishlist!", "success")
        elif choice == "2":
            b_id = input(f"{Colors.BOLD}Enter Book ID to remove: {Colors.RESET}").strip().upper()
            if b_id in wishlist:
                wishlist.remove(b_id)
                db.save()
                print_alert("Book removed from wishlist.", "success")
            else:
                print_alert("Book is not in your wishlist.", "error")
        elif choice == "B" or not choice:
            break


def add_book_review(book_id: str = None):
    """Submits a rating and review for a book."""
    member = CurrentSession.user
    if not book_id:
        book_id = input(f"{Colors.BOLD}Enter Book ID to review: {Colors.RESET}").strip().upper()

    if book_id not in db.books:
        print_alert("Book ID not found.", "error")
        return

    book = db.books[book_id]
    print(f"\n{Colors.CYAN}Reviewing: {Colors.BOLD}{book['title']}{Colors.RESET}")
    rating_str = input(f"{Colors.BOLD}Enter rating (1 to 5 stars): {Colors.RESET}").strip()
    if not rating_str.isdigit() or int(rating_str) not in range(1, 6):
        print_alert("Invalid rating. Must be an integer from 1 to 5.", "error")
        return

    comment = input(f"{Colors.BOLD}Write your review: {Colors.RESET}").strip()
    if not comment:
        comment = "Good book."

    new_review = {
        "review_id": db.generate_review_id(),
        "book_id": book_id,
        "member_id": member["id"],
        "member_name": member["name"],
        "rating": int(rating_str),
        "comment": comment,
        "date": TODAY_STR
    }
    db.reviews.append(new_review)
    db.save()
    print_alert("Thank you! Your review and rating have been recorded.", "success")


def view_notifications():
    """Displays member notifications and marks them as read."""
    member = CurrentSession.user
    notifs = db.notifications.setdefault(member["id"], [])

    print_header("Notifications Inbox", f"{len(notifs)} messages")
    if not notifs:
        print_alert("You have no notifications.", "info")
        return

    headers = ["#", "Date", "Type", "Status", "Message"]
    rows = []
    for idx, n in enumerate(notifs, start=1):
        status_disp = f"{Colors.GREEN}NEW{Colors.RESET}" if not n.get("read") else f"{Colors.DIM}READ{Colors.RESET}"
        rows.append([str(idx), n.get("date", TODAY_STR), n.get("type", "INFO"), status_disp, n.get("message", "")])
    print_table(headers, rows)

    # Mark all as read
    for n in notifs:
        n["read"] = True
    db.save()
    input(f"\n{Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


def show_digital_library_card():
    """Renders the member's official ASCII digital library card."""
    member = CurrentSession.user
    active_loans = [t for t in db.transactions if t.get("member_id") == member["id"] and not t.get("return_date")]
    render_digital_card(member, len(active_loans))
    input(f"\n{Colors.DIM}Press Enter to return to menu...{Colors.RESET}")


# -------------------------------------------------------------
# 5. AI MEMBER FEATURES
# -------------------------------------------------------------

def show_smart_recommendations():
    """Presents AI personalized recommendations for the logged-in member."""
    member = CurrentSession.user
    print_header("AI Smart Recommendation Engine", "Personalized Next Reads based on your profile & peer affinity")

    recommendations = recommend_books_for_member(member["id"])
    if not recommendations:
        print_alert("No tailored recommendations available yet. Try borrowing a few books first!", "info")
    else:
        headers = ["ID", "Title", "Category", "Match Reason", "AI Score", "In Stock"]
        rows = []
        for r in recommendations:
            b = r["book"]
            stock_badge = f"{Colors.GREEN}YES{Colors.RESET}" if r["available"] else f"{Colors.RED}NO (Reserve){Colors.RESET}"
            rows.append([
                b["id"],
                b["title"],
                b["category"],
                r["reason"],
                str(r["score"]),
                stock_badge
            ])
        print_table(headers, rows)

    print(f"\n {Colors.CYAN}[1]{Colors.RESET} Live Web API Discovery (Open Library API query)")
    print(f" {Colors.CYAN}[2]{Colors.RESET} Borrow a recommended book")
    print(f" {Colors.RED}[B]{Colors.RESET} Back")

    choice = input(f"\n{Colors.BOLD}Enter choice: {Colors.RESET}").strip().upper()
    if choice == "1":
        query = input(f"{Colors.BOLD}Enter topic for live AI API book search (e.g. 'deep learning'): {Colors.RESET}").strip()
        if query:
            print_alert("Connecting to Open Library live endpoint via Python urllib...", "ai")
            api_results = fetch_external_openlibrary_recommendations(query)
            if api_results:
                headers = ["Title", "Author(s)", "First Published", "Data Source"]
                rows = [[item["title"], item["author"], item["year"], item["source"]] for item in api_results]
                print_table(headers, rows)
            else:
                print_alert("Could not reach external API. (Offline/network timeout). Local AI models remain active!", "warning")
    elif choice == "2":
        issue_book()


def natural_language_search_menu():
    """Natural Language & Semantic book search interface."""
    print_header("AI Semantic / Natural Language Search", "Search using conversational sentences or topic descriptions")
    print(f"{Colors.DIM}Example queries:{Colors.RESET}")
    print(f"  • 'I am a beginner wanting to learn coding and algorithms'")
    print(f"  • 'Looking for database storage, sql indexing and acid transactions'")
    print(f"  • 'Books about clean code refactoring and software architecture'\n")

    query = input(f"{Colors.BOLD}Enter your natural search query: {Colors.RESET}").strip()
    if not query:
        return

    print_alert("Tokenizing query, expanding domain ontology, and scoring relevance...", "ai")
    matches = semantic_natural_language_search(query)

    if not matches:
        print_alert("No semantic matches found. Try rewording your prompt.", "warning")
        return

    headers = ["ID", "Title", "Category", "Confidence", "Semantic Match Insights"]
    rows = []
    for m in matches:
        b = m["book"]
        conf_str = f"{Colors.GREEN}{m['confidence']}%{Colors.RESET}"
        rows.append([b["id"], b["title"], b["category"], conf_str, m["reason"]])
    print_table(headers, rows)

    view_choice = input(f"\n{Colors.BOLD}Enter Book ID to view details or borrow (or Enter to back): {Colors.RESET}").strip().upper()
    if view_choice and view_choice in db.books:
        view_book_details(view_choice)
