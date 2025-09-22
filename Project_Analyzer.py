import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class RepoFile:
    path: str
    content: str
    size: int
    type: str


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
        
        # Framework detection patterns
        self.framework_patterns = {
            # Python Frameworks
            'FastAPI': [
                r'from\s+fastapi\s+import',
                r'import\s+fastapi',
                r'FastAPI\s*\(',
                r'@app\.(get|post|put|delete)',
                r'uvicorn\.run'
            ],
            'Django': [
                r'from\s+django',
                r'import\s+django',
                r'DJANGO_SETTINGS_MODULE',
                r'django\.conf',
                r'manage\.py'
            ],
            'Flask': [
                r'from\s+flask\s+import',
                r'import\s+flask',
                r'Flask\s*\(',
                r'@app\.route',
                r'flask\.Flask'
            ],
            'Streamlit': [
                r'import\s+streamlit',
                r'streamlit\.',
                r'st\.',
                r'streamlit\s+run'
            ],
            'LangChain': [
                r'from\s+langchain',
                r'import\s+langchain',
                r'langchain\.',
                r'ChatOpenAI',
                r'LLMChain',
                r'VectorStore',
                r'Document\s*\(',
                r'PromptTemplate'
            ],
            'Gradio': [
                r'import\s+gradio',
                r'gradio\.',
                r'gr\.',
                r'gradio\.Interface'
            ],
            
            # JavaScript/TypeScript Frameworks
            'React': [
                r'import.*react',
                r'from\s+["\']react["\']',
                r'React\.',
                r'useState',
                r'useEffect'
            ],
            'Vue.js': [
                r'import.*vue',
                r'from\s+["\']vue["\']',
                r'Vue\.',
                r'createApp'
            ],
            'Angular': [
                r'@angular/',
                r'import.*@angular',
                r'@Component',
                r'@Injectable'
            ],
            'Express.js': [
                r'import.*express',
                r'require\(["\']express["\']\)',
                r'express\(\)',
                r'app\.listen'
            ],
            'Next.js': [
                r'next/',
                r'import.*next',
                r'getStaticProps',
                r'getServerSideProps'
            ],
            
            # Other frameworks
            'TensorFlow': [
                r'import\s+tensorflow',
                r'tensorflow\.',
                r'tf\.',
                r'keras\.'
            ],
            'PyTorch': [
                r'import\s+torch',
                r'torch\.',
                r'torchvision\.',
                r'nn\.Module'
            ],
            'Pandas': [
                r'import\s+pandas',
                r'pandas\.',
                r'pd\.',
                r'DataFrame'
            ],
            'NumPy': [
                r'import\s+numpy',
                r'numpy\.',
                r'np\.',
                r'ndarray'
            ]
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
                '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala',
                '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS', '.sass': 'Sass'
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
        
        # Detect frameworks by analyzing file contents
        analysis['frameworks'] = self._detect_frameworks(files)
        
        # Analyze dependencies from requirement files
        analysis['dependencies'] = self._analyze_dependencies(files)
        
        # Determine project type based on frameworks and files
        analysis['project_type'] = self._determine_project_type(analysis)
        
        # Determine primary language
        if analysis['languages']:
            analysis['primary_language'] = max(analysis['languages'].items(), key=lambda x: x[1])[0]
        
        return analysis
    
    def _detect_frameworks(self, files: List[RepoFile]) -> List[str]:
        """Detect frameworks by analyzing file contents"""
        detected_frameworks = set()
        
        for file in files:
            # Only analyze text files and limit content size
            if file.content and len(file.content) < 50000:  # Skip very large files
                content_lower = file.content.lower()
                
                for framework, patterns in self.framework_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, file.content, re.IGNORECASE | re.MULTILINE):
                            detected_frameworks.add(framework)
                            break  # Found one pattern, move to next framework
        
        return list(detected_frameworks)
    
    def _analyze_dependencies(self, files: List[RepoFile]) -> Dict[str, List[str]]:
        """Analyze dependencies from requirement files"""
        dependencies = {}
        
        for file in files:
            filename = os.path.basename(file.path).lower()
            
            if filename == 'requirements.txt' and file.content:
                deps = []
                for line in file.content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before == or >= etc.)
                        pkg_name = re.split('[><=!]', line)[0].strip()
                        if pkg_name:
                            deps.append(pkg_name)
                dependencies['python'] = deps
            
            elif filename == 'package.json' and file.content:
                try:
                    import json
                    package_data = json.loads(file.content)
                    deps = []
                    if 'dependencies' in package_data:
                        deps.extend(list(package_data['dependencies'].keys()))
                    if 'devDependencies' in package_data:
                        deps.extend(list(package_data['devDependencies'].keys()))
                    dependencies['javascript'] = deps
                except:
                    pass
        
        return dependencies
    
    def _determine_project_type(self, analysis: Dict[str, Any]) -> str:
        """Determine project type based on analysis"""
        frameworks = analysis['frameworks']
        primary_lang = analysis.get('primary_language', '').lower()
        
        # Web applications
        if any(fw in frameworks for fw in ['FastAPI', 'Django', 'Flask', 'Express.js', 'React', 'Vue.js', 'Angular', 'Next.js']):
            return 'web_application'
        
        # Desktop/GUI applications
        if any(fw in frameworks for fw in ['Streamlit', 'Gradio']):
            return 'gui_application'
        
        # Machine Learning projects
        if any(fw in frameworks for fw in ['TensorFlow', 'PyTorch', 'LangChain']):
            return 'machine_learning'
        
        # Data analysis projects
        if any(fw in frameworks for fw in ['Pandas', 'NumPy']) and primary_lang == 'python':
            return 'data_analysis'
        
        # Default based on primary language
        if primary_lang == 'python':
            return 'python_application'
        elif primary_lang in ['javascript', 'typescript']:
            return 'javascript_application'
        
        return 'unknown'