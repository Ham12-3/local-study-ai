from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QHBoxLayout

from studyvault.services.runtime_manager import RECOMMENDED_MODEL
from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import PrimaryButton, SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.progress import SlimProgress
from studyvault.ui.components.setup_step import SetupStep
from studyvault.ui.pages.base import Page


class OnboardingPage(Page):
    auto_requested = Signal()
    check_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.progress = SlimProgress()
        self.message = QLabel("StudyVault is preparing private local AI on this computer.")
        self.message.setObjectName("Muted")
        self.message.setWordWrap(True)

    def refresh(self, runtime_state, busy: bool = False, detail: str | None = None) -> None:
        self.clear()
        hero = Card(elevated=True)
        title = QLabel("Set up private local AI")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "StudyVault prepares the local AI engine and starter model automatically, so the user does not "
            "need terminal commands, model names, or separate setup steps."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        hero.layout().addWidget(Badge("Local-first setup", "primary"))
        hero.layout().addWidget(title)
        hero.layout().addWidget(subtitle)
        hero.layout().addWidget(self.message)
        hero.layout().addWidget(self.progress)
        self.content.addWidget(hero)

        installed_state = "done" if runtime_state.installed else ("active" if busy else "pending")
        running_state = "done" if runtime_state.running else ("pending" if runtime_state.installed else "pending")
        model_state = "done" if runtime_state.models else ("pending" if runtime_state.running else "pending")
        if runtime_state.error and not busy:
            running_state = "error" if runtime_state.installed and not runtime_state.running else running_state

        self.content.addWidget(
            SetupStep(
                "Install local AI engine",
                "StudyVault downloads and opens the official Windows installer when the runtime is missing.",
                installed_state,
            )
        )
        self.content.addWidget(
            SetupStep(
                "Start local AI service",
                "The local API runs in the background and serves requests only on this computer.",
                running_state,
            )
        )
        self.content.addWidget(
            SetupStep(
                "Prepare study model",
                "A recommended study model is downloaded once, then reused offline.",
                model_state,
            )
        )

        actions = Card()
        row = QHBoxLayout()
        auto = PrimaryButton("Prepare now")
        check = SecondaryButton("Check again")
        auto.setEnabled(not busy and not runtime_state.ready)
        check.setEnabled(not busy)
        auto.clicked.connect(self.auto_requested.emit)
        check.clicked.connect(self.check_requested.emit)
        row.addWidget(auto)
        row.addWidget(check)
        row.addStretch()
        actions.layout().addLayout(row)

        advanced = QLabel(
            f"Advanced: StudyVault uses {RECOMMENDED_MODEL} as the fast starter model. "
            "Packaged builds can override this without changing the UI."
        )
        advanced.setObjectName("SmallMuted")
        advanced.setWordWrap(True)
        actions.layout().addWidget(advanced)
        if detail:
            note = QLabel(detail)
            note.setObjectName("Muted")
            note.setWordWrap(True)
            actions.layout().addWidget(note)
        self.content.addWidget(actions)

    def set_progress(self, value: int) -> None:
        self.progress.setValue(value)

    def set_status(self, text: str) -> None:
        self.message.setText(text)
