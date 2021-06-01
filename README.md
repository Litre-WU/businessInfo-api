# 企业工商信息查询接口
企业工商信息接口(包含天眼查、企查查、爱企查、国家企业公示系统平台)

接口文档(http://127.0.0.1:1080/docs)

tip:需设置代理(默认：http://127.0.0.1:1080)

Windows系统运行

$ pip install requirements.txt -i https://pypi.doubanio.com/simple/

$ uvicorn 工商信息查询:app --host 0.0.0.0 --port 8081 --reload

Linux or mac 运行(工商信息查询.py 21行需要注释)

$ gunicorn -c gunicorn.py 工商信息查询:app  
(也可使用uvicorn)

docker 运行(工商信息查询.py 21行需要注释)

$ docker build -t businessInfo .

$ docker run --name businessInfo -d -p 8081:8081 businessInfo
