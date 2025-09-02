#!/usr/bin/env python3
"""
Simple EYN-OS Blog Generator
Automatically generates blog posts from repository updates.
"""

import os
import re
from datetime import datetime
from pathlib import Path

class SimpleBlogGenerator:
    def __init__(self, eynos_path="EYN-OS"):
        self.eynos_path = Path(eynos_path)
        self.blog_path = Path("blog")
        self.template_path = self.blog_path / "template.html"
        
    def scan_for_updates(self):
        """Scan EYN-OS directory for update information."""
        updates = []
        
        # Check README.md
        readme_path = self.eynos_path / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                content = f.read()
                update_info = self.extract_update_info(content, "README.md")
                if update_info:
                    updates.append(update_info)
        
        # Check docs directory
        docs_path = self.eynos_path / "docs"
        if docs_path.exists():
            for doc_file in docs_path.rglob("*.md"):
                with open(doc_file, 'r') as f:
                    content = f.read()
                    update_info = self.extract_update_info(content, str(doc_file.relative_to(self.eynos_path)))
                    if update_info:
                        updates.append(update_info)
        
        return updates
    
    def extract_update_info(self, content, filename):
        """Extract update information from content."""
        # Look for release information
        release_match = re.search(r'release\s+(\d+)', content.lower())
        if not release_match:
            return None
        
        version = release_match.group(1)
        
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"EYN-OS Release {version}"
        
        # Extract features
        features = []
        feature_matches = re.findall(r'^\s*[-*]\s*\*\*(.+?)\*\*:\s*(.+)$', content, re.MULTILINE)
        for match in feature_matches:
            features.append({
                'name': match[0].strip(),
                'description': match[1].strip()
            })
        
        return {
            'title': title,
            'version': version,
            'features': features,
            'source_file': filename,
            'content': content
        }
    
    def generate_blog_post(self, update_info):
        """Generate a blog post HTML file."""
        # Generate filename
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', update_info['title'])
        safe_title = re.sub(r'\s+', '-', safe_title).lower()
        filename = f"release-{update_info['version']}-{safe_title}.html"
        filepath = self.blog_path / filename
        
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        content = template.replace('BLOG_TITLE', update_info['title'])
        content = content.replace('MONTH YEAR', datetime.now().strftime('%B %Y'))
        content = content.replace('Tag1, Tag2, Tag3', f"Release, EYN-OS, Version {update_info['version']}")
        
        # Generate intro
        intro = f"EYN-OS Release {update_info['version']} brings significant updates and improvements to the operating system. "
        if update_info['features']:
            intro += f"This release introduces {len(update_info['features'])} major new features, "
            feature_names = [f['name'] for f in update_info['features'][:3]]
            intro += f"including {', '.join(feature_names)}"
            if len(update_info['features']) > 3:
                intro += f" and {len(update_info['features']) - 3} more"
            intro += ". "
        intro += "The update demonstrates EYN-OS's continued commitment to building everything from scratch while maintaining educational value and system performance."
        
        content = content.replace('INTRODUCTION_PARAGRAPH', intro)
        
        # Generate main content
        main_content = self.generate_main_content(update_info)
        content = content.replace('<!-- CONTENT_PLACEHOLDER -->', main_content)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filename
    
    def generate_main_content(self, update_info):
        """Generate the main content of the blog post."""
        content = []
        
        # Overview section
        content.append('<h2>Release Overview</h2>')
        content.append(f'<p>EYN-OS Release {update_info["version"]} represents a significant step forward in the project\'s development, introducing new capabilities and improvements that enhance the overall user experience and system functionality.</p>')
        
        # Features section
        if update_info['features']:
            content.append('<h2>New Features</h2>')
            content.append('<p>EYN-OS introduces several major new features:</p>')
            content.append('<ul>')
            for feature in update_info['features']:
                content.append(f'<li><strong>{feature["name"]}:</strong> {feature["description"]}</li>')
            content.append('</ul>')
        
        # Technical details
        content.append('<h2>Technical Details</h2>')
        content.append('<p>This release maintains EYN-OS\'s core philosophy of building everything from scratch for educational purposes. Each new feature is implemented with clear, understandable code that serves as both a functional tool and a learning resource.</p>')
        
        # Source information
        content.append('<h2>Source Information</h2>')
        content.append(f'<p>This release information was extracted from <code>{update_info["source_file"]}</code> in the EYN-OS repository. For complete technical details, see the full documentation and source code.</p>')
        
        return '\n'.join(content)
    
    def run(self):
        """Run the blog generator."""
        print("Simple EYN-OS Blog Generator")
        print("============================")
        
        if not self.eynos_path.exists():
            print(f"Error: EYN-OS directory not found at {self.eynos_path}")
            return
        
        if not self.template_path.exists():
            print(f"Error: Blog template not found at {self.template_path}")
            return
        
        # Scan for updates
        print("Scanning EYN-OS directory for updates...")
        updates = self.scan_for_updates()
        
        if not updates:
            print("No updates found.")
            return
        
        print(f"Found {len(updates)} updates:")
        for update in updates:
            print(f"  - {update['title']} (Version {update['version']})")
        
        # Generate blog posts
        for update in updates:
            print(f"\nGenerating blog post for: {update['title']}")
            filename = self.generate_blog_post(update)
            print(f"  Created: blog/{filename}")
        
        print(f"\nBlog generation complete!")
        print(f"Generated {len(updates)} blog posts.")

if __name__ == "__main__":
    generator = SimpleBlogGenerator()
    generator.run()
