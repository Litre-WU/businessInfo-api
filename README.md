# 企业工商信息查询接口

企业工商信息接口(包含天眼查、企查查、爱企查、国家企业公示系统平台)

接口文档(http://127.0.0.1:8081/docs)

tip:需设置代理(默认：http://127.0.0.1:1080)

运行  
` ` `
pip install requirements.txt -i https://pypi.doubanio.com/simple/
` ` `
  
` ` `
uvicorn 工商信息查询:app --host 0.0.0.0 --port 8081 --reload
` ` `  

docker 运行  
` ` `
docker build -t businessInfo .
` ` `  
  
` ` `
docker run --name businessInfo -d -p 8081:8081 businessInfo
` ` `
