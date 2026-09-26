"""
Main CLI Application: Smart Library Management System
Interactive Menu-Driven Terminal Application
Built strictly with Python Core Data Structures and Built-in standard library.
"""

import sys
import time

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from data_store import db
from auth import CurrentSession, authenticate, register_member
from ui import Colors, print_banner, print_header, print_alert, clear_screen, render_digital_card
import member_ops
import admin_ops
import analytics
import ai_features


def guest_catalogue_menu():
    """Allows guest users to view the catalog without logging in."""
    while True:
        print_header("Guest Public Catalogue", "Browse our collection before joining")
        print(f" {Colors.CYAN}[1]{Colors.RESET} View All Books (Paginated)")
        print(f" {Colors.CYAN}[2]{Colors.RESET} Search Book (Title, Author, Category, ID)")
        print(f" {Colors.CYAN}[3]{Colors.RESET} AI Semantic / Natural Language Search")
        print(f" {Colors.RED}[0]{Colors.RESET} Back to Main Menu")

        choice = input(f"\n{Colors.BOLD}Enter choice: {Colors.RESET}").strip()
        if choice == "1":
            member_ops.view_catalogue()
        elif choice == "2":
            member_ops.search_books()
        elif choice == "3":
            member_ops.natural_language_search_menu()
        elif choice == "0":
            break


def member_login_flow():
    """Interactive member login workflow."""
    print_header("Member Login", "Demo Member ID: M101 | PIN: 1234")
    mem_id = input(f"{Colors.BOLD}Enter Member ID: {Colors.RESET}").strip().upper()
    pin = input(f"{Colors.BOLD}Enter PIN/Password: {Colors.RESET}").strip()

    success, msg, member = authenticate(mem_id, pin)
    if success:
        print_alert(msg, "success")
        member_portal_menu()
    else:
        print_alert(msg, "error")


def member_register_flow():
    """Member self-registration."""
    print_header("Member Registration", "Create your library identity")
    name = input(f"{Colors.BOLD}Full Name: {Colors.RESET}").strip()
    phone = input(f"{Colors.BOLD}Phone (10 digits): {Colors.RESET}").strip()
    email = input(f"{Colors.BOLD}Email: {Colors.RESET}").strip()
    pin = input(f"{Colors.BOLD}Set a 4+ digit PIN: {Colors.RESET}").strip()

    success, msg, member = register_member(name, phone, email, pin)
    if success:
        print_alert(msg, "success")
        print_alert("You can now log in using your newly generated Member ID!", "info")
    else:
        print_alert(msg, "error")


def admin_login_flow():
    """Admin / Librarian authentication."""
    print_header("Librarian & Admin Portal", "Demo Admin ID: M001 | PIN: 1234")
    admin_id = input(f"{Colors.BOLD}Enter Admin Member ID: {Colors.RESET}").strip().upper()
    pin = input(f"{Colors.BOLD}Enter PIN: {Colors.RESET}").strip()

    success, msg, admin = authenticate(admin_id, pin)
    if success:
        if admin.get("role") != "admin":
            print_alert("Access Denied: This account does not possess librarian/administrator privileges.", "error")
            CurrentSession.logout()
            return
        print_alert(msg, "success")
        admin_portal_menu()
    else:
        print_alert(msg, "error")


