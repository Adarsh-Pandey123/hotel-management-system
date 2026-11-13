"""
Hotel Management System
=======================
A console-based hotel management application built with Python and MySQL.

Originally created as a Class 12 CBSE Computer Science (083) project at
Kendriya Vidyalaya Mau (session 2021-22), later cleaned up for GitHub.

Author : Adarsh Kumar Pandey

Database settings are read from environment variables (see README.md):
    HMS_DB_HOST      default: localhost
    HMS_DB_USER      default: root
    HMS_DB_PASSWORD  if not set, the program asks for it when it starts
    HMS_DB_NAME      default: hotel
"""

import getpass
import os
import sys
from contextlib import contextmanager
from datetime import date, datetime

import mysql.connector
from mysql.connector import Error

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.environ.get("HMS_DB_HOST", "localhost"),
    "user": os.environ.get("HMS_DB_USER", "root"),
    "password": os.environ.get("HMS_DB_PASSWORD"),
    "database": os.environ.get("HMS_DB_NAME", "hotel"),
}

# Hotel details and tax rates, loaded from the `setting` table at start-up.
SETTINGS = {
    "hotel_name": "",
    "address": "",
    "phone": "",
    "email": "",
    "gst": "0",
    "st": "0",
}

LINE = "-" * 100


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
@contextmanager
def db_cursor(commit=False):
    """Open a connection, yield a cursor and always close both.

    With commit=True all statements inside the block are saved together.
    If anything fails, the whole block is rolled back.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_one(sql, params=()):
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def fetch_all(sql, params=()):
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def load_settings():
    """Read hotel name, address, phone, email, GST and service tax."""
    for field_name, value in fetch_all("SELECT field_name, value FROM setting"):
        if field_name in SETTINGS:
            SETTINGS[field_name] = value


def get_room(room_no):
    """Return (id, room_no, room_type, room_rent, room_bed, status) or None."""
    return fetch_one("SELECT id, room_no, room_type, room_rent, room_bed, status "
                     "FROM rooms WHERE room_no = %s", (room_no,))


def get_customer(cust_id):
    """Return the customer row or None."""
    return fetch_one("SELECT * FROM customer WHERE id = %s", (cust_id,))


# --------------------------------------------------------------------------
# Console helpers
# --------------------------------------------------------------------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause(message="Press Enter to continue..."):
    input("\n\n" + message)


def title(text, char="*", width=100):
    clear()
    print(f" {text}")
    print(char * width)


def fmt(value):
    return "" if value is None else str(value)


def ask_text(prompt, required=True):
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  This field cannot be empty.")


def ask_int(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if value < minimum:
            print(f"  Value must be at least {minimum}.")
            continue
        return value


def ask_float(prompt, minimum=0.0):
    while True:
        try:
            value = float(input(prompt).strip())
        except ValueError:
            print("  Please enter a number.")
            continue
        if value < minimum:
            print(f"  Value must be at least {minimum}.")
            continue
        return value


def ask_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  Please use the format yyyy-mm-dd.")


# --------------------------------------------------------------------------
# Rooms
# --------------------------------------------------------------------------
def add_room():
    title("Add New Room - Screen", "-")
    room_no = ask_int("\n Enter Room No : ", 1)
    if get_room(room_no) is not None:
        print(f"\n Room No {room_no} already exists in our database.")
        pause()
        return
    room_type = ask_text("\n Enter Room Type (AC/DELUX/Super Delux/Queen Delight/"
                         "Kings Special/Super Rich Special) : ")
    room_rent = ask_float("\n Enter Room Rent (INR) : ")
    room_bed = ask_text("\n Enter Room Bed Type (Single/Double/Triple) : ")

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO rooms (room_no, room_type, room_rent, room_bed, status) "
            "VALUES (%s, %s, %s, %s, 'free')",
            (room_no, room_type.upper(), room_rent, room_bed.upper()))
    print("\n Room added successfully.")
    pause()


def modify_room():
    title("Change Room Information")
    print("1.   Room Type")
    print("2.   Room Rent")
    print("3.   Room Bed")
    print("4.   Room Status (free / occupied / renovation)")
    choice = ask_int("Enter your choice : ")
    columns = {1: "room_type", 2: "room_rent", 3: "room_bed", 4: "status"}
    if choice not in columns:
        print("\n Invalid choice.")
        pause()
        return

    room_no = ask_int("Enter room No : ", 1)
    if get_room(room_no) is None:
        print("\n Room does not exist.")
        pause()
        return

    if choice == 2:
        value = ask_float("Enter new value : ")
    elif choice == 4:
        value = ask_text("Enter new value : ").lower()
    else:
        value = ask_text("Enter new value : ").upper()

    # `columns[choice]` comes from the fixed dictionary above, never from the user.
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE rooms SET {columns[choice]} = %s WHERE room_no = %s",
                       (value, room_no))
    print("\n Record Updated.")
    pause()


# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
def add_customer():
    title("Add New Customer - Screen", "-")
    name = ask_text("\n Enter Customer Name : ")
    address = ask_text("\n Enter Customer Address : ")
    phone = ask_text("\n Enter Customer Phone No : ")
    email = ask_text("\n Enter Customer Email ID : ")
    id_proof = ask_text("\n Enter Customer ID (Aadhar/Passport/DL/VoterID) : ")
    id_proof_no = ask_text("\n Enter Customer ID proof No : ")
    males = ask_int("\n Enter Total Males : ")
    females = ask_int("\n Enter Total Females : ")
    children = ask_int("\n Enter Total Children : ")

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO customer (name, address, phone, email, id_proof, "
            "id_proof_no, males, females, children) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (name, address.upper(), phone, email.upper(), id_proof.upper(),
             id_proof_no.upper(), males, females, children))
        new_id = cursor.lastrowid
    print(f"\n Customer added successfully. Customer ID = {new_id}")
    pause()


def modify_customer():
    title("Change Customer Information")
    fields = {
        1: ("Name", "name"),
        2: ("Address", "address"),
        3: ("Phone No", "phone"),
        4: ("Email ID", "email"),
        5: ("ID Proof", "id_proof"),
        6: ("ID Proof No", "id_proof_no"),
        7: ("Males", "males"),
        8: ("Females", "females"),
        9: ("Children", "children"),
    }
    for number, (label, _) in fields.items():
        print(f"{number}.   {label}")
    choice = ask_int("Enter your choice : ")
    if choice not in fields:
        print("\n Invalid choice.")
        pause()
        return

    cust_id = ask_int("Enter Customer No : ", 1)
    if get_customer(cust_id) is None:
        print("\n Customer does not exist.")
        pause()
        return

    column = fields[choice][1]
    if choice in (7, 8, 9):
        value = ask_int("Enter new value : ")
    else:
        value = ask_text("Enter new value : ")

    with db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE customer SET {column} = %s WHERE id = %s",
                       (value, cust_id))
    print("\n Record Updated.")
    pause()


# --------------------------------------------------------------------------
# Booking and billing
# --------------------------------------------------------------------------
def room_booking():
    title("Room Booking", "-")
    room_no = ask_int("Enter room no to book : ", 1)
    cust_id = ask_int("Enter customer ID : ", 1)
    date_of_occ = ask_date("Enter date of occupancy (yyyy-mm-dd) : ")
    advance = ask_float("Enter advance amount : ")

    room = get_room(room_no)
    customer = get_customer(cust_id)

    if room is None:
        print("\n Room does not exist.")
    elif customer is None:
        print("\n Customer does not exist.... Please add the customer first.")
    elif room[5] != "free":
        print(f"\n Room is not available for booking. Right now it is : {room[5]}")
    else:
        # Both statements succeed together or not at all.
        with db_cursor(commit=True) as cursor:
            cursor.execute("UPDATE rooms SET status = 'occupied' WHERE id = %s",
                           (room[0],))
            cursor.execute(
                "INSERT INTO booking (room_id, cust_id, doo, advance) "
                "VALUES (%s, %s, %s, %s)",
                (room[0], cust_id, date_of_occ, advance))
        print(f"\n Room no {room_no} booked for customer {cust_id}")
    pause()


def bill_generation():
    title("Bill Generation", "-")
    room_no = ask_int("Enter room no : ", 1)
    cust_id = ask_int("Enter customer ID : ", 1)

    room = get_room(room_no)
    if room is None:
        print("\n Room does not exist.")
        pause()
        return

    booking = fetch_one(
        "SELECT book_id, doo, advance FROM booking "
        "WHERE cust_id = %s AND room_id = %s AND dol IS NULL",
        (cust_id, room[0]))
    if booking is None:
        print("\n No active booking found for this room and customer.")
        pause()
        return

    customer = get_customer(cust_id)
    book_id, doo, advance = booking[0], booking[1], float(booking[2])
    rent = float(room[3])
    gst = float(SETTINGS["gst"])
    st = float(SETTINGS["st"])

    dol = date.today()
    total_days = max((dol - doo).days, 1)      # minimum charge: one day
    amount = total_days * rent
    gst_amount = amount * gst / 100
    st_amount = amount * st / 100
    payable_amount = amount - advance + gst_amount + st_amount

    with db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE rooms SET status = 'free' WHERE id = %s", (room[0],))
        cursor.execute("UPDATE booking SET dol = %s WHERE book_id = %s",
                       (dol, book_id))
        cursor.execute(
            "INSERT INTO bill (book_id, amount, bill_date, gst, st) "
            "VALUES (%s, %s, %s, %s, %s)",
            (book_id, round(payable_amount, 2), dol, gst, st))
        bill_id = cursor.lastrowid

    clear()
    print(f" {SETTINGS['hotel_name']}".rstrip())
    print(" Bill")
    print(LINE)
    print(f" Bill No            : {bill_id}")
    print(f" Customer           : {customer[1]}")
    print(f" Room No            : {room_no}")
    print(f" Date of Occupancy  : {doo}")
    print(f" Date of Leaving    : {dol}")
    print(f" Total Payable Days : {total_days}")
    print(f" Room Rent Per Day  : {rent:,.2f}")
    print(f" Total Amount       : {amount:,.2f}")
    print(f" Advance            : {advance:,.2f}")
    print(f" GST ({gst:g}%)          : {gst_amount:,.2f}")
    print(f" Service Tax ({st:g}%)  : {st_amount:,.2f}")
    print(f" Amount Payable     : {payable_amount:,.2f}")
    if payable_amount < 0:
        print(" (Negative amount means a refund is due to the customer.)")
    pause()


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------
def search_rooms():
    room_no = ask_int("Enter Room No : ", 1)
    room = get_room(room_no)
    title("Room Status")
    if room is None:
        print("Room does not exist.")
    else:
        print(f"Room NO     : {room[1]}")
        print(f"Room Type   : {room[2]}")
        print(f"Room Rent   : {fmt(room[3])}")
        print(f"Room Bed    : {fmt(room[4])}")
        print(f"Room Status : {fmt(room[5])}")
    pause()


def search_booking():
    cust_no = ask_int("Enter Customer No : ", 1)
    records = fetch_all(
        "SELECT b.book_id, r.room_no, c.name, b.doo, b.advance "
        "FROM booking b "
        "JOIN customer c ON b.cust_id = c.id "
        "JOIN rooms r ON b.room_id = r.id "
        "WHERE b.cust_id = %s AND b.dol IS NULL", (cust_no,))
    title(f"Booking information for customer ID : {cust_no}")
    print(f"{'Booking ID':<12}{'Room No':<10}{'Customer Name':<25}"
          f"{'Date of Occupancy':<20}{'Advance':>10}")
    print(LINE)
    for book_id, room_no, name, doo, advance in records:
        print(f"{book_id:<12}{room_no:<10}{fmt(name):<25}{str(doo):<20}"
              f"{float(advance):>10.2f}")
    if not records:
        print("No active bookings found.")
    pause()


def search_customer():
    title("Search Customer Database")
    fields = {
        1: ("Customer Name", "name"),
        2: ("Customer Address", "address"),
        3: ("Customer Phone", "phone"),
        4: ("Customer Email", "email"),
        5: ("Address Proof", "id_proof"),
        6: ("Address Proof ID", "id_proof_no"),
    }
    for number, (label, _) in fields.items():
        print(f"{number}.   {label}")
    choice = ask_int("Enter your choice : ")
    if choice not in fields:
        print("\n Invalid choice.")
        pause()
        return

    column = fields[choice][1]
    value = ask_text("Enter value that you want to search : ")
    records = fetch_all(f"SELECT * FROM customer WHERE {column} LIKE %s",
                        (f"%{value}%",))

    title(f"Search Result for {column} = {value}", "*", 140)
    print(f"{'ID':<5}{'Name':<22}{'Address':<32}{'Phone':<16}"
          f"{'Email':<32}{'ID Used':<18}{'ID No':<18}")
    for rec in records:
        print(f"{rec[0]:<5}{fmt(rec[1]):<22}{fmt(rec[2]):<32}{fmt(rec[3]):<16}"
              f"{fmt(rec[4]):<32}{fmt(rec[5]):<18}{fmt(rec[6]):<18}")
    if not records:
        print("No matching customers found.")
    pause()


def search_bills():
    bill_no = ask_int("Enter Bill No : ", 1)
    rec = fetch_one(
        "SELECT bl.bill_id, bl.amount, bl.bill_date, bl.gst, bl.st, bk.book_id, "
        "bk.doo, bk.dol, bk.advance, c.name, c.address, c.phone, c.email, r.room_no "
        "FROM bill bl "
        "JOIN booking bk ON bl.book_id = bk.book_id "
        "JOIN customer c ON bk.cust_id = c.id "
        "JOIN rooms r ON bk.room_id = r.id "
        "WHERE bl.bill_id = %s", (bill_no,))
    title(f"Bill information for Bill No : {bill_no}", "*", 100)
    if rec is None:
        print("No bill found with this number.")
    else:
        print(f"Bill NO            : {rec[0]}")
        print(f"Amount             : {rec[1]}")
        print(f"Bill Date          : {rec[2]}")
        print(f"GST Charged (%)    : {rec[3]}")
        print(f"Service Tax (%)    : {rec[4]}")
        print(f"Booking ID         : {rec[5]}")
        print(f"Room No            : {rec[13]}")
        print(f"Date of Occupancy  : {rec[6]}")
        print(f"Date of Leaving    : {rec[7]}")
        print(f"Advance Paid       : {rec[8]}")
        print(f"Customer Name      : {rec[9]}")
        print(f"Customer Address   : {rec[10]}")
        print(f"Customer Phone     : {rec[11]}")
        print(f"Customer Email ID  : {rec[12]}")
    pause()


def search_menu():
    while True:
        title("Search Menu")
        print("\n1.  Room Status")
        print("\n2.  Booking Status")
        print("\n3.  Customer Details")
        print("\n4.  Bills")
        print("\n5.  Back to Main Menu")
        choice = ask_int("\n\nEnter your choice ... : ")
        if choice == 1:
            run_action(search_rooms)
        elif choice == 2:
            run_action(search_booking)
        elif choice == 3:
            run_action(search_customer)
        elif choice == 4:
            run_action(search_bills)
        elif choice == 5:
            break


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
def report_room_status():
    records = fetch_all("SELECT id, room_no, room_type, room_rent, room_bed, status "
                        "FROM rooms ORDER BY room_no")
    title("Rooms Status - Report", "-", 100)
    print(f"{'Room ID':<9}{'Room No':<9}{'Room Type':<22}{'Rent':>10}  "
          f"{'Bedding':<10}{'Status':<12}")
    print(LINE)
    for idr, no, rtype, rent, bed, status in records:
        rent_text = "" if rent is None else f"{float(rent):.2f}"
        print(f"{idr:<9}{no:<9}{fmt(rtype):<22}{rent_text:>10}  "
              f"{fmt(bed):<10}{fmt(status):<12}")
    pause()


def report_booking_status():
    records = fetch_all(
        "SELECT b.book_id, r.room_no, b.doo, b.advance, c.name, c.address, c.phone "
        "FROM booking b "
        "JOIN customer c ON b.cust_id = c.id "
        "JOIN rooms r ON b.room_id = r.id "
        "WHERE b.dol IS NULL ORDER BY b.book_id")
    title("Booking Status - Report (current guests)", "-", 100)
    print(f"{'Booking ID':<12}{'Room No':<9}{'Check-in':<14}{'Advance':>10}  "
          f"{'Name':<22}{'Address':<28}{'Phone':<15}")
    print(LINE)
    for book_id, room_no, doo, advance, name, addr, phone in records:
        print(f"{book_id:<12}{room_no:<9}{str(doo):<14}{float(advance):>10.2f}  "
              f"{fmt(name):<22}{fmt(addr):<28}{fmt(phone):<15}")
    if not records:
        print("No rooms are currently occupied.")
    pause()


def print_collection(records, heading):
    title(heading, "-", 100)
    print(f"{'Bill No':<10}{'Bill Date':<14}{'Room No':<10}{'Customer':<28}"
          f"{'Amount':>12}")
    print(LINE)
    total = 0.0
    for bill_id, bill_date, room_no, name, amount in records:
        total += float(amount)
        print(f"{bill_id:<10}{str(bill_date):<14}{room_no:<10}{fmt(name):<28}"
              f"{float(amount):>12,.2f}")
    if not records:
        print("No bills found for this period.")
    print(LINE)
    print(f"{'Bills: ' + str(len(records)):<62}Total: {total:>12,.2f}")
    pause()


COLLECTION_SQL = (
    "SELECT bl.bill_id, bl.bill_date, r.room_no, c.name, bl.amount "
    "FROM bill bl "
    "JOIN booking bk ON bl.book_id = bk.book_id "
    "JOIN customer c ON bk.cust_id = c.id "
    "JOIN rooms r ON bk.room_id = r.id "
)


def report_todays_collection():
    today = date.today()
    records = fetch_all(COLLECTION_SQL + "WHERE bl.bill_date = %s ORDER BY bl.bill_id",
                        (today,))
    print_collection(records, f"Today's Collection - {today}")


def report_monthly_collection():
    today = date.today()
    month = ask_int(f"Enter month number (1-12) [current: {today.month}] : ", 1)
    year = ask_int(f"Enter year [current: {today.year}] : ", 1900)
    if month > 12:
        print("\n Month must be between 1 and 12.")
        pause()
        return
    records = fetch_all(
        COLLECTION_SQL + "WHERE MONTH(bl.bill_date) = %s AND YEAR(bl.bill_date) = %s "
        "ORDER BY bl.bill_date, bl.bill_id", (month, year))
    print_collection(records, f"Monthly Collection - {month:02d}/{year}")


def report_menu():
    while True:
        title("Report Menu")
        print("\n1.  Room Status")
        print("\n2.  Booking Status")
        print("\n3.  Today's Collection")
        print("\n4.  Monthly Collection")
        print("\n5.  Back to Main Menu")
        choice = ask_int("\n\nEnter your choice ... : ")
        if choice == 1:
            run_action(report_room_status)
        elif choice == 2:
            run_action(report_booking_status)
        elif choice == 3:
            run_action(report_todays_collection)
        elif choice == 4:
            run_action(report_monthly_collection)
        elif choice == 5:
            break


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
def system_settings():
    title("Change System Settings")
    fields = {
        1: ("Hotel Name", "hotel_name"),
        2: ("Hotel Address", "address"),
        3: ("Phone Number(s)", "phone"),
        4: ("Email ID", "email"),
        5: ("Current GST Rate (%)", "gst"),
        6: ("Current Service Rate (%)", "st"),
    }
    for number, (label, _) in fields.items():
        print(f"{number}.   {label}")
    choice = ask_int("Enter your choice : ")
    if choice not in fields:
        print("\n Invalid choice.")
        pause()
        return

    field_name = fields[choice][1]
    if choice in (5, 6):
        value = str(ask_float("Enter new value : "))
    else:
        value = ask_text("Enter new value : ")

    with db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE setting SET value = %s WHERE field_name = %s",
                       (value, field_name))
    load_settings()
    print("\n Record Updated.")
    pause()


# --------------------------------------------------------------------------
# Main menu
# --------------------------------------------------------------------------
def run_action(action):
    """Run a menu action; a database error shows a message instead of crashing."""
    try:
        action()
    except Error as err:
        print(f"\n Database error: {err}")
        pause()


def main_menu():
    actions = {
        1: add_room,
        2: add_customer,
        3: modify_room,
        4: modify_customer,
        5: room_booking,
        6: bill_generation,
        7: search_menu,
        8: report_menu,
        9: system_settings,
    }
    while True:
        title("H O T E L   M A N A G E M E N T   S Y S T E M")
        if SETTINGS["hotel_name"]:
            print(f" {SETTINGS['hotel_name']}")
        print("\n1.   Add New Room")
        print("\n2.   Add Customer")
        print("\n3.   Modify Room Information")
        print("\n4.   Modify Customer Information")
        print("\n5.   Room Booking")
        print("\n6.   Bill Generation")
        print("\n7.   Search Database")
        print("\n8.   Report Menu")
        print("\n9.   Settings")
        print("\n10.  Close application")
        choice = ask_int("\n\nEnter your choice ... : ")
        if choice == 10:
            print("\n Goodbye!")
            break
        if choice in actions:
            run_action(actions[choice])
        else:
            pause("Invalid choice. Press Enter to try again...")


def connect_or_exit():
    """Ask for the password if needed and make sure the database is reachable."""
    if DB_CONFIG["password"] is None:
        DB_CONFIG["password"] = getpass.getpass(
            f"MySQL password for user '{DB_CONFIG['user']}': ")
    try:
        load_settings()
    except Error as err:
        print(f"\nCould not connect to the '{DB_CONFIG['database']}' database: {err}")
        print("Check that MySQL is running, the password is correct and that you "
              "have imported database/hotel.sql (see README.md).")
        sys.exit(1)


if __name__ == "__main__":
    connect_or_exit()
    main_menu()
