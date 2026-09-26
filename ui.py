"""
UI Module for Smart Library Management CLI
Provides ANSI styling, colored badges, table formatters, and ASCII art.
Pure Python standard library - no external packages required.
"""

import os
import sys

# Enable ANSI colors and UTF-8 encoding on Windows terminals
if sys.platform == "win32":
    os.system("color")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# Determine terminal box drawing support
try:
    "┌─┐│└─┘├┼┤┬┴".encode(sys.stdout.encoding or "utf-8")
    B_TL, B_H, B_TR, B_V, B_BL, B_BR = "┌", "─", "┐", "│", "└", "┘"
    B_CROSS, B_TD, B_TU, B_TRT, B_TLT = "┼", "┬", "┴", "├", "┤"
except Exception:
    B_TL, B_H, B_TR, B_V, B_BL, B_BR = "+", "-", "+", "|", "+", "+"
    B_CROSS, B_TD, B_TU, B_TRT, B_TLT = "+", "+", "+", "+", "+"


def print_banner():
    raw_art = r"""
========================================================================
   ____  __  __    _    ____ _____   _     ___ ____  ____      _    ______   __
  / ___||  \/  |  / \  |  _ \_   _| | |   |_ _| __ )|  _ \    / \  |  _ \ \ / /
  \___ \| |\/| | / _ \ | |_) || |   | |    | ||  _ \| |_) |  / _ \ | |_) \ V / 
   ___) | |  | |/ ___ \|  _ < | |   | |___ | || |_) |  _ <  / ___ \|  _ < | |  
  |____/|_|  |_/_/   \_\_| \_\|_|   |_____|___|____/|_| \_\/_/   \_\_| \_\|_|  
========================================================================
"""
    print(f"{Colors.CYAN}{Colors.BOLD}{raw_art}{Colors.YELLOW}     Next-Gen Menu-Driven CLI | Core Python | AI-Powered Horizons{Colors.RESET}\n")


def print_header(title: str, subtitle: str = ""):
    line = B_H * 70
    print(f"\n{Colors.CYAN}{B_TL}{line}{B_TR}{Colors.RESET}")
    print(f"{Colors.CYAN}{B_V}{Colors.BOLD}  {title.center(68)}  {Colors.RESET}{Colors.CYAN}{B_V}{Colors.RESET}")
    if subtitle:
        print(f"{Colors.CYAN}{B_V}{Colors.DIM}  {subtitle.center(68)}  {Colors.RESET}{Colors.CYAN}{B_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{B_BL}{line}{B_BR}{Colors.RESET}\n")


def print_alert(message: str, level: str = "info"):
    levels = {
        "success": (f"{Colors.GREEN}[SUCCESS]{Colors.RESET}", Colors.GREEN),
        "info": (f"{Colors.BLUE}[INFO]{Colors.RESET}", Colors.CYAN),
        "warning": (f"{Colors.YELLOW}[WARNING]{Colors.RESET}", Colors.YELLOW),
        "error": (f"{Colors.RED}[ERROR]{Colors.RESET}", Colors.RED),
        "ai": (f"{Colors.HEADER}[AI COPILOT]{Colors.RESET}", Colors.HEADER)
    }
    badge, color = levels.get(level, levels["info"])
    print(f" {badge} {color}{message}{Colors.RESET}")


def print_table(headers: list, rows: list, col_widths: list = None):
    """
    Renders a formatted table using string slicing, padding, and borders.
    Demonstrates Python string formatting and list manipulation.
    """
    if not headers:
        return

    # Calculate optimal column widths if not provided
    if col_widths is None:
        col_widths = []
        for i in range(len(headers)):
            max_w = len(str(headers[i]))
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(min(max_w + 2, 32))  # Cap width to avoid wrapping

    # Top border
    top_line = B_TL + B_TD.join(B_H * w for w in col_widths) + B_TR
    header_line = B_V + B_V.join(f" {str(headers[i])[:col_widths[i]-2]}".ljust(col_widths[i]) for i in range(len(headers))) + B_V
    sep_line = B_TRT + B_CROSS.join(B_H * w for w in col_widths) + B_TLT
    bot_line = B_BL + B_TU.join(B_H * w for w in col_widths) + B_BR

    print(f"{Colors.CYAN}{top_line}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}{header_line}{Colors.RESET}")
    print(f"{Colors.CYAN}{sep_line}{Colors.RESET}")

    for row_idx, row in enumerate(rows):
        formatted_cols = []
        for i in range(len(headers)):
            val = str(row[i]) if i < len(row) else ""
            # Demonstrate slicing: truncate long strings to fit column
            truncated = val[:col_widths[i]-2] if len(val) > (col_widths[i]-2) else val
            formatted_cols.append(f" {truncated}".ljust(col_widths[i]))
        row_str = B_V + B_V.join(formatted_cols) + B_V
        print(row_str)

    print(f"{Colors.CYAN}{bot_line}{Colors.RESET}")


