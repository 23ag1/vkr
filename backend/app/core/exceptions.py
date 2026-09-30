from fastapi import HTTPException, status

CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

ForbiddenException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions",
)

NotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)

ValidationException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Invalid request",
)
