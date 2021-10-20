#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib.image as img
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns

import time
import datetime
from pyquery import PyQuery as pq

import requests
import json

from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import re  # regex
import datetime

# print("scipy: " + sp.__version__)
# #print("matplotlib: " + plt.__version__)
# print("pandas: " + pd.__version__)
# print("seaborn: " + sns.__version__)
# #print("pyquery: " + pq.__version__)
# #print("bs4: " + BeautifulSoup.__version__)
# print("requests: " + requests.__version__)
# #print("Image: " + __version__)
# #print("pytesseract:" + pts.__version__)
# #print("PIL: " + PIL.__version__)
# print("regex: " + re.__version__)
# #print("datetime: " + datetime.__version__)
# print("json: " + json.__version__)

print("\nLOG: "+str(datetime.datetime.now()))

# In[ ]:


fileroot = '/home/rafael/workspace/dash-covid-sanca/'


# Get urls from page 1

# In[ ]:


urlroot = "http://coronavirus.saocarlos.sp.gov.br/"
last_page_search = 1
indexurls = [urlroot + "page/" + str(i) + '/' for i in range(1,last_page_search+1)]
indexurls


# In[ ]:


index_a_tags = []
for u in indexurls:
    time.sleep(0.5+sp.stats.uniform.rvs())
    page = requests.get(u)
    index_a_tags.append(pq(page.text).find('h2').find('a'))
    print("Got <a> tags from ", u)
    
index_a_tags


# In[ ]:


pageurls = []
for page in index_a_tags:
    for a in page:
        href = pq(a).attr.href
        if 'numeros-covid' in href:
            pageurls.append(href)
pageurls


# In[ ]:


def regexgetdate(search_string, url):
    if 'group' in dir(re.search(search_string + '-' + '(\d{2}-\d{2}-\d{4})', url, re.IGNORECASE)):
        date = re.search(search_string + '-' + '(\d{2}-\d{2}-\d{4})', url, re.IGNORECASE).group(1)
        return int(datetime.datetime.strptime(date, '%d-%m-%Y').strftime('%Y%m%d'))
    elif 'group' in dir(re.search(search_string + '-' + '(\d{2}-\d{2}-\d{2})', url, re.IGNORECASE)):
        date = re.search(search_string + '-' + '(\d{2}-\d{2}-\d{2})', url, re.IGNORECASE).group(1)
        return int(datetime.datetime.strptime(date, '%d-%m-%y').strftime('%Y%m%d'))
    elif 'group' in dir(re.search(search_string + '-' + '(\d{2}-\d{2})', url, re.IGNORECASE)):
        date = re.search(search_string + '-' + '(\d{2}-\d{2})', url, re.IGNORECASE).group(1)
        return int(datetime.datetime.strptime(date + '-2020', '%d-%m-%Y').strftime('%Y%m%d'))
    elif 'group' in dir(re.search(search_string + '-' + '(\d{1}-\d{2})', url, re.IGNORECASE)):
        date = re.search(search_string + '-' + '(\d{1}-\d{2})', url, re.IGNORECASE).group(1)
        return int(datetime.datetime.strptime(date + '-2020', '%d-%m-%Y').strftime('%Y%m%d'))
    else:
        return url


# Load src database

# In[ ]:


with open(fileroot+'urldict.json', 'r') as f:
    urldict = json.load(f)
urldict


# Check for updates

# In[ ]:


urldict_update = {}

for url in pageurls:
    date_string = str(regexgetdate('sao-carlos', url))
    if date_string not in urldict:
        urldict_update[date_string] = {'pageurl': url}

urldict_update


# In[ ]:


have_new = bool(urldict_update)  # Empty dicts return False
have_new


# If have updates available, proceed.

# In[ ]:


if have_new :
    last_update_date = datetime.datetime.now()
    print("Updates were available today: ", last_update_date)
    # All other code
else:
    print("No update was available.")


# Get images

# In[ ]:


