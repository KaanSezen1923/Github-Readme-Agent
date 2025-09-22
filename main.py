import requests
import base64
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai  
from dotenv import load_dotenv

load_dotenv()

@dataclass
class RepoFile:
    path: str
    content: str
    size: int
    type: str

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_repo_structure(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Get repository file structure recursively"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repo structure: {response.json()}")
        
        return response.json()
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Get content of a specific file"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            return None
        
        file_info = response.json()
        if file_info.get('encoding') == 'base64':
            try:
                content = base64.b64decode(file_info['content']).decode('utf-8')
                return content
            except UnicodeDecodeError:
                return None  # Binary file
        
        return file_info.get('content', '')
    
    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get basic repository information"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repo info: {response.json()}")
        
        return response.json()

class ProjectAnalyzer:
    def __init__(self):
        self.important_files = {
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 
            'pom.xml', 'build.gradle', 'composer.json', 'Gemfile',
            'setup.py', 'pyproject.toml', 'CMakeLists.txt', 'Makefile'
        }
        
        self.config_files = {
            '.env.example', 'config.yaml', 'config.json', 'docker-compose.yml',
            'Dockerfile', '.gitignore', 'tsconfig.json', 'webpack.config.js'
        }
        
        self.doc_files = {
            'LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md', 'docs/'
        }
    
    def analyze_project_structure(self, files: List[RepoFile]) -> Dict[str, Any]:
        
        analysis = {
            'languages': {},
            'frameworks': [],
            'dependencies': {},
            'project_type': 'unknown',
            'main_files': [],
            'config_files': [],
            'has_tests': False,
            'has_docs': False
        }
        
        # Analyze file extensions and types
        for file in files:
            ext = os.path.splitext(file.path)[1].lower()
            filename = os.path.basename(file.path).lower()
            
            # Count languages
            lang_map = {
                '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
                '.go': 'Go', '.rs': 'Rust', '.php': 'PHP', '.rb': 'Ruby',
                '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala'
            }
            
            if ext in lang_map:
                lang = lang_map[ext]
                analysis['languages'][lang] = analysis['languages'].get(lang, 0) + 1
            
            # Check for important files
            if filename in self.important_files or any(imp in file.path for imp in self.important_files):
                analysis['main_files'].append(file.path)
            
            # Check for config files
            if filename in self.config_files or any(conf in file.path for conf in self.config_files):
                analysis['config_files'].append(file.path)
            
            # Check for tests
            if 'test' in file.path.lower() or 'spec' in file.path.lower():
                analysis['has_tests'] = True
            
            # Check for documentation
            if any(doc in file.path.lower() for doc in ['readme', 'doc', 'wiki']):
                analysis['has_docs'] = True
        
        # Determine primary language
        if analysis['languages']:
            analysis['primary_language'] = max(analysis['languages'].items(), key=lambda x: x[1])[0]
        
        return analysis

class ReadmeGenerator:
    def __init__(self, llm_client, model="gpt-4"):
        self.llm_client = llm_client
        self.model = model
    
    def generate_readme(self, repo_info: Dict, files: List[RepoFile], analysis: Dict) -> str:
        """Generate README content using LLM"""
        
        # Prepare context for LLM
        context = self._prepare_context(repo_info, files, analysis)
        
        prompt = f"""
You are an expert technical writer tasked with creating a comprehensive README.md file for a GitHub repository.

Repository Information:
{json.dumps(repo_info, indent=2)}

Project Analysis:
{json.dumps(analysis, indent=2)}

Key Files Content:
{context}

Please generate a well-structured README.md file that includes:

1. **Project Title and Description** - Clear, concise project overview
2. **Features** - Key functionality and capabilities
3. **Technology Stack** - Languages, frameworks, and tools used
4. **Installation Instructions** - Step-by-step setup guide
5. **Usage Examples** - Code examples and basic usage
6. **Project Structure** - Important directories and files
7. **Contributing Guidelines** - How others can contribute
8. **License Information** - If license file exists

Guidelines:
- Use proper Markdown formatting
- Be clear and concise
- Include code examples where appropriate
- Make it beginner-friendly but comprehensive
- Use emojis sparingly and professionally
- Ensure the README is engaging and informative

Generate only the README.md content without any additional explanations.
"""

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in creating excellent README files."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _prepare_context(self, repo_info: Dict, files: List[RepoFile], analysis: Dict) -> str:
        """Prepare file contents for LLM context"""
        context_parts = []
        
        # Include important files content (limited to avoid token limits)
        important_files = analysis.get('main_files', [])[:5]  # Limit to 5 most important
        
        for file in files:
            if file.path in important_files and file.size < 10000:  # Skip large files
                context_parts.append(f"=== {file.path} ===\n{file.content[:1000]}...\n")
        
        return "\n".join(context_parts)

class AIReadmeAgent:
    def __init__(self, github_token: str, openai_api_key: str):
        self.github = GitHubClient(github_token)
        self.analyzer = ProjectAnalyzer()
        
        # Initialize OpenAI client
        openai.api_key = openai_api_key
        self.readme_generator = ReadmeGenerator(openai)
    
    def generate_readme_for_repo(self, owner: str, repo: str) -> str:
        """Main method to generate README for a repository"""
        try:
            print(f"Analyzing repository: {owner}/{repo}")
            
            # Get repository information
            repo_info = self.github.get_repo_info(owner, repo)
            
            # Get all files in the repository
            files = self._get_all_files(owner, repo)
            
            # Analyze project structure
            analysis = self.analyzer.analyze_project_structure(files)
            
            # Generate README
            readme_content = self.readme_generator.generate_readme(repo_info, files, analysis)
            
            return readme_content
            
        except Exception as e:
            print(f"Error generating README: {str(e)}")
            return None
    
    def _get_all_files(self, owner: str, repo: str, path: str = "", max_files: int = 50) -> List[RepoFile]:
        """Recursively get all files from repository"""
        files = []
        
        try:
            contents = self.github.get_repo_structure(owner, repo, path)
            
            for item in contents:
                if len(files) >= max_files:  # Limit to prevent API rate limiting
                    break
                
                if item['type'] == 'file':
                    content = self.github.get_file_content(owner, repo, item['path'])
                    if content is not None:
                        files.append(RepoFile(
                            path=item['path'],
                            content=content,
                            size=item['size'],
                            type=item['type']
                        ))
                
                elif item['type'] == 'dir' and not any(skip in item['path'] for skip in ['node_modules', '.git', '__pycache__']):
                    # Recursively get files from directories
                    files.extend(self._get_all_files(owner, repo, item['path'], max_files - len(files)))
        
        except Exception as e:
            print(f"Error fetching files from {path}: {str(e)}")
        
        return files

# Usage Example
if __name__ == "__main__":
    # Initialize the agent
    agent = AIReadmeAgent(
        github_token=os.getenv("GITHUB_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Generate README for a repository
    readme = agent.generate_readme_for_repo("KaanSezen1923", "Agentic-Movie-Recommendation-System-Api")
    
    if readme:
        # Save to file or upload back to GitHub
        with open("generated_README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        
        print("README generated successfully!")
        print(readme)
    else:
        print("Failed to generate README")