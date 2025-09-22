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


class ReadmeGenerator:
    def __init__(self, llm_client, model="gpt-4"):
        self.llm_client = llm_client
        self.model = model
    
    def generate_readme(self, repo_info: Dict, files: List[RepoFile], analysis: Dict) -> str:
        """Generate README content using LLM"""
        
        # Prepare context for LLM
        context = self._prepare_context(repo_info, files, analysis)
        
        # Create a more detailed technology stack description
        tech_stack = self._format_tech_stack(analysis)
        
        prompt = f"""
You are an expert technical writer tasked with creating a comprehensive README.md file for a GitHub repository.

Repository Information:
{json.dumps(repo_info, indent=2)}

Project Analysis:
{json.dumps(analysis, indent=2)}

Technology Stack Details:
{tech_stack}

Key Files Content:
{context}

Please generate a well-structured README.md file that includes:

1. **Project Title and Description** - Clear, concise project overview based on repo name and description
2. **Features** - Key functionality and capabilities (infer from code structure and frameworks)
3. **Technology Stack** - Languages, frameworks, and tools used (use the detailed tech stack info)
4. **Prerequisites** - System requirements and dependencies needed
5. **Installation Instructions** - Step-by-step setup guide based on detected dependencies
6. **Usage Examples** - Code examples and basic usage based on main application files
7. **Project Structure** - Important directories and files explanation
8. **API Documentation** - If REST API detected (FastAPI/Flask/Express)
9. **Contributing Guidelines** - How others can contribute
10. **License Information** - If license file exists

Special Instructions:
- If Streamlit is detected, include `streamlit run app.py` command
- If FastAPI is detected, include `uvicorn` run commands and API endpoints
- If LangChain is detected, mention AI/NLP capabilities
- If requirements.txt exists, mention `pip install -r requirements.txt`
- For web applications, include information about running development server
- Use proper Markdown formatting with badges if appropriate
- Be clear and concise but comprehensive
- Include code examples where relevant
- Make it beginner-friendly but informative

Generate only the README.md content without any additional explanations.
"""

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in creating excellent README files for software projects."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _prepare_context(self, repo_info: Dict, files: List[RepoFile], analysis: Dict) -> str:
        """Prepare file contents for LLM context"""
        context_parts = []
        
        # Prioritize important files
        priority_files = ['app.py', 'main.py', 'requirements.txt', 'package.json', 'setup.py']
        main_files = analysis.get('main_files', [])
        
        # Combine and prioritize files
        files_to_include = []
        
        # First, add priority files if they exist
        for file in files:
            if os.path.basename(file.path) in priority_files:
                files_to_include.append(file)
        
        # Then add main files
        for file in files:
            if file.path in main_files and file not in files_to_include:
                files_to_include.append(file)
        
        # Add other important files
        for file in files:
            if len(files_to_include) >= 6:  # Limit to prevent token overflow
                break
            if (file.path.endswith('.py') or file.path.endswith('.js') or file.path.endswith('.ts')) and file not in files_to_include:
                files_to_include.append(file)
        
        # Generate context
        for file in files_to_include:
            if file.content and file.size < 15000:  # Skip very large files
                # Truncate content if too long
                content = file.content[:2000] + "..." if len(file.content) > 2000 else file.content
                context_parts.append(f"=== {file.path} ===\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _format_tech_stack(self, analysis: Dict) -> str:
        """Format technology stack information for better LLM understanding"""
        tech_info = []
        
        # Primary language
        if 'primary_language' in analysis:
            tech_info.append(f"Primary Language: {analysis['primary_language']}")
        
        # All languages
        if analysis.get('languages'):
            langs = [f"{lang} ({count} files)" for lang, count in analysis['languages'].items()]
            tech_info.append(f"Languages: {', '.join(langs)}")
        
        # Frameworks
        if analysis.get('frameworks'):
            tech_info.append(f"Frameworks/Libraries: {', '.join(analysis['frameworks'])}")
        
        # Dependencies
        if analysis.get('dependencies'):
            for lang, deps in analysis['dependencies'].items():
                if deps:
                    tech_info.append(f"{lang.title()} Dependencies: {', '.join(deps[:10])}")  # Limit to first 10
        
        # Project type
        if analysis.get('project_type') and analysis['project_type'] != 'unknown':
            tech_info.append(f"Project Type: {analysis['project_type'].replace('_', ' ').title()}")
        
        return "\n".join(tech_info)