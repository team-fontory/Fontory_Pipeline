# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Korean Reference Characters for DM-Font
Contains a specific set of Korean characters provided by the user.
"""

korean_chars = [
    # 종성이 없는 글자 (초성 + 중성) ㄱ, ㄲ, ㄴ, ㄷ, ㄸ, ㄹ, ㅁ, ㅂ, ㅃ, ㅅ, ㅆ, ㅇ, ㅈ, ㅉ, ㅊ, ㅋ, ㅌ, ㅍ, ㅎ
    "가", "깨", "냐", "댸", "떠", "레", "며", "볘", "뽀", "솨",
    "쐐", "외", "죠", "쭈", "춰", "퀘", "튀", "퓨", "흐",

    # 종성이 있는 글자 (초성 + 중성 + 종성)
    # 종성 순서 (인덱스 1~27): ㄱ, ㄲ, ㄳ, ㄴ, ㄵ, ㄶ, ㄷ, ㄹ,
    #  ㄺ, ㄻ, ㄼ, ㄽ, ㄾ, ㄿ, ㅀ, ㅁ, ㅂ, ㅄ, ㅅ, ㅆ,
    #  ㅇ, ㅈ, ㅊ, ㅋ, ㅌ, ㅍ, ㅎ
    "긕", "닊", "닧", "낀", "랹", "먢", "떧", "벨", "멹", "셺",
    "옯", "좘", "괥", "굂", "굟", "뿜", "궙", "궶", "큇", "큤",
    "씅", "틪", "찣", "퍸", "혵", "괖", "괳", "괴", "풔", "궤"
]

if __name__ == "__main__":
    print(f"Total Korean reference characters: {len(korean_chars)}")
    print("\n== All Korean Characters (User Provided Set) ==")
    # Print characters in a more readable format
    chars_per_line = 10
    for i in range(0, len(korean_chars), chars_per_line):
        print(", ".join(f"'{c}'" for c in korean_chars[i:i+chars_per_line])) 