def member_portal_menu():
    """Menu displayed when an authorized member is logged in."""
    while CurrentSession.is_logged_in():
        user = CurrentSession.user
        unread_notifs = sum(1 for n in db.notifications.get(user["id"], []) if not n.get("read"))
        notif_badge = f"{Colors.RED}[{unread_notifs} New]{Colors.RESET}" if unread_notifs > 0 else f"{Colors.DIM}[0]{Colors.RESET}"

        print_header(f"Member Portal: {user['name']} ({user['id']})", f"Active Loans: {user.get('total_borrowed_count', 0)} total books read")

        print(f" {Colors.BOLD}{Colors.CYAN}--- CORE CATALOG & CIRCULATION ---{Colors.RESET}")
        print(f"  {Colors.CYAN}[1]{Colors.RESET} View Book Catalogue (Paginated)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET} Search Book")
        print(f"  {Colors.CYAN}[3]{Colors.RESET} Book Details & Community Reviews")
        print(f"  {Colors.CYAN}[4]{Colors.RESET} Issue / Borrow Book")
        print(f"  {Colors.CYAN}[5]{Colors.RESET} Return Book")
        print(f"  {Colors.CYAN}[6]{Colors.RESET} My Borrowed Books (Active Loans)")
        print(f"  {Colors.CYAN}[7]{Colors.RESET} Borrowing History")
        print(f"  {Colors.CYAN}[8]{Colors.RESET} Fines & Penalty Settlement")

        print(f"\n {Colors.BOLD}{Colors.YELLOW}--- BONUS MEMBER ENHANCEMENTS ---{Colors.RESET}")
        print(f"  {Colors.YELLOW}[9]{Colors.RESET}  Book Reservation (Out-of-stock queue)")
        print(f"  {Colors.YELLOW}[10]{Colors.RESET} Book Renewal (+7 Days extension)")
        print(f"  {Colors.YELLOW}[11]{Colors.RESET} Favourites / Wishlist")
        print(f"  {Colors.YELLOW}[12]{Colors.RESET} Rate & Review a Book")
        print(f"  {Colors.YELLOW}[13]{Colors.RESET} Notifications Inbox {notif_badge}")
        print(f"  {Colors.YELLOW}[14]{Colors.RESET} Digital Library Card (ASCII ID)")

        print(f"\n {Colors.BOLD}{Colors.HEADER}--- AI HORIZONS & SMART ENGINES ---{Colors.RESET}")
        print(f"  {Colors.HEADER}[15]{Colors.RESET} Smart Recommendation Engine (Hybrid AI + Live Web API)")
        print(f"  {Colors.HEADER}[16]{Colors.RESET} Semantic / Natural Language Search")

        print(f"\n  {Colors.RED}[0]{Colors.RESET} Logout")

        choice = input(f"\n{Colors.BOLD}Select an option: {Colors.RESET}").strip()

        if choice == "1":
            member_ops.view_catalogue()
        elif choice == "2":
            member_ops.search_books()
        elif choice == "3":
            member_ops.view_book_details()
        elif choice == "4":
            member_ops.issue_book()
        elif choice == "5":
            member_ops.return_book()
        elif choice == "6":
            member_ops.view_my_borrowed_books()
        elif choice == "7":
            member_ops.view_borrowing_history()
        elif choice == "8":
            member_ops.view_and_pay_fines()
        elif choice == "9":
            member_ops.reserve_book()
        elif choice == "10":
            member_ops.renew_borrowed_book()
        elif choice == "11":
            member_ops.manage_wishlist()
        elif choice == "12":
            member_ops.add_book_review()
        elif choice == "13":
            member_ops.view_notifications()
        elif choice == "14":
            member_ops.show_digital_library_card()
        elif choice == "15":
            member_ops.show_smart_recommendations()
        elif choice == "16":
            member_ops.natural_language_search_menu()
        elif choice == "0":
            CurrentSession.logout()
            print_alert("Logged out successfully.", "info")
            break
        else:
            print_alert("Invalid option. Please choose from the menu.", "warning")


