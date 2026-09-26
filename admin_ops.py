"""
Admin / Librarian Operations Module
Implements:
1. Book Management (Add, View, Search, Update, Delete, Manage Quantity, Manage Categories)
2. Member Management (Register, View, Search, Update, Delete/Deactivate)
3. Transaction Management (Issue, Return, View Issued, View Returned, View Overdue)
"""

from data_store import db
from auth import register_member, validate_email, validate_phone
from ui import Colors, print_header, print_alert, print_table, paginate_and_display
from member_ops import check_and_update_overdue_status, TODAY_STR, parse_date
from ai_features import recommend_tags_for_book


# -------------------------------------------------------------
# 1. BOOK MANAGEMENT
# -------------------------------------------------------------

def add_book():
    """Adds a new book title to the catalog with AI smart tag recommendations."""
    print_header("Add New Book")
    title = input(f"{Colors.BOLD}Enter Book Title: {Colors.RESET}").strip()
    if not title:
        print_alert("Title cannot be empty.", "error")
        return

    author = input(f"{Colors.BOLD}Enter Author: {Colors.RESET}").strip()
    if not author:
        print_alert("Author cannot be empty.", "error")
        return

    category = input(f"{Colors.BOLD}Enter Category (e.g. Programming, Database): {Colors.RESET}").strip()
    if not category:
        category = "General"

    copies_str = input(f"{Colors.BOLD}Enter Total Copies (default 5): {Colors.RESET}").strip()
    copies = int(copies_str) if copies_str.isdigit() and int(copies_str) > 0 else 5

    # AI Horizon: Smart tag generator
    suggested_tags = recommend_tags_for_book(title, category)
    print_alert(f"AI recommended semantic tags: {', '.join(suggested_tags)}", "ai")
    custom_tags_input = input(f"{Colors.BOLD}Accept AI tags? (Press Enter to accept or enter comma-separated tags): {Colors.RESET}").strip()
    if custom_tags_input:
        final_tags = [t.strip().lower() for t in custom_tags_input.split(",") if t.strip()]
    else:
        final_tags = suggested_tags

    new_id = db.generate_book_id()
    new_book = {
        "id": new_id,
        "title": title,
        "author": author,
        "category": category,
        "total_copies": copies,
        "available_copies": copies,
        "tags": final_tags,
        "issue_count": 0,
        "added_date": TODAY_STR
    }

    db.books[new_id] = new_book
    db.save()
    print_alert(f"Book '{title}' successfully registered with ID {new_id}!", "success")


def view_all_books():
    """Displays all books with administrative columns and pagination (slicing)."""
    books = list(db.books.values())
    if not books:
        print_alert("No books found.", "info")
        return

    def book_formatter(page_items):
        headers = ["ID", "Title", "Author", "Category", "Copies (Avail/Total)", "Times Borrowed"]
        rows = []
        for b in page_items:
            copies_str = f"{b['available_copies']}/{b['total_copies']}"
            rows.append([b["id"], b["title"], b["author"], b["category"], copies_str, str(b.get("issue_count", 0))])
        print_table(headers, rows)

    paginate_and_display(books, page_size=6, display_title="All Books Catalog (Librarian View)", formatter_fn=book_formatter)


def update_book():
    """Updates existing book metadata (Title, Author, Category)."""
    b_id = input(f"{Colors.BOLD}Enter Book ID to update (e.g. B101): {Colors.RESET}").strip().upper()
    if b_id not in db.books:
        print_alert("Book ID not found.", "error")
        return

    book = db.books[b_id]
    print_header(f"Updating Book: {book['title']} ({b_id})")
    print(f"{Colors.DIM}Leave blank to retain current value.{Colors.RESET}\n")

    new_title = input(f"New Title [{book['title']}]: ").strip()
    if new_title:
        book["title"] = new_title

    new_author = input(f"New Author [{book['author']}]: ").strip()
    if new_author:
        book["author"] = new_author

    new_cat = input(f"New Category [{book['category']}]: ").strip()
    if new_cat:
        book["category"] = new_cat

    db.save()
    print_alert(f"Book '{b_id}' updated successfully.", "success")


