from flask import Flask, render_template, request, redirect, url_for
from logic2 import DB_Manager
from config import DATABASE
import sqlite3

app = Flask(__name__)
manager = DB_Manager(DATABASE)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/projects')
def list_projects():
    user_id = 1  # В реальном приложении — ID текущего пользователя
    projects = manager.get_projects(user_id)
    # Получаем все статусы для отображения в таблице
    statuses = manager.get_statuses()
    status_dict = {status[0]: status[0] for status in statuses}
    return render_template('projects.html', projects=projects, manager=manager, status_dict=status_dict)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # Основная информация о проекте
    cur.execute('''
        SELECT p.*, s.status_name
        FROM projects p
        JOIN status s ON p.status_id = s.status_id
        WHERE p.project_id = ?
    ''', (project_id,))
    project = cur.fetchone()
    if not project:
        conn.close()
        return "Проект не найден", 404

    # Навыки проекта
    cur.execute('''
        SELECT s.skill_name
        FROM skills s
        JOIN project_skills ps ON s.skill_id = ps.skill_id
        WHERE ps.project_id = ?
    ''', (project_id,))
    skills = [row[0] for row in cur.fetchall()]
    conn.close()

    return render_template('project_detail.html', project=project, skills=skills)
@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        user_id = 1  # В реальном приложении — ID текущего пользователя
        project_name = request.form['project_name']
        description = request.form['description']
        url = request.form.get('url', '')  # URL может быть пустым
        status_name = request.form['status_name']

        # Получаем ID статуса
        status_id = manager.get_status_id(status_name)
        if status_id is None:
            return "Статус не найден", 400

        # Добавляем проект
        manager.insert_project([(user_id, project_name, description, url, status_id)])

        # Добавляем навыки (если выбраны)
        selected_skills = request.form.getlist('skills')
        for skill in selected_skills:
            try:
                manager.insert_skill(user_id, project_name, skill)
            except ValueError as e:
                # Логируем ошибку, но не прерываем выполнение
                print(f"Ошибка добавления навыка: {e}")

        return redirect(url_for('list_projects'))

    # Для GET‑запроса получаем данные для формы
    statuses = manager.get_statuses()
    all_skills = manager.select_data('SELECT skill_name FROM skills')
    return render_template('add_project.html',
                        statuses=[s[0] for s in statuses],
                        skills=[s[0] for s in all_skills])

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    user_id = 1  # В реальном приложении — ID текущего пользователя
    manager.delete_project(user_id, project_id)
    return redirect(url_for('list_projects'))


if __name__ == '__main__':
    # Инициализируем БД при запуске
    manager.create_tables()
    manager.default_insert()
    app.run(debug=True)