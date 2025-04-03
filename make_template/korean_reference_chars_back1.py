# -*- coding: utf-8 -*-
# 이 파일은 템플릿 생성 및 기타 파이프라인 단계에서 사용될
# 기준 한글 문자 목록을 정의합니다.

#!/usr/bin/env python3
"""
Korean Reference Characters for DM-Font
Contains optimal Korean characters for use as reference in DM-Font training,
ensuring that every initial consonant (초성), medial vowel (중성),
and final consonant (종성, including 'None') appears at least once.
"""

# List of Korean characters ensuring minimal Jamo coverage (40 characters total)
korean_chars = [
    '깎', '값', '같', '곬', '곶', '넋', '늪', '닫', '닭', '됩', '땀', '뗌', '략', '몃',
    '밟', '볘', '뺐', '뽈', '솩', '쐐', '앉', '않', '얘', '얾', '엌', '옳', '읊', '죡',
    '쮜', '춰', '츄', '코', '퀭', '틔', '핀', '핥', '훟', '빛', '뭍'
]

# The following lists/dictionaries are removed as they became inconsistent
# after ensuring full Jamo coverage in the korean_chars list above.
# unicode_values = [...]
# char_unicode_pairs = [...]
# char_categories = {...}

if __name__ == "__main__":
    print(f"Total Korean reference characters: {len(korean_chars)}")
    print("\n== All Korean Characters (Minimal Jamo Coverage Set) ==")
    print(korean_chars) 