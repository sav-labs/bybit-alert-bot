from app.db import get_session, User
from app.settings import BOT_ADMINS
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

class UserService:
    @staticmethod
    async def get_user(user_id: int) -> User:
        """Get a user by user_id."""
        session = get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    async def create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Create a new user."""
        session = get_session()
        try:
            # Check if user is admin
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
        user = await UserService.get_user(user_id)
        if not user:
            user = await UserService.create_user(user_id, username, first_name, last_name)
        return user
    
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
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error getting pending users: {e}")
            return []
        finally:
            session.close() 