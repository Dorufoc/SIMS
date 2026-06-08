"""控制器层 - 注册所有 Blueprint"""
from controller.auth_controller import auth_bp
from controller.student_controller import student_bp
from controller.department_controller import dept_bp
from controller.major_controller import major_bp
from controller.class_controller import class_bp
from controller.teacher_controller import teacher_bp
from controller.course_controller import course_bp
from controller.semester_controller import semester_bp
from controller.teaching_controller import teaching_bp
from controller.enrollment_controller import enrollment_bp
from controller.reward_controller import reward_bp
from controller.payment_controller import payment_bp
from controller.dorm_controller import dorm_bp
from controller.curriculum_controller import curriculum_bp
from controller.statistics_controller import statistics_bp
from controller.query_controller import query_bp
from controller.csv_controller import csv_bp
from controller.user_controller import user_bp


def register_all(app):
    """注册所有 Blueprint 到 Flask 应用（路由路径已含 /api/ 前缀）"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(dept_bp)
    app.register_blueprint(major_bp)
    app.register_blueprint(class_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(semester_bp)
    app.register_blueprint(teaching_bp)
    app.register_blueprint(enrollment_bp)
    app.register_blueprint(reward_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(dorm_bp)
    app.register_blueprint(curriculum_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(csv_bp)
    app.register_blueprint(user_bp)
