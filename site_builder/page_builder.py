"""
THe page_builder module
=======================
This module contains the PageBuilder class which takes care of rendering the page sections and assembling them. Upon initialization the module:
- Loads all templates from the designated templates folder.
- Finds all stylesheets in the designated templates folder.
- Maps all functions from the section_processing module.

First instantiate the SiteStructure and set it to the PageBuilder structure attribute. After this you can instantiate PageBuilder objects by feeding it PageContent objects. The PageContent can be rendered as html with the build_page method.

    Objects in this module:
    -----------------------
    - PageBuilder (class)
    - build_function_mapping (function)
    - find_stylesheets (function)
    - load_templates (function)
"""

import inspect
import jinja2
import datetime as dt
from bs4 import BeautifulSoup
from site_builder import config
from site_builder import site_specs
from site_builder import section_processing


class PageBuilder:
    """
    The PageBuilder class is used to render all sections from the PageContent class and assemble them into an html string. To do this the PageBuilder uses the following elements:
        - The content from PageContent.
        - The navigational data from SiteStructure.
        - The processing functions from the section_processing module.
        - The jinja base templates loaded from the templates folder.
        - The prettify function from BeautifulSoup.

    Upon initialization the page_builder module:
    1. Loads all templates in the templates folder.
    2. Maps all available rendering functions in the section_processing module.
    3. Creates a list of all available stylesheets from the templates folder.

    The PageBuilder class also keeps track of which stylesheets are used by the instances of the class. After rendering all the pages, this class variable can be used to collect only the relevant stylesheets for packaging with the website (currently not implemented).

    A PageBuilder object is initialized with the following attributes:
    ==============  ==================================================
    Attribute       Description
    ==============  ==================================================
    page_id         Page id
    page_name       Page name
    sections        Content dictionary from PageContent
    ctime           Time of creation for the md file
    mtim            Time of last modification of the md file
    ==============  ==================================================

    The following attributes are created by the PageBuilder object using the build_page method:
    ==============  ==================================================
    Attribute       Description
    ==============  ==================================================
    stylesheets     List of stylesheets used in the page
    page_content    Rendered content without navigation
    page            Fully rendered html output
    ==============  ==================================================

    A PageBuilder object has the following main methods:
    ===============  =================================================
    Method           Description
    ===============  =================================================
    build_page       Return the page as fully rendered html.
    build_sitemap    Return the sitemap as fully rendered html.
    ===============  =================================================
    """

    structure = None
    properties = None
    PageEnv = None
    function_mapping = None
    available_stylesheets = None
    used_stylesheets = set()
    watermark = """
    <!-- This site was built with the site builder at https://github.com/lcvriend/responsive_static_site_builder licensed under the GNU General Public License v3.0. -->
    """

    def __init__(self, content):
        self.page_id = content.page_id
        self.page_name = PageBuilder.structure[self.page_id]['Page']
        self.page_content = ''
        self.page = ''
        self.sections = content.sections
        self.ctime = content.ctime
        self.mtime = content.mtime
        self.stylesheets = []

    def build_page(self):
        """
        Build a page from the loaded PageContent:
            1. Render all sections of the page and return the html.
            2. Convert all crossref codes to working crossref links.
            3. Render the page within the site template (adds navigation etc.)
            4. Prettify the html output with BeautifulSoup.
            5. Return the page.

        -----
        :returns: The rendered and finalized html page as string.
        """

        page_variables = {
            'content': self.page_content,
            'cdate': self.ctime.strftime('%d-%m-%Y'),
            'mdate': self.mtime.strftime('%d-%m-%Y'),
            'document_title': PageBuilder.properties.name,
            'language': PageBuilder.properties.language,
            'version': PageBuilder.properties.version,
            'footer_contact': PageBuilder.properties.footer_contact,
            'footer_info': PageBuilder.properties.footer_info,
            'stylesheets': self.stylesheets,
            'current_page_id': self.page_id,
            'current_page': self.page_name,
            'current_chapter': PageBuilder.structure[self.page_id]['Chapter'],
            'current_section': PageBuilder.structure[self.page_id]['Section'],
            'breadcrumbs': PageBuilder.structure.breadcrumbs(self.page_id),
            'nest': '../' * PageBuilder.structure[self.page_id]['Href_nest'],
            'sections_href': PageBuilder.structure.href_sections,
            'adjacent': PageBuilder.structure.adjacent_pages(self.page_id),
            'sitemap': PageBuilder.structure.sitemap()[PageBuilder.structure[self.page_id]['Section']],
            'set_navigation': True,
        }

        page_variables['content'] = self.render_sections(page_variables)
        if page_variables['content'] == '':
            page_variables['content'] = f'<p>{PageBuilder.properties.tbd}</p>'
        page_variables['content'] = self.set_crossrefs(page_variables)

        self.page = self.render_page('base', page_variables)
        self.page = BeautifulSoup(self.page, 'lxml').prettify()
        self.page = self.page + PageBuilder.watermark
        return self.page

    @staticmethod
    def render_page(template, page_variables):
        """
        Pass the page variables through the selected template in jinja2 and return the rendered page.

        -----
        :param page_variables: Specification of the page as dictionary.
        :return: Rendered html page as string
        """

        page = PageBuilder.PageEnv.get_template(template)
        page.globals = page_variables
        return page.render()

    @staticmethod
    def set_crossrefs(page_variables):
        """
        Check for crossref [codes] defined in the SiteStructure within the page and convert them to crossref format.

        -----
        :param page_variables: Specification of the page as dictionary.
        :returns: html where each occurrence of [code] is replaced by crossreferencing link.
        """

        content = page_variables['content']
        nest = page_variables['nest']
        for code, href in PageBuilder.structure.crossrefs:
            if code == code:
                crossref = f'<a class="crossref" href="{nest}{href}">{code}</a>'
                content = content.replace('[' + code + ']', crossref)
        return content

    def render_sections(self, page_variables):
        """
        Render all sections of the page into html and combine them.

        -----
        :param page_variables: Specification of the page as dictionary.
        :returns: Rendered page as html.
        """
        content = ''
        for section in self.sections:
            text = section['text']
            function = section['function']
            arg = section['arg']
            if arg in page_variables:
                arg = page_variables[arg]
            try:
                render = self.dispatcher(text, function, arg)
            except:
                print(f'Rendering page with {function} {arg} failed on:')
                print(text)
                print('Skipping this passage.')
                render = ''

            content = '\n'.join([content, render])
            if function in PageBuilder.available_stylesheets:
                stylesheet_name = f'styles_{function}.css'
                self.stylesheets.append(stylesheet_name)
                PageBuilder.used_stylesheets.add(stylesheet_name)
        return content

    @classmethod
    def build_sitemap(cls):
        """
        Return sitemap as html from the sitemap template and SiteStructure.

        -----
        :returns: Rendered sitemap as html.
        """

        time = dt.datetime.now().strftime('%d-%m-%Y')

        page_variables = {
            'cdate': time,
            'mdate': time,
            'document_title': cls.properties.name,
            'language': cls.properties.language,
            'version': cls.properties.version,
            'footer_contact': cls.properties.footer_contact,
            'footer_info': cls.properties.footer_info,
            'stylesheets': ['styles_sitemap.css'],
            'current_page': 'Sitemap',
            'breadcrumbs': 'Sitemap',
            'nest': '',
            'sections_href': cls.structure.href_sections,
            'sitemap': cls.structure.sitemap(),
            'adjacent': None,
            'set_navigation': False,
        }
        page = cls.render_page('base_sitemap', page_variables)
        page = BeautifulSoup(page, 'lxml').prettify()
        return page

    @classmethod
    def dispatcher(cls, text, function, arg):
        """
        Pass text and argument to the appropriate function and return the output. If the function keyword is not found in the function mapping or has the name 'skip', then the text is passed through the output untouched.

        -----
        :param text: Text to be rendered as string.
        :param function: Function name of the function to use as string.
        :param arg: Optional argument to be passed to the function as string.
        """

        if function == 'skip':
            return text
        elif not function in cls.function_mapping.keys():
            return text
        elif cls.function_mapping[function][1] == 1:
            return cls.function_mapping[function][0](text)
        else:
            return cls.function_mapping[function][0](text, arg)