if have_new :
    for date,entry in urldict_update.items():
        time.sleep(0.5+sp.stats.uniform.rvs())
        page = requests.get(entry['pageurl'])
        entry['imagesrc'] = pq(page.text)('.news-thumb')('img').attr.src
        print("Got imagesrc for ", date)


# In[ ]:


if have_new :
    for date,entry in urldict_update.items():
        if entry['imagesrc'] is not None:
            time.sleep(0.5+sp.stats.uniform.rvs())
            imgpage = requests.get(entry['imagesrc'])
            with open(fileroot+"images-src/"+str(date)+".jpg", "wb") as f:
                f.write(imgpage.content)
                print("Saved image-src for ", date)
            with open(fileroot+"images/"+str(date)+".jpg", "wb") as f:  # Copy new images from images-src to images!
                f.write(imgpage.content)
                print("Saved image for ", date)


# Updates urldict of sources and images folder

# In[ ]:


if have_new :
    urldict = {**urldict_update, **urldict}  # syntax for merging dictionaries


# In[ ]:


if have_new :
    with open(fileroot+'urldict.json', 'w') as f:
        json.dump(urldict, f, indent = 4)


# Functions for image pre-processing

# In[ ]:


def imgcrop(img, target, date):  # crop_box = (left, up, right, bottom)
    w, h = img.size
    if date >= 20210531:
        if target == 'casos':
            crop_box = (w*570/800, h*164/800, w*(570+98)/800, h*(164+25)/800)  
        elif target == 'obitos':
            crop_box = (w*711/800, h*535/800, w*(711+70)/800, h*(535+28)/800)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20210325:
        if target == 'casos':
            crop_box = (w*259/800, h*384/800, w*(259+140)/800, h*(384+72)/800)  
        elif target == 'obitos':
            crop_box = (w*651/800, h*671/800, w*(651+95)/800, h*(671+42)/800)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20200814:
        if target == 'casos':
            crop_box = (w*259/800, h*384/800, w*(259+140)/800, h*(384+72)/800)  
        elif target == 'obitos':
            crop_box = (w*651/800, h*657/800, w*(651+95)/800, h*(657+41)/800)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20200608:
        if target == 'casos':
            crop_box = (w*259/800, h*464/1080, w*(259+140)/800, h*(464+101)/1080)  
        elif target == 'obitos':
            crop_box = (w*651/800, h*834/1080, w*(651+95)/800, h*(834+57)/1080)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20200515:
        if target == 'casos':
            crop_box = (w*259/800, h*464/1080, w*(259+140)/800, h*(464+101)/1080)  
        elif target == 'obitos':
            crop_box = (w*651/800, h*821/1080, w*(651+95)/800, h*(821+70)/1080)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20200427:
        if target == 'casos':
            crop_box = (w*259/800, h*488/1080, w*(259+140)/800, h*(488+100)/1080)  
        elif target == 'obitos':
            crop_box = (w*651/800, h*821/1080, w*(651+95)/800, h*(821+70)/1080)
        else:
            raise Exception("Target not found on image for OCR detection.")

    elif date >= 20200407:
        if target == 'casos':
            crop_box = (w*273/1080, h*218/641, w*(273+145)/1080, h*(218+89)/641)
        elif target == 'obitos':
            crop_box = (w*757/1080, h*542/641, w*(757+85)/1080, h*(542+81)/641)
        else:
            raise Exception("Target not found on image for OCR detection.")

    else:  # date <= 20200407
        if target == 'casos':
            crop_box = (w*273/1080, h*218/641, w*(273+145)/1080, h*(218+89)/641)
        elif target == 'obitos':
            crop_box = (w*683/1080, h*395/641, w*(683+83)/1080, h*(395+72)/641)
        else:
            raise Exception("Target not found on image for OCR detection.")
    
    return Image.Image.crop(img, box=crop_box)


# In[ ]:


