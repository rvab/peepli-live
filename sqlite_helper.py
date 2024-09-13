import sqlite3
from datetime import datetime

def initialize_database():
  conn = sqlite3.connect('user_messages.db', check_same_thread=False)
  cursor = conn.cursor()

  # Create users table
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id text PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      profile_pic TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  ''')

  # Create messages table
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      from_user_id text,
      for_user_id text,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (from_user_id) REFERENCES users (id),
      FOREIGN KEY (for_user_id) REFERENCES users (id)
    )
  ''')

  conn.commit()
  return conn

def get_distinct_wished_user_receiver_user_combinations(days=15):
  cursor = conn.cursor()
  days = f'-{days} day'
  cursor.execute('''
  SELECT DISTINCT from_user_id, for_user_id FROM messages
  where created_at > datetime('now', ?)
  ''', (days,))
  return cursor.fetchall()

def get_or_create_user(conn, name, email, profile_pic=None, slack_user_id=None):
  cursor = conn.cursor()
  cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
  user = cursor.fetchone()

  if user:
    return user[0]
  else:
    cursor.execute('''
    INSERT INTO users (id, name, email, profile_pic)
    VALUES (?, ?, ?, ?)
    ''', (slack_user_id, name, email, profile_pic))
    conn.commit()
    return slack_user_id

def add_message(conn, from_user, for_user, content):
  from_user_id = get_or_create_user(conn, from_user['name'], from_user['email'], from_user.get('profile_pic'), from_user.get('slack_user_id'))
  for_user_id = get_or_create_user(conn, for_user['name'], for_user['email'], for_user.get('profile_pic'), for_user.get('slack_user_id'))

  cursor = conn.cursor()
  cursor.execute('''
  INSERT INTO messages (from_user_id, for_user_id, content)
  VALUES (?, ?, ?)
  ''', (from_user_id, for_user_id, content))
  conn.commit()
  return cursor.lastrowid

def get_user_messages(id):
  cursor = conn.cursor()
  cursor.execute('''
  with cte1 as (
    SELECT
      m.id,
      u_from.name as from_user,
      u_for.name as for_user,
      m.content,
      m.created_at,
      ROW_NUMBER() OVER (PARTITION BY m.from_user_id, m.for_user_id ORDER BY m.created_at desc) AS rn
    FROM messages m
    JOIN users u_from ON m.from_user_id = u_from.id
    JOIN users u_for ON m.for_user_id = u_for.id
    WHERE u_for.id = ?
    ORDER BY m.created_at DESC
  )
  select * from cte1 where rn = 1;
  ''', (id,))
  return cursor.fetchall()

def get_user_details(id):
  cursor = conn.cursor()
  cursor.execute('''
  SELECT name, email, profile_pic FROM users WHERE id = ?
  ''', (id,))
  return cursor.fetchone()

def get_detailed_wishes_for_user(id):
  cursor = conn.cursor()
  cursor.execute('''
  with cte1 as (
    SELECT
      m.id,
      u_from.name as from_user_name,
      u_from.profile_pic as from_user_profile_pic,
      m.content,
      m.created_at,
      ROW_NUMBER() OVER (PARTITION BY m.from_user_id, m.for_user_id ORDER BY m.created_at desc) AS rn
    FROM messages m
    JOIN users u_from ON m.from_user_id = u_from.id
    JOIN users u_for ON m.for_user_id = u_for.id
    WHERE u_for.id = ?
    ORDER BY m.created_at DESC
  )
  select * from cte1 where rn = 1;
  ''', (id,))
  return cursor.fetchall()

conn = initialize_database()

def add_message_to_db(from_user, for_user, text):
  add_message(conn, from_user, for_user, text)
