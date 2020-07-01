from typing import Optional

import helpers.staff_helpers as staff_helpers
import models.staff as staff_model


def find_pitch(staff: staff_model.Staff, x: int, y: int) -> Optional[int]:
    line_vals = []
    for line in staff.lines:
        line_vals.append(staff_helpers.calc_y(line, x))

    if y < min(line_vals):
        print(f'too high: {y}')
        return None
    elif y > max(line_vals):
        print(f'too low: {y}')
        return None
    else:
        i = 0
        found = False
        while not found:
            i = i + 1
            found = (y < line_vals[i])

        s = line_vals[i - 1]
        e = line_vals[i]

        if y in range(int(e - staff.dist / 4) + 1, e + 1):
            pitch = line_vals.index(e) * 2
        elif y in range(s, int(s + staff.dist / 4)):
            pitch = line_vals.index(s) * 2
        else:
            pitch = line_vals.index(e) * 2 - 1

    return pitch
