"""
tests/conftest.py
By default, bypass auth so the functional endpoint tests can exercise the API
without a real Supabase token. test_auth.py clears this override to test the
real JWT enforcement.
"""

import pytest

from main import app
from security.auth import get_current_user


@pytest.fixture(autouse=True)
def _auth_bypass():
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user", "email": "test@example.com"}
    yield
    app.dependency_overrides.pop(get_current_user, None)
