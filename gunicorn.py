# vim: set fileencoding:utf-8
# -*- coding: utf-8 -*-
# Author: Litre WU
# E-mail: litre-wu@tutanota.com
# Software: PyCharm
# File: gunicorn.py
# Time: 4月 23, 2021
import logging
import logging.handlers
from logging.handlers import WatchedFileHandler
import os
import multiprocessing

# chdir = '/businessInfo'  # 加载应用程序之前将chdir目录指定到指定目录

proc_name = 'businessInfo'  # 进程名

bind = '0.0.0.0:8081'  # 绑定ip和端口号

backlog = 512  # 监听队列

timeout = 20  # 超时

# worker_class = 'gevent' # 默认的是sync模式
# worker_class = 'uvicorn.workers.UvicornWorker'  # 使用uvicorn模式
worker_class = 'uvicorn.workers.UvicornH11Worker'  # 使用纯python模式

# workers = multiprocessing.cpu_count() * 2 + 1  # 进程数
# workers = multiprocessing.cpu_count() * 2 + 1  # 进程数
workers = 4  # 进程数

threads = 4  # 指定每个进程开启的线程数

# deamon = True  # 守护进程

reload = True  # 自动加载

worker_connections = 2000  # 设置最大并发量

loglevel = 'info'  # 日志级别，这个日志级别指的是错误日志的级别，而访问日志的级别无法设置

# accesslog = "/businessInfo/logs/demo_access.log"  # 访问日志文件, "-" 表示标准输出

# errorlog = "/businessInfo/logs/demo_err.log"  # 错误日志文件, "-" 表示标准输出