import re
import requests
from bs4 import BeautifulSoup

class SchedulerScraper:
    LOGIN_URL = 'https://ex-ciem2.petrobras.com.br/Scheduler/login'
    DATA_URL  = 'https://ex-ciem2.petrobras.com.br/Scheduler'

    def __init__(self):
        self.sess = requests.Session()
        # TODO: ajustar para ler de variáveis de ambiente ou arquivo seguro
        self.user = 'SEU_USUARIO'
        self.pw   = 'SUA_SENHA'

    def login(self):
        payload = {
            'username': self.user,
            'password': self.pw
        }
        resp = self.sess.post(self.LOGIN_URL, data=payload)
        resp.raise_for_status()

    def fetch(self):
        # realiza login e busca a página
        self.login()
        r = self.sess.get(self.DATA_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')

        container = soup.select_one('#dps')
        if not container:
            raise RuntimeError("Container #dps não encontrado na página")

        events = container.select('.ciem_theme_event_inner')
        data = {}
        for e in events:
            text = e.get_text(strip=True)
            m = re.search(r"(006000\d+)", text)
            if m:
                key = m.group(1)
                data[key] = text
        return data

