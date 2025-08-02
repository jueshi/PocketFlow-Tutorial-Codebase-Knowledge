import re
import sys

MERMAID_BLOCK_PATTERN = re.compile(r'```mermaid(.*?)```', re.DOTALL)

# Example fix function: cleans up node labels and formatting
# This is a simplified version for the specific Kalman Filter diagram style

def fix_mermaid_block(block):
    # Replace <br> with <br/>
    block = re.sub(r'<br\s*>', '<br/>', block)
    # Quote node labels (for lines like A[Label])
    block = re.sub(r'([A-Za-z0-9_]+)\[([^\[\]\n]+)\]', lambda m: f'{m.group(1)}["{m.group(2).strip()}"]', block)
    # Remove backticks and inline code from node labels
    block = re.sub(r'`([^`]+)`', r'\1', block)
    # Remove font-family and other problematic style attributes
    block = re.sub(r'font-family:[^,;]+,?', '', block)
    # Remove extra spaces in style lines
    block = re.sub(r'style (\w+) ', r'style \1 ', block)
    # Remove double commas in style
    block = block.replace(',,', ',')
    return block

def process_markdown_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        original_block = match.group(1)
        fixed_block = fix_mermaid_block(original_block)
        return f'```mermaid{fixed_block}```'

    new_content = MERMAID_BLOCK_PATTERN.sub(replacer, content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print('Usage: python fix_mermaid.py <markdown_file>')
    #     sys.exit(1)
    # process_markdown_file(sys.argv[1])
    process_markdown_file(r"C:\Users\juesh\OneDrive\Documents\windsurf\PocketFlow-Tutorial-Codebase-Knowledge\output\Kalman_filter2\03_covariance__error_covariance_matrix__.md")
# python fix_mermaid.py C:\Users\juesh\OneDrive\Documents\windsurf\PocketFlow-Tutorial-Codebase-Knowledge\output\Kalman_filter2\03_covariance__error_covariance_matrix__.md