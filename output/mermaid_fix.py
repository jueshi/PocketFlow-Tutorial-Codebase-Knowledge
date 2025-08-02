# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from nodes import batch_fix_mermaid_in_dir

# if __name__ == "__main__":
#     # batch_fix_mermaid_in_dir(os.path.dirname(__file__))
import re

def add_double_quote_around_labels(mermaid_code):
    pattern = re.compile(r'label\s*=\s*"?([^"\n]+)"?')
    def replacer(match):
        label = match.group(1).strip()
        if not (label.startswith('"') and label.endswith('"')):
            return f'label="{label}"'
        return match.group(0)
    return pattern.sub(replacer, mermaid_code)

def fix_mermaid_subgraph_labels(mermaid_code):
    # Fix subgraph labels
    def replacer(match):
        label = match.group(1).strip()
        if not (label.startswith('"') and label.endswith('"')):
            return f'subgraph "{label}"'
        return match.group(0)
    return re.sub(r'subgraph\s+([^\n]+)', replacer, mermaid_code)

def fix_all_mermaid_blocks_in_markdown(markdown_text):
    pattern = re.compile(
        r'^[ \t]*

# Example usage for a file:
input_path = r"C:\Users\juesh\OneDrive\Documents\windsurf\PocketFlow-Tutorial-Codebase-Knowledge\output\Shannon_Weaver_1949_Mathematical\06_连续信号处理__采样与量化__.md"
with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

fixed_content = fix_all_mermaid_blocks_in_markdown(content)

with open(input_path, "w", encoding="utf-8") as f:
    f.write(fixed_content)

print(f"Fixed Mermaid diagrams in: {input_path}")