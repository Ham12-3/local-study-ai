from PySide6.QtWidgets import QLabel

from studyvault.ui.components.badges import Badge
from studyvault.ui.components.buttons import SecondaryButton
from studyvault.ui.components.card import Card
from studyvault.ui.components.empty_state import EmptyState
from studyvault.ui.components.progress import SlimProgress
from studyvault.ui.pages.base import Page


class WeakTopicsPage(Page):
    def refresh(self, repo) -> None:
        self.clear()
        topics = repo.weak_topics()
        if not topics:
            self.content.addWidget(EmptyState("No weak topics yet", "Wrong quiz answers will create local weak topic cards here."))
            return
        for topic in topics:
            card = Card()
            title = QLabel(topic.topic)
            title.setObjectName("SectionTitle")
            meta = QLabel(f"{topic.textbook_title} · Recommended pages: {topic.recommended_pages or 'Not set'}")
            meta.setObjectName("Muted")
            meta.setWordWrap(True)
            card.layout().addWidget(title)
            card.layout().addWidget(Badge(f"{topic.wrong_count} wrong answers", "warning"))
            card.layout().addWidget(meta)
            card.layout().addWidget(SlimProgress(topic.progress))
            card.layout().addWidget(SecondaryButton("Revise"))
            self.content.addWidget(card)

