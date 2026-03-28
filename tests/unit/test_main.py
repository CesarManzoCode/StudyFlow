from fastapi import FastAPI

from app.main import create_app


def test_create_app_builds_fastapi_instance_with_expected_routes() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "StudyFlow"

    route_paths = {route.path for route in app.routes}
    assert "/health" in route_paths
    assert "/" in route_paths

    static_routes = [route for route in app.routes if route.name == "static"]
    assert len(static_routes) == 1
