# Gym Flow Backend

This is the Django backend for the Gym Flow platform.

## Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install django djangorestframework drf-spectacular django-cors-headers Pillow
    ```

4.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Create a superuser:**
    ```bash
    python manage.py createsuperuser
    ```

## Running the Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`.

## Documentation

Swagger documentation is available at:
`http://127.0.0.1:8000/api/docs/`
# gym_flow_backend
# gym_flow_backend