def delete_book():
    """Deletes a book if it has zero active loans."""
    b_id = input(f"{Colors.BOLD}Enter Book ID to delete: {Colors.RESET}").strip().upper()
    if b_id not in db.books:
        print_alert("Book ID not found.", "error")
        return

    book = db.books[b_id]
    # Safety Check: Cannot delete if any copy is currently out on loan
    active_loans = [t for t in db.transactions if t.get("book_id") == b_id and not t.get("return_date")]
    if active_loans:
        print_alert(f"Cannot delete book '{book['title']}'! There are {len(active_loans)} active loans currently out.", "error")
        return

    confirm = input(f"{Colors.RED}{Colors.BOLD}Are you sure you want to delete '{book['title']}'? (yes/no): {Colors.RESET}").strip().lower()
    if confirm == "yes":
        del db.books[b_id]
        # Clean up wishlists
        for mem_id, wishlist in db.wishlists.items():
            if b_id in wishlist:
                wishlist.remove(b_id)
        db.save()
        print_alert(f"Book '{b_id}' permanently deleted from system.", "success")
    else:
        print_alert("Deletion cancelled.", "info")


def manage_quantity():
    """Adjusts physical stock quantity of a book."""
    b_id = input(f"{Colors.BOLD}Enter Book ID to adjust stock: {Colors.RESET}").strip().upper()
    if b_id not in db.books:
        print_alert("Book ID not found.", "error")
        return

    book = db.books[b_id]
    total = book["total_copies"]
    avail = book["available_copies"]
    borrowed = total - avail

    print_header(f"Stock Manager: {book['title']}")
    print(f" Total copies: {total} | Available copies: {avail} | Currently Loaned: {borrowed}")
    print(f" {Colors.CYAN}[1]{Colors.RESET} Add copies")
    print(f" {Colors.CYAN}[2]{Colors.RESET} Remove copies")
    print(f" {Colors.RED}[B]{Colors.RESET} Cancel")

    action = input(f"{Colors.BOLD}Enter choice: {Colors.RESET}").strip().upper()
    if action == "1":
        qty_str = input(f"{Colors.BOLD}Enter number of copies to add: {Colors.RESET}").strip()
        if qty_str.isdigit() and int(qty_str) > 0:
            qty = int(qty_str)
            book["total_copies"] += qty
            book["available_copies"] += qty
            db.save()
            print_alert(f"Added {qty} copies. New total: {book['total_copies']}.", "success")
    elif action == "2":
        qty_str = input(f"{Colors.BOLD}Enter number of copies to remove: {Colors.RESET}").strip()
        if qty_str.isdigit() and int(qty_str) > 0:
            qty = int(qty_str)
            if qty > avail:
                print_alert(f"Cannot remove {qty} copies! Only {avail} unloaned copies are currently on shelves.", "error")
            else:
                book["total_copies"] -= qty
                book["available_copies"] -= qty
                db.save()
                print_alert(f"Removed {qty} copies. New total: {book['total_copies']}.", "success")


def manage_categories():
    """Displays all unique categories and allows category renaming."""
    categories = {}
    for b in db.books.values():
        c = b.get("category", "General")
        categories[c] = categories.get(c, 0) + 1

    print_header("Category Management", f"{len(categories)} unique categories")
    headers = ["#", "Category Name", "Total Book Titles"]
    rows = [[str(idx), cat, str(cnt)] for idx, (cat, cnt) in enumerate(categories.items(), start=1)]
    print_table(headers, rows)

    rename_choice = input(f"\n{Colors.BOLD}Would you like to rename a category across all books? (y/n): {Colors.RESET}").strip().lower()
    if rename_choice == "y":
        old_cat = input(f"{Colors.BOLD}Enter exact existing category name: {Colors.RESET}").strip()
        matching = [b for b in db.books.values() if b.get("category", "").lower() == old_cat.lower()]
        if not matching:
            print_alert(f"Category '{old_cat}' not found.", "error")
            return

        new_cat = input(f"{Colors.BOLD}Enter new category name: {Colors.RESET}").strip()
        if new_cat:
            for b in matching:
                b["category"] = new_cat
            db.save()
            print_alert(f"Successfully updated {len(matching)} books from '{old_cat}' to '{new_cat}'.", "success")