def imgproc(imgcrop, target, date):
    imgproc = Image.Image.convert(imgcrop, mode='L')  # grayscale image
    imgproc = ImageOps.invert(imgproc)  # invert colos
    
    if date <= 20200407 :
        if target is not 'obitos':
            imgproc = ImageOps.invert(imgproc)
        imgproc = ImageEnhance.Brightness(imgproc).enhance(2)
        # Change gamma
    
    return imgproc


# OCR fuctions

# In[ ]:


def ocrgetnumber(imgfinal):
    raw = pytesseract.image_to_string(imgfinal, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
    
    number_str = ''
    for digit in filter(str.isdigit, raw):
        number_str = number_str + digit
    try:
        number = int(number_str)
    except:
        number = 0
        #raise Exception("OCR value did not converted to int.")

    return raw, number


# In[ ]:


def ocrnumberproc(ocrnumber, target, date):
    if target == 'casos' and ocrnumber > 50000 and date > 20200801 and date < 20201101 :
        return ocrnumber - 50000
    elif target == 'obitos' and ocrnumber > 1000 and date < 20210406 :
        return 0
    else:
        return ocrnumber


# Load and update db

# In[ ]:


with open(fileroot+'db.json', 'r') as f:
    dbdict = json.load(f)
dbdict


# In[ ]:


if have_new :
    dbdict_update = {}
    for date,urls in urldict_update.items():
        date = int(date)

        if urls['imagesrc'] is not None:
            imgsrc = Image.open(fileroot+"images/"+str(date)+".jpg")

            dbdict_update[date] = {}
            for target in ['obitos', 'casos']:
                img = imgcrop(imgsrc, target, date)
                imgfinal = imgproc(img, target, date)

                ocrraw, ocrvalue = ocrgetnumber(imgfinal)
                ocrvalue = ocrnumberproc(ocrvalue, target, date)

                dbdict_update[date].update({target: ocrvalue})
                print("OCR for %d (%s) = %d from raw %s" % (date, target, ocrvalue, ocrraw))
                #imgfinal.show()


# Update db file

# In[ ]:

if have_new :
    dbdict = {**dbdict_update, **dbdict}

# temp solution for days with no report autoupdate script
# see if there is no data for yesterday, then copy numbers
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y%m%d')
befyesterday = (datetime.date.today() - datetime.timedelta(days=2)).strftime('%Y%m%d')
yesterday, befyesterday

if yesterday not in dbdict:
    yesterday_none = True
    dbdict_update2 = {}
    dbdict_update2[yesterday] = dbdict[befyesterday]  # without this the new data is placed last in json file
    dbdict = {**dbdict_update2, **dbdict}
else:
    yesterday_none = False

# In[ ]:


must_update = False
if have_new or yesterday_none:
    must_update = True
    with open(fileroot+'db.json', 'w') as f:
        json.dump(dbdict, f, indent = 4)
if yesterday_none:
    must_update = False


# Generate plots

plt.style.use(['bmh', fileroot+'mystyle.mplstyle'])

# In[ ]:


df = pd.DataFrame.from_dict(dbdict, orient='index')
df.index = pd.to_datetime(df.index, format='%Y%m%d')


# In[ ]:

if have_new :
    print("NEW: Total cases: ", df['casos'][0]," / Total deaths: ", df['obitos'][0])
else:
    last_update_date = df.index[0]
print("Last updated: ", last_update_date)


# In[ ]:


daymax = datetime.date.today()
daymin = datetime.date(daymax.year-1,daymax.month,daymax.day)
daymaxfds = datetime.date.today() + datetime.timedelta(days=6-datetime.date.today().weekday())

# In[ ]:

df['casos_diarios'] = df['casos'] - df['casos'].shift(periods=-1)
df['casos_diarios'] = df[df['casos_diarios'].index > np.datetime64(daymin)]['casos_diarios']
ax = df['casos_diarios'].plot(color='mistyrose', kind='area', # stacked=False,
                              title='Casos diários por data de divulgação no site da prefeitura')
ax = df['casos_diarios'].plot(linewidth=0, marker=4, markersize=11, markevery=[0], color=(0.5, 0, 0, 0.2))
ax = df['casos_diarios'].rolling(7, center=True).mean().plot(color='red', linewidth=2.25)
#ax.set_xlim(xmin=daymin, xmax=daymaxfds)
ax.set_xlim(xmin=daymin, xmax=daymax)
ax.set_ylim(ymin=0)
ax.set_axisbelow(False)
ax.lines[1].set_clip_on(False)
ax.legend(["Casos diários", "Último dado: "+last_update_date.strftime('%A, %d-%b-%Y')
           , "Média móvel de 7 dias centralizada"])
footnote_text1 = "* Última atualização: "+ datetime.datetime.now().strftime('%A, %d-%h-%Y às %H:%M')
footnote_text2 = "* Fonte dos dados: " + urlroot[:-1] + "   /   " + \
                    "Fonte da imagem: https://rahcor.github.io/dados-covid-sanca/"
plt.figtext(0.125, 0.02, "2020")
plt.figtext(0.875, 0.02, "("+last_update_date.strftime('%d-%h')+")")
plt.figtext(0.125, -0.035, footnote_text1)
plt.figtext(0.125, -0.085, footnote_text2)
#plt.show()
if must_update:
    plt.savefig(fileroot+'casos-diarios.jpg')
plt.savefig(fileroot+'pessoal-casos-diarios.jpg')
plt.clf()


# In[ ]:

df['obitos_diarios'] = df['obitos'] - df['obitos'].shift(periods=-1)
df['obitos_diarios'] = df[df['obitos_diarios'].index > np.datetime64(daymin)]['obitos_diarios']
ax = df['obitos_diarios'].plot(color='0.9', kind='area',  # stacked=False,
                               title='Óbitos diários por data de divulgação no site da prefeitura')
ax = df['obitos_diarios'].plot(linewidth=0, marker=4, markersize=11, markevery=[0], color=(0, 0, 0, 0.2))
ax = df['obitos_diarios'].rolling(7, center=True).mean().plot(color='black', linewidth=2.25)
#ax.set_xlim(xmin=daymin, xmax=daymaxfds)
ax.set_xlim(xmin=daymin, xmax=daymax)
ax.set_ylim(ymin=0)
ax.set_axisbelow(False)
ax.lines[1].set_clip_on(False)
ax.legend(["Casos diários", "Último dado: "+last_update_date.strftime('%A,%d-%b-%Y')
           , "Média móvel de 7 dias centralizada"])
plt.figtext(0.125, 0.02, "2020")
plt.figtext(0.875, 0.02, "("+last_update_date.strftime('%d-%h')+")")
plt.figtext(0.125, -0.035, footnote_text1)
plt.figtext(0.125, -0.085, footnote_text2)
#plt.show()
if must_update:
    plt.savefig(fileroot+'obitos-diarios.jpg')
plt.savefig(fileroot+'pessoal-obitos-diarios.jpg')
plt.clf()

# In[ ]:


df['casos_circulantes'] = 0
for i in range(1,8):
    df['casos_circulantes'] = df['casos_circulantes'] + (2.0/i) * df['casos_diarios'].shift(-i+1)

df['casos_circulantes'] = df['casos_circulantes'].shift(5) / ((1-0.4)*250000*0.5) * 100
ax = df['casos_circulantes'].plot(color='mistyrose', xlim=(daymin, daymax), title='estimativa da população contaminada em circulação (em %)')
ax = df['casos_circulantes'].rolling(7, center=True).mean().plot(color='red', xlim=(daymin, daymax))
ax.set_ylim(ymin=0)
plt.figtext(0.125, 0.03, "2020")
plt.figtext(0.875, 0.02, "("+last_update_date.strftime('%d-%h')+")")
plt.figtext(0.125, -0.025, footnote_text1)
#plt.show()
plt.savefig(fileroot+'pessoal-casos-circulantes.jpg')
plt.clf()
plt.close()

# In[ ]:




