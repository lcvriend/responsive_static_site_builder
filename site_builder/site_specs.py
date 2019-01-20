"""
The site_specs module
=========================
This module contains:
- The SiteProperties class containing the relevant metadata of the site:
    - Name
    - Version
    - Language
    - Footer data
- The SiteStructure class stores the organizational structure of the site to be built. It defines the order of the sections, chapters, groups and pages. This data is mainly used to generate the navigational elements of the html. Usually, a site structure is instantiated from an excel file using the read_excel function also contained in this module.

    Objects in this module
    ----------------------
    - SiteProperties (class)
    - SiteStructue (class)
    - read_excel (function)
    - convert_to_href (function)

Upon initialization this module reads the properties file in the specified content folder and creates an instance of the SiteProperties class as 'properties'.
"""

import configparser
import pandas as pd
from collections import OrderedDict
from site_builder import section_processing
from site_builder import config


class SiteProperties:
    """
    The SiteProperties class stores the following metadata of the site:
        - name
        - version
        - language
        - footer_info
        - footer_contact

    All the information is stored at the class level. The properties are loaded by the classmethod `load_properties`. There is also a classmethod for returning the settings as an appropriately formatted ini-string.

    COMMENT | Is this a good way to use a class? Is there a more straightforward way of setting this up?
    """

    name = '<name of the site>'
    version = '0'
    language = '<language>'
    tbd = '<message to be printed on empty pages>'
    _footer_info = '<text for the information\n section of the footer\n goes here.>'
    _footer_contact = '<text for the contact\n section of the footer\n goes here.>'

    def __init__(self):
        pass

    @classmethod
    def load_properties(cls, no_increment=False):
        """
        Load the `properties.ini` file in the content folder. If no such file was found, then create one with the default values and read that.

        -----
        :param no_increment: If this flag is set to true, then the build version will not be updated.
        :returns: None
        """

        path_content = config.PATH_CONFIG['content']
        properties_file = path_content / 'properties.ini'
        properties = configparser.ConfigParser()

        try:
            properties.read(properties_file)
        except:
            with open(path_content / 'properties.ini', 'w') as f:
                f.write(SiteProperties.create_ini())
            properties.read(properties_file)
        finally:
            values = properties['PROPERTIES']

            if no_increment == False:
                # Increment build version number
                try:
                    values['version'] = str(int(values['version']) + 1)
                except:
                    pass

            cls.name = values['name']
            cls.version = values['version']
            cls.language = values['language']
            cls.tbd = values['tbd']
            cls._footer_info = values['footer_info']
            cls._footer_contact = values['footer_contact']

            cls.footer_info = section_processing._string_to_markdown(values['footer_info'])
            cls.footer_contact = section_processing._string_to_markdown(values['footer_contact'])

            return None

    @classmethod
    def create_ini(cls):
        """
        TBD
        """
        footer_contact = cls._footer_contact.replace('\n', '\n    ')
        footer_info = cls._footer_info.replace('\n', '\n    ')
        ini = f'[PROPERTIES]\n'\
            f'# Properties\n'\
            f'name = {cls.name}\n'\
            f'version = {cls.version}\n'\
            f'language = {cls.language}\n'\
            f'tbd = {cls.tbd}\n'\
            f'\n'\
            f'# Footer\n'\
            f'footer_contact = {footer_contact}\n'\
            f'footer_info = {footer_info}'
        return ini


