from typing import Optional, TYPE_CHECKING

from helpers.staff_helpers import calc_y

if TYPE_CHECKING:
    from models.staff import Staff


def find_pitch(staff: 'Staff', x: int, y: int) -> Optional[int]:
    line_vals = []
    for line in staff.lines:
        line_vals.append(calc_y(line, x))

    if y < min(line_vals):
#        print(f'too high: {y}')
        return None
    elif y > max(line_vals):
#        print(f'too low: {y}')
        return None
    else:
        i = 0
        found = False
        while not found:
            i = i + 1
            found = (y < line_vals[i])

        upper = line_vals[i - 1]
        lower = line_vals[i]

        if y in range(int(lower - staff.dist / 4) + 1, lower + 1):
            pitch = line_vals.index(lower) * 2
        elif y in range(upper, int(upper + staff.dist / 4)):
            pitch = line_vals.index(upper) * 2
        else:
            pitch = line_vals.index(lower) * 2 - 1

    return pitch
