from Github_Client import GitHubClient
from Project_Analyzer import ProjectAnalyzer,RepoFile
from Readme_Generator import ReadmeGenerator
import openai 
from dotenv import load_dotenv
import os 
import json
from typing import Dict, List, Optional, Any

load_dotenv()






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
            print(f"Total files fetched: {len(files)}")
            print(f"Files: {[file.path for file in files]}")
            
            # Analyze project structure
            analysis = self.analyzer.analyze_project_structure(files)
            print(f"Project analysis: {json.dumps(analysis, indent=2)}")
            
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
    
    
if __name__ == "__main__":
    # Initialize the agent
    agent = AIReadmeAgent(
        github_token=os.getenv("GITHUB_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Generate README for a repository
    readme = agent.generate_readme_for_repo("KaanSezen1923", "Tolkien-Chatbot-Streamlit-App")
    
    if readme:
        # Save to file or upload back to GitHub
        with open("generated_README.md", "w", encoding="utf-8") as f:
            f.write(readme)
        
        print("README generated successfully!")
        print(readme)
    else:
        print("Failed to generate README")