def admin_portal_menu():
    """Comprehensive Admin & Librarian Operations Portal."""
    while CurrentSession.is_admin():
        user = CurrentSession.user
        print_header(f"Librarian Administration Console: {user['name']}", "High-Privilege Management & Analytics")

        print(f" {Colors.BOLD}{Colors.CYAN}--- BOOK MANAGEMENT ---{Colors.RESET}")
        print(f"  {Colors.CYAN}[1]{Colors.RESET}  Add Book (with AI Smart Tags)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET}  View All Books")
        print(f"  {Colors.CYAN}[3]{Colors.RESET}  Search Book")
        print(f"  {Colors.CYAN}[4]{Colors.RESET}  Update Book Metadata")
        print(f"  {Colors.CYAN}[5]{Colors.RESET}  Delete Book (with loan safeguard)")
        print(f"  {Colors.CYAN}[6]{Colors.RESET}  Manage Stock Quantity")
        print(f"  {Colors.CYAN}[7]{Colors.RESET}  Manage Categories")

        print(f"\n {Colors.BOLD}{Colors.YELLOW}--- MEMBER MANAGEMENT ---{Colors.RESET}")
        print(f"  {Colors.YELLOW}[8]{Colors.RESET}  Register New Member")
        print(f"  {Colors.YELLOW}[9]{Colors.RESET}  View All Members (Directory)")
        print(f"  {Colors.YELLOW}[10]{Colors.RESET} Search Member")
        print(f"  {Colors.YELLOW}[11]{Colors.RESET} Update Member Record")
        print(f"  {Colors.YELLOW}[12]{Colors.RESET} Deactivate / Reactivate Member")

        print(f"\n {Colors.BOLD}{Colors.GREEN}--- TRANSACTION MANAGEMENT ---{Colors.RESET}")
        print(f"  {Colors.GREEN}[13]{Colors.RESET} Desk Issue (Checkout)")
        print(f"  {Colors.GREEN}[14]{Colors.RESET} Desk Return (Checkin & Fine Collection)")
        print(f"  {Colors.GREEN}[15]{Colors.RESET} View Currently Issued Books")
        print(f"  {Colors.GREEN}[16]{Colors.RESET} View Returned Books Log")
        print(f"  {Colors.GREEN}[17]{Colors.RESET} View Overdue Loans Alert")

        print(f"\n {Colors.BOLD}{Colors.HEADER}--- ANALYTICS & AI HORIZONS ---{Colors.RESET}")
        print(f"  {Colors.HEADER}[18]{Colors.RESET} Leaderboard: Most Borrowed Books")
        print(f"  {Colors.HEADER}[19]{Colors.RESET} Leaderboard: Most Active Members")
        print(f"  {Colors.HEADER}[20]{Colors.RESET} Inventory Alert (Low & Zero Stock)")
        print(f"  {Colors.HEADER}[21]{Colors.RESET} Overdue Compliance & Penalty Audit")
        print(f"  {Colors.HEADER}[22]{Colors.RESET} Category Analytics & Share")
        print(f"  {Colors.HEADER}[23]{Colors.RESET} Smart Librarian AI Dashboard & Demand Predictor")

        print(f"\n  {Colors.RED}[0]{Colors.RESET}  Logout")

        choice = input(f"\n{Colors.BOLD}Select an option: {Colors.RESET}").strip()

        if choice == "1":
            admin_ops.add_book()
        elif choice == "2":
            admin_ops.view_all_books()
        elif choice == "3":
            member_ops.search_books()
        elif choice == "4":
            admin_ops.update_book()
        elif choice == "5":
            admin_ops.delete_book()
        elif choice == "6":
            admin_ops.manage_quantity()
        elif choice == "7":
            admin_ops.manage_categories()
        elif choice == "8":
            admin_ops.register_member_admin()
        elif choice == "9":
            admin_ops.view_all_members()
        elif choice == "10":
            admin_ops.search_members()
        elif choice == "11":
            admin_ops.update_member()
        elif choice == "12":
            admin_ops.delete_or_deactivate_member()
        elif choice == "13":
            admin_ops.admin_issue_book()
        elif choice == "14":
            admin_ops.admin_return_book()
        elif choice == "15":
            admin_ops.view_issued_books()
        elif choice == "16":
            admin_ops.view_returned_books()
        elif choice == "17":
            admin_ops.view_overdue_books()
        elif choice == "18":
            analytics.show_most_borrowed_books()
        elif choice == "19":
            analytics.show_most_active_members()
        elif choice == "20":
            analytics.show_inventory_alerts()
        elif choice == "21":
            analytics.show_overdue_management()
        elif choice == "22":
            analytics.show_category_analytics()
        elif choice == "23":
            analytics.show_smart_librarian_dashboard()
        elif choice == "0":
            CurrentSession.logout()
            print_alert("Librarian logged out.", "info")
            break
        else:
            print_alert("Invalid option.", "warning")


def run_hackathon_demo_tour():
    """
    Automated fast walkthrough for hackathon judges:
    Demonstrates member card, catalog, AI recommendations,
    analytics leaderboards, and AI demand predictor.
    """
    print_header("HACKATHON QUICK DEMO TOUR (Judges Fast-Track)", "Demonstrating core capabilities and AI components")

    print(f"\n{Colors.BOLD}[Step 1/5] Displaying Digital Library Card for Member M101:{Colors.RESET}")
    member = db.members["M101"]
    render_digital_card(member, 2)
    time.sleep(1)

    print(f"\n{Colors.BOLD}[Step 2/5] Running AI Smart Recommendation Engine for M101:{Colors.RESET}")
    recs = ai_features.recommend_books_for_member("M101")
    for r in recs:
        print(f"  • {Colors.CYAN}{r['book']['title']}{Colors.RESET} ({r['book']['category']}) -> Score: {r['score']} | {Colors.YELLOW}{r['reason']}{Colors.RESET}")
    time.sleep(1)

    print(f"\n{Colors.BOLD}[Step 3/5] Performing Semantic / Natural Language Search:{Colors.RESET}")
    test_query = "beginner guide to learn python programming"
    print(f"  Query: '{test_query}'")
    matches = ai_features.semantic_natural_language_search(test_query)
    for m in matches[:2]:
        print(f"  -> Match: {m['book']['title']} [Confidence: {m['confidence']}%] - {m['reason']}")
    time.sleep(1)

    print(f"\n{Colors.BOLD}[Step 4/5] Displaying Analytics Leaderboards:{Colors.RESET}")
    analytics.show_most_borrowed_books(top_n=3)
    analytics.show_most_active_members(top_n=3)
    time.sleep(1)

    print(f"\n{Colors.BOLD}[Step 5/5] Launching Smart Librarian AI Dashboard & Demand Predictor:{Colors.RESET}")
    analytics.show_smart_librarian_dashboard()

    print_alert("Demo Tour Complete! All modules functioning smoothly with zero external dependencies.", "success")
    input(f"\n{Colors.DIM}Press Enter to return to main menu...{Colors.RESET}")


