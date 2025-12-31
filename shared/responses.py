from rest_framework.response import Response


def handle_success(data=None, message="", status_code=200):
    response = {
        "status": "success",
        "status_code": status_code,
        "message": message,
        "data": data
    }
    return Response(response, status=status_code)

def handle_error(errors=None, message="", status_code=400):
    if errors is None and message:
        errors = {"detail": message}
    response = {
        "status": "error",
        "status_code": status_code,
        "message": message,
        "errors": errors
    }
    return Response(response, status=status_code)

def handle_validation_error(errors=None, message="Validation Error", status_code=422):
    if errors is None and message:
        errors = {"detail": message}
    response = {
        "status": "error",
        "status_code": status_code,
        "message": message,
        "errors": errors
    }
    return Response(response, status=status_code)

def handle_not_found(message="Resource Not Found", status_code=404):
    response = {
        "status": "error",
        "status_code": status_code,
        "message": message,
        "errors": {"detail": message}
    }
    return Response(response, status=status_code)

def handle_permission_denied(message="Permission Denied", status_code=403):
    response = {
        "status": "error",
        "status_code": status_code,
        "message": message,
        "errors": {"detail": message}
    }
    return Response(response, status=status_code)