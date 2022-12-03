# coding: utf-8

# Author: Du Mingzhe (mingzhe@nus.edu.sg)
# Date: 2022 / 12 / 03

import psycopg2
import pandas.io.sql as sqlio
from sshtunnel import SSHTunnelForwarder


class SqlMiddleware(object):
    def __init__(
            self,
            password: str, 
            db_password: str,
            remote_host: str = "159.138.123.191", 
            username: str = "root",
            bind_address: str = "192.168.0.168", 
            bind_port: int = 5432,
            db_name: str = "mimic-iv",
            db_user: str = "team08",
        ):
        self.remote_host = remote_host
        self.username = username
        self.password = password
        self.bind_address = bind_address
        self.bind_port = bind_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password

        # Establish an SSH tunnel
        self.tunnel =  SSHTunnelForwarder(
            ssh_address_or_host = self.remote_host,
            ssh_username = self.username,
            ssh_password = self.password,
            remote_bind_address=(self.bind_address, self.bind_port)
        )
        self.tunnel.start()
        print("[+] SSH tunnel established")

        # Establish a psycopg2 connection
        self.conn = psycopg2.connect(
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.tunnel.local_bind_host,
            port=self.tunnel.local_bind_port,
        )
        self.cursor = self.conn.cursor()
        print("[+] SQL connection established")

        print("[+] Ready to go ^-^")
    
    def __del__(self):
        self.conn.close()
        self.tunnel.stop()
    
    def raw_excute(self, command):
        try:
            self.cursor.execute(command)
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
            self.cursor.execute("ROLLBACK")
            return None
    
    def pd_excute(self, command):
        try:
            data = sqlio.read_sql_query(command, self.conn)
            return data
        except Exception as e:
            print(e)
            self.cursor.execute("ROLLBACK")
            return None