def paginate_and_display(items: list, page_size: int = 5, display_title: str = "Items", formatter_fn=None):
    """
    Paginates any list using Python list slicing [start:end].
    Provides interactive Next/Previous navigation.
    """
    if not items:
        print_alert("No records found.", "info")
        return

    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    current_page = 0

    while True:
        # Slicing in action:
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]

        print_header(f"{display_title} (Page {current_page + 1}/{total_pages})", f"Showing items {start_idx + 1} to {min(end_idx, total_items)} of {total_items}")

        if formatter_fn:
            formatter_fn(page_items)
        else:
            for idx, item in enumerate(page_items, start=start_idx + 1):
                print(f" {Colors.BOLD}{idx}.{Colors.RESET} {item}")

        print("\n" + "─" * 70)
        nav_options = []
        if current_page > 0:
            nav_options.append(f"{Colors.YELLOW}[P]{Colors.RESET} Previous")
        if current_page < total_pages - 1:
            nav_options.append(f"{Colors.YELLOW}[N]{Colors.RESET} Next")
        nav_options.append(f"{Colors.RED}[B]{Colors.RESET} Back")

        print("  " + "  |  ".join(nav_options))
        choice = input(f"\n{Colors.BOLD}Enter option: {Colors.RESET}").strip().upper()

        if choice == "N" and current_page < total_pages - 1:
            current_page += 1
        elif choice == "P" and current_page > 0:
            current_page -= 1
        elif choice == "B" or choice == "":
            break
        else:
            print_alert("Invalid navigation choice.", "warning")


def render_digital_card(member: dict, active_loans_count: int):
    """
    Generates an ASCII Art Digital Library Card with badge and details.
    """
    mem_id = member.get("id", "N/A")
    name = member.get("name", "N/A")
    email = member.get("email", "N/A")
    phone = member.get("phone", "N/A")
    status = member.get("status", "ACTIVE").upper()
    role = member.get("role", "MEMBER").upper()
    join_date = member.get("created_at", "2026-01-01")[:10]

    status_badge = f"{Colors.GREEN}[ACTIVE]{Colors.RESET}" if status == "ACTIVE" else f"{Colors.RED}[DISABLED]{Colors.RESET}"

    card = f"""
{Colors.CYAN}{B_TL}{B_H * 66}{B_TR}
{B_V} {Colors.BOLD}{Colors.HEADER}SMART LIBRARY SYSTEM -- OFFICIAL DIGITAL MEMBERSHIP CARD{Colors.RESET}{Colors.CYAN}          {B_V}
{B_TRT}{B_H * 66}{B_TLT}
{B_V}                                                                  {B_V}
{B_V}   {Colors.BOLD}Member ID :{Colors.RESET} {Colors.YELLOW}{mem_id.ljust(15)}{Colors.RESET}        {Colors.BOLD}Tier  :{Colors.RESET} {Colors.CYAN}{role.ljust(15)}{Colors.RESET} {B_V}
{B_V}   {Colors.BOLD}Full Name :{Colors.RESET} {name.ljust(25)} {Colors.BOLD}Status:{Colors.RESET} {status_badge.ljust(20)} {B_V}
{B_V}   {Colors.BOLD}Email     :{Colors.RESET} {email.ljust(25)} {Colors.BOLD}Loans :{Colors.RESET} {str(active_loans_count).ljust(15)} {B_V}
{B_V}   {Colors.BOLD}Phone     :{Colors.RESET} {phone.ljust(25)} {Colors.BOLD}Joined:{Colors.RESET} {join_date.ljust(15)} {B_V}
{B_V}                                                                  {B_V}
{B_V}   {Colors.DIM}[||| | |||| | ||||| ||| ||||||| | || ||||| ||| | ||||]{Colors.RESET}         {B_V}
{B_V}   {Colors.DIM}         * AUTHENTICATED DIGITAL IDENTITY CARD *           {Colors.RESET}{Colors.CYAN}{B_V}
{B_BL}{B_H * 66}{B_BR}{Colors.RESET}
"""
    print(card)
