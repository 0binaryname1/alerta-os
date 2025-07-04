import tkinter as tk
from scraper import SchedulerScraper
from comparer import DataComparer

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Alerta de Alteração na Carteira de Ordens de Serviço")
        self.root.geometry("800x600")

        # Frame principal
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill='both')

        # Botão para verificar alterações
        self.btn_check = tk.Button(
            self.frame,
            text="Verificar Alterações",
            command=self.check_changes
        )
        self.btn_check.pack(pady=20)

        # Área de log
        self.log = tk.Text(self.frame, height=20)
        self.log.pack(expand=True, fill='both')

        # Rodapé
        rodape = tk.Label(
            self.root,
            text="Made by Almeida, Esdras 07/2025",
            anchor='e'
        )
        rodape.pack(fill='x', side='bottom')

        # Instâncias de scraper e comparador
        self.scraper = SchedulerScraper()
        self.comparer = DataComparer()

    def check_changes(self):
        try:
            new_data = self.scraper.fetch()
            diffs = self.comparer.compare(new_data)
            if diffs:
                self.log.insert('end', "Alterações detectadas:\n")
                for k, v in diffs.items():
                    self.log.insert('end', f"{k}:\n  Antigo: {v['old']}\n  Novo:   {v['new']}\n\n")
                # aqui você pode tocar um som ou exibir uma popup
            else:
                self.log.insert('end', "Nenhuma alteração encontrada.\n\n")
        except Exception as e:
            self.log.insert('end', f"Erro ao verificar: {e}\n\n")

    def run(self):
        self.root.mainloop()