# -------------------------------------------------------------
# 2. MEMBER MANAGEMENT
# -------------------------------------------------------------

def register_member_admin():
    """Allows Admin to register a new member or administrator."""
    print_header("Register New User (Librarian Desk)")
    name = input(f"{Colors.BOLD}Full Name: {Colors.RESET}").strip()
    phone = input(f"{Colors.BOLD}Phone (10 digits): {Colors.RESET}").strip()
    email = input(f"{Colors.BOLD}Email: {Colors.RESET}").strip()
    pin = input(f"{Colors.BOLD}Initial PIN/Password (min 4 chars): {Colors.RESET}").strip()

    print(f"\nSelect Account Role:")
    print(f" {Colors.CYAN}[1]{Colors.RESET} Standard Member")
    print(f" {Colors.CYAN}[2]{Colors.RESET} Administrator / Librarian")
    role_choice = input(f"{Colors.BOLD}Choice (default 1): {Colors.RESET}").strip()
    role = "admin" if role_choice == "2" else "member"

    success, msg, member = register_member(name, phone, email, pin, role=role)
    if success:
        role_label = "Administrator" if role == "admin" else "Member"
        print_alert(f"{role_label} successfully registered! ID: {member['id']}", "success")
    else:
        print_alert(msg, "error")


def view_all_members():
    """Lists all members using slicing for pagination."""
    members = list(db.members.values())
    if not members:
        print_alert("No registered members.", "info")
        return

    def member_formatter(page_items):
        headers = ["Member ID", "Name", "Phone", "Email", "Role", "Status", "All-time Loans"]
        rows = []
        for m in page_items:
            status_disp = f"{Colors.GREEN}ACTIVE{Colors.RESET}" if m.get("status") == "active" else f"{Colors.RED}DISABLED{Colors.RESET}"
            rows.append([
                m["id"],
                m["name"],
                m["phone"],
                m["email"],
                m.get("role", "member").upper(),
                status_disp,
                str(m.get("total_borrowed_count", 0))
            ])
        print_table(headers, rows)

    paginate_and_display(members, page_size=5, display_title="Registered Members Directory", formatter_fn=member_formatter)


def search_members():
    """Searches member records by ID, Name, Phone, or Email."""
    query = input(f"{Colors.BOLD}Enter Member search term (ID, Name, Phone, or Email): {Colors.RESET}").strip().lower()
    if not query:
        return

    results = []
    for m in db.members.values():
        if (query in m["id"].lower() or
            query in m["name"].lower() or
            query in m["phone"] or
            query in m["email"].lower()):
            results.append(m)

    if not results:
        print_alert(f"No members found matching '{query}'.", "warning")
        return

    headers = ["Member ID", "Name", "Phone", "Email", "Status", "Role"]
    rows = [[m["id"], m["name"], m["phone"], m["email"], m.get("status", "active"), m.get("role", "member")] for m in results]
    print_table(headers, rows)


def update_member():
    """Updates member personal details."""
    mem_id = input(f"{Colors.BOLD}Enter Member ID to update (e.g. M101): {Colors.RESET}").strip().upper()
    if mem_id not in db.members:
        print_alert("Member ID not found.", "error")
        return

    mem = db.members[mem_id]
    print_header(f"Update Member: {mem['name']} ({mem_id})")

    new_name = input(f"New Name [{mem['name']}]: ").strip()
    if new_name:
        mem["name"] = new_name

    new_phone = input(f"New Phone [{mem['phone']}]: ").strip()
    if new_phone:
        if validate_phone(new_phone):
            mem["phone"] = new_phone
        else:
            print_alert("Invalid phone format. Kept previous phone.", "warning")

    new_email = input(f"New Email [{mem['email']}]: ").strip()
    if new_email:
        if validate_email(new_email):
            mem["email"] = new_email
        else:
            print_alert("Invalid email format. Kept previous email.", "warning")

    curr_role = mem.get("role", "member")
    role_input = input(f"Change Role [{curr_role}]? ([1] Member, [2] Admin, Enter to keep): ").strip()
    if role_input == "1":
        mem["role"] = "member"
    elif role_input == "2":
        mem["role"] = "admin"

    db.save()
    print_alert(f"Member {mem_id} updated successfully.", "success")


