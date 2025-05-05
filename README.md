# Weight Tracker

A web application for tracking and visualizing your weight over time.

## Features

- Record weight entries with support for different units (kg/lb)
- Visualize weight trends with interactive graphs optimized for mobile and desktop
- Filter by time periods (week, month, year, all time)
- Add notes to weight entries
- View, manage, and delete entries
- Fully responsive design for any device

## Project Structure

The project follows a modular architecture for maintainability and testability:

- `app.py` - Main application entry point with app factory function
- `models.py` - Database models
- `services.py` - Business logic and services
- `routes.py` - API endpoints and routes
- `templates/` - HTML templates
  - `index.html` - Main dashboard with weight input and graph
  - `entries.html` - Entry management page
- `tests/` - Unit tests
- `requirements.txt` - Python dependencies

## Setup and Running

### Local Development

1. Install dependencies:
   ```
   python -m venv venv
   venv/bin/pip install -r requirements.txt
   ```

2. Run the application:
   ```
   venv/bin/python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:8080
   ```

### Testing

Run the unit tests with pytest:
```
venv/bin/python -m pytest
```

## Docker Setup

### Building the Docker Image

The application is designed to be Docker-compatible. To build and run with Docker:

1. Build the Docker image:
   ```
   docker build -t weight-tracker .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 -v /path/to/data:/app/data weight-tracker
   ```

### Using Docker Compose

Alternatively, use Docker Compose for easier deployment:

1. Create a data directory for persistent storage:
   ```
   mkdir -p data
   ```

2. Run with Docker Compose:
   ```
   docker-compose up -d
   ```

3. Access the application at: http://localhost:8080

## Unraid Installation

To run this application on Unraid:

### Method 1: Using Docker Hub (Recommended)

1. Build and push the Docker image to Docker Hub:
   ```
   docker build -t your-username/weight-tracker .
   docker push your-username/weight-tracker
   ```

2. In the Unraid web interface, go to the "Docker" tab.

3. Click "Add Container" and enter the following information:
   - **Name**: weight-tracker
   - **Repository**: your-username/weight-tracker
   - **Network Type**: Bridge
   - **Port Mappings**:
     - Host Port: 8080 (or your preferred port)
     - Container Port: 8080
   - **Volume Mappings**:
     - Host Path: /mnt/user/appdata/weight-tracker (or your preferred path)
     - Container Path: /app/data
     - Access Mode: Read/Write

4. Click "Apply" to create and start the container.

### Method 2: Using Docker Compose on Unraid

1. Copy the `docker-compose.yml` and `Dockerfile` files to your Unraid server.

2. In the Unraid terminal, navigate to the directory containing these files and run:
   ```
   docker-compose up -d
   ```

### Method 3: Manual Image Build on Unraid

If you prefer to build the image directly on Unraid:

1. Copy the project files to your Unraid server.

2. In the Unraid terminal, navigate to the project directory and run:
   ```
   docker build -t weight-tracker .
   ```

3. Run the container:
   ```
   docker run -d -p 8080:8080 -v /mnt/user/appdata/weight-tracker:/app/data --name weight-tracker weight-tracker
   ```

### Accessing the Application

After installation, access your Weight Tracker application at:
```
http://YOUR_UNRAID_IP:8080
```

## Data Persistence

The application stores all data in an SQLite database located at `/app/data/weight_tracker.db` inside the container. The Docker setup maps this directory to a persistent volume on your host system.

To back up your data, simply make a copy of the database file from your mapped volume directory. 