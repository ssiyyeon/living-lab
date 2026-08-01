"""
situations.json 일회성 정리 스크립트.

배경: 초기 세션에서 수작업으로 PDF를 파싱할 때, "담당자" 필드에 실제 연락처 줄
다음에 이어지는 붙임 참고자료 표(무인민원발급기 설치장소 목록, 노숙인 숙박시설
현황, 임시주거시설 현황, 특수규격봉투 판매처 등)가 통째로 같이 들어가버렸다.
그 결과 일부 항목은 "담당자"가 100~500줄(=500명?)에 달해, 실무자에게 그대로
보여주면 오히려 못 쓰게 된다.

수정 방침: 담당자 줄은 "☎" 또는 전화번호 패턴을 포함한 줄만 남기고, 나머지는
삭제하지 않고 참고사항 맨 뒤로 옮긴다(요구사항 "빠짐없이 반영" 유지, 대신
담당자 필드는 실제 연락처만 깔끔하게 보이도록).

한 번 실행하면 끝나는 정리용 스크립트라 반복 실행해도 안전하게(idempotent)
동작하도록, 이미 정리된 상태면 아무것도 안 바꾼다.
"""

import json
import re
from pathlib import Path

SITUATIONS_PATH = Path(__file__).resolve().parent / "situations.json"

_CONTACT_PATTERN = re.compile(r"☎|01[0-9]-\d{3,4}-\d{4}|0\d{1,2}\)\s*\d{3,4}-\d{4}")


def is_contact_line(line: str) -> bool:
    return bool(_CONTACT_PATTERN.search(line))


def main():
    with open(SITUATIONS_PATH, encoding="utf-8") as f:
        situations = json.load(f)

    fixed = 0
    for s in situations:
        contacts = s.get("담당자", [])
        if len(contacts) <= 3:
            continue  # 이미 짧으면(정상 상태) 건드리지 않음

        real_contacts = [l for l in contacts if is_contact_line(l)]
        rest = [l for l in contacts if not is_contact_line(l)]
        if not rest:
            continue

        s["담당자"] = real_contacts
        s["참고사항"] = s.get("참고사항", []) + ["--- 붙임 참고자료 ---"] + rest
        fixed += 1
        print(f"정리: {s['부서']} - {s['민원요지']} | 담당자 {len(contacts)}줄 -> {len(real_contacts)}줄 "
              f"(참고사항으로 {len(rest)}줄 이동)")

    with open(SITUATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(situations, f, ensure_ascii=False, indent=2)
    print(f"\n{fixed}개 항목 정리 완료 -> {SITUATIONS_PATH}")


if __name__ == "__main__":
    main()
