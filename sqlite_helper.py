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

def get_user_messages(conn, user_email):
  cursor = conn.cursor()
  cursor.execute('''
  SELECT m.id, u_from.name as from_user, u_for.name as for_user, m.content, m.created_at
  FROM messages m
  JOIN users u_from ON m.from_user = u_from.id
  JOIN users u_for ON m.for_user = u_for.id
  WHERE u_from.email = ? OR u_for.email = ?
  ORDER BY m.created_at DESC
  ''', (user_email, user_email))
  return cursor.fetchall()

# # Get messages for a user
# messages = get_user_messages(conn, "alice@example.com")
# for message in messages:
#   print(f"From: {message[1]}, To: {message[2]}, Content: {message[3]}, Time: {message[4]}")

# conn.close()
