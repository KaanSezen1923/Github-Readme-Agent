import requests
import base64
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai  
from dotenv import load_dotenv

load_dotenv()



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
    
    
