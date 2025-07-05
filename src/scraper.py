# src/scraper.py

import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

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

        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-gpu")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.wait   = WebDriverWait(self.driver, 20)

    def login(self):
        drv = self.driver
        drv.get(self.LOGIN_URL)

        # seleciona a opção "usuário externo"
        ext = self.wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//label[contains(normalize-space(.), 'usuário externo')]"
        )))
        ext.click()

        # espera o formulário aparecer
        self.wait.until(EC.visibility_of_element_located((By.ID, "txt_user_login")))

        # preenche e envia
        drv.find_element(By.ID, "txt_user_login").send_keys(self.user)
        drv.find_element(By.ID, "pwd_user_password").send_keys(self.pw)
        drv.find_element(By.ID, "button-verify").click()

        # aguarda realmente estar em /Scheduler
        self.wait.until(EC.url_contains("/Scheduler"))

    def fetch(self) -> dict:
        # loga e garante scheduler carregado
        self.login()

        # espera por ao menos um evento renderizado dentro de #dps
        self.wait.until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, "#dps .ciem_theme_event_inner"
        )))

        # captura todos os elementos de evento
        elems = self.driver.find_elements(By.CSS_SELECTOR, "#dps .ciem_theme_event_inner")
        data = {}
        for e in elems:
            text = e.text.strip()
            m = re.search(r"(006000\d+)", text)
            if m:
                data[m.group(1)] = text

        return data

    def close(self):
        self.driver.quit()

