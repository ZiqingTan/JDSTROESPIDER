import requests
import fake_useragent
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from pyquery import PyQuery as pq
import re
import pymongo
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=chrome_options)
#driver = webdriver.Chrome()
wait = WebDriverWait(driver,6)
client = pymongo.MongoClient('localhost')
db = client['JD']
def search():
    driver.get("https://www.jd.com/")
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_cate > ul > li:nth-child(1)')))
    ActionChains(driver).move_to_element(element).perform()
    sleep(2)
    #print(driver.page_source)
    return driver.page_source
def get_index_url(item):
    doc = pq(item)
    items = doc('.cate_part .cate_part_col1 .cate_detail .cate_detail_item .cate_detail_con_lk').items()
    for item in items:
        yield(item.attr('href'))
def get_total(url):
    driver.get(url)
    total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#J_bottomPage > span.p-skip > em:nth-child(1) > b")))
    return total.text
def next_page(total):
    try:
        #input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#page_jump_num")))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#J_bottomPage > span.p-num > a.pn-next")))
        #input.clear()
        #input.send_keys(total)
        parse_text()
        submit.click()
        #wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,"#J_bottomPage > span.p-num > a:nth-child(8)"),str(total)))
    except TimeoutError:
        next_page(total)
def parse_text():
    text = driver.page_source
    docs = pq(text)
    items = docs('.ml-wrap .goods-list-v2 .gl-warp .gl-item .gl-i-wrap').items()
    for item in items:
        #print(item)
        res = re.compile('src="([\s\S].*?)".*?title',re.S)
        photo = re.findall(res,str(item))
        res2 = re.compile('<div[\s\S]*?class="p-name[\s\S]*?">[\s\S].*?<em>([\s\S].*?)</em>.*?',re.S)
        title = re.findall(res2,str(item))
        res3 = re.compile('<a href=.*?title=".*?">(.*?)</a>',re.S)
        store = re.findall(res3,str(item))
        if photo and title and store:
            product = {
                "photo":photo[0],
                "money":item.find(".js_ys").text()[1:].strip(),
                "title":title[0].strip(),
                "store":store[0].strip(),
            }
            save_to_mongo(product)

def save_to_mongo(result):
    if db['JDstor'].insert(result):
        print("数据存储成功!")

if __name__ == "__main__":
    item = search()
    urls = get_index_url(item)
    for url in urls:
        #print(url)
        total = get_total('https:'+url)
        for i in range(2,int(total)+1):
            next_page(i)


