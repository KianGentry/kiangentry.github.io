#!/usr/bin/env python3
"""
Advanced EYN-OS Blog Generator
Automatically generates blog posts from git commits, markdown files, and repository updates.
"""

import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import shutil

class AdvancedEYNOSBlogGenerator:
    def __init__(self, eynos_path="EYN-OS"):
        self.eynos_path = Path(eynos_path)
        self.blog_path = Path("blog")
        self.template_path = self.blog_path / "template.html"
        self.blog_index_path = Path("blog.html")
        
        # Ensure blog directory exists
        self.blog_path.mkdir(exist_ok=True)
        
    def get_git_commits(self, days_back=30):
        """Get recent git commits from the EYN-OS repository."""
        if not (self.eynos_path / ".git").exists():
            print("No git repository found in EYN-OS directory")
            return []
        
        try:
            # Change to EYN-OS directory
            original_dir = os.getcwd()
            os.chdir(self.eynos_path)
            
            # Get recent commits
            cmd = [
                "git", "log", 
                f"--since={days_back} days ago",
                "--pretty=format:%H|%an|%ad|%s|%b",
                "--date=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            os.chdir(original_dir)
            
            if result.returncode != 0:
                print(f"Git command failed: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 4)
                    if len(parts) >= 4:
                        commit = {
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'subject': parts[3],
                            'body': parts[4] if len(parts) > 4 else ''
                        }
                        commits.append(commit)
            
            return commits
            
        except Exception as e:
            print(f"Error getting git commits: {e}")
            return []
    
    def get_file_changes(self, commit_hash):
        """Get files changed in a specific commit."""
        try:
            original_dir = os.getcwd()
            os.chdir(self.eynos_path)
            
            cmd = ["git", "show", "--name-only", "--pretty=format:", commit_hash]
            result = subprocess.run(cmd, capture_output=True, text=True)
            os.chdir(original_dir)
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return []
            
        except Exception as e:
            print(f"Error getting file changes: {e}")
            return []
    
    def get_file_content_at_commit(self, filepath, commit_hash):
        """Get the content of a file at a specific commit."""
        try:
            original_dir = os.getcwd()
            os.chdir(self.eynos_path)
            
            cmd = ["git", "show", f"{commit_hash}:{filepath}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            os.chdir(original_dir)
            
            if result.returncode == 0:
                return result.stdout
            return None
            
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None
    
    def analyze_commit_for_updates(self, commit):
        """Analyze a commit to determine if it contains significant updates."""
        # Check if commit message indicates a release or major update
        release_keywords = [
            'release', 'version', 'major', 'update', 'feature', 'new',
            'add', 'implement', 'complete', 'rewrite', 'overhaul'
        ]
        
        subject_lower = commit['subject'].lower()
        body_lower = commit['body'].lower()
        
        is_significant = False
        for keyword in release_keywords:
            if keyword in subject_lower or keyword in body_lower:
                is_significant = True
                break
        
        if not is_significant:
            return None
        
        # Get files changed in this commit
        changed_files = self.get_file_changes(commit['hash'])
        
        # Look for important file types
        important_files = []
        for filepath in changed_files:
            if any(filepath.endswith(ext) for ext in ['.md', '.c', '.h', 'Makefile', 'README']):
                important_files.append(filepath)
        
        if not important_files:
            return None
        
        # Extract update information
        update_info = {
            'commit_hash': commit['hash'],
            'date': commit['date'],
            'subject': commit['subject'],
            'body': commit['body'],
            'changed_files': important_files,
            'type': 'commit_update'
        }
        
        # Try to extract version information
        version_match = re.search(r'release\s+(\d+)', subject_lower + ' ' + body_lower)
        if version_match:
            update_info['version'] = version_match.group(1)
        
        return update_info
    
    def extract_features_from_changes(self, changed_files, commit_hash):
        """Extract feature information from changed files."""
        features = []
        
        for filepath in changed_files:
            if filepath.endswith('.md'):
                # Check markdown files for feature descriptions
                content = self.get_file_content_at_commit(filepath, commit_hash)
                if content:
                    feature_matches = re.findall(r'^\s*[-*]\s*\*\*(.+?)\*\*:\s*(.+)$', content, re.MULTILINE)
                    for match in feature_matches:
                        features.append({
                            'name': match[0].strip(),
                            'description': match[1].strip(),
                            'source_file': filepath
                        })
            
            elif filepath.endswith('.c') or filepath.endswith('.h'):
                # Check source files for new functionality
                content = self.get_file_content_at_commit(filepath, commit_hash)
                if content:
                    # Look for function definitions and comments
                    func_matches = re.findall(r'/\*\*\s*(.+?)\s*\*/\s*\n\s*\w+\s+\w+\s*\([^)]*\)', content, re.DOTALL)
                    for match in func_matches:
                        features.append({
                            'name': 'New Functionality',
                            'description': match.strip(),
                            'source_file': filepath
                        })
        
        return features
    
    def generate_commit_blog_post(self, update_info):
        """Generate a blog post from commit information."""
        # Generate title
        title = update_info['subject']
        if len(title) > 60:
            title = title[:57] + "..."
        
        # Generate filename
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        safe_title = re.sub(r'\s+', '-', safe_title).lower()
        filename = f"commit-{update_info['commit_hash'][:8]}-{safe_title}.html"
        filepath = self.blog_path / filename
        
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        content = template.replace('BLOG_TITLE', title)
        content = content.replace('MONTH YEAR', update_info['date'])
        content = content.replace('Tag1, Tag2, Tag3', f"Update, EYN-OS, Development")
        content = content.replace('INTRODUCTION_PARAGRAPH', self.generate_commit_intro(update_info))
        
        # Generate main content
        main_content = self.generate_commit_main_content(update_info)
        content = content.replace('<!-- CONTENT_PLACEHOLDER -->', main_content)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filename
    
    def generate_commit_intro(self, update_info):
        """Generate introduction for commit-based blog post."""
        intro = f"EYN-OS development continues with a new update that brings improvements and new features to the operating system. "
        
        if update_info.get('version'):
            intro += f"This update represents progress toward Release {update_info['version']}. "
        
        intro += "The changes demonstrate the ongoing commitment to building a complete operating system from scratch while maintaining educational value and system performance."
        
        return intro
    
    def generate_commit_main_content(self, update_info):
        """Generate main content for commit-based blog post."""
        content = []
        
        # Overview section
        content.append('<h2>Update Overview</h2>')
        content.append(f'<p>This development update introduces changes and improvements to EYN-OS, continuing the project\'s evolution toward a comprehensive operating system platform.</p>')
        
        # Commit details
        content.append('<h2>Commit Information</h2>')
        content.append(f'<p><strong>Commit:</strong> <code>{update_info["commit_hash"]}</code></p>')
        content.append(f'<p><strong>Date:</strong> {update_info["date"]}</p>')
        content.append(f'<p><strong>Subject:</strong> {update_info["subject"]}</p>')
        
        if update_info['body']:
            content.append('<h3>Commit Description</h3>')
            content.append(f'<p>{update_info["body"]}</p>')
        
        # Changed files
        content.append('<h2>Files Modified</h2>')
        content.append('<p>The following files were modified in this update:</p>')
        content.append('<ul>')
        for filepath in update_info['changed_files']:
            content.append(f'<li><code>{filepath}</code></li>')
        content.append('</ul>')
        
        # Technical details
        content.append('<h2>Technical Details</h2>')
        content.append('<p>This update maintains EYN-OS\'s core philosophy of building everything from scratch for educational purposes. Each change is implemented with clear, understandable code that serves as both a functional improvement and a learning resource.</p>')
        
        # Source information
        content.append('<h2>Source Information</h2>')
        content.append(f'<p>This update information was extracted from git commit <code>{update_info["commit_hash"]}</code> in the EYN-OS repository. For complete technical details, see the full source code and documentation.</p>')
        
        return '\n'.join(content)
    
    def generate_blog_from_git_history(self, days_back=30):
        """Generate blog posts from git commit history."""
        print(f"Analyzing git commits from the last {days_back} days...")
        
        commits = self.get_git_commits(days_back)
        if not commits:
            print("No recent commits found.")
            return []
        
        print(f"Found {len(commits)} recent commits")
        
        # Analyze commits for significant updates
        updates = []
        for commit in commits:
            update_info = self.analyze_commit_for_updates(commit)
            if update_info:
                updates.append(update_info)
                print(f"  - Significant update: {commit['subject']}")
        
        if not updates:
            print("No significant updates found in recent commits.")
            return []
        
        # Generate blog posts
        new_posts = []
        for update in updates:
            print(f"\nGenerating blog post for commit: {update['commit_hash'][:8]}")
            filename = self.generate_commit_blog_post(update)
            new_posts.append({
                'filename': filename,
                'title': update['subject'],
                'type': 'commit_update',
                'date': update['date']
            })
            print(f"  Created: blog/{filename}")
        
        return new_posts
    
    def generate_blog_from_markdown_files(self):
        """Generate blog posts from markdown files in the EYN-OS directory."""
        print("Scanning markdown files for update information...")
        
        updates = []
        
        # Check README.md
        readme_path = self.eynos_path / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                content = f.read()
                release_info = self.extract_release_info_from_markdown(content, "README.md")
                if release_info['version'] or release_info['features']:
                    updates.append(release_info)
        
        # Check other markdown files
        for md_file in self.eynos_path.rglob("*.md"):
            if md_file.name not in ["README.md", "CONTRIBUTING.md"]:
                with open(md_file, 'r') as f:
                    content = f.read()
                    release_info = self.extract_release_info_from_markdown(content, str(md_file.relative_to(self.eynos_path)))
                    if release_info['version'] or release_info['features']:
                        updates.append(release_info)
        
        if not updates:
            print("No updates found in markdown files.")
            return []
        
        print(f"Found {len(updates)} potential updates in markdown files:")
        for update in updates:
            print(f"  - {update['title']} (Version: {update['version']})")
        
        # Generate blog posts
        new_posts = []
        for update in updates:
            print(f"\nGenerating blog post for: {update['title']}")
            filename = self.generate_markdown_blog_post(update)
            new_posts.append({
                'filename': filename,
                'title': update['title'],
                'version': update['version'],
                'type': 'markdown_update'
            })
            print(f"  Created: blog/{filename}")
        
        return new_posts
    
    def extract_release_info_from_markdown(self, content, filename):
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
        
        return release_info
    
    def generate_markdown_blog_post(self, release_info):
        """Generate a blog post from markdown file information."""
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
        content = content.replace('INTRODUCTION_PARAGRAPH', self.generate_markdown_intro(release_info))
        
        # Generate main content
        main_content = self.generate_markdown_main_content(release_info)
        content = content.replace('<!-- CONTENT_PLACEHOLDER -->', main_content)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filename
    
    def generate_markdown_intro(self, release_info):
        """Generate introduction for markdown-based blog post."""
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
    
    def generate_markdown_main_content(self, release_info):
        """Generate main content for markdown-based blog post."""
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
        post_type = post_info.get('type', 'update')
        
        if post_type == 'commit_update':
            tags = f"Development, EYN-OS, Update"
            description = f"Development update that brings improvements and new features to EYN-OS. This update demonstrates ongoing development progress and commitment to building a complete operating system from scratch."
        else:
            tags = f"Release, EYN-OS, {version}"
            description = f"EYN-OS {version} brings significant updates and improvements to the operating system. This release introduces new features and enhancements that demonstrate the project's continued development and commitment to educational value."
        
        return f'''<article class="blog-post">
            <header class="post-header">
                <h2><a href="blog/{filename}">{title}</a></h2>
                <div class="post-meta">
                    <span class="post-date">{post_info.get('date', datetime.now().strftime('%B %Y'))}</span>
                    <span class="post-tags">{tags}</span>
                </div>
            </header>
            <div class="post-excerpt">
                <p>{description}</p>
                <p><a href="blog/{filename}" class="read-more">Read Full Post →</a></p>
            </div>
        </article>'''
    
    def run_full_generation(self, days_back=30):
        """Run the full blog generation process."""
        print("Advanced EYN-OS Blog Generator")
        print("===============================")
        
        # Check if EYN-OS directory exists
        if not self.eynos_path.exists():
            print(f"Error: EYN-OS directory not found at {self.eynos_path}")
            return
        
        # Check if template exists
        if not self.template_path.exists():
            print(f"Error: Blog template not found at {self.template_path}")
            return
        
        all_new_posts = []
        
        # Generate posts from git history
        print("\n1. Generating posts from git commit history...")
        git_posts = self.generate_blog_from_git_history(days_back)
        all_new_posts.extend(git_posts)
        
        # Generate posts from markdown files
        print("\n2. Generating posts from markdown files...")
        markdown_posts = self.generate_blog_from_markdown_files()
        all_new_posts.extend(markdown_posts)
        
        if not all_new_posts:
            print("\nNo new blog posts to generate.")
            return
        
        # Update blog index
        print(f"\n3. Updating blog index with {len(all_new_posts)} new posts...")
        self.update_blog_index(all_new_posts)
        
        print(f"\nBlog generation complete!")
        print(f"Generated {len(all_new_posts)} new blog posts:")
        for post in all_new_posts:
            print(f"  - {post['filename']}")
        print(f"\nYou can now view the updated blog at blog.html")

def main():
    """Main function to run the advanced blog generator."""
    generator = AdvancedEYNOSBlogGenerator()
    
    # You can adjust the number of days to look back
    days_back = 30  # Look at commits from the last 30 days
    
    generator.run_full_generation(days_back)

if __name__ == "__main__":
    main()
