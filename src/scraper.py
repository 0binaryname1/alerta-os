# src/scraper.py

import os
import re
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

class SchedulerScraper:
    """
    Realiza login na plataforma da Petrobras e extrai eventos de ordens de serviço
    exibidos no container #dps da página Scheduler.
    """

    LOGIN_URL = (
        "https://loginseguro.petrobras.com.br/fwca/pages/AuthenticationForm.jsp?"
        "successfulUrl=https%3a%2f%2fex-ciem2.petrobras.com.br%2fScheduler"
    )
    TIMEOUT_LOGIN = 20
    TIMEOUT_EVENTS = 30

    def __init__(self):
        # Credenciais
        self.user = os.getenv('CIEM_USER')
        self.pw   = os.getenv('CIEM_PW')
        if not (self.user and self.pw):
            raise RuntimeError('Defina CIEM_USER e CIEM_PW no .env')

        # Chrome headless
        opts = webdriver.ChromeOptions()
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-gpu')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        logger.info('WebDriver inicializado')

    def login_and_wait(self) -> None:
        """
        Executa o fluxo de login e aguarda o carregamento inicial do Scheduler.
        """
        drv = self.driver
        drv.get(self.LOGIN_URL)
        logger.info('Acessando página de login')

        # Seleciona "usuário externo"
        WebDriverWait(drv, self.TIMEOUT_LOGIN).until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(normalize-space(.),'usuário externo')]'"))
        ).click()
        logger.info('Opção usuário externo selecionada')

        # Aguarda formulário
        WebDriverWait(drv, self.TIMEOUT_LOGIN).until(
            EC.visibility_of_element_located((By.ID, 'wrap-login-password'))
        )

        # Preenche
        drv.find_element(By.ID, 'txt_user_login').send_keys(self.user)
        drv.find_element(By.ID, 'pwd_user_password').send_keys(self.pw)
        logger.info('Credenciais preenchidas')

        # Submete
        drv.find_element(By.ID, 'button-verify').click()
        logger.info('Submetido, aguardando Scheduler')

        # Aguarda container #dps inicial
        WebDriverWait(drv, self.TIMEOUT_LOGIN).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#dps'))
        )
        logger.info('Página Scheduler carregada')

    def fetch(self) -> dict:
        """
        Faz login, aguarda eventos aparecerem, e retorna dicionário {id: texto}.
        """
        try:
            self.login_and_wait()
        except TimeoutException as e:
            self._debug('login')
            raise RuntimeError('Falha no login ou carregamento inicial') from e

        # Espera eventos carregarem via AJAX
        try:
            WebDriverWait(self.driver, self.TIMEOUT_EVENTS).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.ciem_theme_event_inner'))
            )
        except TimeoutException:
            logger.warning('Nenhum evento apareceu em %d segundos', self.TIMEOUT_EVENTS)

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        container = soup.select_one('#dps')
        if not container:
            raise RuntimeError('Container #dps ausente no HTML final')

        data = {}
        for element in container.select('.ciem_theme_event_inner'):
            text = element.get_text(strip=True)
            m = re.search(r'(006000\d+)', text)
            if m:
                data[m.group(1)] = text

        logger.info('Eventos extraídos: %d', len(data))
        return data

    def close(self):
        """Encerra o browser."""
        self.driver.quit()
        logger.info('WebDriver finalizado')

    def _debug(self, stage: str):
        """Salva HTML e screenshot para depuração."""
        filename = f'debug_{stage}.html'
        with open(filename, 'w', encoding='utf8') as f:
            f.write(self.driver.page_source)
        self.driver.save_screenshot(f'debug_{stage}.png')
        logger.info('Debug salvo: %s e %s', filename, f'debug_{stage}.png')

