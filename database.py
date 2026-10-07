import aiosqlite

DB_NAME = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                title TEXT,
                description TEXT,
                questions JSON,
                is_public BOOLEAN DEFAULT 1,
                time_limit INTEGER DEFAULT 15,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        try:
            await db.execute('ALTER TABLE tests ADD COLUMN time_limit INTEGER DEFAULT 15')
        except:
            pass
        await db.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                user_id INTEGER,
                score INTEGER,
                total INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_id TEXT,
                description TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE
            )
        ''')
        await db.commit()

async def add_user(user_id, full_name, username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, full_name, username) 
            VALUES (?, ?, ?)
        ''', (user_id, full_name, username))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users') as cursor:
            return await cursor.fetchall()

async def count_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            row = await cursor.fetchone()
            return row[0]

async def add_test(author_id, title, description, questions, time_limit=15, is_public=True):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO tests (author_id, title, description, questions, is_public, time_limit) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (author_id, title, description, questions, is_public, time_limit))
        await db.commit()

async def delete_test(test_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM tests WHERE id = ? AND author_id = ?', (test_id, user_id))
        await db.commit()

async def get_public_tests():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM tests WHERE is_public = 1') as cursor:
            return await cursor.fetchall()

async def get_user_tests(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM tests WHERE author_id = ?', (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_test(test_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM tests WHERE id = ?', (test_id,)) as cursor:
            return await cursor.fetchone()

async def save_test_result(test_id, user_id, score, total):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO test_results (test_id, user_id, score, total) 
            VALUES (?, ?, ?, ?)
        ''', (test_id, user_id, score, total))
        await db.commit()

async def add_book(title, file_id, description):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO books (title, file_id, description) 
            VALUES (?, ?, ?)
        ''', (title, file_id, description))
        await db.commit()

async def get_books():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM books') as cursor:
            return await cursor.fetchall()

async def get_book(book_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM books WHERE id = ?', (book_id,)) as cursor:
            return await cursor.fetchone()

async def add_channel(username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO channels (username) VALUES (?)', (username,))
        await db.commit()

async def remove_channel(username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM channels WHERE username = ?', (username,))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT username FROM channels') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
