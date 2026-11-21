"""Iraqi state salary scale (Law 22 of 2008) used to check allowance rows."""
G = ["أولى", "ثانية", "ثالثة", "رابعة", "خامسة", "سادسة", "سابعة", "ثامنة", "تاسعة", "عاشرة"]
BASE = {1: 910000, 2: 723000, 3: 600000, 4: 509000, 5: 429000, 6: 362000, 7: 296000, 8: 260000, 9: 210000, 10: 170000}
INC = {1: 20000, 2: 17000, 3: 10000, 4: 8000, 5: 6000, 6: 6000, 7: 6000, 8: 3000, 9: 3000, 10: 3000}


def gnum(g):
    return G.index(g.replace("اولى", "أولى")) + 1


def basic(g, s):
    """Basic salary for grade g (name or number) at stage s; stages past 11 rise by the next grade's step."""
    n = gnum(g) if isinstance(g, str) else g
    s = int(s)
    if s <= 11:
        return BASE[n] + INC[n] * (s - 1)
    up = INC[n - 1] if n > 1 else INC[n]
    return BASE[n] + INC[n] * 10 + up * (s - 11)
