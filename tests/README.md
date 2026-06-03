# EFF API Test Suite

Comprehensive pytest test suite for the EFF Fantasy Football API.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_security.py
```

### Run specific test class
```bash
pytest tests/test_security.py::TestPasswordHashing
```

### Run specific test
```bash
pytest tests/test_security.py::TestPasswordHashing::test_hash_password
```

### Run tests by marker
```bash
pytest -m unit
pytest -m integration
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Structure

- **conftest.py**: Pytest configuration and shared fixtures
  - `test_db`: In-memory SQLite database for testing
  - `test_client`: FastAPI TestClient with overridden database
  - `test_user`: Sample user for testing

- **test_security.py**: Authentication and password tests
  - Password hashing and verification
  - JWT token creation and validation

- **test_models.py**: Database model tests
  - User, Lookup, League, Division, Team model creation
  - Field validation and uniqueness constraints

- **test_services.py**: Business logic tests
  - QueryService methods
  - Season ID calculation
  - Query filtering

- **test_auth_endpoints.py**: API endpoint tests
  - SignIn/SignOut/SignInfo endpoints
  - Request/response validation
  - Legacy form-based and REST JSON endpoints

## Fixtures

### test_db
SQLite in-memory database session. Automatically creates all tables.

```python
def test_my_feature(test_db):
    user = User(...)
    test_db.add(user)
    test_db.commit()
```

### test_client
FastAPI TestClient with test database dependency override.

```python
def test_endpoint(test_client):
    response = test_client.get("/api/endpoint")
    assert response.status_code == 200
```

### test_user
Pre-created test user (email: test@example.com, password: password123).

```python
def test_user_feature(test_client, test_user):
    assert test_user.userEmail == "test@example.com"
```

### reset_request_context
Automatically resets RequestContext after each test.

## Best Practices

1. **Use fixtures**: Don't create database sessions manually
2. **Test one thing**: Each test should verify one behavior
3. **Use descriptive names**: Test names should describe what they test
4. **Mark tests appropriately**: Use @pytest.mark.unit or @pytest.mark.integration
5. **Keep tests isolated**: Don't depend on test execution order
6. **Mock external services**: For HTTP calls, email, etc.

## Adding New Tests

1. Create test file in tests/ directory: `test_feature.py`
2. Name test functions starting with `test_`
3. Use fixtures from conftest.py
4. Run: `pytest tests/test_feature.py -v`

Example:
```python
def test_new_feature(test_db):
    """Test new feature behavior."""
    obj = MyModel(...)
    test_db.add(obj)
    test_db.commit()
    
    assert obj.id is not None
```
