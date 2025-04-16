# menu_manager.py
class MenuManager:
    @staticmethod
    def main_menu(data):
        return data.get("main_menu", [])

    @staticmethod
    def topup_menu(data):
        topups = data.get("topups", [])
        buttons = [topups[i:i + 2] for i in range(0, len(topups), 2)]
        buttons.append(["Available balance", "Back ↩️"])
        return buttons