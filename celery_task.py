# celery_task.py
from celery import Celery
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
import os
import pyautogui
import odoorpc
import base64

celery = Celery(
    'celery_tasks',
    broker='redis://localhost:6379/0',  # Replace with your Celery broker URL
    backend='redis://localhost:6379/0',  # Replace with your Celery backend URL
)


def _connect():
    # print("CONNECTING")
    # username = 'admin'
    # pwd = 'Since@2023'
    # dbname = 'flybar-staging-11108069'
    # url = 'flybar-staging-11108069.dev.odoo.com'
    # odoo_rpc_obj = odoorpc.ODOO(url, port=80)
    # odoo_rpc_obj.login(dbname, username, pwd)

    inno_odoo = odoorpc.ODOO('localhost', port=8069)
    inno_odoo.login('odoo16_flybar_2', 'admin', 'admin')
    print("CONNECTED")
    return inno_odoo


def execute_script_success(picking_id, zip_path, odoo_rpc_obj, task_id):
    picking_obj = odoo_rpc_obj.env['stock.picking']
    go_flow_packaging_update_log = odoo_rpc_obj.env['go.flow.packaging.update.log']
    # picking_id = picking_obj.search([('id', '=', picking_id)], limit=1)
    with open(zip_path, "rb") as zip_file:
        data = zip_file.read()
        picking_obj.write([int(picking_id)], {'goflow_document': base64.b64encode(data or b'').decode("ascii"),
                                              'goflow_routing_status': 'doc_generated'})
    go_flow_packaging_update_log.write([int(task_id)],
                                       {'request_status': 'completed'})
    print("Uploaded Zip", zip_path)


def execute_script_fail(picking_id, odoo_rpc_obj, task_id):
    picking_obj = odoo_rpc_obj.env['stock.picking']
    go_flow_packaging_update_log = odoo_rpc_obj.env['go.flow.packaging.update.log']
    print([str(picking_id)])
    picking_obj.write([int(picking_id)], {'goflow_routing_status': 'doc_generated'})
    go_flow_packaging_update_log.write([int(task_id)], {'request_status': 'completed'})
    print("updated failed status Zip", picking_id)


def run_script(new_user_id):
    # with app.app_context():
    print("new_user_id", new_user_id)
    db = sqlite3.connect('my_database.db')
    cursor = db.execute('SELECT * FROM packaging_order WHERE ID = ?', (new_user_id,))
    user_row = cursor.fetchone()
    print(user_row)
    columns = [col[0] for col in cursor.description]

    # Convert the row to a dictionary using column names
    user_dict = dict(zip(columns, user_row))

    order_name = user_dict['order_name']
    weight = user_dict['weight']
    length = user_dict['length']
    width = user_dict['width']
    height = user_dict['height']
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.implicitly_wait(15)
    try:
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
        driver.find_element(By.XPATH, "//input[@placeholder='Search']").send_keys(order_name)
        driver.find_element(By.XPATH, "//td[normalize-space()='" + order_name + "']").click()
        sleep(2)
        driver.find_element(By.XPATH,
                            "(//button[@class='button-secondary button-icon icon-more tooltip-wrapper dropdown-toggle'])[1]").click()
        driver.find_element(By.XPATH, "//a[normalize-space()='Pack & Ship']").click()
        driver.find_element(By.XPATH, "//button[normalize-space()='Pack All']").click()
        driver.find_element(By.XPATH, "//input[@placeholder='Lbs.']").send_keys(str(weight))

        lenght_val = driver.find_element(By.XPATH, "//input[@placeholder='Length']").get_attribute("value")
        width_val = driver.find_element(By.XPATH, "//input[@placeholder='Width']").get_attribute("value")
        height_val = driver.find_element(By.XPATH, "//input[@placeholder='Height']").get_attribute("value")
        driver.find_element(By.XPATH, "//input[@placeholder='Length']").clear()
        driver.find_element(By.XPATH, "//input[@placeholder='Length']").send_keys(str(length))
        driver.find_element(By.XPATH, "//input[@placeholder='Width']").clear()
        driver.find_element(By.XPATH, "//input[@placeholder='Width']").send_keys(str(width))
        driver.find_element(By.XPATH, "//input[@placeholder='Height']").clear()
        driver.find_element(By.XPATH, "//input[@placeholder='Height']").send_keys(str(height))
        sleep(4)
        driver.find_element(By.XPATH, "//button[normalize-space()='Ship & Close']").click()
        sleep(4)
        driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
        sleep(4)
        driver.find_element(By.XPATH, "//i[@class='icon-ex dialog-close']").click()
        sleep(5)
        download_button = driver.find_element(By.XPATH,
                                              "//button[@class='button-secondary button-icon tooltip-wrapper icon-document']")
        actions = ActionChains(driver)
        actions.click(download_button).perform()

        sleep(2)
        driver.find_element(By.XPATH, "//a[normalize-space()='Download All']").click()
        sleep(2)
        pyautogui.press('enter')
        sleep(3)

        driver.quit()
    except Exception as e:
        driver.quit()
        print("==================================>>>>>>>>>>>>>", e)
        raise e


@celery.task
def process_pending_tasks():
    db = sqlite3.connect('my_database.db')
    cursor = db.execute('SELECT * FROM packaging_order WHERE status = ? ORDER BY create_date ASC LIMIT 1', ('pending',))
    pending_task = cursor.fetchone()

    if pending_task:
        task_id = pending_task[0]  # Assuming ID is the first column
        cursor.execute('UPDATE packaging_order SET status = ? WHERE ID = ?', ('processing', task_id))
        db.commit()
        try:
            run_script(task_id)
            cursor.execute('UPDATE packaging_order SET status = ? WHERE ID = ?', ('completed', task_id))
            db.commit()
            cursor = db.execute('SELECT * FROM packaging_order WHERE ID = ?', (task_id,))

            user_row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            found_file_path = False
            user_dict = dict(zip(columns, user_row))
            print(user_dict)
            order_name = user_dict['order_name']
            picking_id = user_dict['picking']
            directory_path = '/home/kunal.chambhare/Downloads'
            substring = order_name
            files_in_directory = os.listdir(directory_path)
            matching_files = [file for file in files_in_directory if substring in file]
            print(substring, directory_path, matching_files)
            if matching_files:
                found_file_path = os.path.join(directory_path, matching_files[0])
            print(found_file_path)
            if found_file_path:
                odoo_obj = _connect()
                execute_script_success(picking_id, found_file_path, odoo_obj, task_id)

        except Exception as e:
            print("EXCEPTION", e)
            cursor.execute('UPDATE packaging_order SET status = ? WHERE ID = ?', ('failed', task_id))
            db.commit()
            cursor = db.execute('SELECT * FROM packaging_order WHERE ID = ?', (task_id,))
            user_row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            user_dict = dict(zip(columns, user_row))
            picking_id = user_dict['picking']
            odoo_obj = _connect()
            execute_script_fail(picking_id, odoo_obj, task_id)

        db.commit()
        cursor = db.execute('SELECT * FROM packaging_order WHERE status = ? ORDER BY create_date ASC LIMIT 1',
                            ('pending',))
        pending_task = cursor.fetchone()
        if pending_task:
            process_pending_tasks.delay()
        else:
            cursor.execute('UPDATE status_boolean_table SET status = ? WHERE ID = ?', (False, 1))
            db.commit()


if __name__ == '__main__':
    celery.start()
