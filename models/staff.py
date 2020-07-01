from typing import Optional, List

import helpers.staff_helpers as helper
import models.measure as measure_model


class Staff:
    def __init__(self, img_bar):
        self.image = img_bar
        first_lines = helper.detect_staff_lines(img_bar)
        self.dist = helper.calc_avg_distance(first_lines)
        self.lines = sorted(
            helper.calc_higher_lines(helper.calc_lower_lines(first_lines, self.dist, img_bar.shape[1]), self.dist,
                              img_bar.shape[1]), key=lambda x: x[1])
        self.divisions = 12
        self.nr_timewise = float('NaN')
        self.nr_instrument = float('NaN')
        self.measures: Optional[List[measure_model.Measure]] = None

    def set_measures(self, measures: List[measure_model.Measure]):
        self.measures = measures

    def set_bar_nrs(self, nr_timewise, nr_instrument):
        # moet dan voor het splitsen naar maten gedaan worden
        self.nr_timewise = nr_timewise
        self.nr_instrument = nr_instrument

    def set_divisions(self, div):
        self.divisions = div
