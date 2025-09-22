from fastapi import FastAPI, HTTPException
from AI_Readme_Agent import AIReadmeAgent
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI README Generator API",
    description="Generate professional README files for GitHub repositories using AI",
    version="1.0.0"
)

# Initialize AI Agent
try:
    agent = AIReadmeAgent(
        github_token=os.getenv("GITHUB_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    logger.info("AI README Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI README Agent: {str(e)}")
    agent = None

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "AI README Generator API",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None
    }

@app.get("/generate_readme/{owner}/{repo}")
async def generate_readme(owner: str, repo: str):
    """
    Generate README for a GitHub repository
    
    Args:
        owner (str): GitHub repository owner/username
        repo (str): Repository name
        
    Returns:
        dict: Generated README content
    """
    
    # Check if agent is initialized
    if agent is None:
        logger.error("AI README Agent is not initialized")
        raise HTTPException(
            status_code=500, 
            detail="AI README Agent is not initialized. Please check your API keys."
        )
    
    # Validate parameters
    if not owner or not repo:
        raise HTTPException(
            status_code=400, 
            detail="Both owner and repo parameters are required"
        )
    
    try:
        logger.info(f"Generating README for repository: {owner}/{repo}")
        
        # Call the correct method with correct parameters
        readme_content = agent.generate_readme_for_repo(owner, repo)
        
        if readme_content:
            logger.info(f"README generated successfully for {owner}/{repo}")
            return {
                "success": True,
                "repository": f"{owner}/{repo}",
                "readme": readme_content,
                "message": "README generated successfully"
            }
        else:
            logger.error(f"Failed to generate README for {owner}/{repo}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate README. Please check if the repository exists and is accessible."
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating README for {owner}/{repo}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/generate_readme/{owner}/{repo}/preview")
async def generate_readme_preview(owner: str, repo: str):
    """
    Generate a preview of README analysis without full generation
    """
    
    if agent is None:
        raise HTTPException(
            status_code=500, 
            detail="AI README Agent is not initialized"
        )
    
    try:
        logger.info(f"Generating README preview for: {owner}/{repo}")
        
        # Get repository info
        repo_info = agent.github.get_repo_info(owner, repo)
        
        # Get files
        files = agent._get_all_files(owner, repo)
        
        # Analyze project
        analysis = agent.analyzer.analyze_project_structure(files)
        
        return {
            "success": True,
            "repository": f"{owner}/{repo}",
            "analysis": {
                "languages": analysis.get("languages", {}),
                "frameworks": analysis.get("frameworks", []),
                "project_type": analysis.get("project_type", "unknown"),
                "has_tests": analysis.get("has_tests", False),
                "has_docs": analysis.get("has_docs", False),
                "file_count": len(files)
            },
            "repo_info": {
                "name": repo_info.get("name"),
                "description": repo_info.get("description"),
                "language": repo_info.get("language"),
                "stars": repo_info.get("stargazers_count"),
                "forks": repo_info.get("forks_count")
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating preview for {owner}/{repo}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating preview: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)