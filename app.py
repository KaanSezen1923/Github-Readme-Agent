import streamlit as st
import requests
import time

# Page configuration
st.set_page_config(
    page_title="AI README Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'readme_content' not in st.session_state:
    st.session_state.readme_content = ""

if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

if 'current_repo' not in st.session_state:
    st.session_state.current_repo = {"username": "", "repo_name": ""}

if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

if 'last_generation_time' not in st.session_state:
    st.session_state.last_generation_time = None

if 'api_status' not in st.session_state:
    st.session_state.api_status = "unknown"

def check_api_health():
    """Check if the FastAPI backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_status = "healthy"
            return True
        else:
            st.session_state.api_status = "unhealthy"
            return False
    except requests.exceptions.RequestException:
        st.session_state.api_status = "unavailable"
        return False

def get_repo_preview(username, repo_name):
    """Get repository analysis preview"""
    try:
        response = requests.get(f"http://localhost:8000/generate_readme/{username}/{repo_name}/preview")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def generate_readme(username, repo_name):
    """Generate README content"""
    try:
        response = requests.get(f"http://localhost:8000/generate_readme/{username}/{repo_name}")
        if response.status_code == 200:
            data = response.json()
            return data.get("readme", ""), None
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return None, f"Error {response.status_code}: {error_detail}"
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to the API server. Make sure the FastAPI server is running."
    except Exception as e:
        return None, f"An error occurred: {str(e)}"

def save_to_history(username, repo_name, readme_content):
    """Save generation to history"""
    history_item = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "repository": f"{username}/{repo_name}",
        "readme_length": len(readme_content),
        "readme_content": readme_content
    }
    st.session_state.generation_history.insert(0, history_item)
    # Keep only last 10 generations
    if len(st.session_state.generation_history) > 10:
        st.session_state.generation_history = st.session_state.generation_history[:10]

def clear_current_readme():
    """Clear current README content"""
    st.session_state.readme_content = ""
    st.session_state.current_repo = {"username": "", "repo_name": ""}

def load_from_history(history_item):
    """Load README from history"""
    st.session_state.readme_content = history_item["readme_content"]
    username, repo_name = history_item["repository"].split("/")
    st.session_state.current_repo = {"username": username, "repo_name": repo_name}

# Main UI
st.title("🤖 AI GitHub README Generator")
st.markdown("Generate professional README files for your GitHub repositories using AI.")

# Sidebar for API status and settings
with st.sidebar:
    st.header("🔧 Settings")
    
    # API Health Check
    if st.button("Check API Status", use_container_width=True):
        with st.spinner("Checking API..."):
            check_api_health()
    
    # Display API status
    if st.session_state.api_status == "healthy":
        st.success("✅ API Server: Online")
    elif st.session_state.api_status == "unhealthy":
        st.error("❌ API Server: Unhealthy")
    else:
        st.warning("⚠️ API Server: Unknown Status")
    
    st.divider()
    
    # Generation History
    st.header("📚 History")
    
    if st.session_state.generation_history:
        for i, item in enumerate(st.session_state.generation_history):
            with st.container():
                st.write(f"**{item['repository']}**")
                st.caption(f"{item['timestamp']} • {item['readme_length']} chars")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{i}", use_container_width=True):
                        load_from_history(item)
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_{i}", use_container_width=True):
                        st.session_state.generation_history.pop(i)
                        st.rerun()
                
                st.divider()
    else:
        st.info("No generation history yet.")
    
    if st.session_state.generation_history:
        if st.button("Clear All History", use_container_width=True):
            st.session_state.generation_history = []
            st.rerun()

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Repository Information")
    
    # Repository input form
    with st.form("repo_form"):
        username = st.text_input(
            "GitHub Username", 
            value=st.session_state.current_repo.get("username", ""),
            placeholder="e.g., octocat"
        )
        
        repo_name = st.text_input(
            "Repository Name", 
            value=st.session_state.current_repo.get("repo_name", ""),
            placeholder="e.g., Hello-World"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            preview_button = st.form_submit_button("🔍 Preview", use_container_width=True)
        
        with col_btn2:
            generate_button = st.form_submit_button("🚀 Generate", use_container_width=True)
        
        with col_btn3:
            clear_button = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    # Handle form submissions
    if clear_button:
        clear_current_readme()
        st.rerun()
    
    if preview_button and username and repo_name:
        if check_api_health():
            with st.spinner("Getting repository preview..."):
                preview_data = get_repo_preview(username, repo_name)
                
                if preview_data and preview_data.get("success"):
                    st.success("Repository found!")
                    
                    # Display repository info
                    repo_info = preview_data.get("repo_info", {})
                    analysis = preview_data.get("analysis", {})
                    
                    st.subheader("Repository Details")
                    st.write(f"**Name:** {repo_info.get('name', 'N/A')}")
                    st.write(f"**Description:** {repo_info.get('description', 'No description')}")
                    st.write(f"**Primary Language:** {repo_info.get('language', 'N/A')}")
                    st.write(f"**Stars:** {repo_info.get('stars', 0)} ⭐")
                    st.write(f"**Forks:** {repo_info.get('forks', 0)} 🍴")
                    
                    st.subheader("Project Analysis")
                    st.write(f"**Project Type:** {analysis.get('project_type', 'unknown').replace('_', ' ').title()}")
                    st.write(f"**Languages:** {', '.join(analysis.get('languages', {}).keys())}")
                    
                    if analysis.get('frameworks'):
                        st.write(f"**Frameworks:** {', '.join(analysis.get('frameworks', []))}")
                    
                    st.write(f"**Files Analyzed:** {analysis.get('file_count', 0)}")
                    st.write(f"**Has Tests:** {'✅' if analysis.get('has_tests') else '❌'}")
                    st.write(f"**Has Documentation:** {'✅' if analysis.get('has_docs') else '❌'}")
                else:
                    st.error("Repository not found or not accessible.")
        else:
            st.error("API server is not available. Please check the server status.")
    
    if generate_button:
        if not username or not repo_name:
            st.error("Please enter both GitHub username and repository name.")
        elif not check_api_health():
            st.error("API server is not available. Please check the server status.")
        else:
            # Update session state
            st.session_state.current_repo = {"username": username, "repo_name": repo_name}
            st.session_state.is_generating = True
            
            with st.spinner("🤖 Generating README... This may take a moment."):
                readme_content, error = generate_readme(username, repo_name)
                
                if readme_content:
                    st.session_state.readme_content = readme_content
                    st.session_state.last_generation_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_to_history(username, repo_name, readme_content)
                    st.success("✅ README generated successfully!")
                    st.balloons()
                else:
                    st.error(f"❌ Failed to generate README: {error}")
            
            st.session_state.is_generating = False

with col2:
    st.header("📄 Generated README")
    
    if st.session_state.readme_content:
        # Display generation info
        if st.session_state.current_repo.get("username") and st.session_state.current_repo.get("repo_name"):
            current_repo_str = f"{st.session_state.current_repo['username']}/{st.session_state.current_repo['repo_name']}"
            st.info(f"**Repository:** {current_repo_str}")
            
            if st.session_state.last_generation_time:
                st.caption(f"Generated on: {st.session_state.last_generation_time}")
        
        # Display README content
        st.text_area(
            "Generated README Content",
            value=st.session_state.readme_content,
            height=500,
            key="readme_display"
        )
        
        # Download and copy options
        col_down1, col_down2 = st.columns(2)
        
        with col_down1:
            st.download_button(
                "📥 Download README.md",
                data=st.session_state.readme_content,
                file_name="README.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col_down2:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.write("```markdown")
                st.code(st.session_state.readme_content, language="markdown")
                st.write("```")
                st.info("💡 Select and copy the content from the code block above.")
        
        # README Preview
        with st.expander("👀 README Preview (Rendered)", expanded=False):
            st.markdown(st.session_state.readme_content)
    
    else:
        st.info("👆 Enter repository details and click 'Generate' to create a README.")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🤖 Powered by AI • Made with ❤️ using Streamlit</p>
        <p><small>Make sure your FastAPI server is running on localhost:8000</small></p>
    </div>
    """,
    unsafe_allow_html=True
)
