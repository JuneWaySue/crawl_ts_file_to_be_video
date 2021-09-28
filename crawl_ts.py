# 导入相关包或模块
import threading, queue
import time, os, subprocess
import requests, urllib, parsel
import random, re, base64

# 拿到播放页网址
def get_bofangye_url(url):
    r=requests.get(url,headers=headers)
    response=parsel.Selector(r.text)
    bofangye_url='https://www.dsm8.cc' + response.xpath('//div[@id="vlink_1"]/ul/li/a/@href').get()
    return bofangye_url

# 拿到js文件网址
def get_js_url(bofangye_url):
    r=requests.get(bofangye_url,headers=headers)
    response=parsel.Selector(r.text)
    js_url='https://www.dsm8.cc'+response.xpath('//div[@id="flash"]/script/@src').get()
    return js_url

# 拿到所有的m3u8文件网址
def get_all_url(js_url):
    r=requests.get(js_url,headers=headers)
    a=re.findall("base64decode\('(.*?)\)",r.text)[0]
    temp_url=re.findall('\$(.*?)\#',urllib.parse.unquote(str(base64.b64decode(a))))
    r=requests.get(temp_url[0],headers=headers)
    all_url=[]
    for i in temp_url:
        all_url.append(i.replace('index.m3u8',r.text.split('\n')[-1]))
    return all_url

# 下载ts文件
def download_ts(urlQueue): 
    while True:
        try: 
            #不阻塞的读取队列数据 
            url = urlQueue.get_nowait()
            n=int(url[-6:-3])
        except Exception as e:
            break
        response=requests.get(url,stream=True,headers=headers)
        ts_path = "./ts/%03d.ts"%n  # 注意这里的ts文件命名规则
        with open(ts_path,"wb+") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print("%03d.ts OK..."%n)

if __name__ == '__main__':
    url='https://www.dsm8.cc/TVB/wanshuiqianshanzongshiqingyueyu.html' # 万水千山总是情粤语版
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400'}
    bofangye_url=get_bofangye_url(url)
    js_url=get_js_url(bofangye_url)
    all_url=get_all_url(js_url)
    
    # 下面开始循环下载所有剧集
    for num,url in enumerate(all_url):
        r=requests.get(url,headers=headers)
        urlQueue = queue.Queue()
        for i in r.text.split('\n'):
            if i.endswith('.ts'):
                urlQueue.put(url.replace('index.m3u8',i))
                
        # 下面开始多线程下载
        startTime = time.time()
        threads = []
        # 可以适当调节线程数,进而控制抓取速度
        threadNum = 4
        for i in range(threadNum):
            t = threading.Thread(target=download_ts, args=(urlQueue,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        endTime = time.time()
        print ('Done, Time cost: %s ' %  (endTime - startTime))
        
        # 下面是执行cmd命令来合成mp4视频
        command=r'copy/b D:\python3.7\HEHE\爬虫\ts\*.ts D:\python3.7\HEHE\爬虫\mp4\万水千山总是情-第{0}集.mp4'.format(num+1)
        output=subprocess.getoutput(command)
        print('万水千山总是情-第{0}集.mp4  OK...'.format(num+1))
        
        # 下面是把这一集所有的ts文件给删除
        file_list = []
        for root, dirs, files in os.walk('D:/python3.7/HEHE/爬虫/ts'):
            for fn in files:
                p = str(root+'/'+fn)
                file_list.append(p)
        for i in file_list:
            os.remove(i)
