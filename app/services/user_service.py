from app.db import get_session, User
from app.settings import BOT_ADMINS, ADMIN_USER_IDS
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

class UserService:
    @staticmethod
    async def get_user(user_id: int) -> Optional[User]:
        """Get user by ID."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            logger.debug(f"Retrieved user from DB: {user_id} (exists: {user is not None})")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    async def create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Optional[User]:
        """Create a new user."""
        session = get_session()
        try:
            # Check if user already exists
            existing = session.query(User).filter(User.user_id == user_id).first()
            if existing:
                logger.debug(f"User {user_id} already exists, updating info")
                if username is not None:
                    existing.username = username
                if first_name is not None:
                    existing.first_name = first_name
                if last_name is not None:
                    existing.last_name = last_name
                    
                session.commit()
                return existing
            
            # Set as admin if in admin list
            is_admin = user_id in ADMIN_USER_IDS
            
            # Create new user
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin,
                is_approved=is_admin  # Auto-approve admins
            )
            
            session.add(user)
            session.commit()
            
            name_str = f"@{username}" if username else first_name
            logger.info(f"Created new user: {name_str} (ID: {user_id}, admin: {is_admin})")
            
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating user {user_id}: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    async def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Get a user or create if not exists."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                is_admin = user_id in BOT_ADMINS
                is_approved = is_admin  # Admins are auto-approved
                
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=is_admin,
                    is_approved=is_approved
                )
                
                session.add(user)
                session.commit()
            
            _ = user.is_admin
            _ = user.is_blocked
            _ = user.is_approved
            _ = user.username
            _ = user.first_name
            _ = user.last_name
            
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error getting or creating user {user_id}: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    async def approve_user(user_id: int) -> bool:
        """Approve a user."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_approved = True
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error approving user {user_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    async def block_user(user_id: int) -> bool:
        """Block a user."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_blocked = True
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error blocking user {user_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    async def unblock_user(user_id: int) -> bool:
        """Unblock a user."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_blocked = False
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error unblocking user {user_id}: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    async def get_all_users() -> list:
        """Get all users."""
        session = get_session()
        try:
            users = session.query(User).all()
            
            for user in users:
                _ = user.is_admin
                _ = user.is_blocked
                _ = user.is_approved
                _ = user.username
                _ = user.first_name
                _ = user.last_name
                
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            session.close()
    
    @staticmethod
    async def get_pending_users() -> list:
        """Get users waiting for approval."""
        session = get_session()
        try:
            users = session.query(User).filter(User.is_approved == False, User.is_blocked == False).all()
            
            for user in users:
                _ = user.is_admin
                _ = user.is_blocked
                _ = user.is_approved
                _ = user.username
                _ = user.first_name
                _ = user.last_name
                
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error getting pending users: {e}")
            return []
        finally:
            session.close() 