class SiteStructure:
    """
    The SiteStructure class contains the structure for the site. It determines the hierarchy and order of the site pages. During site construction the SiteStructure is used to generate the navigational elements of the html. A SitesStructure has the following hierarchy:

    > Site
    > > Sections
    > > > Chapters
    > > > > Groups
    > > > > > Pages

    At its core the SiteStructure consists of a DataFrame with the following  columns:
    ==============  ========================================
    Column name     Description
    ==============  ========================================
    Section_order   Order of the section within the site
    Section         Section name
    Chapter_order   Order of the chapter within the section
    Chapter         Chapter name
    Group_order     Order of the group within the chapter
    Group           Group name
    Page_order      Order of the page within the group
    Page            Page name
    Code            Code for crossreferencing to this page
    Href            Href of the page
    Href_nest       Nest level of the page
    ==============  ========================================
    Each row represents a page on the site and is indexed by its page id.    The underlying df is directly accessible through the `df_site` attribute. Site pages can be retrieved through the class index. The indexing method accepts either page ids or integers and returns the page information as a pandas Series.

    A SiteStructure object has the following attributes and methods:
    ==============  ==================================================
    Attribute       Description
    ==============  ==================================================
    df_site         Site structure as DataFrame
    page_ids        Page_ids as list
    sections        Sections as list
    href_sections   Section names with their href as list of tuples
    href_pages      Pages with their hrefs as list of tuples
    crossrefs       Crossref codes with their hrefs as list of tuples
    ==============  ==================================================

    ===============  =================================================
    Method           Description
    ===============  =================================================
    sitemap          Return the sitemap as a nested dictionary.
    adjacent pages   Return previous and next name/href from page id.
    ===============  =================================================

    The class also contains the following static methods which are used during class instantiation:
    =====================  ======================================
    Static method          Description
    =====================  ======================================
    _find_hrefs_sections   Return hrefs_sections from DataFrame.
    _find_hrefs_pages      Return hrefs_pages from DataFrame.
    _find_crossrefs        Return crossrefs from DataFrame.
    =====================  ======================================
    """

    def __init__(self, df_site):
        self.df_site = df_site
        self.page_ids = self.df_site.index.values
        self.sections = self.df_site.Section.unique().tolist()
        self.href_sections = self._find_hrefs_sections(self.df_site)
        self.href_pages = self._find_hrefs_pages(self.df_site)
        self.crossrefs = self._find_crossrefs(self.df_site)

    def __getitem__(self, page_id):
        if isinstance(page_id, str):
            return self.df_site.loc[page_id]
        elif isinstance(page_id, int):
            return self.df_site.iloc[page_id]

    def __len__(self):
        return len(self.df_site)

    def sitemap(self):
        """
        Create sitemap as nested ordered dictionaries from site structure.

        -----
        :returns: sitemap as nested OrderedDict.
        """

        def serie_to_df(df):
            if isinstance(df, pd.Series):
                return df.to_frame().T
            else:
                return df

        df = (self.df_site[['Section', 'Chapter', 'Group', 'Page', 'Href']]
                  .fillna({'Chapter': self.df_site.Chapter_order,
                           'Group': self.df_site.Group_order}))

        dct_sitemap = OrderedDict()
        for section in df.Section.unique():
            dct_section = OrderedDict()
            df_section = serie_to_df(df.set_index('Section')
                                       .xs(section))
            for chapter in df_section.Chapter.unique():
                dct_chapter = OrderedDict()
                df_chapter = serie_to_df(df_section.set_index('Chapter')
                                                   .xs(chapter))
                for group in df_chapter.Group.unique():

                    pages = df_chapter.set_index('Group').loc[group].Page
                    hrefs = df_chapter.set_index('Group').loc[group].Href

                    if isinstance(pages, str):
                        pages = [pages]
                        hrefs = [hrefs]
                    else:
                        pages = pages.values
                        hrefs = hrefs.values

                    page_href = list(zip(pages, hrefs))
                    dct_chapter[group] = page_href
                    dct_section[chapter] = dct_chapter
                    dct_sitemap[section] = dct_section

        return dct_sitemap

    def adjacent_pages(self, page_id):
        """
        Returns name and href of previous and next pages of given page id in a dictionary.
        - First page refers to last page for previous.
        - Last page refers to first page for next.

        -----
        :param page_id: id of the current page.
        :returns: Name and href of previous and next page as dictionary.
        """

        idx_current = list(self.href_pages.keys()).index(page_id)

        prev_id = list(self.href_pages.keys())[idx_current - 1]
        prev_page = self.href_pages[prev_id][0]
        prev_href = self.href_pages[prev_id][1]

        try:
            next_id = list(self.href_pages.keys())[idx_current + 1]
        except IndexError:
            next_id = list(self.href_pages.keys())[0]
        finally:
            next_page = self.href_pages[next_id][0]
            next_href = self.href_pages[next_id][1]

        return dict(prev_page=prev_page,
                    prev_href=prev_href,
                    next_page=next_page,
                    next_href=next_href)

    def breadcrumbs(self, page_id):
        """
        Returns page name in breadcrumb format:

            section | chapter | group | page

        - Elements are ignored if they do not have a string format.
        - If all string elements are equal, only the first is used.

        :param page_id: id of the current page.
        :returns: Breadcrumb representation of the page as string.
        """

        section = self[page_id]['Section']
        chapter = self[page_id]['Chapter']
        group = self[page_id]['Group']
        page_name = self[page_id]['Page']

        page_items = [section, chapter, group, page_name]
        page_items = [item for item in page_items if isinstance(item, str)]
        if len(set(page_items)) == 1:
            page_items = [page_items[0]]

        return ' | '.join(page_items)

    @staticmethod
    def _find_hrefs_sections(df_site):
        """
        Create a list of tuples, associating a section with the href of the first page of that section.

        -----
        :param df_site: The site structure dataframe
        :returns: A list of tuples containing section name and href of its
        associated page.
        """

        df = (df_site.loc[:, ['Section_order', 'Section', 'Href']]
                     .groupby(['Section_order', 'Section'])
                     .first())
        df.index = df.index.droplevel()
        return list(zip(df.index, df.Href.values))

    @staticmethod
    def _find_hrefs_pages(df_site):
        """
        Helper function for creating a list of page id, href tuples.

        -----
        :param df_site: The site structure dataframe
        :returns: A list of tuples containing the page id and its href.
        """

        href_pages = OrderedDict()
        for page_id, page, href in list(zip(df_site.index.values,
                                            df_site.Page.values,
                                            df_site.Href.values)):
            href_pages[page_id] = (page, href)
        return href_pages

    @staticmethod
    def _find_crossrefs(df_site):
        """
        Helper function for creating a list of crossreference code, href tuples.

        -----
        :param df_site: The site structure dataframe
        :returns: List of tuples containing the crossreference code and its
        href.
        """

        df = df_site.loc[df_site.Code.isna() == False]
        return list(zip(df.Code.values, df.Href.values))


