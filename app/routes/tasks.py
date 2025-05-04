from flask import render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.forms import TaskForm, SearchForm
from app.models import Task
from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@tasks_bp.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = SearchForm()
    query = current_user.tasks.order_by(Task.timestamp.desc())

    if request.method == 'POST' and form.validate():
        search_term = form.search.data.strip().lower()
        status_filter = form.status.data

        if search_term:
            query = query.filter(
                db.or_(
                    Task.title.ilike(f'%{search_term}%'),
                    Task.description.ilike(f'%{search_term}%')
                )
            )

        if status_filter != 'all':
            query = query.filter_by(status=status_filter)

    tasks = query.all()

    return render_template('dashboard.html',
                           title='My Tasks',
                           tasks=tasks,
                           form=form)

@tasks_bp.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            status=form.status.data,
            author=current_user
        )

        if form.attachment.data:
            file = form.attachment.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                task.file_path = filename

        db.session.add(task)
        db.session.commit()
        flash('Your task has been created!')
        return redirect(url_for('tasks.tasks'))

    return render_template('task_form.html', title='New Task', form=form)


@tasks_bp.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)

    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data
        task.status = form.status.data

        if form.attachment.data:
            file = form.attachment.data
            if file and allowed_file(file.filename):
                if task.file_path:
                    old_file = os.path.join(current_app.config['UPLOAD_FOLDER'], task.file_path)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                task.file_path = filename

        db.session.commit()
        flash('Your task has been updated!')
        return redirect(url_for('tasks.tasks'))
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.due_date.data = task.due_date
        form.status.data = task.status

    return render_template('task_form.html', title='Edit Task', form=form)


@tasks_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)

    if task.file_path:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], task.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(task)
    db.session.commit()
    flash('Your task has been deleted!')
    return redirect(url_for('tasks.tasks'))