from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
import pyautogui

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
driver.implicitly_wait(15)

# Get Url
driver.get("https://fb.goflow.com/")
# sleep(1)
driver.find_element(By.NAME, "userName").send_keys("Robinb")
# sleep(1)
driver.find_element(By.NAME, "password").send_keys("Robin1600!")
# sleep(1)
driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
# sleep(10)
driver.find_element(By.XPATH, "//div[@class='summary-value']").click()
# sleep(5)
driver.find_element(By.XPATH, "//input[@placeholder='Search']").send_keys("108901040186593")
driver.find_element(By.XPATH, "//td[normalize-space()='108901040186593']").click()
sleep(2)
driver.find_element(By.XPATH,
                    "(//button[@class='button-secondary button-icon icon-more tooltip-wrapper dropdown-toggle'])[1]").click()
driver.find_element(By.XPATH, "//a[normalize-space()='Pack & Ship']").click()
driver.find_element(By.XPATH, "//button[normalize-space()='Pack All']").click()
driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").send_keys("2")

lenght_val = driver.find_element(By.XPATH, "//input[@placeholder='Length']").get_attribute("value")
driver.find_element(By.XPATH, "//input[@placeholder='Length']").clear()
driver.find_element(By.XPATH, "//input[@placeholder='Length']").send_keys("28")
driver.find_element(By.XPATH, "//input[@placeholder='Width']").clear()
driver.find_element(By.XPATH, "//input[@placeholder='Width']").send_keys("28")
driver.find_element(By.XPATH, "//input[@placeholder='Height']").clear()
driver.find_element(By.XPATH, "//input[@placeholder='Height']").send_keys("2")
sleep(4)
driver.find_element(By.XPATH, "//button[normalize-space()='Ship & Close']").click()
sleep(4)
driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
sleep(4)
driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
sleep(2)
download_button = driver.find_element(By.XPATH,
                                   "//button[@class='button-secondary button-icon tooltip-wrapper icon-document']")
actions = ActionChains(driver)
actions.click(download_button).perform()

sleep(2)
driver.find_element(By.XPATH, "//a[normalize-space()='Download All']").click()
sleep(2)
pyautogui.press('enter')

driver.quit()


# import PyPDF2
# import zipfile
#
# def extract_text_from_pdf(pdf_file):
#     pdf_reader = PyPDF2.PdfFileReader(pdf_file)
#     text = ''
#     for page_num in range(pdf_reader.numPages):
#         page = pdf_reader.getPage(page_num)
#         text += page.extractText()
#     return text
#
# zip_file_path = "test_108901040186593.zip"
#
# with zipfile.ZipFile(zip_file_path) as z:
#     for file_name in z.namelist():
#         if file_name.lower().endswith('.pdf'):
#             with z.open(file_name) as pdf_file:
#                 pdf_text = extract_text_from_pdf(pdf_file)
#                 print(type(pdf_text))
#