def read_excel(path_to_structure_file):
    """
    Helper function for creating a SiteStructure object from an excel file.
    - Read excel file into a dataframe.
    - Sort data according to the 'order' columns.
    - Add href and nest level to each page.
    - Set divergent href and nest level for home.
    - Create a SiteStructure instance and return it.

    The excel file has to contain the following columns:
    ==============  =======================================
    Column name     Description
    ==============  =======================================
    Section_order   Order of the section within the site
    Section         Section name
    Chapter_order   Order of the chapter within the section
    Chapter         Chapter name
    Group_order     Order of the group within the chapter
    Group           Group name
    Page_order      Order of the page within the group
    Page            Page name
    Code            Code for crossreferencing to this page
    ==============  =======================================

    The following columns will be added before the class is instantiated:
    ==============  =======================
    Column name     Description
    ==============  =======================
    Href            Href of the page
    Href_nest       Nest level of the page
    ==============  =======================

    NOTE: The first page will always be set to 'home.html'.

    -----
    :param path_to_structure_file: Path to the excel file containing the site structure.
    :returns: Instance of the SiteStructure class.
    """

    df = pd.read_excel(path_to_structure_file, index_col=0)

    df.sort_values(by=[col for col in df.columns if '_order' in col],
                   inplace=True)
    df['Href'] = df.apply(lambda row: convert_to_href(row.Section,
                                                      row.Chapter,
                                                      row.Page), axis=1)
    df['Href_nest'] = df.apply(lambda row: (not pd.isna(row.Section)) +
                                           (not pd.isna(row.Chapter)), axis=1)
    df.loc[df.index[0], 'Href'] = 'index.html'
    df.loc[df.index[0], 'Href_nest'] = 0
    return SiteStructure(df)


def convert_to_href(*args):
    """
    Create href from cleaned up arguments (joined left to right).
    - Leading and trailing whitespaces are removed.
    - Spaces are converted to underscores.
    - Non-string arguments are ignored.
    - Returns `None` if no arguments are passed.

    -----
    :param *args: Strings to be joined into an href.
    :returns: Href as string / `None` if no arguments are passed.
    """

    href_elements = list()
    for arg in args:
        if type(arg) == str:
            href_elements.append(arg.lower().strip().replace(' ', '_'))

    try:
        href_elements[-1] = href_elements[-1] + '.html'
        return '/'.join(href_elements)
    except:
        return None


properties = SiteProperties()
