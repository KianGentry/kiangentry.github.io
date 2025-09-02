#!/usr/bin/env python3
"""
GitHub Commit-Based EYN-OS Blog Generator
Pulls actual development commits from GitHub and generates blog posts.
Excludes documentation changes and highlights releases.
"""

import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import requests

class GitHubBlogGenerator:
    def __init__(self, repo_owner="kiangentry", repo_name="EYN-OS"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.blog_path = Path("blog")
        self.template_path = self.blog_path / "template.html"
        self.blog_index_path = Path("blog.html")
        
        # Ensure blog directory exists
        self.blog_path.mkdir(exist_ok=True)
        
        # GitHub API base URL
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
    def get_github_commits(self, days_back=30):
        """Get recent commits from GitHub API."""
        try:
            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # GitHub API endpoint for commits
            url = f"{self.api_base}/commits"
            params = {
                'since': since_date,
                'per_page': 100  # Get more commits
            }
            
            # Make request to GitHub API
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            commits = response.json()
            
            # Check if we need to get more commits (GitHub API pagination)
            all_commits = commits.copy()
            
            # Follow pagination links to get all commits
            while 'next' in response.links:
                next_url = response.links['next']['url']
                response = requests.get(next_url)
                if response.status_code == 200:
                    next_commits = response.json()
                    all_commits.extend(next_commits)
                    print(f"  Fetched additional {len(next_commits)} commits...")
                else:
                    break
            
            print(f"  Total commits fetched: {len(all_commits)}")
            
            # Process commits
            processed_commits = []
            for commit in all_commits:
                commit_info = {
                    'sha': commit['sha'],
                    'message': commit['commit']['message'],
                    'author': commit['commit']['author']['name'],
                    'date': commit['commit']['author']['date'][:10],  # YYYY-MM-DD
                    'url': commit['html_url']
                }
                processed_commits.append(commit_info)
            
            return processed_commits
            
        except Exception as e:
            print(f"Error getting GitHub commits: {e}")
            return []
    
    def is_significant_commit(self, commit):
        """Determine if a commit is significant enough for a blog post."""
        # Clean the message: remove newlines and normalize whitespace
        message = commit['message'].replace('\n', ' ').replace('\r', ' ').lower()
        message = ' '.join(message.split())  # Normalize whitespace
        
        # Skip documentation-only commits
        if self.is_documentation_only_commit(message):
            return False
        
        # Look for significant keywords
        significant_keywords = [
            'release', 'version', 'major', 'feature', 'new', 'add', 'implement',
            'complete', 'rewrite', 'overhaul', 'fix', 'bug', 'improve', 'enhance',
            'kernel', 'driver', 'filesystem', 'game', 'engine', 'assembler',
            'memory', 'system', 'optimize', 'performance', 'security'
        ]
        
        for keyword in significant_keywords:
            if keyword in message:
                return True
        
        return False
    
    def is_documentation_only_commit(self, message):
        """Check if a commit only changes documentation."""
        # If the commit contains "release", it's never documentation-only
        if 'release' in message.lower():
            return False
            
        doc_keywords = [
            'docs', 'documentation', 'readme', 'contributing', 'changelog',
            'update readme', 'fix readme', 'update docs', 'fix docs'
        ]
        
        for keyword in doc_keywords:
            if keyword in message:
                return True
        
        return False
    
    def categorize_commit(self, commit):
        """Categorize the type of commit."""
        message = commit['message'].lower()
        
        if 'release' in message:
            return 'release'
        elif any(word in message for word in ['feature', 'new', 'add', 'implement']):
            return 'feature'
        elif any(word in message for word in ['fix', 'bug', 'patch']):
            return 'fix'
        elif any(word in message for word in ['improve', 'enhance', 'optimize']):
            return 'improvement'
        else:
            return 'update'
    
    def extract_version_from_release(self, message):
        """Extract version number from release commit message."""
        # Look for patterns like "Release 13", "Version 14", etc.
        version_match = re.search(r'release\s+(\d+)', message.lower())
        if version_match:
            return version_match.group(1)
        
        # Also check for version patterns
        version_match = re.search(r'version\s+(\d+)', message.lower())
        if version_match:
            return version_match.group(1)
        
        return None
    
    def generate_commit_blog_post(self, commit):
        """Generate a blog post from commit information."""
        commit_type = self.categorize_commit(commit)
        
        # Generate title
        title = commit['message']
        if len(title) > 60:
            title = title[:57] + "..."
        
        # Generate filename
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        safe_title = re.sub(r'\s+', '-', safe_title).lower()
        
        if commit_type == 'release':
            version = self.extract_version_from_release(commit['message'])
            if version:
                filename = f"release-{version}-{safe_title}.html"
            else:
                filename = f"release-{safe_title}.html"
        else:
            filename = f"commit-{commit['sha'][:8]}-{safe_title}.html"
        
        filepath = self.blog_path / filename
        
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Replace placeholders
        content = template.replace('BLOG_TITLE', title)
        content = content.replace('MONTH YEAR', commit['date'])
        
        # Set appropriate tags
        if commit_type == 'release':
            version = self.extract_version_from_release(commit['message'])
            tags = f"Release, EYN-OS, Version {version}" if version else "Release, EYN-OS"
        else:
            tags = f"{commit_type.title()}, EYN-OS, Development"
        
        content = content.replace('Tag1, Tag2, Tag3', tags)
        content = content.replace('INTRODUCTION_PARAGRAPH', self.generate_commit_intro(commit, commit_type))
        
        # Generate main content
        main_content = self.generate_commit_main_content(commit, commit_type)
        content = content.replace('<!-- CONTENT_PLACEHOLDER -->', main_content)
        
        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filename
    
    def generate_commit_intro(self, commit, commit_type):
        """Generate introduction for commit-based blog post."""
        if commit_type == 'release':
            version = self.extract_version_from_release(commit['message'])
            intro = f"EYN-OS Release {version} has been completed and is now available. "
            intro += "This release brings significant improvements and new features to the operating system, "
            intro += "demonstrating continued development progress and commitment to building everything from scratch."
        else:
            intro = f"EYN-OS development continues with a new {commit_type} that brings improvements to the operating system. "
            intro += "This update demonstrates the ongoing commitment to building a complete operating system from scratch "
            intro += "while maintaining educational value and system performance."
        
        return intro
    
    def generate_commit_main_content(self, commit, commit_type):
        """Generate main content for commit-based blog post."""
        content = []
        
        # Overview section
        content.append('<h2>Update Overview</h2>')
        if commit_type == 'release':
            version = self.extract_version_from_release(commit['message'])
            content.append(f'<p>EYN-OS Release {version} represents a significant milestone in the project\'s development, '
                         f'introducing new capabilities and improvements that enhance the overall user experience and system functionality.</p>')
        else:
            content.append(f'<p>This {commit_type} represents progress in EYN-OS development, '
                         f'introducing improvements and enhancements that contribute to the overall system quality.</p>')
        
        # Commit details
        content.append('<h2>Commit Information</h2>')
        content.append(f'<p><strong>Commit:</strong> <code>{commit["sha"]}</code></p>')
        content.append(f'<p><strong>Date:</strong> {commit["date"]}</p>')
        content.append(f'<p><strong>Type:</strong> {commit_type.title()}</p>')
        content.append(f'<p><strong>Message:</strong> {commit["message"]}</p>')
        content.append(f'<p><strong>GitHub:</strong> <a href="{commit["url"]}" target="_blank">View on GitHub</a></p>')
        
        # Technical details
        content.append('<h2>Technical Details</h2>')
        content.append('<p>This update maintains EYN-OS\'s core philosophy of building everything from scratch for educational purposes. '
                      'Each change is implemented with clear, understandable code that serves as both a functional improvement and a learning resource.</p>')
        
        # Source information
        content.append('<h2>Source Information</h2>')
        content.append(f'<p>This update information was extracted from GitHub commit <code>{commit["sha"]}</code> in the EYN-OS repository. '
                      'For complete technical details, see the full source code and documentation.</p>')
        
        return '\n'.join(content)
    
    def update_blog_index(self, new_posts):
        """Update the main blog index with new posts."""
        print("Blog posts generated. Now updating blog index dynamically...")
        
        # Instead of hard-coding posts, we'll use the dynamic index generator
        # This ensures the blog index always reflects the actual /blog/ directory
        try:
            # Import and run the dynamic index generator
            from dynamic_blog_index import DynamicBlogIndexGenerator
            
            dynamic_generator = DynamicBlogIndexGenerator()
            dynamic_generator.run()
            
        except ImportError:
            print("Warning: Could not import dynamic blog index generator.")
            print("Please run 'python3 dynamic-blog-index.py' to update the blog index.")
        
        print("Blog index will be updated from actual blog post files.")
    
    def generate_blog_index_entry(self, post_info):
        """Generate a blog index entry for a post."""
        filename = post_info.get('filename', 'unknown.html')
        title = post_info.get('title', 'Unknown Post')
        commit_type = post_info.get('type', 'update')
        date = post_info.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if commit_type == 'release':
            version = post_info.get('version', '')
            tags = f"🚀 Release, EYN-OS, Version {version}" if version else "🚀 Release, EYN-OS"
            description = f"EYN-OS Release {version} brings significant updates and improvements to the operating system. This release introduces new features and enhancements that demonstrate the project's continued development and commitment to educational value."
        else:
            tags = f"📝 {commit_type.title()}, EYN-OS, Development"
            description = f"Development update that brings improvements and new features to EYN-OS. This update demonstrates ongoing development progress and commitment to building a complete operating system from scratch."
        
        return f'''<article class="blog-post">
            <header class="post-header">
                <h2><a href="blog/{filename}">{title}</a></h2>
                <div class="post-meta">
                    <span class="post-date">{date}</span>
                    <span class="post-tags">{tags}</span>
                </div>
            </header>
            <div class="post-excerpt">
                <p>{description}</p>
                <p><a href="blog/{filename}" class="read-more">Read Full Post →</a></p>
            </div>
        </article>'''
    
    def run(self, days_back=30):
        """Run the GitHub-based blog generator."""
        print("GitHub Commit-Based EYN-OS Blog Generator")
        print("==========================================")
        print(f"Repository: {self.repo_owner}/{self.repo_name}")
        print(f"Looking back: {days_back} days")
        print()
        
        # Check if template exists
        if not self.template_path.exists():
            print(f"Error: Blog template not found at {self.template_path}")
            return
        
        # Get GitHub commits
        print("Fetching commits from GitHub...")
        commits = self.get_github_commits(days_back)
        
        if not commits:
            print("No recent commits found.")
            return
        
        print(f"Found {len(commits)} recent commits")
        
        # Show the most recent commits for debugging
        print("\nMost recent commits found:")
        for i, commit in enumerate(commits[:10]):
            print(f"  {i+1}. {commit['date']}: {commit['message'][:60]}...")
        if len(commits) > 10:
            print(f"  ... and {len(commits) - 10} more commits")
        
        # Filter for significant commits
        significant_commits = []
        
        for commit in commits:
            if self.is_significant_commit(commit):
                commit_type = self.categorize_commit(commit)
                significant_commits.append(commit)
                
                if commit_type == 'release':
                    version = self.extract_version_from_release(commit['message'])
                    print(f"  🚀 RELEASE: {commit['message']} (Version {version})")
                else:
                    print(f"  📝 {commit_type.title()}: {commit['message']}")
        
        if not significant_commits:
            print("\nNo significant commits found for blog posts.")
            print("(Documentation-only commits are excluded)")
            return
        
        print(f"\nFound {len(significant_commits)} significant commits for blog posts:")
        
        # Generate blog posts
        new_posts = []
        for commit in significant_commits:
            print(f"\nGenerating blog post for: {commit['message']}")
            commit_type = self.categorize_commit(commit)
            filename = self.generate_commit_blog_post(commit)
            
            new_posts.append({
                'filename': filename,
                'title': commit['message'],
                'type': commit_type,
                'date': commit['date'],
                'version': self.extract_version_from_release(commit['message'])
            })
            
            print(f"  Created: blog/{filename}")
        
        # Update blog index dynamically
        print("\nUpdating blog index dynamically...")
        self.update_blog_index(new_posts)
        
        # Now run the dynamic index generator to ensure the blog index reflects all posts
        print("Running dynamic blog index generator...")
        try:
            import subprocess
            result = subprocess.run(['python3', 'dynamic-blog-index.py'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Dynamic blog index updated successfully!")
            else:
                print(f"Warning: Dynamic index update failed: {result.stderr}")
        except Exception as e:
            print(f"Warning: Could not run dynamic index generator: {e}")
            print("Please run 'python3 dynamic-blog-index.py' manually to update the blog index.")
        
        print(f"\nBlog generation complete!")
        print(f"Generated {len(new_posts)} new blog posts:")
        for post in new_posts:
            if post['type'] == 'release':
                print(f"  🚀 Release {post['version']}: {post['title']}")
            else:
                print(f"  📝 {post['type'].title()}: {post['title']}")

def main():
    """Main function to run the GitHub blog generator."""
    generator = GitHubBlogGenerator()
    
    # You can adjust the number of days to look back
    days_back = 120  # Look at commits from the last 120 days to ensure we get all recent ones
    
    generator.run(days_back)

if __name__ == "__main__":
    main()
