import click

from schedule_crawler import schedule_start
from sql_app import main as sql_app_main

@click.group()
def main():
    pass

# 設定要接收的執行參數
@main.command()
@click.option('-s', '--start_time', 'start_time', help='start time for schedule(min)',default=00)
def run(start_time):
    print(f"start from{start_time}")
    schedule_start(start_time)

@main.command()
@click.option('-d', '--clear_database', 'clear_database', help='drop and create a database')
def drop(clear_database):
    q = input("drop table? y/n")
    if q == "y":
        sql_app_main.drop_table()
        sql_app_main.create_table()
    else:
        pass

if __name__ == '__main__':
    main()