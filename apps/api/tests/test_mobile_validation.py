import pytest
from httpx import AsyncClient
from app.auth.utils import validate_and_normalize_phone_number
from fastapi import HTTPException

def test_mobile_number_validation_unit():
    # 1. 9876543210 -> Accepted
    assert validate_and_normalize_phone_number("9876543210") == "+919876543210"

    # 2. 9199256141 -> Accepted
    assert validate_and_normalize_phone_number("9199256141") == "+919199256141"

    # 3. 919925614120 -> Rejected (12 digits)
    with pytest.raises(HTTPException) as exc3:
        validate_and_normalize_phone_number("919925614120")
    assert exc3.value.status_code == 400
    assert "India (+91) numbers must contain exactly 10 digits" in exc3.value.detail

    # 4. 12345 -> Rejected (5 digits)
    with pytest.raises(HTTPException) as exc4:
        validate_and_normalize_phone_number("12345")
    assert exc4.value.status_code == 400
    assert "India (+91) numbers must contain exactly 10 digits" in exc4.value.detail

    # 5. abc1234567 -> Rejected (contains letters)
    with pytest.raises(HTTPException) as exc5:
        validate_and_normalize_phone_number("abc1234567")
    assert exc5.value.status_code == 400
    assert "India (+91) numbers must contain exactly 10 digits" in exc5.value.detail

    # 6. 98765-43210 -> Rejected (contains dash)
    with pytest.raises(HTTPException) as exc6:
        validate_and_normalize_phone_number("98765-43210")
    assert exc6.value.status_code == 400
    assert "India (+91) numbers must contain exactly 10 digits" in exc6.value.detail

    # 7. 98765 43210 -> Rejected (contains space)
    with pytest.raises(HTTPException) as exc7:
        validate_and_normalize_phone_number("98765 43210")
    assert exc7.value.status_code == 400
    assert "India (+91) numbers must contain exactly 10 digits" in exc7.value.detail

    # Extra Country rule test: US/Canada (+1) exactly 10 digits
    assert validate_and_normalize_phone_number("+14155552671") == "+14155552671"
    with pytest.raises(HTTPException) as exc_us:
        validate_and_normalize_phone_number("+141555526")
    assert exc_us.value.status_code == 400
    assert "US / Canada (+1) numbers must contain exactly 10 digits" in exc_us.value.detail

@pytest.mark.asyncio
async def test_registration_api_mobile_validation(client: AsyncClient):
    base_payload = {
        "email": "test_mobile_val@mindmesh.com",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User"
    }

    # 1. Reject 12 digits: 919925614120
    res1 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "919925614120"})
    assert res1.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res1.json()["detail"]

    # 2. Reject 5 digits: 12345
    res2 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "12345"})
    assert res2.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res2.json()["detail"]

    # 3. Reject invalid chars: abc1234567
    res3 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "abc1234567"})
    assert res3.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res3.json()["detail"]

    # 4. Reject dash: 98765-43210
    res4 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "98765-43210"})
    assert res4.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res4.json()["detail"]

    # 5. Reject space: 98765 43210
    res5 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "98765 43210"})
    assert res5.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res5.json()["detail"]

    # 6. Accept valid 10 digits: 9876543210
    res6 = await client.post("/api/v1/auth/register", json={**base_payload, "phone_number": "9876543210"})
    assert res6.status_code == 200
    assert "registration_token" in res6.json()
