import os
import re
from bs4 import BeautifulSoup

class PineScriptDocsProcessor:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        # Place the processed output as a sibling `processed` folder next to
        # the `input_dir` (which will be the new `unprocessed` folder).
        base_dir = os.path.dirname(input_dir)
        self.output_dir = os.path.join(base_dir, "processed")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def clean_navigation(self, text):
        """Remove navigation elements and links"""
        # Remove navigation sections
        text = re.sub(r'Version Version.*?Auto', '', text, flags=re.DOTALL)
        text = re.sub(r'\* \[.*?\n', '', text)
        text = re.sub(r'Copyright © .*?TradingView.*?\n', '', text)
        text = re.sub(r'On this page.*?\n', '', text)
        return text
        
    def extract_code_blocks(self, text):
        """Preserve and clean code blocks"""
        # Find Pine Script code blocks
        code_blocks = re.findall(r'```(?:pine)?(.*?)```', text, re.DOTALL)
        clean_blocks = []
        for block in code_blocks:
            # Clean the code block
            clean_block = block.strip()
            if clean_block:
                clean_blocks.append(f"```pine\n{clean_block}\n```")
        return clean_blocks
        
    def extract_function_docs(self, text):
        """Extract function documentation"""
        # Find function descriptions
        functions = re.findall(r'@function.*?@returns.*?\n', text, re.DOTALL)
        return functions

    def remove_markdown_links(self, text):
        """Replace inline markdown links like [text](url) with just the display text.

        This preserves any leading/trailing spaces inside the [brackets], so
        cases such as "### [ Intrabars](...)" become "###  Intrabars" (note
        the intentional double spacing when the bracketed text starts with a
        space). It replaces any occurrence of [display](...) with display.
        """
        # Replace any [display](url) with the captured display text.
        # Using a non-greedy match for the parentheses content.
        return re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        
    def process_file(self, filename):
        """Process a single documentation file"""
        with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Clean navigation and basic structure
        content = self.clean_navigation(content)
        
        # Remove inline markdown links so only their display text remains
        content = self.remove_markdown_links(content)
        
        # Extract valuable parts
        code_blocks = self.extract_code_blocks(content)
        function_docs = self.extract_function_docs(content)
        
        # Extract main content sections. Accept headings like:
        #   ## [Title]\n...
        #   ## Title\n...
        # Capture either the bracketed title (group 1) or the plain title (group 2)
        sections_raw = re.findall(r"##\s+(?:\[(.*?)\]|([^\n]+))\s*\n(.*?)(?=^##\s+|\Z)", content, re.DOTALL | re.MULTILINE)
        sections = []
        for g1, g2, body in sections_raw:
            title = (g1 or g2 or '').strip()
            sections.append((title, body))
        
        # Build processed content
        processed = []
        
        if sections:
            for title, section in sections:
                if any(keyword in section.lower() for keyword in ['pine', 'script', 'function', 'indicator', 'value', 'parameter']):
                    clean_section = re.sub(r'\[\^.*?\]', '', section)  # Remove footnotes
                    clean_section = re.sub(r'\(https://.*?\)', '', clean_section)  # Remove links
                    processed.append(f"## {title}\n{clean_section.strip()}")

        # Fallback: if nothing useful was extracted but there are code blocks or
        # function docs, or the document contains Pine-related keywords, turn
        # the whole document into a single section so it doesn't get skipped.
        if not processed:
            content_lower = content.lower()
            has_keywords = any(k in content_lower for k in ['pine', 'script', 'function', 'indicator'])
            if code_blocks or function_docs or has_keywords:
                fallback_title = os.path.splitext(filename)[0]
                clean_content = re.sub(r'\[\^.*?\]', '', content)  # remove footnotes
                processed.append(f"## {fallback_title}\n{clean_content.strip()}")
        
        if code_blocks:
            processed.append("\n## Code Examples\n")
            processed.extend(code_blocks)
            
        if function_docs:
            processed.append("\n## Function Documentation\n")
            processed.extend(function_docs)
            
        if not processed:
            return None
            
        # Save processed content
        output_filename = f"processed_{filename}"
        with open(os.path.join(self.output_dir, output_filename), 'w', encoding='utf-8') as f:
            f.write("\n\n".join(processed))
            
        return output_filename
        
    def process_all(self):
        """Process all markdown files in the input directory"""
        processed_files = []
        print(f"Looking for files in: {self.input_dir}")
        
        # Collect markdown files and sort them in natural numeric order so
        # files named like "1_name.md", "2_name.md", ..., "10_name.md" are
        # processed in ascending numeric order.
        all_files = [f for f in os.listdir(self.input_dir) if f.endswith('.md') and f != 'all_docs.md']
        print(f"Found files (unsorted): {all_files}")

        # Natural sort: prefer leading numeric prefix when present
        def _sort_key(name):
            m = re.match(r'^(\d+)[._-]?', name)
            if m:
                # numeric-prefixed files come first, sorted by integer value
                return (0, int(m.group(1)), name)
            # non-prefixed files come after, sorted lexicographically
            return (1, name)

        all_files.sort(key=_sort_key)
        print(f"Processing files in order: {all_files}")

        for filename in all_files:
            print(f"Processing file: {filename}")
            output_file = self.process_file(filename)
            if output_file:
                processed_files.append(output_file)
                print(f"Successfully processed: {output_file}")
            else:
                print(f"Skipped file: {filename} (no valid content found)")
        
        # Create a combined processed file in the script's directory (not inside the processed folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        combined_path = os.path.join(script_dir, 'processed_all_docs.md')
        with open(combined_path, 'w', encoding='utf-8') as combined:
            for filename in processed_files:
                with open(os.path.join(self.output_dir, filename), 'r', encoding='utf-8') as f:
                    combined.write(f"\n\n# {filename[:-3]}\n\n")
                    combined.write(f.read())
                    combined.write("\n\n---\n\n")

        print(f"Combined processed file written to: {combined_path}")

if __name__ == "__main__":
    # Get the script's directory and set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Read from the new `unprocessed` folder created by the crawler
    input_dir = os.path.join(script_dir, "pinescript_docs", "unprocessed")
    
    processor = PineScriptDocsProcessor(input_dir, "processed")
    processor.process_all()