#all modules are imported for their specific task

# output of endpoint in json format 
import json
# database connection made by using pymysql connection
import pymysql as p
# getting time in string format
import time
# to analyse records of data
import pandas as pd
#to reduce time complexity threading concept used
import threading
# to connect the internal connection by using os
import os
# entire application make by using flask framework
from flask import Flask, render_template, flash, request, redirect, url_for,send_file
#for getting rule based methods getting from test.py file
from test import get_image,get_timing,get_temp,get_id,get_temp_time
# for getting  database and weather api details
from dotenv import load_dotenv


# load data from .env file
load_dotenv()
# Getting data from .env file
host = os.environ.get('RDS_URL')
user = os.environ.get('RDS_USER')
password = os.environ.get('RDS_PASS')
database = os.environ.get('RDS_DB')


# take one record for each hour using list like ‘rest’ -->its a temperary variable changed for each hour
rest=[]
#assigning Flask method to app variable
app=Flask(__name__)


# getting data from .env file
account = os.environ.get('QRCODE_ACCOUNT')
site =os.environ.get('QRCODE_SITE')


# main api calling through
# getting site and qr_code id from api and route to desired location
#routing api for qr code
@app.route('/<int:site>/<int:account>', methods=['GET'])
#-→ when calling api index function will executed
def index(site,account):
    #→for getting time format in string
    tm=time.strftime("%Y-%m-%d %H-%M-%S")
    #→requesting from api
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        #→ from flask getting visitor info into data
        try:
            data={'ip': request.environ['REMOTE_ADDR'],'timestamp':tm,'browser':request.user_agent._browser, 'os':request.user_agent._platform }
        except:
            data={'ip': request.environ['REMOTE_ADDR'],'timestamp':tm,'browser':request.user_agent.browser, 'os':request.user_agent.platform }
        #→assigning ‘a’ variable to what getting data from flask
        a = [tm[:10],tm[11:13],data['ip'],data['browser'],data['os']]
    else:
        #→ from flask getting visitor info into data
        try:
            data={'ip': request.environ['HTTP_X_FORWARDED_FOR'],'timestamp':tm,'browser':request.user_agent._browser, 'os':request.user_agent._platform }
        except:
            data={'ip': request.environ['HTTP_X_FORWARDED_FOR'],'timestamp':tm,'browser':request.user_agent.browser, 'os':request.user_agent.platform }
        #→assigning ‘a’ variable to what getting data from flask
        a = [tm[:10],tm[11:13],data['ip'],data['browser'],data['os']] 
    #threading applied to extra functions what needs to done  and for store data in database 
    threading.Thread(target=dbstdata(a,data,site,account,tm)).start()
    #qr_code_id as account , site_id as site
    #calling rule function for getting rule from qr_code_id

    r=rule(account)
    #defaultly taken condition_id 1 as from ad variable
    ad=1
    try:
        if r == 1:
            #-->calling get_id function for getting image path id
            re=get_id(ad,r,account,site)
            #→getting image from id
            res = get_image(re[0])
        elif r == 2:
            #→getting timing ads from given variables
            re = get_timing(site,account,r)
            #→getting image from id
            res = get_image(re[0])
        elif r == 3:
            #→getting temperature based ads and ids from rule
            re = get_temp(site,account,r)
            #→getting image from id
            res = get_image(re[0])
        else:
            #→getting temp_time based on rule 2 & 3
            re = get_temp_time(site,account,r)
            #→getting image from id
            res = get_image(re[0])
            
    except:
        # defaultly gave image path
        res = "https://wallpaperaccess.com/full/57166.jpg"

    # returned when calling above api index.html will displayed
    return render_template('index.html',res = res)


   