def delete_or_deactivate_member():
    """Deactivates a member account after checking for unreturned books and unpaid fines."""
    mem_id = input(f"{Colors.BOLD}Enter Member ID to deactivate/delete: {Colors.RESET}").strip().upper()
    if mem_id not in db.members:
        print_alert("Member ID not found.", "error")
        return

    member = db.members[mem_id]
    if member.get("role") == "admin":
        print_alert("Cannot deactivate primary administrator account.", "error")
        return

    # Check active loans
    active_loans = [t for t in db.transactions if t.get("member_id") == mem_id and not t.get("return_date")]
    if active_loans:
        print_alert(f"Cannot deactivate! Member has {len(active_loans)} unreturned books.", "error")
        return

    # Check pending fines
    unpaid_fines = [t for t in db.transactions if t.get("member_id") == mem_id and t.get("fine_amount", 0) > 0 and not t.get("fine_paid", False)]
    if unpaid_fines:
        print_alert(f"Cannot deactivate! Member has unpaid fines.", "error")
        return

    current_status = member.get("status", "active")
    new_status = "deactivated" if current_status == "active" else "active"
    action_label = "Deactivated" if new_status == "deactivated" else "Reactivated"

    confirm = input(f"{Colors.YELLOW}Change status of {member['name']} to '{new_status}'? (y/n): {Colors.RESET}").strip().lower()
    if confirm == "y":
        member["status"] = new_status
        db.save()
        print_alert(f"Member account {mem_id} {action_label}.", "success")


# -------------------------------------------------------------
# 3. TRANSACTION MANAGEMENT
# -------------------------------------------------------------

def admin_issue_book():
    """Admin desk checkout for any member."""
    mem_id = input(f"{Colors.BOLD}Enter Member ID: {Colors.RESET}").strip().upper()
    if mem_id not in db.members:
        print_alert("Member not found.", "error")
        return

    b_id = input(f"{Colors.BOLD}Enter Book ID: {Colors.RESET}").strip().upper()
    if b_id not in db.books:
        print_alert("Book not found.", "error")
        return

    book = db.books[b_id]
    if book["available_copies"] <= 0:
        print_alert(f"Book '{book['title']}' has no available copies.", "error")
        return

    member = db.members[mem_id]
    if member.get("status") == "deactivated":
        print_alert("Member account is deactivated.", "error")
        return

    # Deduct stock and increment issue count
    book["available_copies"] -= 1
    book["issue_count"] = book.get("issue_count", 0) + 1
    member["total_borrowed_count"] = member.get("total_borrowed_count", 0) + 1

    issue_dt = parse_date(TODAY_STR)
    from datetime import timedelta
    due_dt = issue_dt + timedelta(days=14)

    new_txn = {
        "txn_id": db.generate_txn_id(),
        "book_id": b_id,
        "book_title": book["title"],
        "member_id": mem_id,
        "member_name": member["name"],
        "issue_date": TODAY_STR,
        "due_date": due_dt.strftime("%Y-%m-%d"),
        "return_date": None,
        "status": "ISSUED",
        "fine_amount": 0.0,
        "fine_paid": False
    }

    db.transactions.append(new_txn)
    db.save()
    print_alert(f"Book '{book['title']}' issued to {member['name']} (Due: {new_txn['due_date']}).", "success")


