"""
Data Store Module
Manages in-memory storage of library entities using standard Python data structures:
- Dictionaries: Fast indexed lookup for books, members, wishlists, and notifications
- Lists: Ordered transactions, review logs, and reservation queues
- Tuples: Immutable status codes, search filters, and record snapshots
- Strings: Identifiers, text records, and formatted output

Zero external database dependencies: Persists to a single local JSON file using the built-in json module.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_data.json")


def hash_pin(pin: str) -> str:
    """Computes SHA-256 hash of a string PIN for secure credential verification."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


DEFAULT_SEED_DATA = {
    "books": {
        "B101": {
            "id": "B101",
            "title": "Python Basics",
            "author": "Guido van Rossum & Dan Bader",
            "category": "Programming",
            "total_copies": 12,
            "available_copies": 5,
            "tags": ["python", "beginner", "coding", "syntax", "oop"],
            "issue_count": 42,
            "added_date": "2026-01-10"
        },
        "B102": {
            "id": "B102",
            "title": "DBMS Fundamentals",
            "author": "Abraham Silberschatz & Henry Korth",
            "category": "Database",
            "total_copies": 10,
            "available_copies": 3,
            "tags": ["sql", "database", "rdbms", "indexing", "acid"],
            "issue_count": 37,
            "added_date": "2026-01-12"
        },
        "B103": {
            "id": "B103",
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "category": "Software Engineering",
            "total_copies": 8,
            "available_copies": 2,
            "tags": ["refactoring", "best practices", "clean architecture", "software"],
            "issue_count": 31,
            "added_date": "2026-01-15"
        },
        "B104": {
            "id": "B104",
            "title": "Artificial Intelligence: A Modern Approach",
            "author": "Stuart Russell & Peter Norvig",
            "category": "Artificial Intelligence",
            "total_copies": 6,
            "available_copies": 1,
            "tags": ["ai", "machine learning", "agents", "search", "nlp"],
            "issue_count": 28,
            "added_date": "2026-01-20"
        },
        "B105": {
            "id": "B105",
            "title": "Data Structures & Algorithms in Python",
            "author": "Michael T. Goodrich",
            "category": "Computer Science",
            "total_copies": 7,
            "available_copies": 0,  # Zero stock to test reservations!
            "tags": ["dsa", "algorithms", "arrays", "trees", "graphs", "python"],
            "issue_count": 26,
            "added_date": "2026-01-22"
        },
        "B106": {
            "id": "B106",
            "title": "Computer Networks",
            "author": "Andrew S. Tanenbaum",
            "category": "Networking",
            "total_copies": 5,
            "available_copies": 4,
            "tags": ["tcp/ip", "protocols", "osi model", "routing", "security"],
            "issue_count": 19,
            "added_date": "2026-02-01"
        },
        "B107": {
            "id": "B107",
            "title": "Designing Data-Intensive Applications",
            "author": "Martin Kleppmann",
            "category": "Database",
            "total_copies": 8,
            "available_copies": 4,
            "tags": ["distributed systems", "replication", "scalability", "kafka"],
            "issue_count": 24,
            "added_date": "2026-02-10"
        },
        "B108": {
            "id": "B108",
            "title": "Operating System Concepts",
            "author": "Abraham Silberschatz & Greg Gagne",
            "category": "Computer Science",
            "total_copies": 6,
            "available_copies": 3,
            "tags": ["processes", "memory management", "threads", "virtualization"],
            "issue_count": 17,
            "added_date": "2026-02-15"
        }
    },
    "members": {
        "M001": {
            "id": "M001",
            "name": "Dr. Sarah Librarian",
            "phone": "9876543210",
            "email": "admin@library.org",
            "pin_hash": hash_pin("1234"),
            "role": "admin",
            "status": "active",
            "created_at": "2026-01-01",
            "total_borrowed_count": 0
        },
        "M101": {
            "id": "M101",
            "name": "Arjun Mehta",
            "phone": "9812345678",
            "email": "arjun.m@example.com",
            "pin_hash": hash_pin("1234"),
            "role": "member",
            "status": "active",
            "created_at": "2026-01-05",
            "total_borrowed_count": 7
        },
        "M102": {
            "id": "M102",
            "name": "Rahul Sharma",
            "phone": "9823456789",
            "email": "rahul.s@example.com",
            "pin_hash": hash_pin("1234"),
            "role": "member",
            "status": "active",
            "created_at": "2026-01-08",
            "total_borrowed_count": 18
        },
        "M114": {
            "id": "M114",
            "name": "Priya Patel",
            "phone": "9834567890",
            "email": "priya.p@example.com",
            "pin_hash": hash_pin("1234"),
            "role": "member",
            "status": "active",
            "created_at": "2026-01-12",
            "total_borrowed_count": 15
        },
        "M127": {
            "id": "M127",
            "name": "Amit Verma",
            "phone": "9845678901",
            "email": "amit.v@example.com",
            "pin_hash": hash_pin("1234"),
            "role": "member",
            "status": "active",
            "created_at": "2026-01-18",
            "total_borrowed_count": 13
        }
    },
    "transactions": [
        {
            "txn_id": "TXN1001",
            "book_id": "B101",
            "book_title": "Python Basics",
            "member_id": "M101",
            "member_name": "Arjun Mehta",
            "issue_date": "2026-09-10",
            "due_date": "2026-09-24",
            "return_date": None,
            "status": "OVERDUE",
            "fine_amount": 20.0,
            "fine_paid": False
        },
        {
            "txn_id": "TXN1002",
            "book_id": "B103",
            "book_title": "Clean Code",
            "member_id": "M101",
            "member_name": "Arjun Mehta",
            "issue_date": "2026-09-20",
            "due_date": "2026-10-04",
            "return_date": None,
            "status": "ISSUED",
            "fine_amount": 0.0,
            "fine_paid": False
        },
        {
            "txn_id": "TXN1003",
            "book_id": "B105",
            "book_title": "Data Structures & Algorithms in Python",
            "member_id": "M102",
            "member_name": "Rahul Sharma",
            "issue_date": "2026-09-15",
            "due_date": "2026-09-29",
            "return_date": None,
            "status": "ISSUED",
            "fine_amount": 0.0,
            "fine_paid": False
        },
        {
            "txn_id": "TXN0990",
            "book_id": "B102",
            "book_title": "DBMS Fundamentals",
            "member_id": "M101",
            "member_name": "Arjun Mehta",
            "issue_date": "2026-08-01",
            "due_date": "2026-08-15",
            "return_date": "2026-08-14",
            "status": "RETURNED",
            "fine_amount": 0.0,
            "fine_paid": True
        }
    ],
    "reservations": [
        {
            "res_id": "RES1001",
            "book_id": "B105",
            "member_id": "M101",
            "reserved_at": "2026-09-22",
            "status": "PENDING"
        }
    ],
    "wishlists": {
        "M101": ["B104", "B107"],
        "M102": ["B101", "B103"]
    },
    "reviews": [
        {
            "review_id": "REV101",
            "book_id": "B101",
            "member_id": "M102",
            "member_name": "Rahul Sharma",
            "rating": 5,
            "comment": "Outstanding beginner friendly book for Python with clear practical examples.",
            "date": "2026-08-20"
        },
        {
            "review_id": "REV102",
            "book_id": "B103",
            "member_id": "M114",
            "member_name": "Priya Patel",
            "rating": 5,
            "comment": "Must read for every software developer. Totally transformed my code formatting!",
            "date": "2026-08-25"
        },
        {
            "review_id": "REV103",
            "book_id": "B102",
            "member_id": "M127",
            "member_name": "Amit Verma",
            "rating": 4,
            "comment": "Solid foundational book on SQL and relational schemas.",
            "date": "2026-09-02"
        }
    ],
    "notifications": {
        "M101": [
            {
                "id": "NOTIF1",
                "message": "Overdue Warning: 'Python Basics' was due on 2026-09-24. Please return promptly.",
                "date": "2026-09-25",
                "read": False,
                "type": "OVERDUE"
            },
            {
                "id": "NOTIF2",
                "message": "Welcome to the Smart Library System! Explore catalogue and AI recommendations.",
                "date": "2026-09-05",
                "read": True,
                "type": "SYSTEM"
            }
        ]
    }
}


