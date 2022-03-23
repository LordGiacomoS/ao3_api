import os
import AO3

passkey = os.environ["passkey"]
session = AO3.Session("L_GS", passkey)


#url = "http://archiveofourown.org/collections/L_GSTest"
url = "http://archiveofourown.org/collections/L_GSsFicRecommendations"
collid = AO3.utils.collectionid_from_url(url)
collection = AO3.Collection(collid, session)

print(f"Bookmarks: {session.bookmarks}")
print(f"Collection ID: {collid}")
#print(f"Pages of works: {collection.work_pages}")

#session.refresh_auth_token()
#collection._manage_items_action(session, type="approved", item_num=26, action="unreview")

#manage_list = collection._manage_items_list(session, type="approved")

collection.print_management_list(session, type="approved", item_amt=)



#print(type(manage_list))
#if type(manage_list) is list:
#    for num, item in enumerate(manage_list, 1):
#        print(num, item)
#elif type(manage_list) is str:
#    print(manage_list)

#item_pages = collection._manage_items_pages(session, type="approved")
#print(f'Items Pages: {item_pages}')



#for item in collection.items:
#    print(f"{item}")
      
  





#print(list)








#output = []

#item_list = list.find("form", {"method": "post"})
#for item in item_list.find_all("li", {"class": "collection item picture blurb group"}):
#    h4 = item.find_all("h4")[1]
#    if h4 is None:
#        continue
    #output.append(item.find_all("h4"))
#    if "/works/" in str(h4.contents):
#        output.append("work")
#    elif "/series/" in str(h4.contents):
#        output.append("series")
#print(output)




#soup = collection.get(f"https://archiveofourown.org/collections/{collection.id}/items")

#print(soup.status_code)
#soup = BeautifulSoup(soup.content, "lxml")
#error_div = soup.find("div", {"class": "error"})


#html = list.prettify()
#with open("RecsList.html", "w") as f:
#    f.write(html)