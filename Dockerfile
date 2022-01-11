# 基于镜像基础
FROM python:3.10.1

# 设置时区
ENV TZ Asia/Shanghai

# 设置代码文件夹工作目录 /app
WORKDIR /app

# 复制当前代码文件到容器中 /app
ADD . /app

# 安装所需的包
RUN pip install -r requirements.txt -i https://pypi.doubanio.com/simple/

CMD ["gunicorn", "-c", "conf.py", "看准-企业工商信息查询:app"]