# store hourwise data using funcion
def dbstdata(a,data,site,account,tm):
    #database connection here
    con=p.connect(host=host,user=user,password=password,database=database)
    # calling database connection
    cur=con.cursor()
    #inserting records of RawData query
    sql="insert into qr_user_data(site_id,qr_code_id,scanned_date,hour,ipaddress,user_browser,user_device_os)values(%s,%s,%s,%s,%s,%s,%s)"
    #inserting records of HourlyData query
    sqls="insert into qr_hourly_user_data(site_id,qr_code_id,scanned_date,hour,VISITS,UNIQUES,user_browser,user_device_os,ipaddress)values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    #getting visited hour time record of the same date and hour, by the specific site and qrcode_id 
    cur.executemany("select * from qr_hourly_user_data where scanned_date=%s and hour=%s and site_id=%s and qr_code_id=%s order by scanned_date and hour",[(tm[:10],tm[11:13],site,account)])
    #above executed records will store in check variable in tuple format
    check=cur.fetchall()
    #excuting insering of the rawdata click wise records-->rawdata query will executed
    cur.executemany(sql,[(site,account,a[0],a[1],a[2],a[-2],a[-1])])
    con.commit() #for the confirmation inserting or updation

    #checking visited hour time record in check or not 
    if len(check)==0:
        #if incase check variable has empty tuple then rest list will be clear
        rest.clear()
    else:
        #if incase check variable has tuple record then tuple will updated into rest list by using append
        mn=[tm[:10],tm[11:13],eval(check[-1][5]),eval(check[-1][6]),eval(check[-1][-3]),eval(check[-1][-2]),eval(check[-1][-1])]
        rest.append(mn)

        

    #if incase rest list is empty this condition executed if case
    if len(rest)==0:
        #default visits as v and uniques as u will be stored as 1
        v,u=1,1
        #here required data will be stored in format of list and appended to rest
        mn=[tm[:10],tm[11:13],v,u,{data['browser']:1},{data['os']:1},[data['ip']]]
        rest.append(mn)
        #checking visited hour time record in check or not 
        if len(check)==0:
            #if incase check variable has empty tuple then hourlydata query will executed
            cur.executemany(sqls,[(site,account,rest[-1][0],rest[-1][1],str(rest[-1][2]),str(rest[-1][3]),str(rest[-1][-3]),str(rest[-1][-2]),str(rest[-1][-1]))])
            con.commit()#for the confirmation inserting or updation
    #if incase rest list has record this condition executed else case
    else:
        #in rest list last of the record of 2nd index element will be visits and it should be incremented in each else case
        rest[-1][2]+=1
        #in rest list last of the record of last index element will be ipaddress and it should be incremented if it is not in 'a' list in 2nd element in each else case -->ip
        if a[2] not in rest[-1][-1]:
            #if above ip case satifies rest of uniques will be incremented and ip address add to rest in last element
            rest[-1][3]+=1
            rest[-1][-1].append(a[2])
        #in rest list last of the record of 4th index element will be browsers and it should be incremented if it is in 'a' list in 3rd element in each else case -->browser
        if a[3] in rest[-1][4]:
            rest[-1][4][a[3]] += 1
        #if above browser case not satifies rest of browsers will be 1 add to rest in 4th element
        else:
            rest[-1][4][a[3]] = 1
        #in rest list last of the record from last 2nd index element will be os and it should be incremented if it is in 'a' list in last element in each else case -->os
        if a[-1] in rest[-1][-2]:
            rest[-1][-2][a[-1]] += 1
        #if above browser case not satifies rest of os will be 1 add to rest from last to 2nd element
        else:
            rest[-1][-2][a[-1]] = 1
        #updating rest record into hourlydata table record for the specific hour of each else case 
        cur.executemany("update qr_hourly_user_data set site_id=%s,qr_code_id=%s,VISITS=%s,UNIQUES=%s,user_browser=%s,user_device_os=%s,ipaddress=%s where scanned_date=%s and hour=%s and site_id=%s and qr_code_id=%s order by scanned_date and hour desc limit 1",\
        [(site,account,str(rest[-1][2]),str(rest[-1][3]),str(rest[-1][-3]),str(rest[-1][-2]),str(rest[-1][-1]),tm[:10],tm[11:13],site,account)])
        con.commit()#for the confirmation inserting or updation


# connect database here by using this function
def db():
    # #mysql database connection
    dbcon=p.connect(host=host,user=user,password=password,database=database)
    # returning assigned cursor for the execution 
    return dbcon.cursor()
# query execution block
def query_db(query, args=(), one=False):
    # calling database connection
    cur = db()
    #applied what query as getting in argument
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    #return tuples format records of given query wise data
    return (r[0] if r else None) if one else r

# rule for ads
def rule(account):
    #calling database connection
    cur=db()
    #getting rule id from qr_code_id
    cur.execute("select qr_rule_id from t_qr_rules where qr_code_id={}".format(account))
    rule=cur.fetchone()[0]
    return rule


# sub api calling thrigh endpoints like /hr/result
@app.route('/<int:site>/<int:account>/hr/result', methods=['GET'])
def res(site,account):
    #calling query_db function forb required table
    my_query = query_db("select * from qr_hourly_user_data where site_id={} and qr_code_id={}".format(site,account))
    #converted tuple format data into json data
    json_output = json.dumps(my_query)
    #getting original format json data by using eval method
    jsn=eval(json_output)

    d={}
    date=[]
    l=[]
    for i in jsn:
        if i['scanned_date'] in date:
            l.append(i)
            d[i['scanned_date']]=l
            del i['scanned_date']
            del i['ipaddress']
            del i['site_id']
            del i['qr_code_id']
            del i['id']
        else:
            date.append(i['scanned_date'])
            d[i['scanned_date']]=[i]
            del i['scanned_date']
            del i['ipaddress']
            del i['site_id']
            del i['qr_code_id']
            del i['id']
            l=[i]
    #converted dictionary into json data
    dfc=json.dumps(d,indent=4)
    return dfc


# calling api's
