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
    Realiza login na página segura da Petrobras e extrai eventos de ordens de serviço
    exibidos no container #dps.
    """

    # URL de login já com parâmetro para redirecionar ao Scheduler
    LOGIN_URL = (
        "https://loginseguro.petrobras.com.br/fwca/pages/AuthenticationForm.jsp?"
        "successfulUrl=https%3a%2f%2fex-ciem2.petrobras.com.br%2fScheduler"
    )

    # Tempo máximo de espera (em segundos)
    TIMEOUT = 30

    def __init__(self):
        # Lê credenciais do .env
        self.user = os.getenv('CIEM_USER')
        self.pw   = os.getenv('CIEM_PW')
        if not self.user or not self.pw:
            raise RuntimeError('Defina CIEM_USER e CIEM_PW no .env')

        # Configura Chrome headless
        opts = webdriver.ChromeOptions()
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-gpu')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        logger.info('WebDriver inicializado')

    def login_and_wait(self) -> str:
        """
        Executa o fluxo de login (seleciona usuário externo, preenche credenciais,
        envia o formulário) e aguarda o carregamento da página do Scheduler.
        Retorna o HTML da página ao final.
        """
        self.driver.get(self.LOGIN_URL)
        logger.info('Acessando a página de login')

        # Aguarda as opções de login aparecerem
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.ID, 'wrap-options-login'))
        )

        # Clica em "Logar com usuário externo"
        self.driver.find_element(
            By.XPATH,
            "//div[@id='wrap-options-login']//label[contains(normalize-space(.), 'usuário externo')]"
        ).click()
        logger.info('Selecionada opção usuário externo')

        # Aguarda o formulário de usuário externo aparecer
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.visibility_of_element_located((By.ID, 'wrap-login-password'))
        )

        # Preenche usuário e senha
        self.driver.find_element(By.ID, 'txt_user_login').send_keys(self.user)
        self.driver.find_element(By.ID, 'pwd_user_password').send_keys(self.pw)
        logger.info('Credenciais preenchidas')

        # Envia o formulário
        self.driver.find_element(By.ID, 'button-verify').click()
        logger.info('Formulário enviado, aguardando Scheduler')

        # Aguarda o container #dps na página do Scheduler
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#dps'))
        )
        logger.info('Scheduler carregado com sucesso')

        return self.driver.page_source

    def fetch(self) -> dict:
        """
        Faz o login e retorna um dicionário com as entradas 006000xxxxxx mapeadas
        para o texto completo de cada evento.
        """
        try:
            html = self.login_and_wait()
        except TimeoutException as e:
            # Salva debug em caso de falha
            with open('debug.html', 'w', encoding='utf8') as f:
                f.write(self.driver.page_source)
            self.driver.save_screenshot('debug.png')
            raise RuntimeError('Timeout ao carregar Scheduler. Veja debug.html/debug.png') from e

        # Parse do HTML
        soup = BeautifulSoup(html, 'lxml')
        container = soup.select_one('#dps')
        if not container:
            raise RuntimeError('#dps não encontrado no HTML')

        data = {}
        for element in container.select('.ciem_theme_event_inner'):
            text = element.get_text(strip=True)
            m = re.search(r'(006000\d+)', text)
            if m:
                data[m.group(1)] = text

        logger.info('Extraídos %d eventos', len(data))
        return data

    def close(self):
        """Encerra o browser."""
        self.driver.quit()
        logger.info('WebDriver finalizado')

