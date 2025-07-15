from Contacts import CNContactStore, CNContactFetchRequest, CNContactGivenNameKey, CNContactFamilyNameKey, CNContactPhoneNumbersKey
import re

def get_group_participants(chat_cursor, chat_id, contact_map):
    """
    For a given chat_id, return a list of participant names.
    """
    query = """
    SELECT handle.id
    FROM chat_handle_join
    JOIN handle ON chat_handle_join.handle_id = handle.ROWID
    WHERE chat_handle_join.chat_id = ?;
    """
    chat_cursor.execute(query, (chat_id,))
    participants = []
    for row in chat_cursor.fetchall():
        handle_id = row[0]
        name = contact_map.get(handle_id, handle_id)
        participants.append(name)
    return participants


def get_contacts():
    store = CNContactStore.alloc().init()
    
    keys_to_fetch = [
        CNContactGivenNameKey,
        CNContactFamilyNameKey,
        CNContactPhoneNumbersKey
    ]
    
    request = CNContactFetchRequest.alloc().initWithKeysToFetch_(keys_to_fetch)
    
    contacts = {}
    success, error = store.enumerateContactsWithFetchRequest_error_usingBlock_(
        request, None,
        lambda contact, stop: contacts.update(parse_contact(contact))
    )
    
    if not success:
        if error:
            print(f"Error fetching contacts: {error.localizedDescription()}")
        else:
            print("Unknown error fetching contacts.")
    return contacts

def parse_contact(contact):
    contact_data = {}
    
    first_name = contact.givenName() or ""
    last_name = contact.familyName() or ""
    full_name = f"{first_name} {last_name}".strip()
    
    if not full_name:
        full_name = "Unknown Contact" 

    for phone_number_obj in contact.phoneNumbers():
        phone_number = phone_number_obj.value().stringValue()
        normalized_number = re.sub(r'[\s\-()]+', '', phone_number)
        if not normalized_number.startswith('+') and len(normalized_number) > 7: 
            normalized_number = '+' + normalized_number 
        
        contact_data[normalized_number] = full_name

    return contact_data

if __name__ == "__main__":
    print("Fetching contacts...")
    contact_map = get_contacts()
    if contact_map:
        print(f"Successfully fetched {len(contact_map)} contact entries.")
        print("\nPartial Contact Map:")
        for num, name in list(contact_map.items())[:100]:
            print(f"  {num}: {name}")
    else:
        print("No contacts fetched.")