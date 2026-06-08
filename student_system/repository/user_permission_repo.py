from repository.base import BaseRepo
from entity.user_permission import UserPermission


class UserPermissionRepo(BaseRepo):
    model = UserPermission
    field_map = {}

    def find_by_user_uuid(self, user_uuid: str):
        return self.find_all_by(user_uuid=user_uuid)

    def find_by_user_and_table(self, user_uuid: str, table_name: str):
        return self.db.query(UserPermission).filter_by(
            user_uuid=user_uuid, table_name=table_name
        ).first()

    def upsert(self, user_uuid: str, table_name: str, permission_code: str):
        """插入或更新权限"""
        existing = self.find_by_user_and_table(user_uuid, table_name)
        if existing:
            existing.permission_code = permission_code
            self.db.commit()
            return existing
        else:
            perm = UserPermission(
                user_uuid=user_uuid,
                table_name=table_name,
                permission_code=permission_code
            )
            self.create(perm)
            return perm
