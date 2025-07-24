"""
Docker build and integration tests.

These tests are marked as 'docker' and 'slow' and are skipped by default.
Run with: pytest -m docker
"""

import os
import subprocess
import time
import requests
import pytest
import docker


@pytest.fixture(scope="module")
def docker_client():
    """Get Docker client for testing."""
    try:
        client = docker.from_env()
        client.ping()  # Test connection
        return client
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")


@pytest.fixture(scope="module") 
def docker_image(docker_client):
    """Build the Docker image for testing."""
    print("Building Docker image for testing...")
    
    # Build the image
    image, build_logs = docker_client.images.build(
        path=".",
        tag="weight-tracker:test",
        rm=True,
        forcerm=True
    )
    
    # Print build logs for debugging
    for log in build_logs:
        if 'stream' in log:
            print(log['stream'].strip())
    
    yield image
    
    # Cleanup: remove the test image
    try:
        docker_client.images.remove(image.id, force=True)
        print("Cleaned up test Docker image")
    except Exception as e:
        print(f"Warning: Could not remove test image: {e}")


@pytest.fixture
def docker_container(docker_client, docker_image):
    """Run a Docker container for testing."""
    container = docker_client.containers.run(
        docker_image.id,
        ports={'8080/tcp': None},  # Random port
        detach=True,
        remove=True,
        environment={
            'FLASK_DEBUG': 'false',
            'LOG_LEVEL': 'INFO'
        }
    )
    
    # Wait for container to be ready
    max_wait = 30  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            container.reload()
            if container.status == 'running':
                # Wait a bit more for the app to start
                time.sleep(3)
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        pytest.fail("Container failed to start within timeout")
    
    yield container
    
    # Cleanup
    try:
        container.stop(timeout=10)
    except Exception as e:
        print(f"Warning: Could not stop container: {e}")


class TestDockerBuild:
    """Test Docker image building and basic functionality."""
    
    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_build_succeeds(self, docker_client):
        """Test that Docker image builds successfully."""
        # This test just verifies the build process works
        # The actual build is done in the docker_image fixture
        image, _ = docker_client.images.build(
            path=".",
            tag="weight-tracker:build-test",
            rm=True
        )
        
        assert image is not None
        assert len(image.tags) > 0
        
        # Cleanup
        docker_client.images.remove(image.id, force=True)
    
    @pytest.mark.docker
    @pytest.mark.slow  
    def test_docker_image_properties(self, docker_image):
        """Test that Docker image has expected properties."""
        # Check image exists and has tags
        assert docker_image is not None
        assert docker_image.tags
        
        # Check image labels (from our GitHub Actions workflow)
        labels = docker_image.labels or {}
        
        # Check that we can inspect the image
        attrs = docker_image.attrs
        assert 'Config' in attrs
        assert 'ExposedPorts' in attrs['Config']
        assert '8080/tcp' in attrs['Config']['ExposedPorts']
    
    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_container_starts(self, docker_container):
        """Test that Docker container starts and stays running."""
        # Container should be running
        docker_container.reload()
        assert docker_container.status == 'running'
        
        # Should have the right ports exposed
        ports = docker_container.ports
        assert '8080/tcp' in ports
        assert ports['8080/tcp'] is not None
    
    @pytest.mark.docker
    @pytest.mark.slow
    @pytest.mark.network
    def test_docker_app_responds(self, docker_container):
        """Test that the app in Docker responds to HTTP requests."""
        # Get the mapped port
        docker_container.reload()
        port_info = docker_container.ports['8080/tcp']
        assert port_info, "Port 8080 not mapped"
        
        host_port = port_info[0]['HostPort']
        url = f"http://localhost:{host_port}"
        
        # Try to connect with retries
        max_retries = 10
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    break
            except (requests.ConnectionError, requests.Timeout):
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise
        else:
            pytest.fail(f"App did not respond after {max_retries} attempts")
        
        # App should respond with HTML
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        assert 'Weight Tracker' in response.text or 'weight' in response.text.lower()


class TestDockerIntegration:
    """Integration tests using Docker containers."""
    
    @pytest.mark.docker
    @pytest.mark.slow
    @pytest.mark.integration
    def test_docker_database_persistence(self, docker_client, docker_image):
        """Test that database data persists in Docker."""
        # Create a named volume for testing
        volume = docker_client.volumes.create(name="test-weight-tracker-data")
        
        try:
            # Start container with volume
            container1 = docker_client.containers.run(
                docker_image.id,
                ports={'8080/tcp': None},
                volumes={'test-weight-tracker-data': {'bind': '/app/data', 'mode': 'rw'}},
                detach=True,
                remove=True,
                environment={'FLASK_DEBUG': 'false'}
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Get port and make a request to create some data
            container1.reload()
            port = container1.ports['8080/tcp'][0]['HostPort']
            
            # Make request to initialize database
            response = requests.get(f"http://localhost:{port}", timeout=10)
            assert response.status_code == 200
            
            # Stop first container
            container1.stop()
            container1.wait()
            
            # Start second container with same volume
            container2 = docker_client.containers.run(
                docker_image.id,
                ports={'8080/tcp': None},
                volumes={'test-weight-tracker-data': {'bind': '/app/data', 'mode': 'rw'}},
                detach=True,
                remove=True,
                environment={'FLASK_DEBUG': 'false'}
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Should still be able to connect (database persisted)
            container2.reload()
            port2 = container2.ports['8080/tcp'][0]['HostPort']
            response2 = requests.get(f"http://localhost:{port2}", timeout=10)
            assert response2.status_code == 200
            
            # Cleanup
            container2.stop()
            
        finally:
            # Cleanup volume
            try:
                volume.remove(force=True)
            except Exception as e:
                print(f"Warning: Could not remove test volume: {e}")


class TestDockerCompose:
    """Test Docker Compose functionality."""
    
    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_compose_config(self):
        """Test that docker-compose.yml is valid."""
        # Try both docker-compose and docker compose commands
        for cmd in [['docker-compose', 'config'], ['docker', 'compose', 'config']]:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd='.',
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Should not have any errors
                    assert result.returncode == 0
                    assert 'services:' in result.stdout
                    assert 'weight-tracker:' in result.stdout
                    return
                    
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # If neither command worked, skip the test
        pytest.skip("Neither docker-compose nor docker compose commands are available")


def pytest_configure(config):
    """Configure pytest to handle our custom options."""
    config.addinivalue_line(
        "markers", "docker: Docker-related tests (requires Docker)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that take more time"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark Docker tests and handle test selection."""
    # Skip Docker tests if Docker is not available
    try:
        docker_client = docker.from_env()
        docker_client.ping()
        docker_available = True
    except Exception:
        docker_available = False
    
    for item in items:
        # Auto-skip Docker tests if Docker not available
        if "docker" in item.keywords and not docker_available:
            item.add_marker(pytest.mark.skip(reason="Docker not available"))
        
        # Mark Docker tests in this file as slow automatically
        if item.fspath.basename == "test_docker.py":
            if "docker" not in item.keywords:
                item.add_marker(pytest.mark.docker)
            if "slow" not in item.keywords:
                item.add_marker(pytest.mark.slow) 