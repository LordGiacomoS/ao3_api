import re
import lxml

from datetime import date
from functools import cached_property

from bs4 import BeautifulSoup

from . import threadable, utils
from .common import get_work_from_banner, get_series_from_banner, url_join
from .requester import requester
from .users import User

class Collection:
    def __init__(self, collectionid, session=None, load=True):
        """Creates a new collection object

        Args:
            collectionid (int/str): ID of the collection
            session (AO3.Session, optional): Session object. Defaults to None.
            load (bool, optional): If true, the collection is loaded on initialization. Defaults to True.

        Raises:
            utils.InvalidIdError: Invalid collection ID
        """

        self.id = collectionid
        self._session = session
        self._soup = None
        if load:
            self.reload()
      
    def __eq__(self, other):
        return isinstance(other, __class__) and other.id == self.id
    
    def __repr__(self):
        try:
            return f"<Collection [{self.name}]>" 
        except:
            return f"<Collection [{self.id}]>"
        
    def __getstate__(self):
        d = {}
        for attr in self.__dict__:
            if isinstance(self.__dict__[attr], BeautifulSoup):
                d[attr] = (self.__dict__[attr].encode(), True)
            else:
                d[attr] = (self.__dict__[attr], False)
        return d
                
    def __setstate__(self, d):
        for attr in d:
            value, issoup = d[attr]
            if issoup:
                self.__dict__[attr] = BeautifulSoup(value, "lxml")
            else:
                self.__dict__[attr] = value
                
    def set_session(self, session):
        """Sets the session used to make requests for this collection

        Args:
            session (AO3.Session/AO3.GuestSession): session object
        """
        
        self._session = session 
        
    @threadable.threadable
    def reload(self):
        """
        Loads information about this collection.
        This function is threadable.
        """
        
        for attr in self.__class__.__dict__:
            if isinstance(getattr(self.__class__, attr), cached_property):
                if attr in self.__dict__:
                    delattr(self, attr)
                    
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}")
        if "Error 404" in self._soup.text:
            raise utils.InvalidIdError("Cannot find collection")

    @cached_property
    def url(self):
        """Returns the URL to this collection

        Returns:
            str: series URL
        """    

        return f"https://archiveofourown.org/collections/{self.id}"
        
    @property
    def loaded(self):
        """Returns True if this collection has been loaded"""
        return self._soup is not None
        
    @cached_property
    def authenticity_token(self):
        """Token used to take actions that involve this collection"""
        
        if not self.loaded:
            return None
        
        token = self._soup.find("meta", {"name": "csrf-token"})
        return token["content"]

    @cached_property
    def name(self):
        h2 = self._soup.find("h2", {"class": "collections"})
        name = h2.get_text().strip()
        return name
        
    @cached_property
    def maintainers(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        ul = self._soup.find("ul", {"class": "mods"})
        return [User(maintainer.getText(), load=False) for maintainer in ul.find_all("a")]
    
    @cached_property
    def date_begun(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        dl = self._soup.find("dl", {"class": "meta group"})
        info = dl.findAll(("dd", "dt"))
        last_dt = None
        for field in info:
            if field.name == "dt":
                last_dt = field.getText().strip()
            elif last_dt == "Active since:":
                date_str = field.getText().strip()
                break
        return date(*list(map(int, date_str.split("-"))))

    @cached_property
    def nworks(self):
        a = self._soup.find("a", {"href": f"/collections/{self.id}/works"})
        works = a.get_text().replace("Works (","").replace(")","")
        return int(works.replace(",", ""))

    @cached_property
    def description(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        div = self._soup.find("div", {"class": "primary header module"})
        if div is not None: 
            info = div.findAll("blockquote")
            desc = None
            for field in info:
                if field.name == "blockquote":
                    desc = field.getText().strip()
        if div is None: desc = "This collection has no description."
        return desc
      
    @cached_property
    def intro(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        div = self._soup.find("div", {"class": "module", "id": "intro"})
        if div is not None: 
            info = div.findAll("p")
            intro = None
            for field in info:
                if field.name == "p":
                    intro = field.getText().strip()
        if div is None: intro = "This collection has no introduction."
        return intro

    @cached_property
    def faq(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        div = self._soup.find("div", {"class": "module", "id": "faq"})
        if div is not None: 
            info = div.findAll("p")
            faq = None
            for field in info:
                if field.name == "p":
                    faq = field.getText().strip()
        if div is None: faq = "This collection has no FAQ."
        return faq

    @cached_property
    def rules(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        div = self._soup.find("div", {"class": "module", "id": "rules"})
        if div is not None: 
            info = div.findAll("p")
            rules = None
            for field in info:
                if field.name == "p":
                    rules = field.getText().strip()
        if div is None: rules = "This collection has no rules."
        return rules
    
    @cached_property
    def type(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/profile")
        p = self._soup.find("p", {"class": "type"})
        info = p.get_text().replace("(","").replace(")","").strip()
        openness, moderation = info.split(",")
        return openness, moderation

    @cached_property
    def parent(self):
        div = self._soup.find("div", {"class": "region", "id": "dashboard", "role": "navigation region"})
        a = div.find(string="Parent Collection")
        #This uses a somewhat convoluted method to find the right place for the link to the parent collection (because AO3 didn't give any special classes or IDs to the html tag it's in), but it works.
        if a is not None:
            parentid = a.parent['href'].replace("/collections/","")
        if a is None: parentid = "This collection has no parent collections."
        return parentid
        
    @cached_property
    def subcollections(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/collections")
        ul = self._soup.find("ul", {"class": "collection picture index group"})
        subs = []
        for sub in ul.find_all("span", {"class": "name"}):
            subs.append(sub.get_text().replace("(","").replace(")",""))
        return subs
    
    @staticmethod
    def str_format(string):
        """Formats a given string

        Args:
            string (str): String to format

        Returns:
            str: Formatted string
        """

        return string.replace(",", "")

    @cached_property
    def bookmarks(self):
        """Returns the number of works bookmarked to collection

        Returns:
            int: Number of bookmarks 
        """
        self._soup_bookmarks = self.request(f"https://archiveofourown.org/collections/{self.id}/bookmarks")
        div = self._soup_bookmarks.find("div", {"id": "inner"})
        span = div.find("span", {"class": "current"}).getText().replace("(", "").replace(")", "")
        n = span.split(" ")[2]
        return int(self.str_format(n))

    @cached_property
    def _bookmarks_pages(self):
        self._soup_bookmarks = self.request(f"https://archiveofourown.org/collections/{self.id}/bookmarks")
        pages = self._soup_bookmarks.find("ol", {"title": "pagination"})
        if pages is None:
            return 1
        n = 1
        for li in pages.findAll("li"):
            text = li.getText()
            if text.isdigit():
                n = int(text)
        return n

    def get_bookmarks(self, use_threading=False):
        """
        Get this collection's bookmarked works. Loads them if they haven't been previously

        Returns:
            list: List of works
        """
        
        if self._bookmarks is None:
            if use_threading:
                self.load_bookmarks_threaded()
            else:
                self._bookmarks = []
                for page in range(self._bookmarks_pages):
                    self._load_bookmarks(page=page+1)
        return self._bookmarks
    
    @threadable.threadable
    def load_bookmarks_threaded(self):
        """
        Get the collection's bookmarks using threads.
        This function is threadable.
        """ 
        
        threads = []
        self._bookmarks = []
        for page in range(self._bookmarks_pages):
            threads.append(self._load_bookmarks(page=page+1, threaded=True))
        for thread in threads:
            thread.join()
  
    @threadable.threadable
    def _load_bookmarks(self, page=1):
        from .works import Work
        from .series import Series
        self._soup_bookmarks = self.request(f"https://archiveofourown.org/collections/{self.id}/bookmarks?page={page}")
            
        ol = self._soup_bookmarks.find("ol", {"class": "bookmark index group"})

        for item in ol.find_all("li", {"role": "article"}):
            authors = []
            if item.h4 is None:
                continue
            if "/works/" in str(item.h4.contents):
                self._bookmarks.append(get_work_from_banner(item))
            elif "/series/" in str(item.h4.contents):
                self._bookmarks.append(get_series_from_banner(item))

    @cached_property
    def _works_pages(self):
        self._soup_works = self.request(f"https://archiveofourown.org/collections/{self.id}/works")
        pages = self._soup_works.find("ol", {"title": "pagination"})
        if pages is None:
            return 1
        n = 1
        for li in pages.findAll("li"):
            text = li.getText()
            if text.isdigit():
                n = int(text)
        return n

    @property
    def work_pages(self):
        """
        Returns how many pages of works a collection has

        Returns:
            int: Amount of pages
        """
        return self._works_pages
    
    @cached_property
    def work_list(self):
        self._soup = self.request(f"https://archiveofourown.org/collections/{self.id}/works")
        ol = self._soup.find("ol", {"class": "work index group"})
        works = []
        for work in ol.find_all("li", {"role": "article"}):
            if work.h4 is None:
                continue
            works.append(get_work_from_banner(work))
        #     authors = []
        #     if work.h4 is None:
        #         continue
        #     for a in work.h4.find_all("a"):
        #         if "rel" in a.attrs.keys():
        #             if "author" in a["rel"]:
        #                 authors.append(User(a.string, load=False))
        #         elif a.attrs["href"].startswith("/works"):
        #             workname = a.string
        #             workid = utils.workid_from_url(a["href"])
        #     new = Work(workid, load=False)
        #     setattr(new, "title", workname)
        #     setattr(new, "authors", authors)
        #     works.append(new)
        return works

    def _manage_items_pages(self, session, type):
        if type == "awaiting_approval" or type == "" or type is None:
            url = f"https://archiveofourown.org/collections/{self.id}/items"
        if type == "invited":
            url = f"https://archiveofourown.org/collections/{self.id}/items?invited=true"
        if type == "rejected":
            url = f"https://archiveofourown.org/collections/{self.id}/items?rejected=true"
        if type == "approved":
            url = f"https://archiveofourown.org/collections/{self.id}/items?approved=true"

        page_tag = ("&amp;page=")
        self._soup_items = self.request(f"{url}{page_tag}1")
        
        pages = self._soup_items.find("ol", {"class": "pagination actions"})
        if pages is None:
            return 1
        n = 1
        for li in pages.findAll("li"):
            text = li.getText()
            if text.isdigit():
                n = int(text)
        return n
    
    def _manage_items_action(self, session, type, item_num=None, action=None, item_amt=None, start_from=None):
        if start_from is None:
            start_from = 1
        self._soup = self._manage_items_list(session, type, item_amt, start_from)
        if item_num is None and action is not None:
            raise utils.UnselectedError(f"Item to {action} is unspecified.")
        if item_num is not None and action is None:
            raise utils.UnselectedError("No action is specified for this item.")

        if type == "awaiting_approval" or type == "" or type is None:
            url = f"https://archiveofourown.org/collections/{self.id}/items"
        if type == "invited":
            url = f"https://archiveofourown.org/collections/{self.id}/items?invited=true"
        if type == "rejected":
            url = f"https://archiveofourown.org/collections/{self.id}/items?rejected=true"
        if type == "approved":
            url = f"https://archiveofourown.org/collections/{self.id}/items?approved=true"

        page, item = divmod(item_num, 20)
        item_loc = int(item*2)-1
        print (page+1, item_loc)
        self._soup_items = self.request(url_join(url, f"&amp;page={page+1}"))
                                        
        item_html = self._soup_items.find("form", {"method": "post"})
        
        self.authenticity_token = self._soup_items.find("meta", {"name": "csrf-token"}).get('content')
      
        count = 1
        if item_html is not None:
            for h4 in item_html.find_all("h4"):
                if count == item_loc:
                    id = h4.get('id')
                count += 1
            idnum = id.split("_")[2]
        if item_html is None:
            raise utils.BlankError("No items in this category to be reviewed.")

        if self.authenticity_token is not None:
            at = self.authenticity_token
        else:
            at = session.authenticity_token

        data = {
            "authenticity_token": at,
            "commit": "Submit",
            "_method": "patch"
        }
        
        if action == "unreview": data[f"collection_items[{idnum}][collection_approval_status]"] = "unreviewed"
        if action == "approve": data[f"collection_items[{idnum}][collection_approval_status]"] = "approved"
        if action == "reject": data[f"collection_items[{idnum}][collection_approval_status]"] = "rejected"

        if action == "remove": data[f"collection_items[{idnum}][remove]"] = "1"
        url = f"https://archiveofourown.org/collections/{self.id}/items/update_multiple"
        req = session.session.post(url, data=data)
      
        print(req.status_code)
      
        if req.status_code == 302:
            print(req.headers["Location"])
            if req.headers["Location"] == utils.AO3_AUTH_ERROR_URL:
                raise utils.AuthError("Invalid authentication token. Try calling session.refresh_auth_token()")
  
    def _manage_items_list(self, session, type="", item_amt=None, start_from=None):
        from .works import Work
        from .series import Series
          
        start_page, start_item = divmod(start_from, 20)
      
        if type == "awaiting_approval" or type == "" or type is None:
            url = f"https://archiveofourown.org/collections/{self.id}/items"
        if type == "invited":
            url = f"https://archiveofourown.org/collections/{self.id}/items?invited=true"
        if type == "rejected":
            url = f"https://archiveofourown.org/collections/{self.id}/items?rejected=true"
        if type == "approved":
            url = f"https://archiveofourown.org/collections/{self.id}/items?approved=true"

        self._soup_items = self.request(f"{url}&amp;page=1")
        ol = self._soup_items.find("ol", {"class": "pagination actions"})

        if ol is None:
            pages = 1
        pages = 1
        for li in ol.findAll("li"):
            text = li.getText()
            if text.isdigit():
                pages = int(text)
                  
        items = []
        count = 0

        for page in range(start_page, pages):
            if page+1 != 0:
                self._page_soup_items = self.request(f"{url}&amp;page={page+1}")
                item_list = self._page_soup_items.find("form", {"method": "post"})

            if item_list is not None:
                for item in item_list.find_all("li", {"class": "collection item picture blurb group"}):
                    if item_amt is not None and len(items) >= item_amt:
                        return items
                    
                    for h4 in item.find_all("h4"):
                        if h4.get('id') is not None:
                            continue
                        count += 1
                        if count <= start_item:
                            continue
                        for a in h4.find_all("a"):
                            if a.attrs["href"].startswith("/series/"):
                                seriesname = a.string
                                seriesid = utils.seriesid_from_url(a['href'])
                                new = Series(seriesid, load=False)
                                if seriesname is not None:
                                      setattr(new, "name", seriesname)
                            if a.attrs["href"].startswith("/collections/"):
                                workname = a.string
                                workid = utils.workid_from_url(a['href'])
                                new = Work(workid, load=False)
                                if workname is not None:
                                    setattr(new, "title", workname)
                        if new is not None:
                            items.append(new)
            if item_list is None:
                items = "No items in this category."
        return items

    def print_management_list(self, session, type=None, item_amt=None, start_from=None):
        if start_from is None:
            start_from = 1

        manage_list = self._manage_items_list(session, type, item_amt, start_from)
        
        if isinstance(manage_list, list):
            for num, item in enumerate(manage_list, start_from):
                print(num, item)
            if item_amt is not None and len(manage_list) < item_amt:
                print(f"Remaining items in category is less than {item_amt}. ({len(manage_list)})")
        elif isinstance(manage_list, str):
            print(manage_list)
      
    def get(self, *args, **kwargs):
        """Request a web page and return a Response object"""  
        
        if self._session is None:
            req = requester.request("get", *args, **kwargs)
        else:
            req = requester.request("get", *args, **kwargs, session=self._session.session)
        if req.status_code == 429:
            raise utils.HTTPError("We are being rate-limited. Try again in a while or reduce the number of requests")
        return req

    def request(self, url):
        """Request a web page and return a BeautifulSoup object.

        Args:
            url (str): Url to request

        Returns:
            bs4.BeautifulSoup: BeautifulSoup object representing the requested page's html
        """

        req = self.get(url)
        soup = BeautifulSoup(req.content, "lxml")
        return soup