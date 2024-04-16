# @Author: jwli.
# @Date  : 2024/04/16

import sys
from bs4 import BeautifulSoup

# Check if the file path was passed as a command line argument
if len(sys.argv) < 2:
    print("Usage: python script.py <path_to_html_file>")
    sys.exit(1)

# The first command line argument is the script name, the second is the file path
file_path = sys.argv[1]

# Read the HTML content from the file
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
except FileNotFoundError:
    print("File not found. Please check the path and try again.")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find the <pre> tag with the class "search-results-chunk"
pre_tag = soup.find('pre', class_='search-results-chunk')

# Get the text from the <pre> tag
text = pre_tag.get_text() if pre_tag else "No matching element found."

print(text)