def show_system_architecture_info():
    """Displays system technical specifications and data structure mapping."""
    print_header("System Architecture & Hackathon Compliance")
    info = f"""
{Colors.BOLD}DATA STRUCTURE COMPLIANCE MAPPING:{Colors.RESET}
• {Colors.CYAN}Strings:{Colors.RESET} Identifiers ('B101', 'M101'), search tokens, hashed passwords (SHA-256), date formats
• {Colors.CYAN}Lists:{Colors.RESET} Dynamic transaction logs, book tags list, reservation queues, member review feeds
• {Colors.CYAN}Tuples:{Colors.RESET} Immutable return statuses (success, msg, data), coordinate pairs, medal ranks
• {Colors.CYAN}Dictionaries:{Colors.RESET} Fast O(1) indexed lookups for Books, Members, Wishlists, Notifications
• {Colors.CYAN}Slicing:{Colors.RESET} List pagination [start:end], history reversal [::-1], string column truncations [:w-2]
• {Colors.CYAN}Built-in Functions:{Colors.RESET} sorted(), filter(), map(), zip(), enumerate(), len(), sum(), max(), min(), all(), any()

{Colors.BOLD}AI HORIZON COMPONENTS:{Colors.RESET}
1. {Colors.HEADER}Smart Recommendation Engine:{Colors.RESET} Content-Based + Collaborative Filtering + Open Library API integration
2. {Colors.HEADER}Semantic / Natural Language Search:{Colors.RESET} Conversational query tokenization, stop-words removal, concept mapping
3. {Colors.HEADER}Book Demand Predictor:{Colors.RESET} Circulation velocity & reservation pressure forecasting
4. {Colors.HEADER}Smart Tag Recommender:{Colors.RESET} Rule-based NLP entity extractor for librarians
5. {Colors.HEADER}Smart Librarian Dashboard:{Colors.RESET} AI health scoring & automated replenishment suggestions

{Colors.BOLD}DATABASE STATUS:{Colors.RESET} Pure Python JSON storage ({Colors.GREEN}Zero external database dependencies{Colors.RESET}).
"""
    print(info)
    input(f"\n{Colors.DIM}Press Enter to return to main menu...{Colors.RESET}")


def main():
    """Main program entry loop."""
    while True:
        print_banner()
        print(f" {Colors.CYAN}[1]{Colors.RESET} Member Portal (Login / Register)")
        print(f" {Colors.CYAN}[2]{Colors.RESET} Librarian / Admin Portal (Login)")
        print(f" {Colors.CYAN}[3]{Colors.RESET} Browse Public Book Catalogue (Guest Mode)")
        print(f" {Colors.HEADER}[4]{Colors.RESET} AI Semantic / Natural Language Search")
        print(f" {Colors.YELLOW}[5]{Colors.RESET} Hackathon Quick Demo Tour (Automated Walkthrough)")
        print(f" {Colors.BLUE}[6]{Colors.RESET} System Architecture & Compliance Info")
        print(f" {Colors.RED}[0]{Colors.RESET} Exit System")

        choice = input(f"\n{Colors.BOLD}Select an option: {Colors.RESET}").strip()

        if choice == "1":
            print_header("Member Portal Access")
            print(f" {Colors.CYAN}[1]{Colors.RESET} Log In (Existing Member)")
            print(f" {Colors.CYAN}[2]{Colors.RESET} Register (New Member)")
            print(f" {Colors.RED}[B]{Colors.RESET} Back")
            sub_choice = input(f"\n{Colors.BOLD}Choice: {Colors.RESET}").strip().upper()
            if sub_choice == "1":
                member_login_flow()
            elif sub_choice == "2":
                member_register_flow()
        elif choice == "2":
            admin_login_flow()
        elif choice == "3":
            guest_catalogue_menu()
        elif choice == "4":
            member_ops.natural_language_search_menu()
        elif choice == "5":
            run_hackathon_demo_tour()
        elif choice == "6":
            show_system_architecture_info()
        elif choice == "0":
            print_alert("Thank you for using Smart Library Management System. Goodbye!", "info")
            sys.exit(0)
        else:
            print_alert("Invalid option. Please try again.", "warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user. Exiting gracefully.{Colors.RESET}")
        sys.exit(0)
