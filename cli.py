import click
from schedule_crawler import schedule_start

# 排程
@click.command()
@click.option('-s', '--start_time', 'start_time', help='start time for schedule(min)',default=00)
def run_schedule(start_time):
    print(f"start from{start_time}")
    schedule_start(start_time)

if __name__ == '__main__':
    run_schedule()