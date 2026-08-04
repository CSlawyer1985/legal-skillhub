#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, re, os, json
OUT="D:/工作/Agent/无效测试/output_冷藏箱_CN202310824943.5"
FIGDIR=os.path.join(OUT,"figures"); os.makedirs(FIGDIR,exist_ok=True)
HDR={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# 1) 探测 PatSeek 同目录附图
base="https://patentimages.storage.googleapis.com/78/ef/72/70f4db0dcca64b"
for name in ["FT_1.JPG","FT_2.JPG","FT_3.JPG","FT_4.JPG","FT_5.JPG","FT_6.JPG","202310824943.JPG"]:
    url=f"{base}/{name}"
    try:
        r=requests.get(url,headers=HDR,timeout=20)
        print("PATSEEK",name,r.status_code,len(r.content))
        if r.status_code==200 and len(r.content)>2000:
            open(os.path.join(FIGDIR,name),"wb").write(r.content)
    except Exception as e:
        print("PATSEEK",name,"ERR",e)

# 2) Google Patents 页面：提取附图与自引文献
gurl="https://patents.google.com/patent/CN116697662A/zh"
try:
    g=requests.get(gurl,headers=HDR,timeout=30)
    html=g.text
    print("GP status",g.status_code,"len",len(html))
    # 附图 URL（patentimages）
    imgs=re.findall(r'https://patentimages\.storage\.googleapis\.com/[^\s"<>]+\.(?:png|jpg|jpeg|gif)', html)
    imgs=list(dict.fromkeys(imgs))
    print("GP images found",len(imgs))
    # 自引文献（citation 区域里的 patent 链接）
    cites=re.findall(r'/patent/([A-Z]{2}\d+[A-Z]\d*)', html)
    cites=list(dict.fromkeys(cites))
    print("GP patent links",len(cites), cites[:40])
    # 保存
    json.dump({"images":imgs[:12],"cites":cites}, open(os.path.join(OUT,"gp_meta.json"),"w"), ensure_ascii=False, indent=2)
    # 下载前 6 张附图（按出现顺序，跳过 pdf）
    cnt=0
    for u in imgs:
        if u.lower().endswith(".pdf"): continue
        try:
            r=requests.get(u,headers=HDR,timeout=20)
            if r.status_code==200 and len(r.content)>3000:
                fn=f"gp_{cnt+1}{os.path.splitext(u)[1]}"
                open(os.path.join(FIGDIR,fn),"wb").write(r.content)
                cnt+=1
                print("DL",fn,len(r.content))
                if cnt>=6: break
        except Exception as e:
            print("DL ERR",e)
except Exception as e:
    print("GP ERR",e)
