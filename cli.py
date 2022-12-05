import click
from schedule_crawler import schedule_start

@click.command()
@click.option('-s', '--start_time', 'start_time', help='start time for schedule(min)',default=00)
def run_schedule(start_time):
    if 0<=start_time<=59:
        print(f"start from{start_time}")
        schedule_start(start_time)
    else:
        print("數字格式不正確，請重新呼叫")

if __name__ == '__main__':
    run_schedule()