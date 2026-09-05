"""Tests for contact validation and JSON storage (pytest, tmp_path)."""

import json

import pytest

import contact
from contact import (
    Contact,
    add_contact,
    edit_contact,
    load_contacts,
    save_contacts,
    validate_email,
    validate_phone,
)


@pytest.fixture
def contacts_file(tmp_path, monkeypatch):
    """Point the module at a per-test JSON file inside tmp_path."""
    path = tmp_path / "contacts.json"
    monkeypatch.setattr(contact, "CONTACTS_FILE", str(path))
    return path


class TestValidatePhone:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("5551234567", "5551234567"),
            ("555-123-4567", "5551234567"),
            ("555 123 4567", "5551234567"),
        ],
    )
    def test_valid_returns_digits(self, raw, expected):
        assert validate_phone(raw) == expected

    @pytest.mark.parametrize(
        "bad", ["555123456", "55512345678", "abc-def-ghij", "555-123-456a", ""]
    )
    def test_invalid_raises_value_error(self, bad):
        with pytest.raises(ValueError):
            validate_phone(bad)


class TestValidateEmail:
    @pytest.mark.parametrize(
        "good", ["alice@example.com", "bob.smith@test.org", "a@b.co"]
    )
    def test_valid_passes_through(self, good):
        assert validate_email(good) == good

    @pytest.mark.parametrize(
        "bad", ["no-at-sign.com", "a@b", "a b@c.com", "@example.com", "alice@", ""]
    )
    def test_invalid_raises_value_error(self, bad):
        with pytest.raises(ValueError):
            validate_email(bad)


class TestJsonStorage:
    def test_missing_file_loads_as_empty(self, contacts_file):
        assert load_contacts() == []

    def test_save_then_load_roundtrip(self, contacts_file):
        alice = Contact("Alice", "5551234567", "alice@example.com", "123 Main St", True)
        bob = Contact("Bob", "5559998888", "bob@test.org")
        save_contacts([alice, bob])

        assert json.loads(contacts_file.read_text(encoding="utf-8")) == [
            {
                "name": "Alice",
                "phone": "5551234567",
                "email": "alice@example.com",
                "address": "123 Main St",
                "favorite": True,
            },
            {
                "name": "Bob",
                "phone": "5559998888",
                "email": "bob@test.org",
                "address": None,
                "favorite": False,
            },
        ]
        assert load_contacts() == [alice, bob]

    def test_favorites_survive_roundtrip(self, contacts_file):
        save_contacts(
            [Contact("Alice", "5551234567", "alice@example.com", favorite=True)]
        )
        assert load_contacts()[0].favorite is True

    def test_load_ignores_missing_favorite_key(self, contacts_file):
        # A file written before the favorite field existed.
        contacts_file.write_text(
            json.dumps(
                [
                    {
                        "name": "Old",
                        "phone": "5551234567",
                        "email": "old@x.com",
                        "address": None,
                    }
                ]
            ),
            encoding="utf-8",
        )
        assert load_contacts() == [Contact("Old", "5551234567", "old@x.com")]


class TestAddContact:
    def test_add_persists_normalized_contact(self, contacts_file):
        added = add_contact(
            "Alice", "555-123-4567", "alice@example.com", favorite=True
        )
        assert load_contacts() == [added]
        assert added.phone == "5551234567"
        assert added.favorite is True

    def test_duplicate_name_case_insensitive(self, contacts_file):
        add_contact("Alice", "5551234567", "alice@example.com")
        with pytest.raises(ValueError, match="already exists"):
            add_contact("ALICE", "5550001111", "other@example.com")
        assert len(load_contacts()) == 1

    def test_invalid_phone_raises_and_writes_nothing(self, contacts_file):
        with pytest.raises(ValueError, match="10 digits"):
            add_contact("Alice", "12345", "alice@example.com")
        assert not contacts_file.exists()

    def test_invalid_email_raises_and_writes_nothing(self, contacts_file):
        with pytest.raises(ValueError):
            add_contact("Alice", "5551234567", "not-an-email")
        assert not contacts_file.exists()


class TestEditContact:
    @pytest.fixture
    def alice(self, contacts_file):
        return add_contact("Alice", "5551234567", "alice@example.com", "123 Main St")

    def test_edit_phone_and_favorite(self, alice):
        updated = edit_contact("Alice", phone="555-000-1111", favorite=True)
        assert updated.phone == "5550001111"
        assert updated.favorite is True
        stored = load_contacts()[0]
        assert (stored.phone, stored.favorite) == ("5550001111", True)
        assert stored.address == "123 Main St"  # untouched field

    def test_edit_rename(self, alice):
        updated = edit_contact("alice", name="Alicia")
        assert updated.name == "Alicia"
        assert [c.name for c in load_contacts()] == ["Alicia"]

    def test_edit_rename_to_duplicate_rejected(self, alice):
        add_contact("Bob", "5559998888", "bob@test.org")
        with pytest.raises(ValueError, match="already exists"):
            edit_contact("Alice", name="BOB")

    def test_edit_invalid_phone_rejected_and_file_unchanged(self, alice, contacts_file):
        before = contacts_file.read_text(encoding="utf-8")
        with pytest.raises(ValueError):
            edit_contact("Alice", phone="12")
        assert contacts_file.read_text(encoding="utf-8") == before

    def test_edit_unknown_contact_raises(self, contacts_file):
        with pytest.raises(ValueError, match="No contact"):
            edit_contact("Zoe", phone="5551234567")

    def test_edit_without_fields_raises(self, alice):
        with pytest.raises(ValueError, match="No fields"):
            edit_contact("Alice")
