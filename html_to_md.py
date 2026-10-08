import os
import sys
from bs4 import BeautifulSoup
import markdownify

def html_to_md(html_content):
    """
    Converts the main content of the Unitree HTML documentation string to Markdown.
    Args:
        html_content (str): The raw HTML content.
    Returns:
        str: The converted Markdown content, or None if main content is not found.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Target specific content containers based on Unitree doc structure
    # Priority 1: 文档中心
    main_content = soup.find('article', id='unitree-preview')
    
    # Priority 2: 文档中心2
    if not main_content:
        main_content = soup.find('div', id='docCont')

    # Priority 3: 帮助中心
    if not main_content:
        main_content = soup.find('div', class_='article_wrapper')
    
    # Priority 4: GitHub README
    if not main_content:
        main_content = soup.find('article', class_='markdown-body entry-content container-lg')

    if main_content:
        # Convert to markdown
        # heading_style="ATX" ensures # headers instead of underlines
        return markdownify.markdownify(str(main_content), heading_style="ATX")
    
    return None



def convert_file(input_path, output_path):
    """
    Reads an HTML file, converts it to Markdown, and saves it.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        md_content = html_to_md(html_content)
        
        if md_content:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"Successfully converted '{input_path}' to '{output_path}'")
        else:
            print(f"Error: Could not find main content in '{input_path}'")
            
    except Exception as e:
        print(f"Error processing '{input_path}': {e}")

if __name__ == "__main__":
    # Default behavior if run as a script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(project_root, 'html', 'unitree_document.html')
    output_file = os.path.join(project_root, 'html', 'unitree_document.md')
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
        
    if os.path.exists(input_file):
        convert_file(input_file, output_file)
    else:
        print(f"Input file not found: {input_file}")
