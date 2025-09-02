#!/usr/bin/env python3
"""
EYN-OS Blog Generator
Automatically generates blog posts from repository updates and markdown files.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
import subprocess
import shutil

class EYNOSBlogGenerator:
    def __init__(self, eynos_path="EYN-OS"):
        self.eynos_path = Path(eynos_path)
        self.blog_path = Path("blog")
        self.template_path = self.blog_path / "template.html"
        self.blog_index_path = Path("blog.html")
        
        # Ensure blog directory exists
        self.blog_path.mkdir(exist_ok=True)
        
    def extract_release_info(self, content, filename):
        """Extract release information from markdown content."""
        release_info = {
            'title': '',
            'date': '',
            'version': '',
            'features': [],
            'changes': [],
            'content': content,
            'source_file': filename
        }
        
        # Try to extract version from filename or content
        version_match = re.search(r'release\s+(\d+)', content.lower())
        if version_match:
            release_info['version'] = version_match.group(1)
        
        # Extract title from first heading
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            release_info['title'] = title_match.group(1)
        
        # Extract features from markdown lists
        feature_matches = re.findall(r'^\s*[-*]\s*\*\*(.+?)\*\*:\s*(.+)$', content, re.MULTILINE)
        for match in feature_matches:
            release_info['features'].append({
                'name': match[0].strip(),
                'description': match[1].strip()
            })
        
        # Extract changes from sections
        changes_match = re.search(r'(?:##\s+Changes?|##\s+What\'s New|##\s+Updates?)(.*?)(?=##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if changes_match:
            changes_text = changes_match.group(1)
            change_items = re.findall(r'^\s*[-*]\s*(.+)$', changes_text, re.MULTILINE)
            release_info['changes'] = [item.strip() for item in change_items if item.strip()]
        
        return release_info
    
    def generate_blog_post(self, release_info):
        """Generate a blog post HTML file from release information."""
        if not release_info['title']:
            release_info['title'] = f"EYN-OS Update - {release_info['source_file']}"
        
        if not release_info['version']:
            release_info['version'] = "Update"
        
        # Generate filename
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', release_info['title'])
        safe_title = re.sub(r'\s+', '-', safe_title).lower()
        filename = f"{safe_title}.html"
        filepath = self.blog_path / filename
        
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        content = template.replace('BLOG_TITLE', release_info['title'])
        content = content.replace('MONTH YEAR', datetime.now().strftime('%B %Y'))
        content = content.replace('Tag1, Tag2, Tag3', f"Release, EYN-OS, Update")
        content = content.replace('INTRODUCTION_PARAGRAPH', self.generate_intro(release_info))
        
        # Generate main content
        main_content = self.generate_main_content(release_info)
        content = content.replace('<!-- CONTENT_PLACEHOLDER -->', main_content)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filename
    
    def generate_intro(self, release_info):
        """Generate an introduction paragraph for the blog post."""
        intro = f"EYN-OS {release_info['version']} brings significant updates and improvements to the operating system. "
        
        if release_info['features']:
            intro += f"This release introduces {len(release_info['features'])} major new features, "
            feature_names = [f['name'] for f in release_info['features'][:3]]
            intro += f"including {', '.join(feature_names)}"
            if len(release_info['features']) > 3:
                intro += f" and {len(release_info['features']) - 3} more"
            intro += ". "
        
        intro += "The update demonstrates EYN-OS's continued commitment to building everything from scratch while maintaining educational value and system performance."
        
        return intro
    
    def generate_main_content(self, release_info):
        """Generate the main content of the blog post."""
        content = []
        
        # Overview section
        content.append('<h2>Overview</h2>')
        content.append(f'<p>This update represents a significant step forward in EYN-OS development, introducing new capabilities and improvements that enhance the overall user experience and system functionality.</p>')
        
        # Features section
        if release_info['features']:
            content.append('<h2>New Features</h2>')
            content.append('<p>EYN-OS introduces several major new features:</p>')
            content.append('<ul>')
            for feature in release_info['features']:
                content.append(f'<li><strong>{feature["name"]}:</strong> {feature["description"]}</li>')
            content.append('</ul>')
        
        # Changes section
        if release_info['changes']:
            content.append('<h2>Key Changes</h2>')
            content.append('<ul>')
            for change in release_info['changes']:
                content.append(f'<li>{change}</li>')
            content.append('</ul>')
        
        # Technical details
        content.append('<h2>Technical Details</h2>')
        content.append('<p>This update maintains EYN-OS\'s core philosophy of building everything from scratch for educational purposes. Each new feature is implemented with clear, understandable code that serves as both a functional tool and a learning resource.</p>')
        
        # Source information
        content.append('<h2>Source Information</h2>')
        content.append(f'<p>This update information was extracted from <code>{release_info["source_file"]}</code> in the EYN-OS repository. For complete technical details, see the full documentation and source code.</p>')
        
        return '\n'.join(content)
    
    def update_blog_index(self, new_posts):
        """Update the main blog index with new posts."""
        # Read current blog index
        with open(self.blog_index_path, 'r') as f:
            content = f.read()
        
        # Find the blog-posts section
        posts_start = content.find('<section class="blog-posts">')
        posts_end = content.find('</section>', posts_start)
        
        if posts_start == -1 or posts_end == -1:
            print("Could not find blog-posts section in blog.html")
            return
        
        # Generate new posts HTML
        new_posts_html = []
        for post in new_posts:
            post_html = self.generate_blog_index_entry(post)
            new_posts_html.append(post_html)
        
        # Insert new posts at the beginning
        new_content = content[:posts_start + len('<section class="blog-posts">')]
        new_content += '\n        '
        new_content += '\n        '.join(new_posts_html)
        new_content += '\n        '
        new_content += content[posts_start + len('<section class="blog-posts">'):]
        
        # Write updated content
        with open(self.blog_index_path, 'w') as f:
            f.write(new_content)
    
    def generate_blog_index_entry(self, post_info):
        """Generate a blog index entry for a post."""
        filename = post_info.get('filename', 'unknown.html')
        title = post_info.get('title', 'Unknown Post')
        version = post_info.get('version', 'Update')
        
        return f'''<article class="blog-post">
            <header class="post-header">
                <h2><a href="blog/{filename}">{title}</a></h2>
                <div class="post-meta">
                    <span class="post-date">{datetime.now().strftime('%B %Y')}</span>
                    <span class="post-tags">Release, EYN-OS, {version}</span>
                </div>
            </header>
            <div class="post-excerpt">
                <p>EYN-OS {version} brings significant updates and improvements to the operating system. This release introduces new features and enhancements that demonstrate the project's continued development and commitment to educational value.</p>
                <p><a href="blog/{filename}" class="read-more">Read Full Post →</a></p>
            </div>
        </article>'''
    
    def scan_eynos_updates(self):
        """Scan EYN-OS directory for update information."""
        updates = []
        
        # Check README.md for release information
        readme_path = self.eynos_path / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                content = f.read()
                release_info = self.extract_release_info(content, "README.md")
                if release_info['version'] or release_info['features']:
                    updates.append(release_info)
        
        # Check CONTRIBUTING.md for updates
        contributing_path = self.eynos_path / "CONTRIBUTING.md"
        if contributing_path.exists():
            with open(contributing_path, 'r') as f:
                content = f.read()
                release_info = self.extract_release_info(content, "CONTRIBUTING.md")
                if release_info['version'] or release_info['features']:
                    updates.append(release_info)
        
        # Check docs directory for update information
        docs_path = self.eynos_path / "docs"
        if docs_path.exists():
            for doc_file in docs_path.rglob("*.md"):
                if doc_file.name not in ["README.md", "CONTRIBUTING.md"]:
                    with open(doc_file, 'r') as f:
                        content = f.read()
                        release_info = self.extract_release_info(content, str(doc_file.relative_to(self.eynos_path)))
                        if release_info['version'] or release_info['features']:
                            updates.append(release_info)
        
        return updates
    
    def generate_blog_from_updates(self):
        """Main function to generate blog posts from EYN-OS updates."""
        print("Scanning EYN-OS directory for updates...")
        updates = self.scan_eynos_updates()
        
        if not updates:
            print("No updates found in EYN-OS directory.")
            return
        
        print(f"Found {len(updates)} potential updates:")
        for update in updates:
            print(f"  - {update['title']} (Version: {update['version']})")
        
        # Generate blog posts
        new_posts = []
        for update in updates:
            print(f"\nGenerating blog post for: {update['title']}")
            filename = self.generate_blog_post(update)
            new_posts.append({
                'filename': filename,
                'title': update['title'],
                'version': update['version']
            })
            print(f"  Created: blog/{filename}")
        
        # Update blog index
        print("\nUpdating blog index...")
        self.update_blog_index(new_posts)
        print("Blog index updated successfully!")
        
        print(f"\nGenerated {len(new_posts)} new blog posts:")
        for post in new_posts:
            print(f"  - {post['filename']}")

def main():
    """Main function to run the blog generator."""
    generator = EYNOSBlogGenerator()
    
    print("EYN-OS Blog Generator")
    print("=====================")
    
    # Check if EYN-OS directory exists
    if not generator.eynos_path.exists():
        print(f"Error: EYN-OS directory not found at {generator.eynos_path}")
        print("Please ensure the EYN-OS repository is in the current directory.")
        return
    
    # Check if template exists
    if not generator.template_path.exists():
        print(f"Error: Blog template not found at {generator.template_path}")
        print("Please ensure the blog template exists.")
        return
    
    # Generate blog posts
    generator.generate_blog_from_updates()
    
    print("\nBlog generation complete!")
    print("You can now view the updated blog at blog.html")

if __name__ == "__main__":
    main()
