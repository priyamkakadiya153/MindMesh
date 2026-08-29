import re
from typing import Optional, Dict
from fastapi import HTTPException, status

COUNTRY_PHONE_RULES: Dict[str, dict] = {
    "+91": {"name": "India", "min": 10, "max": 10},
    "+1": {"name": "US / Canada", "min": 10, "max": 10},
    "+44": {"name": "United Kingdom", "min": 10, "max": 10},
    "+971": {"name": "UAE", "min": 9, "max": 9},
    "+61": {"name": "Australia", "min": 9, "max": 9},
    "+49": {"name": "Germany", "min": 10, "max": 11},
    "+33": {"name": "France", "min": 9, "max": 9},
    "+65": {"name": "Singapore", "min": 8, "max": 8},
    "+81": {"name": "Japan", "min": 10, "max": 10},
}

def validate_and_normalize_phone_number(
    phone: Optional[str],
    default_country_code: str = "+91"
) -> str:
    """
    Validates and normalizes a mobile phone number based on country rules.
    Strictly accepts numeric digits only (and optional leading '+' for country code).
    Rejects spaces, dashes, symbols, letters, and invalid digit lengths with HTTP 400.
    """
    if not phone or not phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number is required."
        )

    clean_raw = phone.strip()

    # Digits-only validation (allowing at most 1 leading '+')
    if not re.match(r"^\+?[0-9]+$", clean_raw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mobile number. India (+91) numbers must contain exactly 10 digits."
        )

    # Determine country code prefix and national digits
    country_code = None
    national_digits = ""

    if clean_raw.startswith("+"):
        matched_cc = None
        for cc in sorted(COUNTRY_PHONE_RULES.keys(), key=lambda x: len(x), reverse=True):
            if clean_raw.startswith(cc):
                matched_cc = cc
                break
        
        if matched_cc:
            country_code = matched_cc
            national_digits = clean_raw[len(matched_cc):]
        else:
            country_code = "+91"
            national_digits = clean_raw.lstrip("+")
    else:
        country_code = default_country_code if default_country_code.startswith("+") else f"+{default_country_code.lstrip('+')}"
        national_digits = clean_raw

    rule = COUNTRY_PHONE_RULES.get(country_code, {"name": "Selected Country", "min": 7, "max": 15})
    c_name = rule["name"]
    min_len = rule["min"]
    max_len = rule["max"]

    if min_len == max_len:
        if len(national_digits) != min_len:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mobile number. {c_name} ({country_code}) numbers must contain exactly {min_len} digits."
            )
    else:
        if not (min_len <= len(national_digits) <= max_len):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mobile number. {c_name} ({country_code}) numbers must contain between {min_len} and {max_len} digits."
            )

    return f"{country_code}{national_digits}"

def normalize_phone_number(phone: Optional[str], default_country_code: str = "+91") -> Optional[str]:
    """
    Normalizes a phone number to standard E.164 string format.
    
    1. Returns None if phone is empty or None.
    2. Trims leading and trailing whitespace.
    3. Removes formatting characters (spaces, dashes, parentheses, dots).
    4. If no country code is present (doesn't start with '+'), automatically attaches default_country_code.
    5. Returns format: +<country_code><digits>, e.g. +919925614120.
    """
    if not phone:
        return None
        
    clean = phone.strip()
    if not clean:
        return None
        
    default_cc = default_country_code.strip()
    if not default_cc.startswith("+"):
        default_cc = "+" + default_cc
    cc_digits = default_cc.lstrip("+")
    
    if clean.startswith("+"):
        digits = "".join(c for c in clean[1:] if c.isdigit())
        if not digits:
            return None
        return f"+{digits}"
    else:
        digits = "".join(c for c in clean if c.isdigit())
        if not digits:
            return None
        # Check if digits start with default country code digits (e.g. '91' for '+91') and total length matches cc_digits + 10
        if digits.startswith(cc_digits) and len(digits) == (len(cc_digits) + 10):
            return f"+{digits}"
        return f"{default_cc}{digits}"
