import regex as re
import unicodedata

import numpy as np
import sys
from Bio import Align
from pprint import pprint
np.set_printoptions(linewidth=np.inf, threshold=sys.maxsize)

ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
# ascii_to_wide.update({0x20: '\u3000', 0x2D: '\u2212'})  # space and minus
kata_hira = dict((0x30a1 + i, chr(0x3041 + i)) for i in range(0x56))
kansuu_to_ascii = dict([(ord('一'), '１'), (ord('二'), '２'), (ord('三'), '３'), (ord('四'), '４'), (ord('五'), '５'), (ord('六'), '６'), (ord('七'), '７'), (ord('八'), '８'), (ord('九'), '９'), (ord('◯'), '０') ,(ord('零'), '０'), (ord('十'), '１')])
allt = kata_hira | ascii_to_wide
# allt = kansuu_to_ascii | ascii_to_wide
def clean(s, normalize=True):
    # TODO(YM): check this doesn't catastrophically backtrack
    # 、。？ are mostlly correctly guessed by whisper
    # Idk which one is better, at least the ver that doesn't remove them can be adjusted a little more intelligently?
    r = r"(?![、。？])[\p{C}\p{M}\p{P}\p{S}\p{Z}\sーぁぃぅぇぉっゃゅょゎゕゖァィゥェォヵㇰヶㇱㇲッㇳㇴㇵㇶㇷㇷ゚ㇸㇹㇺャュョㇻㇼㇽㇾㇿヮ]+"
    # r = r"[\p{C}\p{M}\p{P}\p{S}\p{Z}\sーぁぃぅぇぉっゃゅょゎゕゖァィゥェォヵㇰヶㇱㇲッㇳㇴㇵㇶㇷㇷ゚ㇸㇹㇺャュョㇻㇼㇽㇾㇿヮ]+"
    s = re.sub(r, "", s.translate(kansuu_to_ascii).translate(allt))
    return unicodedata.normalize("NFKD", s) if normalize else s

def align_sub(coords, text, subs):
    current = [0, 0]
    pos, toff = np.array([0, 0]), 0
    p, gaps = np.array([0, 0]), np.array([0, 0])
    segments = []
    unused = []
    for i in range(coords.shape[1]):
        c = coords[:, i]
        isgap = 0 in (c - p)
        while current[1] < len(subs) and (pos[1] + len(subs[current[1]])) <= c[1]:
            pos[1] += len(subs[current[1]])
            if isgap: gaps += np.clip((pos - p)[::-1], 0, None)

            diff = len(subs[current[1]]) + gaps[1] - gaps[0]
            print(subs[current[1]], pos[0], i, c, diff, gaps[1], gaps[0])#, coords[:, i+1])

            if diff < len(subs[current[1]])//2:
                unused.append(subs[current[1]])

            segments.append([*current, toff, 0])
            pos[0] += diff
            toff += diff
            print(len(text[current[0]]), toff)
            while toff > len(text[current[0]]):
                toff -= len(text[current[0]])
                current[0] += 1
                segments.append([*current, 0, 0])
            segments.append([*current, toff, 0])

            current[1], gaps[...], p[:] = current[1]+1, 0, pos[:]

        if isgap: gaps += (c - p)[::-1]
        p = c

    pprint(unused)
    # pprint(segments)
    return segments

    # el = [0, 0]
    # pos, off = [0, 0], [0, 0]
    # idx = 0
    # segments = []
    # while el[1] < len(subs):
    #     segments.append([*el, *off])
    #     l = len(subs[el[1]])

    #     pend = pos[1] + l
    #     gap = [0, 0]
    #     eidx = idx
    #     while eidx < coords.shape[1] and pend > coords[1][eidx]:
    #         eidx += 1

    #     lc = np.copy(coords[:, max(idx-1, 0):eidx+1])
    #     print(idx, eidx)
    #     print(lc)
    #     lc[1, -1] = pend
    #     lc[1, 0] = pos[1]
    #     lc[0, 0] = pos[0]
    #     print(lc)

    #     for k in range(lc.shape[1]-1):
    #         for i in range(2):
    #             if lc[i, k] == lc[i, k+1]:
    #                 f, s = lc[1-i, k], lc[1-i, k+1]
    #                 gap[i] += s - f
    #     print(gap)

    #     idx = eidx
    #     off[1] = 0
    #     el[1] += 1
    #     pos[1] += l

    #     advance = l + gap[1] - gap[0]
    #     if advance == 0:
    #         continue
    #     # print(advance)
    #     while el[0] < len(text) and (advance - (len(text[el[0]]) - off[0])) > 0:
    #         advance -= len(text[el[0]]) - off[0]
    #         off[0] = 0
    #         el[0] += 1
    #         # segments.append([*el, *off])
    #     off[0] += advance
    #     pos[0] += l + gap[1] - gap[0]
    # pprint(segments)
    # return segments


