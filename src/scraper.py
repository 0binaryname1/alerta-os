# src/scraper.py

import os
import re
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# carrega CIEM_USER e CIEM_PW de .env
load_dotenv()

class SchedulerScraper:
    LOGIN_URL = (
        "https://loginseguro.petrobras.com.br/fwca/pages/AuthenticationForm.jsp?"
        "successfulUrl=https%3a%2f%2fex-ciem2.petrobras.com.br%3a443%2f"
        "&ssoEnabled=False&applicationCatalogId=CIE2"
        "&appEnvUid=5013&integratedAuthenticationEnabled=False"
        "&logonPage=&hxid=f47309d2917dbf0c#"
    )
    SCHEDULER_URL = "https://ex-ciem2.petrobras.com.br/Scheduler"

    def __init__(self):
        self.user = os.getenv("CIEM_USER")
        self.pw   = os.getenv("CIEM_PW")
        if not self.user or not self.pw:
            raise RuntimeError("CIEM_USER ou CIEM_PW não definidos no .env")

        chrome_opts = webdriver.ChromeOptions()
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-gpu")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_opts)

    def login(self):
        drv = self.driver
        drv.get(self.LOGIN_URL)

        # 1) Clicar na opção "Logar com usuário externo"
        ext_label = WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@id='wrap-options-login']//label[contains(normalize-space(.), 'usuário externo')]"
            ))
        )
        ext_label.click()

        # 2) Aguarda até o bloco de senha externo ficar visível
        WebDriverWait(drv, 10).until(
            EC.visibility_of_element_located((By.ID, "txt_user_login"))
        )

        # 3) Preenche usuário e senha
        drv.find_element(By.ID, "txt_user_login").send_keys(self.user)
        drv.find_element(By.ID, "pwd_user_password").send_keys(self.pw)

        # 4) Clica em “Entrar”
        drv.find_element(By.ID, "button-verify").click()

        # 5) Aguarda o redirecionamento ao Scheduler
        WebDriverWait(drv, 15).until(
            EC.url_contains("/Scheduler")
        )

    def fetch(self) -> dict:
        # realiza todo o fluxo de login
        self.login()

        # aguarda o container #dps carregar
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#dps"))
        )

        # pega o HTML autenticado
        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")

        container = soup.select_one("#dps")
        i

