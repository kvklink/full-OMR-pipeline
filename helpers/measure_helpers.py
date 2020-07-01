from typing import List, Optional, TYPE_CHECKING

from models.staff_objects import Barline
from models.measure import Measure

if TYPE_CHECKING:
    from models.staff import Staff
    from models.template import Template


def split_measures(barlines: List['Barline'], staff: 'Staff'):  # barlines sorted on x
    x1, x2 = (0, 0)
    measures = []
    for i in range(0, len(barlines) + 1):
        if i == len(barlines):
            x2 = staff.lines[0][2]
        else:
            x2 = barlines[i].x
        measures.append(Measure(staff, i, x1, x2))
        x1 = x2
    return measures


def find_measure(measures: List['Measure'], x: int) -> Optional['Measure']:
    for measure in measures:
        if measure.start < x < measure.end:
            return measure
    return None


def select_barlines(measure_locations: (int, int), staff: 'Staff', template: 'Template') -> List['Barline']:
    bar_h = int(template.height_units * staff.dist)
    bar_w = int(bar_h * template.w / template.h)

    barlines = []
    measure_locations = sorted(measure_locations, key=lambda x: x[0])
    for meas in measure_locations:
        if abs(staff.lines[4][1] - meas[1]) < 3 and abs(staff.lines[8][1] - (meas[1] + bar_h)) < 3:
            barlines.append(Barline(int(meas[0] + bar_w / 2), meas[1], meas[1] + bar_h))

    return barlines
