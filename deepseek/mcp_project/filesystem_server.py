import os
import json
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
import shutil

# Initialize FastMCP server for filesystem operations
mcp = FastMCP("filesystem")

@mcp.tool()
def list_directory(path: str = ".") -> List[str]:
    """
    List contents of a directory.
    
    Args:
        path: Directory path to list (default: current directory)
        
    Returns:
        List of files and directories in the specified path
    """
    try:
        if not os.path.exists(path):
            return [f"Error: Directory '{path}' does not exist"]
        
        if not os.path.isdir(path):
            return [f"Error: '{path}' is not a directory"]
        
        items = os.listdir(path)
        # Add type indicators
        result = []
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                result.append(f"📁 {item}/")
            else:
                result.append(f"📄 {item}")
        
        return result
    except Exception as e:
        return [f"Error listing directory: {str(e)}"]

@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Read contents of a text file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents as string
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"Content of '{file_path}':\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path where to write the file
        content: Content to write to the file
        
    Returns:
        Success or error message
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def create_directory(dir_path: str) -> str:
    """
    Create a new directory.
    
    Args:
        dir_path: Path of the directory to create
        
    Returns:
        Success or error message
    """
    try:
        if os.path.exists(dir_path):
            return f"Directory '{dir_path}' already exists"
        
        os.makedirs(dir_path)
        return f"Successfully created directory '{dir_path}'"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
def delete_file(file_path: str) -> str:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        Success or error message
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"
        
        os.remove(file_path)
        return f"Successfully deleted file '{file_path}'"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@mcp.tool()
def get_file_info(file_path: str) -> str:
    """
    Get information about a file or directory.
    
    Args:
        file_path: Path to the file or directory
        
    Returns:
        Information about the file/directory
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: Path '{file_path}' does not exist"
        
        stat = os.stat(file_path)
        info = {
            "path": file_path,
            "type": "directory" if os.path.isdir(file_path) else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:]
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

@mcp.tool()
def search_files(directory: str, pattern: str) -> List[str]:
    """
    Search for files matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: Pattern to match (supports wildcards)
        
    Returns:
        List of matching files
    """
    try:
        import glob
        
        if not os.path.exists(directory):
            return [f"Error: Directory '{directory}' does not exist"]
        
        search_pattern = os.path.join(directory, pattern)
        matches = glob.glob(search_pattern, recursive=True)
        
        if not matches:
            return [f"No files found matching pattern '{pattern}' in '{directory}'"]
        
        return [os.path.relpath(match, directory) for match in matches]
    except Exception as e:
        return [f"Error searching files: {str(e)}"]

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')