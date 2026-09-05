"""Contact book: a Contact dataclass with validation and JSON storage."""

import json
import re
from dataclasses import dataclass, asdict
from typing import Optional

CONTACTS_FILE = "contacts.json"

PHONE_RE = re.compile(r"^\d{10}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Contact:
    name: str
    phone: str
    email: str
    address: Optional[str] = None
    favorite: bool = False


def validate_phone(phone: str) -> str:
    """Return the phone number with dashes/spaces stripped.

    Raises ValueError unless exactly 10 digits remain.
    """
    digits = phone.replace("-", "").replace(" ", "")
    if not PHONE_RE.match(digits):
        raise ValueError(
            f"Invalid phone number {phone!r}: must contain exactly 10 digits"
        )
    return digits


def validate_email(email: str) -> str:
    """Return the email address after a basic format check.

    Raises ValueError if it doesn't look like name@domain.tld.
    """
    if not EMAIL_RE.match(email):
        raise ValueError(f"Invalid email address {email!r}")
    return email


def load_contacts() -> list[Contact]:
    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    return [Contact(**item) for item in data]


def save_contacts(contacts: list[Contact]) -> None:
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in contacts], f, indent=2)


def add_contact(
    name: str,
    phone: str,
    email: str,
    address: Optional[str] = None,
    favorite: bool = False,
) -> Contact:
    """Validate and append a contact to contacts.json.

    Raises ValueError on invalid phone/email or a duplicate name
    (names are compared case-insensitively).
    """
    phone = validate_phone(phone)
    email = validate_email(email)

    contacts = load_contacts()
    if any(c.name.lower() == name.lower() for c in contacts):
        raise ValueError(f"Contact {name!r} already exists")

    contact = Contact(
        name=name, phone=phone, email=email, address=address, favorite=favorite
    )
    contacts.append(contact)
    save_contacts(contacts)
    return contact


def edit_contact(
    current: str,
    *,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    favorite: Optional[bool] = None,
) -> Contact:
    """Update fields of the contact named `current` and persist the change.

    Only fields whose value is not None are changed. Phone and email are
    revalidated; renaming is rejected if it would collide with another
    contact (case-insensitively).
    """
    contacts = load_contacts()
    match = next((c for c in contacts if c.name.lower() == current.lower()), None)
    if match is None:
        raise ValueError(f"No contact named {current!r}")

    changes = {
        key: value
        for key, value in {
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
            "favorite": favorite,
        }.items()
        if value is not None
    }
    if not changes:
        raise ValueError("No fields to update")

    if "phone" in changes:
        changes["phone"] = validate_phone(changes["phone"])
    if "email" in changes:
        changes["email"] = validate_email(changes["email"])
    if "name" in changes and any(
        c is not match and c.name.lower() == changes["name"].lower()
        for c in contacts
    ):
        raise ValueError(f"Contact {changes['name']!r} already exists")

    for field, value in changes.items():
        setattr(match, field, value)
    save_contacts(contacts)
    return match
