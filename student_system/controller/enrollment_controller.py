"""选课管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.enrollment_service import EnrollmentService
from middleware.auth_middleware import require_login, csrf_protect
from repository.base import escape_like
import logging

enrollment_bp = Blueprint('enrollment', __name__)


@enrollment_bp.route('/enrollments')
def enrollments_page():
    return render_template('enrollments.html')


@enrollment_bp.route('/grades')
def grades_page():
    return render_template('grades.html')


@enrollment_bp.route('/api/enrollment/available', methods=['GET'])
@require_login
def api_available_courses():
    student_id = request.args.get('student_id', '')
    svc = EnrollmentService()
    try:
        courses = svc.get_available_courses(student_id)
        data = [{'teaching_id': c.teaching_id, 'course_id': c.course_id, 'teacher_id': c.teacher_id,
                 'semester_id': c.semester_id, 'classroom': c.classroom, 'schedule': c.schedule} for c in courses]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@enrollment_bp.route('/api/enrollment', methods=['POST'])
@require_login
@csrf_protect
def api_enroll():
    data = request.get_json()
    svc = EnrollmentService()
    try:
        success, msg = svc.enroll(data.get('student_id', ''), data.get('teaching_id', 0))
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@enrollment_bp.route('/api/enrollment/<int:enroll_id>/drop', methods=['POST'])
@require_login
@csrf_protect
def api_drop(enroll_id):
    svc = EnrollmentService()
    try:
        success, msg = svc.drop(enroll_id)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@enrollment_bp.route('/api/grades', methods=['GET'])
@require_login
def api_grades():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    from entity.enrollment import Enrollment
    from entity.teaching import Teaching
    from entity.course import Course
    from entity.semester import Semester
    from entity.student import Student
    from sqlalchemy.orm import joinedload

    svc = EnrollmentService()
    try:
        q = svc.repo.db.query(Enrollment).options(
            joinedload(Enrollment.student),
            joinedload(Enrollment.teaching).joinedload(Teaching.course),
            joinedload(Enrollment.teaching).joinedload(Teaching.semester),
        )

        _teaching_joined = False

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []
            for f in filters:
                field = f.get('field', '')
                op = f.get('op', 'eq')
                value = f.get('value', '')
                if field == 'student_id':
                    if op == 'contains':
                        q = q.filter(Enrollment.student_id.like(f'%{escape_like(value)}%', escape='\\'))
                    else:
                        q = q.filter(Enrollment.student_id == value)
                elif field == 'status':
                    q = q.filter(Enrollment.status == value)
                elif field == 'score':
                    val = float(value)
                    if op == 'gt':
                        q = q.filter(Enrollment.score > val)
                    elif op == 'lt':
                        q = q.filter(Enrollment.score < val)
                    elif op == 'gte':
                        q = q.filter(Enrollment.score >= val)
                    elif op == 'lte':
                        q = q.filter(Enrollment.score <= val)
                    else:
                        q = q.filter(Enrollment.score == val)
                elif field == 'student_name':
                    q = q.join(Student, Enrollment.student_id == Student.student_id).filter(
                        Student.name.like(f'%{escape_like(value)}%', escape='\\')
                    )
                elif field == 'course_name':
                    if not _teaching_joined:
                        q = q.join(Teaching, Enrollment.teaching_id == Teaching.teaching_id)
                        _teaching_joined = True
                    q = q.join(Course, Teaching.course_id == Course.course_id).filter(
                        Course.course_name.like(f'%{escape_like(value)}%', escape='\\')
                    )
                elif field == 'capacity':
                    if not _teaching_joined:
                        q = q.join(Teaching, Enrollment.teaching_id == Teaching.teaching_id)
                        _teaching_joined = True
                    val = int(value)
                    if op == 'gt':
                        q = q.filter(Teaching.capacity > val)
                    elif op == 'lt':
                        q = q.filter(Teaching.capacity < val)
                    elif op == 'gte':
                        q = q.filter(Teaching.capacity >= val)
                    elif op == 'lte':
                        q = q.filter(Teaching.capacity <= val)
                    else:
                        q = q.filter(Teaching.capacity == val)
                elif field == 'schedule':
                    if not _teaching_joined:
                        q = q.join(Teaching, Enrollment.teaching_id == Teaching.teaching_id)
                        _teaching_joined = True
                    q = q.filter(
                        Teaching.schedule.like(f'%{escape_like(value)}%', escape='\\')
                    )

        q = q.order_by(Enrollment.enroll_id.desc())
        items, total = svc.repo.paginate(page, page_size, q)
        total_pages = (total + page_size - 1) // page_size

        data = []
        for e in items:
            student = e.student
            teaching = e.teaching
            course = teaching.course if teaching else None
            semester = teaching.semester if teaching else None
            data.append({
                'enroll_id': e.enroll_id,
                'student_id': e.student_id,
                'student_name': student.name if student else '',
                'course_name': course.course_name if course else '',
                'credits': float(course.credits) if course and course.credits else None,
                'capacity': teaching.capacity if teaching else None,
                'schedule': teaching.schedule if teaching else '',
                'score': float(e.score) if e.score else None,
                'grade_point': float(e.grade_point) if e.grade_point else None,
                'semester_name': f"{semester.academic_year} {semester.semester_name}" if semester else '',
                'status': e.status or '',
            })
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@enrollment_bp.route('/api/students/<student_id>/enrolled-courses', methods=['GET'])
@require_login
def api_student_enrolled_courses(student_id):
    """获取学生已选课程（含课程名、授课信息），用于成绩管理新增成绩时选择"""
    from entity.enrollment import Enrollment
    from entity.teaching import Teaching
    from entity.course import Course
    from sqlalchemy.orm import joinedload

    svc = EnrollmentService()
    try:
        enrollments = svc.repo.db.query(Enrollment).options(
            joinedload(Enrollment.teaching).joinedload(Teaching.course)
        ).filter(
            Enrollment.student_id == student_id,
            Enrollment.status != '退课'
        ).all()
        data = []
        seen = set()
        for e in enrollments:
            if not e.teaching or not e.teaching.course:
                continue
            cid = e.teaching.course.course_id
            if cid in seen:
                continue
            seen.add(cid)
            data.append({
                'course_id': cid,
                'course_name': e.teaching.course.course_name,
                'teaching_id': e.teaching_id,
            })
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@enrollment_bp.route('/api/grades/add', methods=['POST'])
@require_login
@csrf_protect
def api_grade_add():
    """手动新增单条成绩"""
    import json
    from service.grade_service import GradeService
    from entity.teaching import Teaching
    from entity.course import Course
    from entity.enrollment import Enrollment

    data = request.get_json()
    student_id = (data.get('student_id') or '').strip()
    course_id = (data.get('course_id') or '').strip()
    score = data.get('score')

    if not student_id or not course_id or score is None:
        return jsonify({'code': 1, 'msg': '学号、课程和成绩不能为空'})
    try:
        score = float(score)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'msg': '成绩格式不正确'})

    gsvc = GradeService()
    try:
        # 查找该课程的最新授课记录
        teaching = gsvc.repo.db.query(Teaching).join(
            Course, Teaching.course_id == Course.course_id
        ).filter(
            Course.course_id == course_id
        ).order_by(Teaching.teaching_id.desc()).first()
        if not teaching:
            return jsonify({'code': 1, 'msg': f'课程 {course_id} 当前无授课安排'})

        # 查找或创建选课记录
        enrollment = gsvc.repo.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.teaching_id == teaching.teaching_id
        ).first()

        if not enrollment:
            # 检查学生是否存在
            from entity.student import Student
            student = gsvc.repo.db.query(Student).filter(Student.student_id == student_id).first()
            if not student:
                return jsonify({'code': 1, 'msg': f'学生 {student_id} 不存在'})
            enrollment = Enrollment(
                student_id=student_id,
                teaching_id=teaching.teaching_id,
                status='正常'
            )
            gsvc.repo.db.add(enrollment)
            gsvc.repo.db.flush()

        # 设置成绩
        enrollment.score = score
        enrollment.grade_point = gsvc._calc_grade_point(score)
        gsvc.repo.db.commit()
        return jsonify({'code': 0, 'msg': '成绩添加成功'})
    except Exception as e:
        gsvc.repo.db.rollback()
        logging.exception('添加成绩失败')
        return jsonify({'code': 1, 'msg': f'添加失败：{str(e)}'})
    finally:
        gsvc.close()


@enrollment_bp.route('/api/import/grade/template', methods=['GET'])
@require_login
def api_grade_template():
    """生成成绩导入模板 CSV"""
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['学号', '课程编号', '成绩'])
    from flask import send_file
    data = output.getvalue().encode('utf-8-sig')
    return send_file(io.BytesIO(data), as_attachment=True,
                     download_name='grade_template.csv', mimetype='text/csv')


@enrollment_bp.route('/api/grades/import', methods=['POST'])
@require_login
@csrf_protect
def api_grade_import():
    """批量导入成绩"""
    data = request.get_json()
    rows = data.get('data', [])
    from service.grade_service import GradeService
    svc = GradeService()
    try:
        from entity.enrollment import Enrollment
        count = 0
        errors = []
        for idx, row in enumerate(rows):
            student_id = row[0].strip() if len(row) > 0 else ''
            course_id = row[1].strip() if len(row) > 1 else ''
            score_str = row[2].strip() if len(row) > 2 else ''
            if not student_id or not course_id or not score_str:
                errors.append(f'第{idx+1}行：数据不完整')
                continue
            try:
                score = float(score_str)
            except ValueError:
                errors.append(f'第{idx+1}行：成绩格式不正确')
                continue
            # 查找对应的选课记录
            from entity.teaching import Teaching
            from entity.course import Course
            teaching = svc.repo.db.query(Teaching).join(
                Course, Teaching.course_id == Course.course_id
            ).filter(
                Course.course_id == course_id
            ).first()
            if not teaching:
                errors.append(f'第{idx+1}行：课程 {course_id} 不存在或无授课安排')
                continue
            enrollment = svc.repo.db.query(Enrollment).filter(
                Enrollment.student_id == student_id,
                Enrollment.teaching_id == teaching.teaching_id
            ).first()
            if not enrollment:
                errors.append(f'第{idx+1}行：学生 {student_id} 未选该课程')
                continue
            enrollment.score = score
            enrollment.grade_point = svc._calc_grade_point(score)
            count += 1
        svc.repo.db.commit()
        msg = f'成功导入 {count} 条成绩'
        if errors:
            msg += '；' + '；'.join(errors[:5])
            if len(errors) > 5:
                msg += f'（还有{len(errors)-5}条错误）'
        return jsonify({'code': 0, 'msg': msg, 'count': count})
    except Exception as e:
        svc.repo.db.rollback()
        logging.exception('成绩导入失败')
        return jsonify({'code': 1, 'msg': f'导入失败：{str(e)}'})
    finally:
        svc.close()


@enrollment_bp.route('/api/import/grade/export', methods=['GET'])
@require_login
def api_grade_export():
    """导出成绩数据"""
    import io
    import csv
    from entity.enrollment import Enrollment
    from entity.teaching import Teaching
    from entity.course import Course
    from entity.student import Student
    svc = EnrollmentService()
    try:
        enrollments = svc.repo.db.query(Enrollment).join(
            Teaching, Enrollment.teaching_id == Teaching.teaching_id
        ).join(
            Course, Teaching.course_id == Course.course_id
        ).join(
            Student, Enrollment.student_id == Student.student_id
        ).order_by(Enrollment.enroll_id).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['学号', '姓名', '课程', '成绩', '绩点', '状态'])
        for e in enrollments:
            writer.writerow([
                e.student_id, e.student.name if e.student else '',
                e.teaching.course.course_name if e.teaching and e.teaching.course else '',
                float(e.score) if e.score else '',
                float(e.grade_point) if e.grade_point else '',
                e.status or ''
            ])
        from flask import send_file
        data = output.getvalue().encode('utf-8-sig')
        return send_file(io.BytesIO(data), as_attachment=True,
                         download_name='grade_data.csv', mimetype='text/csv')
    finally:
        svc.close()


@enrollment_bp.route('/api/students/<student_id>/enrollment', methods=['GET'])
@enrollment_bp.route('/api/students/<student_id>/enrollments', methods=['GET'])
@require_login
def api_student_enrollments(student_id):
    from entity.enrollment import Enrollment
    from entity.teaching import Teaching
    from sqlalchemy.orm import joinedload

    svc = EnrollmentService()
    try:
        enrollments = svc.repo.db.query(Enrollment).options(
            joinedload(Enrollment.teaching).joinedload(Teaching.course),
            joinedload(Enrollment.teaching).joinedload(Teaching.teacher),
            joinedload(Enrollment.teaching).joinedload(Teaching.semester),
        ).filter(Enrollment.student_id == student_id).all()
        data = []
        for e in enrollments:
            course_name = e.teaching.course.course_name if e.teaching and e.teaching.course else None
            credits = float(e.teaching.course.credits) if e.teaching and e.teaching.course and e.teaching.course.credits else None
            teacher_name = e.teaching.teacher.name if e.teaching and e.teaching.teacher else None
            sem = e.teaching.semester
            semester_display = (sem.academic_year + ' ' + sem.semester_name) if sem else None
            data.append({
                'enroll_id': e.enroll_id,
                'student_id': e.student_id,
                'teaching_id': e.teaching_id,
                'course_name': course_name,
                'credits': credits,
                'teacher_name': teacher_name,
                'semester_display': semester_display,
                'score': float(e.score) if e.score else None,
                'grade_point': float(e.grade_point) if e.grade_point else None,
                'status': e.status,
            })
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()
