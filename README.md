# Weight Tracker

A web application for tracking and visualizing your weight over time.

## Features

- Record weight entries with support for different units (kg/lb)
- Visualize weight trends with interactive graphs optimized for mobile and desktop
- Filter by time periods (week, month, year, all time)
- Add notes to weight entries
- View, manage, and delete entries
- Fully responsive design for any device
- Progressive Web App (PWA) support for installation on mobile devices

## Project Structure

The project follows a modular architecture for maintainability and testability:

- `src/app.py` - Main application entry point with app factory function
- `src/models.py` - Database models
- `src/services.py` - Business logic and services
- `src/routes.py` - API endpoints and routes
- `src/templates/` - HTML templates
- `src/static/` - Static assets for the web interface
- `tests/` - Unit tests

## Development Workflow

This project is designed to be used with Docker. The recommended workflow is:

1. Make code changes
2. Run tests to ensure everything works
3. Build and run the Docker image to verify functionality

### Running Tests

```bash
python -m pytest
```

### Docker Setup

#### Building and Running the Docker Image

```bash
# Build the Docker image
docker build -t weight-tracker .

# Run the container
docker run -p 8080:8080 -v $(pwd)/data:/app/data weight-tracker
```

#### Using Docker Compose

Alternatively, use Docker Compose for easier deployment:

```bash
# Run with Docker Compose
docker-compose up -d

# Stop the application
docker-compose down
```

Access the application at: http://localhost:8080

## Unraid Installation

To run this application on Unraid:

### Method 1: Using Docker Hub (Recommended)

1. Build and push the Docker image to Docker Hub:
   ```
   docker build -t calomal/weight-tracker .
   docker push calomal/weight-tracker
   ```

2. In the Unraid web interface, go to the "Docker" tab.

3. Click "Add Container" and enter the following information:
   - **Name**: weight-tracker
   - **Repository**: calomal/weight-tracker
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

## Data Persistence

The application stores all data in an SQLite database located at `/app/data/weight_tracker.db` inside the container. The Docker setup maps this directory to a persistent volume on your host system.

To back up your data, simply make a copy of the database file from your mapped volume directory.

## Progressive Web App (PWA)

This application supports PWA features, allowing you to install it on your iPhone or Android device home screen:

### Installing on iPhone
1. Open the application in Safari
2. Tap the Share button (box with up arrow)
3. Scroll down and tap "Add to Home Screen"
4. Give it a name and tap "Add"

### Installing on Android
1. Open the application in Chrome
2. Tap the menu (three dots)
3. Tap "Add to Home Screen" or "Install App"
4. Follow the prompts

Once installed, the app will:
- Open in full-screen mode (without browser UI)
- Work offline with cached data
- Have its own icon on your home screen

## Running with Docker

The easiest way to run Weight Tracker is using Docker:

```bash
docker run -d \
  --name weight-tracker \
  -p 8080:8080 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -v ./instance:/app/instance \
  calomal/weight-tracker
```

This will run the container in the background, mapping port 8080 on your host to the container, and creating three volumes:
- `./data`: For storing exported data files
- `./logs`: For application logs
- `./instance`: For the database file

You can access the application at http://localhost:8080

### Database Migration from Older Versions

Weight Tracker supports automatic migration from older database versions. If you're upgrading from an older version, you can mount your existing database into the `/app/data` directory, and it will be automatically migrated to the current schema.

Example:
```bash
docker run -d \
  --name weight-tracker \
  -p 8080:8080 \
  -v /path/to/your/old/database/directory:/app/data \
  -v ./logs:/app/logs \
  -v ./instance:/app/instance \
  calomal/weight-tracker
```

The application will:
1. Detect the old database
2. Create a backup of your original database in the data directory
3. Copy the database to the instance directory
4. Perform all necessary schema migrations
5. Start normally with your existing data

A backup of your original database is automatically created with the naming format: `weight_tracker.db.backup-YYYYmmdd-HHMMSS`. 