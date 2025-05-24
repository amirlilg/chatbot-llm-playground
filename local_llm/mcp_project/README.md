# Local LLM with MCP Tools

A powerful local AI chatbot that combines Ollama for local LLM inference with the Model Context Protocol (MCP) for extensible tool integration. This setup allows you to run a completely local AI assistant with filesystem capabilities and easy extensibility for additional tools.

## 🎯 What This Does

- **Local LLM**: Uses Ollama to run language models entirely on your machine
- **Tool Integration**: Leverages MCP (Model Context Protocol) to provide the LLM with filesystem tools
- **Function Calling**: The LLM can intelligently decide when and how to use available tools
- **Extensible**: Easy to add new MCP servers and tools
- **Privacy**: Everything runs locally - no data sent to external services

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Local LLM       │───▶│  MCP Servers    │
│                 │    │  (via Ollama)    │    │  - Filesystem   │
└─────────────────┘    └──────────────────┘    │  - [Future...]  │
                                 │              └─────────────────┘
                                 ▼
                       ┌──────────────────┐
                       │  Tool Results    │
                       │  Back to LLM     │
                       └──────────────────┘
```

## 📋 Prerequisites

### 1. Python Dependencies
```bash
pip install ollama mcp
```

### 2. Ollama Installation
- **macOS**: `brew install ollama`
- **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
- **Windows**: Download from [ollama.ai](https://ollama.ai)

### 3. Compatible LLM Model
Install a model that **supports function calling**:
```bash
# Recommended options (choose one):
ollama pull llama3.2:3b      # Good balance of size/capability
ollama pull qwen2.5:3b       # Alternative option
ollama pull mistral:7b       # Larger, more capable
```

## 🚀 Quick Start

1. **Clone/Download the files** to a directory
2. **Test your model supports function calling**:
   ```bash
   python test_model_tools.py
   ```
3. **Test the MCP server**:
   ```bash
   python test_mcp_server.py
   ```
4. **Start the chatbot**:
   ```bash
   python local_llm_mcp_chatbot.py
   ```

## 📁 Project Structure

```
mcp_project/
├── local_llm_mcp_chatbot.py    # Main chatbot application
├── filesystem_server.py        # MCP filesystem server
├── server_config.json          # MCP server configuration
├── test_mcp_server.py          # Test MCP functionality
└── test_model_tools.py         # Test model tool support
```

## 🔧 Components Explained

### 1. Filesystem MCP Server (`filesystem_server.py`)
Provides the LLM with filesystem capabilities:

**Available Tools:**
- `list_directory(path)` - List directory contents with file/folder indicators
- `read_file(file_path)` - Read text file contents
- `write_file(file_path, content)` - Write content to files
- `create_directory(dir_path)` - Create new directories
- `delete_file(file_path)` - Delete files safely
- `get_file_info(file_path)` - Get file metadata (size, permissions, etc.)
- `search_files(directory, pattern)` - Search for files using patterns

### 2. Main Chatbot (`local_llm_mcp_chatbot.py`)
The core application that:
- Connects to Ollama for LLM inference
- Manages MCP server connections
- Handles tool calling workflow
- Provides interactive chat interface

**Key Features:**
- Automatic tool discovery from MCP servers
- Intelligent function calling based on user queries
- Conversation memory across the session
- Error handling and recovery

### 3. Configuration (`server_config.json`)
Simple JSON configuration for MCP servers:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["filesystem_server.py"]
    }
  }
}
```

## 💬 Usage Examples

### Basic File Operations
```
You: Create a file called notes.txt with the content "Hello World"
Llama3.2: I'll create that file for you.
🔧 Llama is calling tools...
   Calling write_file with args: {'file_path': 'notes.txt', 'content': 'Hello World'}
Llama3.2: I've successfully created the file 'notes.txt' with the content "Hello World". The file contains 11 characters.
```

### Directory Exploration
```
You: What files are in the current directory?
Llama3.2: Let me check the current directory contents for you.
🔧 Llama is calling tools...
   Calling list_directory with args: {'path': '.'}
Llama3.2: Here are the files and directories in the current directory:
📁 __pycache__/
📄 filesystem_server.py
📄 local_llm_mcp_chatbot.py
📄 notes.txt
📄 server_config.json
📄 test_mcp_server.py
📄 test_model_tools.py
```

### Complex File Management
```
You: Read the content of notes.txt, then create a backup copy
Llama3.2: I'll read the file and create a backup for you.
🔧 Llama is calling tools...
   Calling read_file with args: {'file_path': 'notes.txt'}
   Calling write_file with args: {'file_path': 'notes_backup.txt', 'content': 'Hello World'}
Llama3.2: I've read the content of notes.txt which contains "Hello World", and I've created a backup copy as notes_backup.txt with the same content.
```

## 🔧 Customization

### Adding New Tools to Filesystem Server
Add new functions with the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> str:
    """
    Description of what this tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        
    Returns:
        Description of return value
    """
    # Your implementation here
    return "Result"
```

### Adding New MCP Servers
1. Create a new server file (e.g., `web_server.py`)
2. Add it to `server_config.json`:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["filesystem_server.py"]
    },
    "web": {
      "command": "python",
      "args": ["web_server.py"]
    }
  }
}
```

### Changing the LLM Model
Edit the `desired_model` in `local_llm_mcp_chatbot.py`:
```python
self.desired_model = "qwen2.5:3b"  # or your preferred model
```

## 🧪 Testing

### Test Model Function Calling Support
```bash
python test_model_tools.py
```
This will test all available models and tell you which ones support function calling.

### Test MCP Server Functionality
```bash
python test_mcp_server.py
```
This will test all filesystem tools to ensure they're working correctly.

## 🐛 Troubleshooting

### Common Issues

**"Model does not support tools"**
- Solution: Use a compatible model like `llama3.2:3b`, `qwen2.5:3b`, or `mistral:7b`
- Run `python test_model_tools.py` to check compatibility

**"Failed to connect to filesystem"**
- Check that all Python dependencies are installed: `pip install ollama mcp`
- Ensure `filesystem_server.py` is in the same directory

**"Error loading server configuration"**
- Verify `server_config.json` exists and has valid JSON syntax
- Check file paths in the configuration

**Ollama not responding**
- Make sure Ollama is running: `ollama serve`
- Test with: `ollama list` to see available models

### Performance Tips

- **For faster responses**: Use smaller models like `llama3.2:1b` or `qwen2.5:1.5b`
- **For better accuracy**: Use larger models like `llama3.1:8b` or `mistral:7b`
- **Memory usage**: Monitor system resources and adjust model size accordingly

## 🚀 Next Steps

### Potential Enhancements
- **Web Search Tools**: Add an MCP server for web searching
- **Database Tools**: Connect to databases via MCP
- **API Integration**: Create MCP servers for external APIs
- **Code Execution**: Add safe code execution capabilities
- **Memory**: Implement persistent conversation memory
- **GUI**: Create a web interface or desktop app

### Example Additional MCP Servers
- Weather information
- Calendar management
- Email operations
- Image processing
- Data analysis tools

## 🎉 Congratulations!

You now have a fully functional local LLM with tool capabilities! The system is designed to be extensible, so you can easily add new tools and capabilities as needed. The combination of local inference (privacy) with powerful tool integration makes this a very capable AI assistant.

## 📚 References

- [Ollama Documentation](https://ollama.ai)
- [Model Context Protocol (MCP)](https://model
