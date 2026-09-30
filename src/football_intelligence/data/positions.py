"""Conservative positional groups; originals stay in lineup JSON."""


def position_group(name: str | None) -> str | None:
    if not name:
        return None
    n = name.lower().replace("centre", "center")
    if "goalkeeper" in n:
        return "GK"
    if "center back" in n or "central defender" in n:
        return "CB"
    if "back" in n:
        return "FB/WB"
    if "defensive midfield" in n:
        return "DM"
    if "attacking midfield" in n:
        return "AM"
    if "wing" in n or n in ("left midfield", "right midfield"):
        return "W"
    if "midfield" in n:
        return "CM"
    if "forward" in n or "striker" in n:
        return "ST"
    return None
