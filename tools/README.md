# Development Tools

This directory contains helper scripts for developing and running the Weight Tracker app.

## launch_app.py

A convenience script that:
- Starts the Flask app in development mode (debug=True, auto-reload enabled)
- Automatically opens the app in your default browser
- Runs on `http://localhost:5000` by default

### Usage

```bash
# Run from the project root directory
python tools/launch_app.py

# Or make it executable and run directly
chmod +x tools/launch_app.py
./tools/launch_app.py
```

### Features

- **Auto-browser opening**: Automatically opens `http://localhost:5000` in your default browser
- **Development mode**: Debug mode enabled with auto-reload on file changes  
- **Clean output**: Formatted startup messages and graceful shutdown
- **Error handling**: Proper error messages and exit codes
- **Threaded**: Handles multiple requests concurrently

### Environment Variables

- `PORT`: Override the default port (5000)
- `FLASK_DEBUG`: Set to 'false' to disable debug mode (defaults to 'true')

### Requirements

Make sure you have the required dependencies installed:
```bash
pip install -r requirements.txt
``` 