"""
The build_structure script
==========================
This script builds or rebuilds the site structure within the content folder according to the table in `structure.xlsx`. It will do the following things:

1. Try to read the site structure from `structure.xlsx` in the content folder. If this fails it will create an empty structure table (with only a homepage) and store it in the content folder.
2. Check if any rows lack a page_id and if so create and add unique page_ids to these rows.
3. Loop over the .md files in the content folder and for every file:
    - Check the page_id; if a page_id is found that is unknown to the site structure definition, then prompt the user to delete the file. (Files with page_ids that are not defined in the site structure are ignored when building the site. Thus they can be safely left within the content folder. However this may later lead to confusion when maintaining the site.)
    - Check if each path and filename follows this naming convention:

        [ content folder / section_order + section / chapter_order + group_order + page_order + page_name ]

    if not: rename the path and/or filename.
4. Check if all page_ids have an associated .md file. If this is not the case:
    - Create the .md file following the naming convention above.
5. Save the updated table in `structure.xlsx`.

This script can add page ids where they are missing but other than that the site structure must be well formatted. At this point in time there is no other validation performed on the structure table. This means that the order for each page needs to be fully specified. Make sure that section_oder, chapter_order and group_order are filled for each page. If there are no groups within a chapter or no chapters within a section the order value should be 1.

Another thing to note is that this script will organize the .md files into folders for convenience only. Where the .md files are stored has no bearing on how the site is actually built. You could move the files around and it would make no difference - as long as the site builder is able to find the relevant files.
"""

import pandas as pd
from site_builder import config


def generate_id(page_ids):
    """
    Generate a unique id.

    :param page_ids: Array of existing page_ids.
    :returns: Unique id as string.
    """
    test = False
    while test == False:
        new_id = pd.util.testing.rands_array(5, 1)[0]
        if not new_id in page_ids:
            test = True
    return new_id


if __name__ == '__main__':
    path_templates = config.PATH_CONFIG['templates']
    path_content = config.PATH_CONFIG['content']

    structure_file = path_content / 'structure.xlsx'

    try:
        df = pd.read_excel(structure_file)
    except:
        data = {'Page_id': [None],
                'Section_order': [1],
                'Section': ['Home'],
                'Chapter_order': [1],
                'Chapter': [None],
                'Group_order': [1],
                'Group': [None],
                'Page_order': [1],
                'Page': ['Home'],
                'Code': [None]}
        df = pd.DataFrame(data=data)

    page_ids = df.Page_id.values
    df['Page_id'] = df['Page_id'].apply(lambda x: generate_id(page_ids) if pd.isna(x) else x)
    df = df.set_index('Page_id').fillna(value='')

    # Rename existing files according to site structure spec
    # Prompt to delete files with unknown page ids
    # Store found page ids
    found_page_ids = list()
    files = path_content.glob('**/*.md')
    for file_path in files:
        text = file_path.read_text(encoding='utf-8')
        if not '\n' in text:
            continue

        page_id, text_body = text.split('\n', 1)
        if not len(page_id) == 5:
            continue

        if page_id not in page_ids:
            delete = None
            while not delete in ['y', 'j', 'n']:
                delete = input(
                    f"File '{file_path.name}' has unknown page id <{page_id}>. Delete (y/n)? ")
                delete = delete.lower()[0]
            if not delete == 'n':
                print(f'Deleting {file_path.name}.')
                file_path.unlink()
            continue

        found_page_ids.append(page_id)

        section_order = f"{df.loc[page_id]['Section_order']:02}"
        chapter_order = f"{df.loc[page_id]['Chapter_order']:02}"
        group_order = f"{df.loc[page_id]['Group_order']:02}"
        page_order = f"{df.loc[page_id]['Page_order']:02}"
        section = df.loc[page_id]['Section'].lower()
        chapter = df.loc[page_id]['Chapter'].lower()
        page_name = df.loc[page_id]['Page'].lower()

        path_section = (section_order + '_' + section)
        order = chapter_order + group_order + page_order
        fn_elements = list(filter(None, [order, chapter, page_name]))

        filename = ' - '.join(fn_elements) + '.md'

        renamed_path = path_content / path_section / filename
        if not file_path == renamed_path:
            if not renamed_path.parent.exists():
                renamed_path.parent.mkdir(parents=True)
            file_path.rename(renamed_path)

    # Create files for new page ids
    new_page_ids = set(df.index.values) - set(found_page_ids)
    for page_id in new_page_ids:
        section_order = f"{df.loc[page_id]['Section_order']:02}"
        chapter_order = f"{df.loc[page_id]['Chapter_order']:02}"
        group_order = f"{df.loc[page_id]['Group_order']:02}"
        page_order = f"{df.loc[page_id]['Page_order']:02}"
        section = df.loc[page_id]['Section'].lower()
        chapter = df.loc[page_id]['Chapter'].lower()
        page_name = df.loc[page_id]['Page'].lower()

        path_section = (section_order + '_' + section)
        order = chapter_order + group_order + page_order
        fn_elements = list(filter(None, [order, chapter, page_name]))

        filename = ' - '.join(fn_elements) + '.md'
        file_path = path_content / path_section / filename

        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)

        text = page_id + '\n'
        file_path.write_text(text, encoding='utf-8')

    # Save structure file
    writer = pd.ExcelWriter(structure_file)
    df.to_excel(writer, 'site structure')
    writer.save()
