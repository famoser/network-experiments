# This script captures HAR files of all bitrates of a specific video
# It uses a incorrect approach of choosing the bitrates, and should only be used as a reference 

import requests as request
import datetime
import psutil
import subprocess
import time
import json
from selenium import webdriver


def start_browser_proxy():
    subprocess.Popen(["../libs/browsermob-proxy-2.1.4/bin/browsermob-proxy"])
    i = 3
    while i > 0:
        print("waiting " + str(i))
        time.sleep(1)
        i -= 1


def end_browser_proxy():
    found = None
    dictionary = {}
    for process in psutil.process_iter():
        dictionary[process.pid] = process

    for pid in sorted(dictionary):
        if 'browsermob-prox' in dictionary[pid].name():
            dictionary[pid].kill()
            found = True
            print("found & killed old process")
        if "java" in dictionary[pid].name() and found:
            dictionary[pid].kill()
            print("found & killed old java process")
            return


def start_capture():
    startUrl = 'http://localhost:8080/proxy'
    startData = '{}'
    response = request.post(startUrl, startData)
    startResponse = json.loads(response.content)
    port = startResponse["port"]
    assert (response.status_code == 200)
    print("initialized at port " + str(port))

    harUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    harData = '{}'
    response = request.put(harUrl, harData)
    print(response.status_code)
    assert (response.status_code == 204)
    print('started capture at port ' + str(port))

    return port


def play_in_browser(netflix_id, rate, port):
    video_url = 'https://www.netflix.com/watch/' + str(netflix_id) + '?rate=' + str(rate)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % "127.0.0.1:" + str(port))
    chrome_options.add_extension('../netflix-1080p-1.2.9.crx')

    chrome = webdriver.Chrome(chrome_options=chrome_options)
    chrome.get(video_url)

    trying_to_login = False
    try:
        login_link = chrome.find_element_by_class_name("authLinks")
        link = login_link.get_attribute("href")
        chrome.get(link)
        trying_to_login = True

        credentials = json.load(open('../credentials.json'))

        username_field = selenium_try_find_element_by_id(chrome, "email")
        username_field.send_keys(credentials["netflix"]["username"])

        password_field = selenium_try_find_element_by_id(chrome, "password")
        password_field.send_keys(credentials["netflix"]["password"])

        password_field.submit()

        chrome.get("https://www.netflix.com/SwitchProfile?tkn=" + credentials["netflix"]["profile"])
        chrome.get(video_url)
    except:
        if trying_to_login:
            print("login failed")
            return False
        else:
            print("already logged in")

    try:
        'check for fatal error && sleeps 5 seconds if not'
        if selenium_try_find_element_by_class(chrome, "nfp-fatal-error-view") is None:
            chrome.close()
            return True
    except:
        time.sleep(5)

    chrome.execute_script("fasterPlayback()")
    i = 200
    while i > 0:
        if not chrome.execute_script("return stillActive()"):
            break

        time.sleep(5)
        i -= 1

    chrome.close()
    return True


def selenium_try_find_element_by_id(driver, element_id):
    retries = 5
    while retries > 0:
        try:
            return driver.find_element_by_id(element_id)
        finally:
            time.sleep(1)
            retries -= 1
    return None


def selenium_try_find_element_by_class(driver, element_id):
    retries = 5
    while retries > 0:
        try:
            element = driver.find_element_by_class_name(element_id)
            return element
        finally:
            time.sleep(1)
            retries -= 1
    return None


def end_capture(netflix_id, rate, port):
    saveUrl = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = request.get(saveUrl)
    fileName = str(netflix_id) + '_' + str(rate) + "_ " + datetime.datetime.now().isoformat()
    with open(fileName + '.json', "w") as text_file:
        print(response.content.decode(), file=text_file)
    assert (response.status_code == 200)
    print('saved capture')

    stopUrl = 'http://localhost:8080/proxy/' + str(port)
    response = request.delete(stopUrl)
    assert (response.status_code == 200)
    print('stopped at port ' + str(port))


end_browser_proxy()
start_browser_proxy()

'testvideo 80018499'
netflix_ids = [80111448]
no_errors = True
for netflix_id in netflix_ids:
    rate = 3
    while rate <= 4 and no_errors:
        port = start_capture()
        no_errors = no_errors and play_in_browser(netflix_id, rate, port)
        end_capture(netflix_id, rate, port)
        rate += 1


end_browser_proxy()

if not no_errors:
    print("something failed; stopped capture early")