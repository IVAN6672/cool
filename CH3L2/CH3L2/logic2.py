
import sqlite3
from config import DATABASE

skills = [(skill,) for skill in ['Python', 'SQL', 'API', 'Telegram']]
statuses = [(status,) for status in ['На этапе проектирования', 'В процессе разработки',
                                    'Разработан. Готов к использованию.', 'Обновлен',
                                    'Завершен. Не поддерживается']]

class DB_Manager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        con = sqlite3.connect(self.database)
        cur = con.cursor()

        with con:
            # Таблица статусов
            cur.execute('''
                CREATE TABLE IF NOT EXISTS status (
                    status_id INTEGER PRIMARY KEY,
            status_name TEXT NOT NULL
                )
            ''')

            # Таблица навыков
            cur.execute('''
                CREATE TABLE IF NOT EXISTS skills (
            skill_id INTEGER PRIMARY KEY,
            skill_name TEXT NOT NULL
                )
            ''')

            # Таблица проектов
            cur.execute('''
                CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            description TEXT,
            url TEXT,
            status_id INTEGER,
            FOREIGN KEY (status_id) REFERENCES status(status_id)
                )
            ''')
            # Индекс для ускорения запросов по user_id
            cur.execute('CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)')

            # Связующая таблица project_skills
            cur.execute('''
                CREATE TABLE IF NOT EXISTS project_skills (
            project_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            UNIQUE(skill_id, project_id),
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            ''')

    def executemany(self, sql, data):
        con = sqlite3.connect(self.database)
        with con:
            con.executemany(sql, data)

    def select_data(self, sql, data=tuple()):
        con = sqlite3.connect(self.database)
        with con:
            cur = con.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) VALUES (?)'
        self.executemany(sql, skills)
        sql = 'INSERT OR IGNORE INTO status (status_name) VALUES (?)'
        self.executemany(sql, statuses)

    def insert_project(self, data):
        sql = '''INSERT INTO projects (user_id, project_name, description, url, status_id)
               VALUES (?, ?, ?, ?, ?)'''
        self.executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        project_data = self.select_data(
            'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?',
            (project_name, user_id)
        )
        if not project_data:
            raise ValueError(f"Проект '{project_name}' не найден для пользователя {user_id}")
        project_id = project_data[0][0]

        skill_data = self.select_data(
            'SELECT skill_id FROM skills WHERE skill_name = ?',
            (skill,)
        )
        if not skill_data:
            raise ValueError(f"Навык '{skill}' не найден")
        skill_id = skill_data[0][0]

        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills (project_id, skill_id) VALUES (?, ?)'
        self.executemany(sql, data)

    def get_statuses(self):
        return self.select_data('SELECT status_name FROM status')

    def get_status_id(self, status_name):
        res = self.select_data('SELECT status_id FROM status WHERE status_name = ?', (status_name,))
        return res[0][0] if res else None

    def get_projects(self, user_id):
        return self.select_data('SELECT * FROM projects WHERE user_id = ?', (user_id,))

    def get_project_id(self, project_name, user_id):
        res = self.select_data(
            'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?',
            (project_name, user_id)
        )
        return res[0][0] if res else None

    def get_skills(self):
        return self.select_data('SELECT * FROM project_skills')

    def get_project_skills(self, project_name):
        res = self.select_data('''
            SELECT skill_name FROM projects
            JOIN project_skills ON projects.project_id = project_skills.project_id
            JOIN skills ON skills.skill_id = project_skills.skill_id
            WHERE project_name = ?
        ''', (project_name,))
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        return self.select_data('''
            SELECT project_name, description, url, status_name FROM projects
            JOIN status ON status.status_id = projects.status_id
            WHERE project_name = ? AND user_id = ?
        ''', (project_name, user_id))

    def update_projects(self, param, data):
        sql = f'''UPDATE projects SET {param} = ?
               WHERE project_name = ? AND user_id = ?'''
        self.executemany(sql, [data])

    def delete_project(self, user_id, project_id):
        sql = '''DELETE FROM projects
                 WHERE user_id = ? AND project_id = ?'''
        self.executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        sql = '''DELETE FROM project_skills
                 WHERE skill_id = ? AND project_id = ?'''
        self.executemany(sql, [(skill_id, project_id)])
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()  # Создаём таблицы
    manager.default_insert()  # Заполняем базовые данные

    # Вставляем проект (передаём status_id вместо строки)
    status_id = manager.get_status_id('Разработан. Готов к использованию.')
    manager.insert_project([
        (123,
         "бот про глобальное потепление",
         "Описание проекта",
         "https://github.com/ITemik-rr/global_problem",
         status_id)
    ])

      