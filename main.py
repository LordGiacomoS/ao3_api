import AO3

session = AO3.Session("[username]", "[password]")


url = "http://archiveofourown.org/collections/L_GSTest"
collid = AO3.utils.collectionid_from_url(url)
collection = AO3.Collection(collid, session)

print(f"Bookmarks: {session.bookmarks}")
print(f"Collection ID: {collid}")

collection.print_management_list(session, type="approved")