# def align_sub(coords, *arrs):
#     pos, off = [0, 0], [0, 0]
#     el, idx = [0, 0], 0

#     segments = []
#     while el[0] < len(arrs[0]) and el[1] < len(arrs[1]):
#         segments.append([*el, *off])
#         i = 0 if (len(arrs[0][el[0]])-off[0]) < (len(arrs[1][el[1]])-off[1]) else 1
#         smaller = len(arrs[i][el[i]]) - off[i]

#         gap = [0, 0]
#         while (idx+1) < coords.shape[1] and pos[i] + smaller > coords[i][idx]:
#             idx += 1
#             if coords[i, idx] == coords[i, idx-1]: gap[i] += coords[1-i, idx] - coords[1-i, idx-1]
#             if coords[1-i, idx] == coords[1-i, idx-1]: gap[1-i] += coords[i, idx] - coords[i, idx-1]

#         off[i] = 0
#         el[i] += 1
#         pos[i] += smaller

#         advance = smaller + gap[i] - gap[1-i]
#         while el[1-i] < len(arrs[1-i]) and (advance - (len(arrs[1-i][el[1-i]]) - off[1-i])) > 0:
#             advance -= len(arrs[1-i][el[1-i]]) - off[1-i]
#             off[1-i] = 0
#             el[1-i] += 1
#             segments.append([*el, *off])
#         off[1-i] += advance
#         pos[1-i] += smaller + gap[i] - gap[1-i]

#     return segments

# # Here be dragons
# def find(segments, start, end):
#     for i, v in enumerate(segments):
#         if v[1] == start:
#             print(v[1], start)
#             break
#     for j, v in enumerate(segments[i:]): # First end
#         if v[1] == end:
#             break
#     # for k, v in enumerate(segments[i+j:]): # Last end
#     #     if v[1] != end:
#     #         break
#     k = 1
#     return i, i+j+k

# # Really best effort crap
# def replace(segments, text, replacement):
#     start, end = replacement[0][1], replacement[-1][1]
#     start, end = find(segments, start, end)
#     print(start, end)
#     h = type(segments[start][0]) == str
#     while start < len(segments) and type(segments[start][0]) == str:
#         start += 1

#     if not h:
#         if segments[start][2] >= len(text[segments[start][0]])//2:
#             while start < len(segments) and segments[start][0] == segments[start-1][0]:
#                 segments[start][1] = segments[start-1][1]
#                 start += 1
#         else:
#             while start > 0 and segments[start][0] == segments[start-1][0]:
#                 start -= 1

#     for i in segments[start:end]:
#         i[1] = segments[end][1]
#     segments[start:start] = replacement

def fix(original, edited, segments):
    s, e = 0, 0
    while e < len(segments):
        e += 1
        if e == len(segments) or segments[s][0] != segments[e][0]:
            if segments[s][0] >= len(original):
                break
            orig, cl = original[segments[s][0]].translate(allt), edited[segments[s][0]]
            i, j, jj = 0, 0, s
            while i < len(orig) and j < len(cl) and jj < e:
                while jj < e and j >= segments[jj][2]:
                    segments[jj][2] = i
                    jj += 1
                if orig[i] == cl[j]:
                    j += 1
                i += 1
            while jj < e:
                segments[jj][2] = i
                jj += 1
            s = e

def align(model, transcript, text, prepend, append):
    transcript_str = [i['text'] for i in transcript['segments']]
    transcript_str_clean = [clean(i, normalize=False) for i in transcript_str]
    transcript_str_joined = ''.join(transcript_str_clean)

    aligner = Align.PairwiseAligner(scoring=None, mode='global', match_score=1, open_gap_score=-1, mismatch_score=-1, extend_gap_score=-0.7)
    def inner(text_str):
        text_str_clean = [clean(i, normalize=False) for i in text_str]
        text_str_joined = ''.join(text_str_clean)

        if not len(text_str_joined) or not len(transcript_str_joined): return []
        alignment = aligner.align(text_str_joined, transcript_str_joined)[0]
        print(alignment.__str__().replace('-', "ー"))
        coords = alignment.coordinates
        print(coords)

        segments = align_sub(coords, text_str_clean, transcript_str_clean)
        fix(text_str, text_str_clean, segments)
        # fix_punc(text_str, segments, prepend, append)
        return segments

    references = {k.element.attrs['id']:k for i in text for k in i.references} # Filter out dups

    text_str = [i.text() for i in text]
    segments = inner(text_str)
    # pprint(segments)
    # for k, v in references.items():
    #     ref_segments = inner([v.text()], fix3=True)
    #     pprint(ref_segments)
    #     for i in range(len(ref_segments)):
    #         ref_segments[i][0] = k
    #     replace(segments, text_str, ref_segments)

    return segments, references