def build_function_mapping():
    """
    Build function mapping for (non-helper) functions in the section_processing module. Mapping consists of a dictionary of tuples:
    - Key: function name as string
    - Value: (function object | # of arguments function object takes)

    Helper functions in the section_processing module (prefixed with an underscore '_') are ignored.

    -----
    :returns: Function mapping as dictionary of tuples.
    """

    functions = inspect.getmembers(section_processing, inspect.isfunction)
    function_mapping = dict()
    for function in functions:
        func_name = function[0]
        if not func_name.startswith('_'):
            func_obj = function[1]
            numb_args = len(inspect.signature(func_obj).parameters)
            function_mapping[func_name] = (func_obj, numb_args)
    return function_mapping


def find_stylesheets():
    """
    Return a list of the names of the (sub)stylesheets in the project templates folder.

    -----
    :returns: names of the (sub)stylesheets as list.
    """
    stylesheets = list()
    for stylesheet in config.PATH_CONFIG['templates'].glob('styles_*.css'):
        stylesheets.append(stylesheet.stem[7:])
    return stylesheets


def load_templates():
    """
    Load base templates from the project templates folder in a jinja2 environment.

    -----
    :returns: Base templates as jinja2 enivronment.
    """
    base_templates = dict()
    for base_template in config.PATH_CONFIG['templates'].glob('base*.html'):
        template_name = base_template.stem
        template = base_template.read_text(encoding='utf-8')
        base_templates[template_name] = template
    return jinja2.Environment(loader=jinja2.DictLoader(base_templates), trim_blocks=True, lstrip_blocks=True)


# Initialize class constants
PageBuilder.PageEnv = load_templates()
PageBuilder.function_mapping = build_function_mapping()
PageBuilder.available_stylesheets = find_stylesheets()
PageBuilder.properties = site_specs.properties
