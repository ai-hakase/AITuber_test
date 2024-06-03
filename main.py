from ui import UI
import os
import asyncio


if __name__ == "__main__":
    ui = UI()
    print(os.path.abspath("start.py"))
    # asyncio.run(ui.launch())
    asyncio.run(ui.create_ui())

