from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


RESULT_HEADERS = {
    "로그온 / 로그오프 활동": [
        "로그인 기록",
        "로그온 실패 기록",
        "마지막 로그인 기록",
        "시스템 ON / OFF"
    ],
    "프로그램 실행 활동": [
        "프로그램 실행 기록",
        "실행한 프로그램 목록",
        "명령어 실행 기록"
    ],
    "파일 및 폴더 접근 활동": [
        "파일 열람 기록",
        "삭제한 파일 목록"
    ],
    "인터넷 사용 활동": [
        "네트워크 설정 기록",
        "사이트 접속 기록",
        "다운로드 목록"
    ],
    "외부 저장 장치 연결 활동": [
        "USB 장치 목록",
        "드라이브 목록",
        "연결 시간"
    ],
    "프로그램 변경 활동": [
        "설치 기록",
        "제거 기록"
    ]
}

class ArtifactModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        for parent in RESULT_HEADERS:
            item = QStandardItem(parent)
            for child in RESULT_HEADERS[parent]:
                item.appendRow(QStandardItem(child))
            self.appendRow(item)