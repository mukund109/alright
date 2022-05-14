"""
Alright is unofficial Python wrapper for whatsapp web made as an inspiration from PyWhatsApp
allowing you to send messages, images, video and documents programmatically using Python
"""


import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote


class WhatsApp(object):
    def __init__(self, browser=None, time_out=600):
        # CJM - 20220419: Added time_out=600 to allow the call with less than 600 sec timeout
        # web.open(f"https://web.whatsapp.com/send?phone={phone_no}&text={quote(message)}")

        self.BASE_URL = "https://web.whatsapp.com/"
        self.suffix_link = "https://wa.me/"

        if not browser:
            browser = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=self.chrome_options,
            )

        self.browser = browser
        # CJM - 20220419: Added time_out=600 to allow the call with less than 600 sec timeout
        self.wait = WebDriverWait(self.browser, time_out)
        self.login()
        self.mobile = ""

    @property
    def chrome_options(self):
        chrome_options = Options()
        if sys.platform == "win32":
            chrome_options.add_argument("--profile-directory=Default")
            chrome_options.add_argument("--user-data-dir=C:/Temp/ChromeProfile")
        else:
            chrome_options.add_argument("start-maximized")
            chrome_options.add_argument("--user-data-dir=./User_Data")
        return chrome_options

    def login(self):
        self.browser.get(self.BASE_URL)
        self.browser.maximize_window()

    def logout(self):
        prefix = "//div[@id='side']/header/div[2]/div/span/div[3]"
        dots_button = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"{prefix}/div[@role='button']",
                )
            )
        )
        dots_button.click()

        logout_item = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"{prefix}/span/div[1]/ul/li[last()]/div[@role='button']",
                )
            )
        )
        logout_item.click()

    def get_phone_link(self, mobile) -> str:
        """get_phone_link (), create a link based on whatsapp (wa.me) api

        Args:
            mobile ([type]): [description]

        Returns:
            str: [description]
        """
        return f"{self.suffix_link}{mobile}"

    def catch_alert(self, seconds=3):
        """catch_alert()

        catches any sudden alert
        """
        try:
            WebDriverWait(self.browser, seconds).until(EC.alert_is_present())
            alert = self.browser.switch_to_alert.accept()
            return True
        except Exception as e:
            print(e)
            return False

    def find_user(self, mobile) -> None:
        """find_user()
        Makes a user with a given mobile a current target for the wrapper

        Args:
            mobile ([type]): [description]
        """
        try:
            self.mobile = mobile
            link = self.get_phone_link(mobile)
            self.browser.get(link)
            action_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="action-button"]'))
            )
            action_button.click()
            time.sleep(2)
            go_to_web = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="fallback_block"]/div/div/h4[2]/a')
                )
            )
            go_to_web.click()
            time.sleep(1)
        except UnexpectedAlertPresentException as bug:
            print(bug)
            time.sleep(1)
            self.find_user(mobile)

    def find_by_username(self, username):
        """find_user_by_name ()

        locate existing contact by username or number

        Args:
            username ([type]): [description]
        """
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="side"]/div[1]/div/label/div/div[2]')
                )
            )
            search_box.clear()
            search_box.send_keys(username)
            search_box.send_keys(Keys.ENTER)
        except Exception as bug:
            error = f"Exception raised while finding user {username}\n{bug}"
            print(error)

    def username_exists(self, username):
        """username_exists ()

        Returns True or False whether the contact exists or not, and selects the contact if it exists, by checking if the search performed actually opens a conversation with that contact

        Args:
            username ([type]): [description]
        """
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="side"]/div[1]/div/label/div/div[2]')
                )
            )
            search_box.clear()
            search_box.send_keys(username)
            search_box.send_keys(Keys.ENTER)
            opened_chat = self.browser.find_element_by_xpath(
                "/html/body/div/div[1]/div[1]/div[4]/div[1]/header/div[2]/div[1]/div/span"
            )
            title = opened_chat.get_attribute("title")
            if title.upper() == username.upper():
                return True
            else:
                return False
        except Exception as bug:
            error = f"Exception raised while finding user {username}\n{bug}"
            print(error)

    def send_message1(self, mobile: str, message: str):
        """CJM - 20220419:
        Send WhatsApp Message With Different URL, NOT using https://wa.me/ to prevent WhatsApp Desktop to open
        Also include the Number we want to send to"""
        try:
            # Browse to a "Blank" message state
            self.browser.get(f"https://web.whatsapp.com/send?phone={mobile}&text")

            # This is the XPath of the message textbox
            inp_xpath = (
                '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]'
            )
            # This is the XPath of the "ok button" if the number was not found
            nr_not_found_xpath = (
                '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[2]/div/div'
            )

            # If the number is NOT a WhatsApp number then there will be an OK Button, not the Message Textbox
            # Test for both situations -> find_elements returns a List
            ctrl_element = self.wait.until(
                lambda ctrl_self: ctrl_self.find_elements(By.XPATH, nr_not_found_xpath)
                or ctrl_self.find_elements(By.XPATH, inp_xpath)
            )
            # Iterate through the list of elements to test each if they are a textBox or a Button
            for i in ctrl_element:
                if i.aria_role == "textbox":
                    # This is a WhatsApp Number -> Send Message
                    i.send_keys(message + Keys.ENTER)
                    msg = f"Message sent successfully to {mobile}"
                    # Found alert issues when we send messages too fast, so I called the below line to catch any alerts
                    self.catch_alert()

                elif i.aria_role == "button":
                    # Did not find the Message Text box
                    # BUT we possibly found the XPath of the error "Phone number shared via url is invalid."
                    if i.text == "OK":
                        # This is NOT a WhatsApp Number -> Press enter and continue
                        i.send_keys(Keys.ENTER)
                        msg = f"Not a WhatsApp Number {mobile}"

        except (NoSuchElementException, Exception) as bug:
            print(bug)
            msg = f"Failed to send a message to {self.mobile}"

        finally:
            print(msg)

    def send_message(self, message):
        """send_message ()
        Sends a message to a target user

        Args:
            message ([type]): [description]
        """
        try:
            inp_xpath = (
                '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]'
            )
            input_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, inp_xpath))
            )
            input_box.send_keys(message + Keys.ENTER)
            print(f"Message sent successfuly to {self.mobile}")
        except (NoSuchElementException, Exception) as bug:
            print(bug)
            print(f"Failed to send a message to {self.mobile}")

        finally:
            print("send_message() finished running ")

    def find_attachment(self):
        clipButton = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main"]/footer//*[@data-icon="clip"]/..')
            )
        )
        clipButton.click()

    def send_attachment(self):
        # Waiting for the pending clock icon to disappear
        self.wait.until_not(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
            )
        )

        sendButton = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="app"]/div[1]/div[1]/div[2]/div[2]/span/div[1]/span/div[1]/div/div[2]/div/div[2]/div[2]/div/div/span',
                )
            )
        )
        sendButton.click()

    def send_picture(self, picture, message):
        """send_picture ()

        Sends a picture to a target user

        Args:
            picture ([type]): [description]
        """
        try:
            filename = os.path.realpath(picture)
            self.find_attachment()
            # To send an Image
            imgButton = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="main"]/footer//*[@data-icon="attach-image"]/../input',
                    )
                )
            )
            imgButton.send_keys(filename)
            inp_xpath = '//*[@id="app"]/div[1]/div[1]/div[2]/div[2]/span/div[1]/span/div[1]/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div/div[2]'
            input_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, inp_xpath))
            )
            input_box.send_keys(message)
            self.send_attachment()
            print(f"Picture has been successfully sent to {self.mobile}")
        except (NoSuchElementException, Exception) as bug:
            print(bug)
            print(f"Failed to send a picture to {self.mobile}")

        finally:
            print("send_picture() finished running ")

    def send_video(self, video):
        """send_video ()

        Sends a video to a target user

        Args:
            video ([type]): [description]
        """
        try:
            filename = os.path.realpath(video)
            self.find_attachment()
            # To send a Video
            video_button = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="main"]/footer//*[@data-icon="attach-image"]/../input',
                    )
                )
            )
            video_button.send_keys(filename)
            self.send_attachment()
            print(f"Video has been successfully sent to {self.mobile}")
        except (NoSuchElementException, Exception) as bug:
            print(bug)
            print(f"Failed to send a video to {self.mobile}")
        finally:
            print("send_video() finished running ")

    def send_file(self, filename):
        """send_file()

        Sends a file to target user

        Args:
            filename ([type]): [description]
        """
        try:
            filename = os.path.realpath(filename)
            self.find_attachment()
            document_button = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="main"]/footer//*[@data-icon="attach-document"]/../input',
                    )
                )
            )
            document_button.send_keys(filename)
            self.send_attachment()
        except (NoSuchElementException, Exception) as bug:
            print(bug)
            print(f"Failed to send a PDF to {self.mobile}")
        finally:
            print("send_file() finished running ")
