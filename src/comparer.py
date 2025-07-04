from utils import load_json, save_json

class DataComparer:
    SNAPSHOT_FILE = 'data/last_snapshot.json'

    def compare(self, new_data: dict):
        old = load_json(self.SNAPSHOT_FILE) or {}
        diffs = {}

        # entradas novas ou modificadas
        for k, v in new_data.items():
            if k not in old or old[k] != v:
                diffs[k] = {'old': old.get(k), 'new': v}

        # (opcional) detectar removidos:
        # for k in old:
        #     if k not in new_data:
        #         diffs[k] = {'old': old[k], 'new': None}

        save_json(self.SNAPSHOT_FILE, new_data)
        return diffs

