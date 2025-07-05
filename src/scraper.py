# src/scraper.py

import os
import re
from datetime import datetime, timedelta
from time import sleep
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


load_dotenv()  # carrega CIEM_USER e CIEM_PW do .env

class SchedulerScraper:
    LOGIN_URL     = (
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
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_opts
        )

    def login(self):
        drv = self.driver
        drv.get(self.LOGIN_URL)

        # clicar em "Logar com usuário externo"
        WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'usuário externo')]"))
        ).click()

        # preencher e submeter credenciais
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.NAME, "j_username")))
        drv.find_element(By.NAME, "j_username").send_keys(self.user)
        drv.find_element(By.NAME, "j_password").send_keys(self.pw)
        drv.find_element(By.XPATH, "//button[@type='submit']").click()

        # aguardar o redirecionamento à página Scheduler
        WebDriverWait(drv, 15).until(EC.url_contains("/Scheduler"))

    def fetch(self) -> dict:
        """
        Retorna um dict { identificador: "006000xxxxxx - SERVIÇO" }
        apenas para eventos cuja data de início esteja entre hoje e hoje+14 dias.
        """
        self.login()
        drv = self.driver

        # garantir que o container exista
        WebDriverWait(drv, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#dps"))
        )

        # calcular intervalo de datas
        hoje  = datetime.today().date()
        fim   = hoje + timedelta(days=14)

        data = {}
        # percorrer apenas os eventos “com janelaFimFora”
        eventos = drv.find_elements(By.CSS_SELECTOR, ".ciem_theme_event.janelaFimFora")
        for ev in eventos:
            title = ev.get_attribute("title") or ""
            # extrair identificador
            m_id   = re.search(r"Identificador:\s*(006000\d+)", title)
            # extrair data de início do “Duração”
            m_dur  = re.search(r"Duração:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", title)
            # extrair o texto do serviço
            m_serv = re.search(r"Serviço:\s*(.+)", title)
            if not (m_id and m_dur and m_serv):
                continue

            ident = m_id.group(1)
            # converte “dd/mm/yyyy” → date
            data_inicio = datetime.strptime(m_dur.group(1), "%d/%m/%Y").date()
            if not (hoje <= data_inicio <= fim):
                continue

            serv = m_serv.group(1).strip()
            data[ident] = f"{ident} - {serv}"

        return data

    def close(self):
        self.driver.quit()

