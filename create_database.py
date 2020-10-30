import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("""CREATE TABLE List (
                ss_id text,
                server_id integer,
                phase integer
                );""")

c.execute("""CREATE TABLE Users (
                user_id integer,
                wish text
                );""")

c.execute("""CREATE TABLE Entries (
                ss_id text,
                user_id integer,
                match integer,
                submitted integer
                );""")

c.execute("""CREATE TABLE Submissions (
                ss_id text,
                user_id integer,
                message integer
                );""")

conn.commit()
conn.close()