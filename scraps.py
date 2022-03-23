    def _manage_items_pages2(self, session, type):
        if type == "awaiting_approval" or type == "" or type is None:
            self._soup_items = self.request(f"https://archiveofourown.org/collections/{self.id}/items")
        if type == "invited":
            self._soup_items = self.request(f"https://archiveofourown.org/collections/{self.id}/items?invited=true")
        if type == "rejected":
            self._soup_items = self.request(f"https://archiveofourown.org/collections/{self.id}/items?rejected=true")
        if type == "approved":
            self._soup_items = self.request(f"https://archiveofourown.org/collections/{self.id}/items?approved=true")

        ol = self._soup_items.find("ol", {"class": "pagination actions"})

        pages = 0
        if ol is None:
            pages = 1
        else:
            for li in ol.findAll("li"):
                if li.getText().isdigit():
                    pages = int(li.getText())
        return pages