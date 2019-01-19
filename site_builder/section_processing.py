"""
The section_processing module
============================
This module contains the functions needed for processing page sections. The general structure for these functions is as follows:

    [INPUT]
      text: Text body of section collected from the .md file as string.
      arg: (Optional) additional argument extracted from function call in the section heading as string.
        |
    [PROCESSING]
        |
    [OUTPUT]
      output_html: Processed html output as string.

The module loads all 'snippet_*.html' files from the defined template folder location as jinja2 templates. These templates are stored into a jinja2 environment (`SNIPPETS_ENV`) upon initialization and are available for any functions that need to use it.

The PageBuilder class will automatically load all processing functions from this module into its dispatcher. To prevent helper functions from being loaded by the PageBuilder class, they are distinguished by prefixing an underscore '_' to their name.

Thus, additional section processing functions can be added easily as long as they follow the general structure requirements above and a correctly named snippet file is added to the template repository if necessary.

The following functions are currently available:

    Objects in this module
    ----------------------
    Processing functions:
    - container (required argument)
    - collapsible
    - iframe (required argument)
    - card
    - table (optional argument)
    - flextable
    - markdown

    Helper functions:
    - _csv_to_df
    - _string_to_markdown

The keyword 'skip' is also reserved by the dispatcher and is used to pass the input of a section to the output unaltered.
"""

import pandas as pd
import uuid
import markdown as md
import jinja2
from collections import OrderedDict
from io import StringIO
from site_builder import config


def container(text, arg, process=True):
    """
    Render text to html with markdown if applicable and wrap it in div container with
    custom css class.
    |Uses 'container' snippet.

    -----
    :param text: Text to be processed as string.
    :param arg: Name of custom class as string.
    :returns: html-output as string.
    """
    template = SNIPPETS_ENV.get_template('container')

    if '\n' in text and process == True:
        text = md.markdown(text, extensions=['nl2br'])
    output_html = template.render(content=text, custom_class=arg)
    return output_html


def collapsible(text):
    """
    Separate section into subsections and render these as markdown into a collapsible container.
    |Uses 'collapsible' snippet.

    -----
    :param text: Text to be processed as string.
    :returns: html-output as string.
    """
    template = SNIPPETS_ENV.get_template('collapsible')

    collapsibles = list()
    for item in text.split('###')[1:]:
        new_items = item.split('\n', 1)
        collapsibles.append((new_items))

    output_html = ''
    for collapsible in collapsibles:
        checked = None
        if ':' in collapsible[0]:
            label, checked = collapsible[0].split(':')
        else:
            label = collapsible[0]
        code = str(uuid.uuid4())[:8]
        content = md.markdown(collapsible[1], extensions=['nl2br'])

        render = template.render(content=content,
                                 label=label,
                                 code=code,
                                 checked=checked)
        output_html = '\n'.join([output_html, render])
    return output_html


def iframe(text, arg):
    """
    Render text definig the page in the iframes folder to be linked to into an iframe.
    |Uses 'iframe' snippet.

    -----
    :param text: Text to be processed as string.
    :returns: html-output as string.
    """

    template = SNIPPETS_ENV.get_template('iframe')
    output_html = template.render(iframe_code=text, nest=arg)
    return output_html


def card(text):
    """
    Render html for card from csv.
    |Uses 'card' snippet.

    -----
    :param text: Table as csv.
    :returns: html-output as string.
    """
    df = _csv_to_df(text, header_row=None, header_names=['key', 'value'])
    template = SNIPPETS_ENV.get_template('card')
    content = OrderedDict(zip(df.key, df.value))
    output_html = template.render(content=content)
    return output_html


def table(text, arg):
    """
    Render html for basic table from csv.

    -----
    :param text: Table as csv.
    :returns: html-output as string.
    """
    df = _csv_to_df(text)
    with pd.option_context('display.max_colwidth', -1):
        output_html = df.to_html(index=False,
                                 na_rep='',
                                 classes=arg,
                                 escape=False)
    output_html = container(output_html,
                            'table__container',
                            process=False)
    return output_html


def flextable(text):
    """
    Render html for flexible table from csv.

    -----
    :param text: Table as csv.
    :returns: html-output as string.
    """
    df = _csv_to_df(text)
    number_of_cols = len(df.columns)
    number_of_rows = len(df.index)

    flextable_header = ''
    for column in df.columns:
        flextable_header += f'<div class="flextable__header">{column.strip()}</div>\n'

    flextable_body = ''
    for row_idx, *items in df.itertuples():
        for col_idx, item in enumerate(items):
            # Add css class to end of row / end of last row.
            if col_idx + 1 == number_of_cols:
                if row_idx + 1 == number_of_rows:
                    css_class = ' flextable__item__last-row'
                else:
                    css_class = ' flextable__item__end-of-row'
            else:
                css_class = ''
            # Add header as category in the flextable if cell is not empty, add css class to remove padding when empty.
            if item == '':
                category = ''
                css_class = ' remove_padding'
            else:
                category = f'\t<div class="flextable__category">{df.columns[col_idx]}</div>\n'
            # Build up flextable body.
            flextable_body += (f'<div class="flextable__item{css_class}">\n'
                               f'{category}'
                               f'\t<div>{item}</div>\n'
                               f'</div>\n')

    flextable = flextable_header + flextable_body
    output_html = f'<div class="flextable" style="grid-template-columns: repeat({number_of_cols}, auto)">\n{flextable}\n</div>\n'
    return output_html


def markdown(text):
    """
    Render html from markdown.

    -----
    :param text: Markdown to be processed as string.
    :returns: html-output as string.
    """
    output_html = md.markdown(text, extensions=['nl2br'])
    return output_html


def _csv_to_df(text, header_row=0, header_names=None):
    """
    Converts csv to dataframe and applies markdown to cells if applicable.

    -----
    :param text_input: Table as csv.
    :returns: Table as DataFrame.
    """
    df = pd.read_csv(StringIO(text), skipinitialspace=True,
                     quotechar="'", header=header_row, names=header_names)
    return df.applymap(_string_to_markdown)


def _string_to_markdown(string):
    """
    Returns html from string if it contains any of the following symbols:
        [*, #, `, \\n]

    -----
    :param string: String to be processed.
    :returns: rendered html if markdown symbols are present, returns string if not.
    """
    symbols = ['*', '#', '`', '\n']
    if not string == string:
        string = ''
    string = str(string)
    if not any(symbol in char for char in string for symbol in symbols):
        return string
    return md.markdown(string, extensions=['nl2br']).replace('\n', '')


snippets = dict()
for snippet_file in config.PATH_CONFIG['templates'].glob('**/snippet_*.html'):
    name = snippet_file.stem[8:]
    template = snippet_file.read_text(encoding='utf-8')
    snippets[name] = template
SNIPPETS_ENV = jinja2.Environment(loader=jinja2.DictLoader(snippets))
