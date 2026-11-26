"""Cliente de prueba que acciona la interfaz real de Streamlit (AppTest)."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

class Chat:
    def __init__(self, root=None, timeout=45):
        self.at = AppTest.from_file(str(Path(root or Path.cwd())/"app.py"), default_timeout=timeout).run()
        self.check()

    def check(self):
        if self.at.exception:
            raise AssertionError("Excepción visible en Streamlit: " + self.at.exception[0].message)
        return self

    @property
    def state(self):
        return self.at.session_state["nexo"]

    @property
    def last(self):
        return self.state["messages"][-1]

    def say(self, text):
        self.at.chat_input[0].set_value(text).run()
        return self.check()

    def click(self, label):
        choices = [b for b in self.at.button if b.label == label]
        assert choices, "Falta el botón " + label
        choices[0].click().run()
        return self.check()

