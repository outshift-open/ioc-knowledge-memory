"""UserTable service - Business logic for user operations"""

import logging
from datetime import datetime, timezone
import uuid
import os
from typing import List

from fastapi import HTTPException, status

from server.schemas.user import UserCreate, UserResponse, UserDetail
from server.database.relational_db.models.user import User
from server.database.relational_db.db import RelationalDB
from server.common import get_global_encryption_key, encrypt_data

# Get logger instance (logging is setup in main.py)
logger = logging.getLogger(__name__)

# Admin user constants
ADMIN_USER_USERNAME_DEFAULT = "admin"
ADMIN_USER_PASSWORD_DEFAULT = "admin"
ADMIN_USER_DOMAIN_DEFAULT = "tkf.local"
ADMIN_USER_ROLE_DEFAULT = "Software Admin"


class UserService:
    """Service layer for user business logic"""

    def create_admin_user(self) -> UserResponse:
        """
        Create a new admin user
        Kept as a separate function for future expansion to the admin user functionality
        Returns:
            UserResponse with the created user ID
        Raises:
            HTTPException: If error
        """
        logger.info("Starting admin user creation process")

        try:
            # Get database instance
            logger.debug("Initializing database connection")
            db = RelationalDB()
            session = db.get_session()

            try:
                # Check if admin user already exists
                existing_user = (
                    session.query(User)
                    .filter(User.username == ADMIN_USER_USERNAME_DEFAULT, User.deleted_at.is_(None))
                    .first()
                )

                if existing_user:
                    logger.info(
                        f"Admin user '{ADMIN_USER_USERNAME_DEFAULT}' already exists with ID: {existing_user.id}"
                    )
                    return UserResponse(id=existing_user.id)

                # Create new admin user
                user_id = str(uuid.uuid4())
                password = os.getenv("ADMIN_USER_PASSWORD", ADMIN_USER_PASSWORD_DEFAULT)
                key = get_global_encryption_key()
                encrypted_password = encrypt_data(password, key)

                admin_user = User(
                    id=user_id,
                    username=ADMIN_USER_USERNAME_DEFAULT,
                    password=encrypted_password,
                    domain=ADMIN_USER_DOMAIN_DEFAULT,
                    role=ADMIN_USER_ROLE_DEFAULT,
                )

                # Add to database
                session.add(admin_user)
                session.commit()

                logger.info(
                    f"Successfully created admin user - "
                    f"Username: {ADMIN_USER_USERNAME_DEFAULT}, "
                    f"Domain: {ADMIN_USER_DOMAIN_DEFAULT}, "
                    f"Role: {ADMIN_USER_ROLE_DEFAULT} "
                    f"with ID: {user_id}"
                )

                return UserResponse(id=user_id)

            except Exception as e:
                session.rollback()
                logger.error(f"Database error while creating admin user: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}"
                )
            finally:
                session.close()
                logger.debug("Database session closed")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating admin user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating admin user: {str(e)}"
            )


# Global service instance
user_service = UserService()
