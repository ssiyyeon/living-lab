"""
Phase 6(README 참고) 실시간 피드백 루프의 최소 구현.

recommend()가 내놓은 추천에 대해 담당자가 "맞음/틀림"과(틀렸을 때는) 실제 처리부서를
한 줄로 남기면 append-only CSV에 쌓인다. 이 로그는:
1. 추천이 자주 틀리는 지점을 찾는 데 쓰고
2. 쌓이면 model/train_and_save.py 재학습 시 원본 민원 데이터에 합쳐 반영할 수 있다
   (특히 매뉴얼에도 없고 ML도 처음 보는 새로운 상황일수록 이 로그가 유일한 신호다).

사용 예:
    from app.recommend import recommend
    from app.feedback import save_feedback

    outcome = recommend("궁동에서 유기견을 발견했어요")
    save_feedback(text="궁동에서 유기견을 발견했어요", outcome=outcome, correct=True)

    # 추천이 틀렸거나 추천 자체가 없었던 경우
    save_feedback(
        text="철도 공사장 근처 소음 민원",
        outcome=outcome,
        correct=False,
        actual_dept="철도건설국(외부기관)",
        note="유성구청 소관 아님, 매뉴얼에도 없는 상황",
    )
"""

import csv
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDBACK_LOG_PATH = os.path.join(BASE_DIR, "analysis", "feedback_log.csv")

_FIELDS = ["시각", "민원내용", "출처", "추천부서_1순위", "정확여부", "실제부서", "메모"]


def save_feedback(
    text: str,
    outcome: dict,
    correct: bool,
    actual_dept: str = "",
    note: str = "",
) -> None:
    """recommend()가 반환한 outcome 하나에 대한 담당자 피드백을 한 줄 기록한다.

    - correct=True: 1순위 추천이 맞았다. actual_dept는 비워도 자동으로 1순위 부서로 채운다.
    - correct=False: 틀렸거나 추천 자체가 없었다. actual_dept에 실제 처리부서를 남겨야
      재학습 시 새 학습 데이터로 쓸 수 있다.
    """
    top1 = outcome["결과"][0]["부서"] if outcome["결과"] else ""
    row = {
        "시각": datetime.datetime.now().isoformat(timespec="seconds"),
        "민원내용": text,
        "출처": outcome["출처"],
        "추천부서_1순위": top1,
        "정확여부": "맞음" if correct else "틀림",
        "실제부서": actual_dept or (top1 if correct else ""),
        "메모": note,
    }

    os.makedirs(os.path.dirname(FEEDBACK_LOG_PATH), exist_ok=True)
    is_new = not os.path.exists(FEEDBACK_LOG_PATH)
    with open(FEEDBACK_LOG_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def load_feedback_log():
    """쌓인 피드백을 DataFrame으로 읽어온다 (분석·재학습용). 로그가 없으면 빈 DataFrame."""
    import pandas as pd

    if not os.path.exists(FEEDBACK_LOG_PATH):
        return pd.DataFrame(columns=_FIELDS)
    return pd.read_csv(FEEDBACK_LOG_PATH, encoding="utf-8-sig")
