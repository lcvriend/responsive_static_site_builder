"""
The page_loader module
======================
This module contains the PageContent class that is used to make the following page elements accessible for further processing:

    - page_id
    - page content
        stored as respective sections containing:
        - section text
        - function call
        - optional argument
    - creation date of the content
    - modification data of the content

 Generally, the page content is stored in an md file in the content folder of the project. A class can be instantiated from this md file by using the read_md function also contained in this module.

    Objects in this module
    ----------------------
    - PageContent (class)
    - read_md (function)
"""

import re
import datetime as dt


class PageContent:
    """
    The PageContent class is used to collect all sections in a page. Page sections are stored as a dictionary. These dictionaries contain the recipe for parsing the section into the correct html.

    The class can be instantiated from a markdown file by using the function read_md. Indexing the instance will return the section at the given index. Iterating over the instance will return all sections.
    """

    def __init__(self, page_id, page_text, ctime, mtime):
        self.page_id = page_id
        self.ctime = ctime
        self.mtime = mtime
        self.sections = self._extract_sections(page_text)

    def __iter__(self):
        idx = 0
        while idx < len(self.sections):
            yield self.sections[idx]
            idx += 1

    def __getitem__(self, idx):
        return self.sections[idx]

    @staticmethod
    def _extract_sections(page_text):
        """
        Split the markdown text into a list of section objects based on the section separator (five or more underscores).

        The resulting section objects consist of a dictionary of the following items:
        =========  ======================================
        Key        Value
        =========  ======================================
        text       Text content of the section
        function   Function for rendering the section
        arg        Argument to be passed to the function
        =========  ======================================

        -----
        :param text: Page text as string.
        :returns: page_id and the contents of the page as a list of section
        dictionaries.
        """

        out_sections = list()
        sections = re.split(r"_{5,}\n", page_text)
        for section in sections:
            arg = None
            if len(section) == 0:
                continue
            elif section[0] == '|':
                first_line, text = section.split('\n', 1)
                if ':' in first_line:
                    first_line, arg = first_line.split(':')
                function = first_line[1:].lower()
            else:
                text = section
                function = 'markdown'

            out_sections.append(dict(text=text,
                                     function=function,
                                     arg=arg))
        return out_sections


def read_md(file_path_md, page_ids):
    """
    Read markdown file and check its page id. If the page id exists within the
    site structure return an instance of PageContent, else return None.
    Extracts the following elements from the md file:
    - Page id
    - Page text
    - Creation time
    - Modification time

    -----
    :param file_path: Path to the markdown file to be read.
    :returns: Instance of PageContent or None if no valid page_id/text_body is found.
    """
    ctime = dt.datetime.fromtimestamp(file_path_md.stat().st_ctime)
    mtime = dt.datetime.fromtimestamp(file_path_md.stat().st_mtime)
    md = file_path_md.read_text(encoding='utf-8')

    if not '\n' in md:
        return None

    page_id, page_text = md.split('\n', 1)

    if not page_id in page_ids:
        return None

    return PageContent(page_id, page_text, ctime, mtime)
