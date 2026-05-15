from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.pages.base import Page


class SettingsPage(Page):
    def refresh(
        self,
        repo,
        ollama_status,
        runtime_state,
        runtime_busy,
        refresh_callback,
        reset_callback,
        runtime_action_callback,
    ) -> None:
        self.clear()
        connection = Card(elevated=True)
        header = QHBoxLayout()
        title = QLabel("Local AI")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(Badge("Online" if ollama_status.running else "Offline", "success" if ollama_status.running else "error"))
        connection.layout().addLayout(header)

        status = QLabel(self._runtime_message(runtime_state))
        status.setObjectName("Muted")
        status.setWordWrap(True)
        connection.layout().addWidget(status)
        if runtime_busy:
            busy = Badge("Setup running", "primary")
            connection.layout().addWidget(busy)

        actions = QHBoxLayout()
        install = PrimaryButton("Install Local AI")
        start = PrimaryButton("Start Local AI")
        pull = PrimaryButton("Download Study Model")
        refresh = SecondaryButton("Refresh models")
        install.setEnabled(not runtime_busy and not runtime_state.installed)
        start.setEnabled(not runtime_busy and runtime_state.installed and not runtime_state.running)
        pull.setEnabled(not runtime_busy and runtime_state.running and not bool(runtime_state.models))
        refresh.setEnabled(not runtime_busy)
        install.clicked.connect(lambda: runtime_action_callback("install"))
        start.clicked.connect(lambda: runtime_action_callback("start"))
        pull.clicked.connect(lambda: runtime_action_callback("pull_model"))
        refresh.clicked.connect(refresh_callback)
        actions.addWidget(install)
        actions.addWidget(start)
        actions.addWidget(pull)
        actions.addWidget(refresh)
        actions.addStretch()
        connection.layout().addLayout(actions)

        chat = QComboBox()
        embed = QComboBox()
        if ollama_status.models:
            chat.addItems(ollama_status.models)
            embed.addItems(ollama_status.models)
        else:
            chat.addItem("No local models found")
            embed.addItem("No local models found")
            chat.setEnabled(False)
            embed.setEnabled(False)
        connection.layout().addWidget(QLabel("Chat model"))
        connection.layout().addWidget(chat)
        connection.layout().addWidget(QLabel("Embedding model"))
        connection.layout().addWidget(embed)
        self.content.addWidget(connection)

        local = Card()
        title = QLabel("Local data")
        title.setObjectName("SectionTitle")
        path = QLabel(str(repo.data_dir))
        path.setObjectName("Muted")
        path.setWordWrap(True)
        privacy = QLabel("Textbooks, notes, flashcards, quiz history, and weak topics stay on this device.")
        privacy.setObjectName("Muted")
        privacy.setWordWrap(True)
        reset = DangerButton("Reset local cache")
        reset.clicked.connect(lambda: self._confirm_reset(reset_callback))
        local.layout().addWidget(title)
        local.layout().addWidget(path)
        local.layout().addWidget(QLabel("Privacy"))
        local.layout().addWidget(privacy)
        local.layout().addWidget(reset)
        self.content.addWidget(local)

    def _runtime_message(self, runtime_state) -> str:
        if runtime_state.installed and runtime_state.running and runtime_state.models:
            return "Local AI is ready. Model choices below come from the local Ollama runtime."
        if runtime_state.error:
            return runtime_state.error
        if not runtime_state.installed:
            return "Ollama is not installed. StudyVault can download and open the official Windows installer with your permission."
        if not runtime_state.running:
            return "Ollama is installed but not running. StudyVault can start it in the background."
        if not runtime_state.models:
            return "Ollama is running, but no local models are installed yet."
        return runtime_state.error or "Local AI status is unknown."

    def _confirm_reset(self, reset_callback) -> None:
        result = QMessageBox.question(
            self,
            "Reset local cache",
            "Reset generated notes, flashcards, quiz attempts, and weak topics? Imported textbooks will remain.",
        )
        if result == QMessageBox.StandardButton.Yes:
            reset_callback()
