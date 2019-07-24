import argparse
import sys

parser = argparse.ArgumentParser()
arg = parser.add_argument
arg('--host', type=str, default="172.16.16.97")
arg('--passwd', type=str, default="123456")
arg('--db', type=str, default="test")
arg('--data_from', type=str, default="sql")


args = parser.parse_args()


