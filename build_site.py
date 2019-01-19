"""
The build_structure script
==========================
This script will build the site in the output folder designated in `config.ini`. Any time you run the build site script it will increment the build number (which is printed in the footer of the page). If you want to run this script without incrementing the build number, flag it with 'no_increment'.

- The script will render all .md files with a valid page id in the content folder and store them in the output folder.
- It will copy the iframes and images folders to the output folder.
- It will store `properties.ini` with the updated build version in the content folder.
"""

import timeit
start = timeit.default_timer()

import argparse
import shutil
from site_builder import config
from site_builder import site_specs
from site_builder import page_loader
from site_builder import page_builder


path_templates = config.PATH_CONFIG['templates']
path_content = config.PATH_CONFIG['content']
path_output = config.PATH_CONFIG['output']

# Load site properties
parser = argparse.ArgumentParser(description='Build static site')
parser.add_argument('--no_increment', help='set flag if version number should not be incremented', action='store_true')
args = parser.parse_args()
site_specs.SiteProperties.load_properties(no_increment=args.no_increment)

# Load site structure
structure = site_specs.read_excel(path_content / 'structure.xlsx')
page_builder.PageBuilder.structure = structure

# Pages
for file in path_content.glob('**/*.md'):
    content = page_loader.read_md(file, structure.page_ids)
    href = structure[content.page_id]['Href']
    page = page_builder.PageBuilder(content)
    output_html = page.build_page()
    full_path = path_output / href
    path_out = full_path.parent

    if not path_out.exists():
        path_out.mkdir(parents=True)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(output_html)

# Sitemap
output_html = page_builder.PageBuilder.build_sitemap()
full_path = path_output / 'sitemap.html'
with open(full_path, 'w', encoding='utf-8') as f:
    f.write(output_html)

# Iframes
path_src = path_content / 'iframes'
path_dst = path_output / 'iframes'
if path_src.exists():
    if not path_dst.exists():
        shutil.copytree(path_src, path_dst)

# Images
path_src = path_content / 'images'
path_dst = path_output / 'images'
if path_src.exists():
    if not path_dst.exists():
        shutil.copytree(path_src, path_dst)

# CSS files
output_css = ''
path_css = path_output / 'css'
if not path_css.exists():
    path_css.mkdir(parents=True)

css_files = [
    'styles_card.css',
    'styles_collapsible.css',
    'styles_table.css',
    'styles_flextable.css',
    'styles_iframe.css',
    'styles_sitemap.css',
    ]

for css_file in css_files:
    in_file = path_templates / css_file
    out_file = path_css / css_file
    shutil.copy(in_file, path_css)

css_files = [
    'styles_base.css',
    'styles_custom_formatting.css'
    ]
for css_file in css_files:
    css_path = path_templates / css_file
    output_css += css_path.read_text()
full_path = path_css / 'styles_base.css'
with open(full_path, 'w', encoding='utf-8') as f:
    f.write(output_css)

# Save ini with incremented build version number
with open(path_content / 'properties.ini', 'w') as f:
    f.write(site_specs.SiteProperties.create_ini())

stop = timeit.default_timer()
time = stop - start
print(f'Finished in {time:.2f} sec.')
