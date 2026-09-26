"""
Authentication Module
Handles Member & Admin registration, credential hashing, session tracking,
and input validation using core Python string and dictionary methods.
"""

from typing import Tuple, Optional
from data_store import db, hash_pin


class CurrentSession:
    """Stores active session state in-memory."""
    user: Optional[dict] = None

    @classmethod
    def login(cls, user_data: dict):
        cls.user = user_data

    @classmethod
    def logout(cls):
        cls.user = None

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls.user is not None

    @classmethod
    def is_admin(cls) -> bool:
        return cls.user is not None and cls.user.get("role") == "admin"


def validate_email(email: str) -> bool:
    """Validates email format using core string operations."""
    if "@" not in email or "." not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local_part, domain_part = parts
    return len(local_part) > 0 and "." in domain_part and len(domain_part.split(".")[-1]) >= 2


def validate_phone(phone: str) -> bool:
    """Validates 10-digit phone number using string isdigit()."""
    cleaned = phone.strip().replace("-", "").replace(" ", "")
    return len(cleaned) == 10 and cleaned.isdigit()


def register_member(name: str, phone: str, email: str, pin: str, role: str = "member") -> Tuple[bool, str, Optional[dict]]:
    """
    Registers a new member with validation.
    Returns: (success: bool, message: str, member_dict: Optional[dict])
    """
    name = name.strip()
    phone = phone.strip()
    email = email.strip().lower()
    pin = pin.strip()

    if not name or len(name) < 2:
        return False, "Name must be at least 2 characters long.", None

    if not validate_phone(phone):
        return False, "Invalid phone number. Must be a valid 10-digit phone.", None

    if not validate_email(email):
        return False, "Invalid email address format (e.g., user@domain.com).", None

    if len(pin) < 4:
        return False, "PIN/Password must be at least 4 digits/characters.", None

    # Check for existing email or phone in members dictionary
    for mem_id, mem in db.members.items():
        if mem.get("email", "").lower() == email:
            return False, f"Email '{email}' is already registered with Member ID {mem_id}.", None
        if mem.get("phone") == phone:
            return False, f"Phone number is already associated with Member ID {mem_id}.", None

    new_id = db.generate_member_id()
    new_member = {
        "id": new_id,
        "name": name,
        "phone": phone,
        "email": email,
        "pin_hash": hash_pin(pin),
        "role": role,
        "status": "active",
        "created_at": "2026-09-26",
        "total_borrowed_count": 0
    }

    db.members[new_id] = new_member
    # Initialize empty wishlist & welcome notification
    db.wishlists[new_id] = []
    db.notifications.setdefault(new_id, []).append({
        "id": f"NOTIF_{new_id}_INIT",
        "message": f"Welcome to Smart Library, {name}! Your Member ID is {new_id}.",
        "date": "2026-09-26",
        "read": False,
        "type": "SYSTEM"
    })
    db.save()

    return True, f"Registration successful! Your Member ID is {new_id}.", new_member


def authenticate(member_id: str, pin: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Authenticates a member or librarian by ID and PIN.
    Returns: (success: bool, message: str, member_dict: Optional[dict])
    """
    member_id = member_id.strip().upper()
    pin = pin.strip()

    if member_id not in db.members:
        return False, f"Member ID '{member_id}' not found.", None

    member = db.members[member_id]

    if member.get("status") == "deactivated":
        return False, "This account has been deactivated. Please contact the librarian.", None

    if member.get("pin_hash") != hash_pin(pin):
        return False, "Incorrect PIN/Password. Please try again.", None

    CurrentSession.login(member)
    return True, f"Welcome back, {member['name']}!", member
