#!/usr/bin/env python3
"""
Dynamic Blog Index Generator
Scans the /blog/ directory and generates the blog index from actual blog post files.
"""

import os
import re
from datetime import datetime
from pathlib import Path

class DynamicBlogIndexGenerator:
    def __init__(self):
        self.blog_path = Path("blog")
        self.blog_index_path = Path("blog.html")
        
    def scan_blog_directory(self):
        """Scan the blog directory for HTML files."""
        if not self.blog_path.exists():
            print(f"Blog directory not found: {self.blog_path}")
            return []
        
        blog_posts = []
        
        # Get all HTML files in the blog directory
        for html_file in self.blog_path.glob("*.html"):
            if html_file.name == "template.html":
                continue  # Skip the template file
                
            post_info = self.extract_post_info(html_file)
            if post_info:
                blog_posts.append(post_info)
        
        # Sort by date (newest first)
        blog_posts.sort(key=lambda x: x['date'], reverse=True)
        
        return blog_posts
    
    def extract_post_info(self, html_file):
        """Extract information from a blog post HTML file using regex."""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from h1 tag
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
            if not title_match:
                return None
            
            title = title_match.group(1).strip()
            
            # Extract date from post-date span
            date_match = re.search(r'<span class="post-date">(.*?)</span>', content)
            if date_match:
                date_str = date_match.group(1).strip()
                # Try to parse the date
                try:
                    if '-' in date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_obj = datetime.strptime(date_str, '%B %Y')
                    date = date_obj
                except ValueError:
                    date = datetime.now()
            else:
                date = datetime.now()
            
            # Extract tags from post-tags span
            tags_match = re.search(r'<span class="post-tags">(.*?)</span>', content)
            if tags_match:
                tags = tags_match.group(1).strip()
            else:
                tags = "EYN-OS, Update"
            
            # Extract excerpt/intro from post-intro paragraph
            intro_match = re.search(r'<p class="post-intro">(.*?)</p>', content, re.DOTALL)
            if intro_match:
                excerpt = intro_match.group(1).strip()
            else:
                # Fallback: get first paragraph
                first_p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
                if first_p_match:
                    excerpt = first_p_match.group(1).strip()
                    if len(excerpt) > 200:
                        excerpt = excerpt[:200] + "..."
                else:
                    excerpt = "Development update that brings improvements and new features to EYN-OS."
            
            # Determine post type and version
            post_type = "Update"
            version = None
            
            if "🚀 Release" in tags or "Release" in tags:
                post_type = "Release"
                # Try to extract version number
                version_match = re.search(r'Version (\d+)', tags)
                if version_match:
                    version = version_match.group(1)
                else:
                    # Look in title
                    version_match = re.search(r'Release (\d+)', title, re.IGNORECASE)
                    if version_match:
                        version = version_match.group(1)
            
            # Generate filename for link
            filename = html_file.name
            
            return {
                'title': title,
                'date': date,
                'tags': tags,
                'excerpt': excerpt,
                'filename': filename,
                'type': post_type,
                'version': version
            }
            
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
            return None
    
    def generate_blog_index(self, blog_posts):
        """Generate the blog index HTML."""
        # Read the current blog.html to get the header and footer
        with open(self.blog_index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the blog-posts section
        posts_start = content.find('<section class="blog-posts">')
        posts_end = content.find('</section>', posts_start)
        
        if posts_start == -1 or posts_end == -1:
            print("Could not find blog-posts section in blog.html")
            return
        
        # Generate new posts HTML
        new_posts_html = []
        for post in blog_posts:
            post_html = self.generate_blog_index_entry(post)
            new_posts_html.append(post_html)
        
        # Replace the blog-posts section
        new_content = content[:posts_start]
        new_content += '<section class="blog-posts">\n        '
        new_content += '\n        '.join(new_posts_html)
        new_content += '\n        </section>'
        new_content += content[posts_end + len('</section>'):]
        
        # Write updated content
        with open(self.blog_index_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def generate_blog_index_entry(self, post):
        """Generate a blog index entry for a post."""
        # Format date
        if isinstance(post['date'], datetime):
            date_str = post['date'].strftime('%B %Y')
        else:
            date_str = str(post['date'])
        
        # Generate tags with emojis
        if post['type'] == 'Release' and post['version']:
            tags = f"🚀 Release, EYN-OS, Version {post['version']}"
        elif post['type'] == 'Release':
            tags = f"🚀 Release, EYN-OS"
        else:
            tags = f"📝 {post['type']}, EYN-OS, Development"
        
        return f'''<article class="blog-post">
            <header class="post-header">
                <h2><a href="blog/{post['filename']}">{post['title']}</a></h2>
                <div class="post-meta">
                    <span class="post-date">{date_str}</span>
                    <span class="post-tags">{tags}</span>
                </div>
            </header>
            <div class="post-excerpt">
                <p>{post['excerpt']}</p>
                <p><a href="blog/{post['filename']}" class="read-more">Read Full Post →</a></p>
            </div>
        </article>'''
    
    def run(self):
        """Run the dynamic blog index generator."""
        print("Dynamic Blog Index Generator")
        print("============================")
        
        # Check if blog directory exists
        if not self.blog_path.exists():
            print(f"Error: Blog directory not found at {self.blog_path}")
            return
        
        # Check if blog.html exists
        if not self.blog_index_path.exists():
            print(f"Error: Blog index not found at {self.blog_index_path}")
            return
        
        # Scan blog directory
        print("Scanning blog directory for posts...")
        blog_posts = self.scan_blog_directory()
        
        if not blog_posts:
            print("No blog posts found in the blog directory.")
            return
        
        print(f"Found {len(blog_posts)} blog posts:")
        for post in blog_posts:
            if post['type'] == 'Release' and post['version']:
                print(f"  🚀 Release {post['version']}: {post['title']}")
            else:
                print(f"  📝 {post['type']}: {post['title']}")
        
        # Generate blog index
        print("\nGenerating dynamic blog index...")
        self.generate_blog_index(blog_posts)
        
        print("Blog index updated successfully!")
        print(f"Generated index for {len(blog_posts)} blog posts.")

def main():
    """Main function to run the dynamic blog index generator."""
    generator = DynamicBlogIndexGenerator()
    generator.run()

if __name__ == "__main__":
    main()
