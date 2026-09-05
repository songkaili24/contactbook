"""Command-line interface for the contact book."""

import argparse
import sys

from tabulate import tabulate

from contact import add_contact, load_contacts, save_contacts


def print_table(contacts: list) -> None:
    rows = [[c.name, c.phone, c.email, c.address or ""] for c in contacts]
    print(tabulate(rows, headers=["Name", "Phone", "Email", "Address"]))


def cmd_add(args) -> None:
    try:
        contact = add_contact(args.name, args.phone, args.email, args.address)
    except ValueError as e:
        sys.exit(f"Error: {e}")
    print(f"Added contact: {contact.name}")


def cmd_search(args) -> None:
    query = args.query.lower()
    # Phone numbers are stored as digits only, so compare the query the same way.
    query_digits = query.replace("-", "").replace(" ", "")
    matches = [
        c
        for c in load_contacts()
        if query in c.name.lower()
        or query_digits in c.phone
        or query in c.email.lower()
    ]
    if not matches:
        print(f"No contacts match {args.query!r}")
        return
    print_table(matches)


def cmd_list(_) -> None:
    contacts = sorted(load_contacts(), key=lambda c: c.name.lower())
    if not contacts:
        print("No contacts stored.")
        return
    print_table(contacts)


def cmd_delete(args) -> None:
    name = args.name or input("Name: ")
    contacts = load_contacts()
    match = next((c for c in contacts if c.name.lower() == name.lower()), None)
    if match is None:
        print(f"No contact named {name!r}")
        return
    print_table([match])
    if input("Are you sure? y/n").strip().lower() == "y":
        save_contacts([c for c in contacts if c is not match])
        print(f"Deleted contact: {match.name}")
    else:
        print("Aborted.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the contact book.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new contact")
    p_add.add_argument("name")
    p_add.add_argument("phone")
    p_add.add_argument("email")
    p_add.add_argument("--address", default=None)
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="Search name, phone, and email fields")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_list = sub.add_parser("list", help="List all contacts sorted by name")
    p_list.set_defaults(func=cmd_list)

    p_delete = sub.add_parser("delete", help="Delete a contact by name")
    p_delete.add_argument("name", nargs="?", default=None)
    p_delete.set_defaults(func=cmd_delete)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
