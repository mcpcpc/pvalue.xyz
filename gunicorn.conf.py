import multiprocessing

chdir = "/root"
bind = ":80"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1
