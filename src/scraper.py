# src/scraper.py

import os
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
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

        chrome_opts = webdriver.ChromeOptions()
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-gpu")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_opts)

    def login(self):
        drv = self.driver
        drv.get(self.LOGIN_URL)

        # Aguarda o campo de usuário externo aparecer
        WebDriverWait(drv, 15).until(
            EC.visibility_of_element_located((By.ID, "txt_user_login"))
        )

        # Preenche usuário e senha
        drv.find_element(By.ID, "txt_user_login").send_keys(self.user)
        drv.find_element(By.ID, "pwd_user_password").send_keys(self.pw)

        # Clica em “Entrar”
        drv.find_element(By.ID, "button-verify").click()

        # Aguarda o redirecionamento ao Scheduler
        WebDriverWait(drv, 15).until(
            EC.url_contains("/Scheduler")
        )

    def fetch(self) -> dict:
        # executa login + navega para scheduler
        self.login()

        # aguarda o container #dps carregar
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#dps"))
        )

        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")

        container = soup.select_one("#dps")
        if not container:
            raise RuntimeError("Container #dps não encontrado")

        data = {}
        for e in container.select(".ciem_theme_event_inner"):
            text = e.get_text(strip=True)
            m = re.search(r"(006000\d+)", text)
            if m:
                data[m.group(1)] = text
        return data

    def close(self):
        """Encerra o browser cleanly."""
        self.driver.quit()