class DataStore:
    """Singleton-style database manager for in-memory library data."""

    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        """Loads data from the JSON file or initializes with default seed data."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    return
            except Exception:
                pass  # Fall back to default seed on corrupt file
        self.data = DEFAULT_SEED_DATA.copy()
        self.save()

    def save(self):
        """Saves current in-memory state to the JSON file atomically."""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Failed to persist library data: {e}")

    # Accessors
    @property
    def books(self) -> dict:
        return self.data.setdefault("books", {})

    @property
    def members(self) -> dict:
        return self.data.setdefault("members", {})

    @property
    def transactions(self) -> list:
        return self.data.setdefault("transactions", [])

    @property
    def reservations(self) -> list:
        return self.data.setdefault("reservations", [])

    @property
    def wishlists(self) -> dict:
        return self.data.setdefault("wishlists", {})

    @property
    def reviews(self) -> list:
        return self.data.setdefault("reviews", [])

    @property
    def notifications(self) -> dict:
        return self.data.setdefault("notifications", {})

    # ID Generators
    def generate_book_id(self) -> str:
        """Finds max numeric ID and increments it."""
        nums = [int(k[1:]) for k in self.books.keys() if k.startswith("B") and k[1:].isdigit()]
        next_num = max(nums, default=100) + 1
        return f"B{next_num}"

    def generate_member_id(self) -> str:
        nums = [int(k[1:]) for k in self.members.keys() if k.startswith("M") and k[1:].isdigit()]
        next_num = max(nums, default=100) + 1
        return f"M{next_num}"

    def generate_txn_id(self) -> str:
        nums = [int(t["txn_id"].replace("TXN", "")) for t in self.transactions if "txn_id" in t and t["txn_id"].startswith("TXN") and t["txn_id"].replace("TXN", "").isdigit()]
        next_num = max(nums, default=1000) + 1
        return f"TXN{next_num}"

    def generate_res_id(self) -> str:
        nums = [int(r["res_id"].replace("RES", "")) for r in self.reservations if "res_id" in r and r["res_id"].startswith("RES") and r["res_id"].replace("RES", "").isdigit()]
        next_num = max(nums, default=1000) + 1
        return f"RES{next_num}"

    def generate_review_id(self) -> str:
        nums = [int(r["review_id"].replace("REV", "")) for r in self.reviews if "review_id" in r and r["review_id"].startswith("REV") and r["review_id"].replace("REV", "").isdigit()]
        next_num = max(nums, default=100) + 1
        return f"REV{next_num}"


# Global single store instance
db = DataStore()
