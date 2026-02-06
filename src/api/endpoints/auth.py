"""
Authentication and user management endpoints
"""

import base64
import json
import logging
from fastapi import APIRouter, Request
from typing import Optional

from ..models import UserInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["auth"])


def get_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from Azure AD authentication headers
    
    Azure Container Apps Easy Auth provides user information in the
    X-MS-CLIENT-PRINCIPAL header (base64 encoded JSON)
    """
    try:
        # Get the principal header
        principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
        if not principal_header:
            logger.warning("No X-MS-CLIENT-PRINCIPAL header found")
            return None
        
        # Decode the base64 principal data
        principal_data = json.loads(base64.b64decode(principal_header))
        logger.debug(f"Principal data structure: {list(principal_data.keys())}")
        
        # Try multiple claim types that might contain the user ID
        claims = principal_data.get("claims", [])
        
        # Try to find user ID in claims
        for claim in claims:
            typ = claim.get("typ", "")
            val = claim.get("val", "")
            
            # Check various claim types that contain user ID
            if typ in ["oid", "http://schemas.microsoft.com/identity/claims/objectidentifier"]:
                logger.info(f"Found user ID in claim type '{typ}': {val}")
                return val
            elif typ == "sub" and not any(c.get("typ") == "oid" for c in claims):
                # Use sub as fallback if oid not found
                logger.info(f"Using sub claim as user ID: {val}")
                return val
        
        # If no claims found, try direct userId field
        if "userId" in principal_data:
            user_id = principal_data["userId"]
            logger.info(f"Found user ID in userId field: {user_id}")
            return user_id
        
        logger.warning("Could not find user ID in any expected claim type")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}", exc_info=True)
        return None


def get_user_name(request: Request) -> Optional[str]:
    """Extract user name from Azure AD authentication headers"""
    try:
        principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
        if not principal_header:
            return None
        
        principal_data = json.loads(base64.b64decode(principal_header))
        claims = principal_data.get("claims", [])
        
        # Look for name claim
        for claim in claims:
            if claim.get("typ") == "name":
                return claim.get("val")
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user name: {e}", exc_info=True)
        return None


@router.get("/userinfo", response_model=UserInfo)
async def get_user_info(request: Request):
    """
    Get current user information from Azure AD
    
    Returns user details if authenticated, or a not-authenticated response
    """
    user_id = get_user_id(request)
    user_name = get_user_name(request)
    
    if user_id or user_name:
        return UserInfo(
            authenticated=True,
            id=user_id,
            name=user_name or "User"
        )
    
    return UserInfo(authenticated=False)


@router.post("/signout")
async def sign_out():
    """
    Sign out endpoint (handled by Azure Container Apps Easy Auth)
    
    Redirects to /.auth/logout/aad which handles the actual sign-out
    """
    return {"redirect": "/.auth/logout/aad"}
