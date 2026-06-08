from repository.base import BaseRepo
from entity.user import User


class UserRepo(BaseRepo):
    model = User

    field_map = {
        'user_id': 'user_id',
        'username': 'username',
        'role': 'role',
        'ref_id': 'ref_id',
        'email': 'email',
        'phone': 'phone',
        'uuid': 'uuid',
    }

    def find_by_username(self, username: str):
        return self.find_by(username=username)

    def find_by_uuid(self, uuid: str):
        return self.find_by(uuid=uuid)

    def find_by_ref_id(self, ref_id: str):
        return self.find_by(ref_id=ref_id)

    def find_by_email(self, email: str):
        return self.find_by(email=email)

    def find_by_phone(self, phone: str):
        return self.find_by(phone=phone)

    def find_by_identifier(self, identifier: str):
        """通过用户名/学号/邮箱/手机号查找用户"""
        return self.db.query(User).filter(
            (User.username == identifier) |
            (User.ref_id == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()