def admin_return_book():
    """Admin desk check-in for returned books."""
    check_and_update_overdue_status()
    query = input(f"{Colors.BOLD}Enter Transaction ID or Book ID to return: {Colors.RESET}").strip().upper()
    if not query:
        return

    active_txns = [t for t in db.transactions if not t.get("return_date") and (t.get("txn_id") == query or t.get("book_id") == query)]
    if not active_txns:
        print_alert(f"No active loan found for identifier '{query}'.", "warning")
        return

    txn = active_txns[0]
    txn["return_date"] = TODAY_STR
    txn["status"] = "RETURNED"

    b_id = txn["book_id"]
    if b_id in db.books:
        db.books[b_id]["available_copies"] += 1

    print_alert(f"Book '{txn['book_title']}' successfully checked in!", "success")
    if txn.get("fine_amount", 0) > 0 and not txn.get("fine_paid"):
        print_alert(f"Overdue Fine: Rs. {txn['fine_amount']:.2f}", "warning")
        clear_fine = input(f"{Colors.BOLD}Mark fine as collected? (y/n): {Colors.RESET}").strip().lower()
        if clear_fine == "y":
            txn["fine_paid"] = True
            print_alert("Fine collected and cleared.", "success")

    # Check reservations
    pending = [r for r in db.reservations if r["book_id"] == b_id and r["status"] == "PENDING"]
    if pending:
        r = pending[0]
        r["status"] = "FULFILLED"
        db.notifications.setdefault(r["member_id"], []).append({
            "id": f"NOTIF_RES_{r['res_id']}",
            "message": f"Reserved book '{txn['book_title']}' is now available!",
            "date": TODAY_STR,
            "read": False,
            "type": "RESERVATION_READY"
        })
        print_alert(f"Reservation fulfilled for Member {r['member_id']}. Notification dispatched.", "ai")

    db.save()


def view_issued_books():
    """Lists all active loans currently circulating."""
    check_and_update_overdue_status()
    issued = [t for t in db.transactions if not t.get("return_date")]
    print_header(f"Currently Issued Books ({len(issued)} active loans)")

    if not issued:
        print_alert("No books are currently issued out.", "info")
        return

    headers = ["Txn ID", "Book ID", "Title", "Member ID", "Member Name", "Due Date", "Status"]
    rows = []
    for t in issued:
        status_disp = f"{Colors.RED}OVERDUE{Colors.RESET}" if t["status"] == "OVERDUE" else f"{Colors.GREEN}ACTIVE{Colors.RESET}"
        rows.append([t["txn_id"], t["book_id"], t["book_title"], t["member_id"], t["member_name"], t["due_date"], status_disp])
    print_table(headers, rows)


def view_returned_books():
    """Displays history of all returned transactions using slicing."""
    returned = [t for t in db.transactions if t.get("return_date")]
    if not returned:
        print_alert("No returned transaction history.", "info")
        return

    reversed_returned = returned[::-1]

    def return_formatter(page_items):
        headers = ["Txn ID", "Book ID", "Title", "Member", "Issue Date", "Return Date", "Fine Status"]
        rows = []
        for t in page_items:
            fine_str = "Clean (Rs. 0)" if t.get("fine_amount", 0) == 0 else ("Paid" if t.get("fine_paid") else f"Pending Rs. {t['fine_amount']:.2f}")
            rows.append([t["txn_id"], t["book_id"], t["book_title"], t["member_name"], t["issue_date"], t["return_date"], fine_str])
        print_table(headers, rows)

    paginate_and_display(reversed_returned, page_size=6, display_title="Returned Books Audit Log", formatter_fn=return_formatter)


def view_overdue_books():
    """Displays all overdue books with days late and calculated fine."""
    check_and_update_overdue_status()
    overdue = [t for t in db.transactions if t.get("status") == "OVERDUE" and not t.get("return_date")]

    print_header(f"Overdue Books Alert ({len(overdue)} items)")
    if not overdue:
        print_alert("No books are currently overdue. Excellent compliance!", "success")
        return

    headers = ["Txn ID", "Book Title", "Member ID", "Member Name", "Due Date", "Days Late", "Fine Accrued"]
    rows = []
    for t in overdue:
        due = parse_date(t["due_date"])
        today = parse_date(TODAY_STR)
        days = max((today - due).days, 0)
        rows.append([t["txn_id"], t["book_title"], t["member_id"], t["member_name"], t["due_date"], str(days), f"Rs. {t['fine_amount']:.2f}"])
    print_table(headers, rows)
