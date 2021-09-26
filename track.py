from util import *


class Drop:
    def __init__(self):
        self.id = 0
        self.detect_rect = None     # detected rect by model
        self.droplet_rect = None    # rect for only droplet
        self.count_rect = None      # rect for counting processing
        self.crystal_rects = []     # crystal rect

        self.ndetected = 1          # detected number of droplet
        self.ncrystals = 0          # detected number of crystal
        self.ndisapper = 0          # undetected number of droplet

        self.droplet_areas = []     # area list of droplet of so far
        self.droplet_wdths = []     # width list of droplet of so far
        self.droplet_hghts = []     # height list of droplet of so far
        self.status = -1            # -1 : no counted, 0 : counting, 1 : counted
        self.final_area = 0         # final area of droplet
        self.final_wdth = 0         # final width of droplet
        self.final_hght = 0         # final height of droplet

        self.start_cnt = False

    def get_area(self):
        dd = (self.droplet_rect.w - self.droplet_rect.h) if (self.droplet_rect.w - self.droplet_rect.h > 0) else 0
        return int(self.droplet_rect.h ** 2 * 3.14 / 4 + dd * self.droplet_rect.h)

    def get_final_area(self):
        if len(self.droplet_areas) > 0:
            self.final_area = int(sum(self.droplet_areas) / len(self.droplet_areas))

    def get_final_width(self):
        if len(self.droplet_wdths) > 0:
            self.final_wdth = int(sum(self.droplet_wdths) / len(self.droplet_wdths))

    def get_final_height(self):
        if len(self.droplet_hghts) > 0:
            self.final_hght = int(sum(self.droplet_hghts) / len(self.droplet_hghts))


class Tracker:
    def __init__(self):
        self.drops = []
        self.last_id = 0

    def update(self, drops):
        if self.drops.__len__() < 1:
            self.drops = drops
            return []

        # find matched drops
        updated_old_drops = []
        updated_new_drops = []
        removed_drops = []
        if drops.__len__() < 1:
            for od in self.drops:
                if od.ndisapper == 1:
                    removed_drops.append(od)
                else:
                    od.ndisapper = 1
                    updated_old_drops.append(od)
            self.drops = updated_old_drops
            return removed_drops
        for i, od in enumerate(self.drops):
            overlaps = []
            for j, nd in enumerate(drops):
                ret = isoverlap(od.count_rect, nd.count_rect)
                if ret:
                    dist = od.droplet_rect.dist(nd.count_rect)
                    overlaps.append(dist)
                else:
                    overlaps.append(10000)

            minval = min(overlaps)
            minidx = overlaps.index(minval)

            if minval < 10000:
                # update drop object
                od.detect_rect = drops[minidx].detect_rect
                od.droplet_rect = drops[minidx].droplet_rect
                od.count_rect = drops[minidx].count_rect
                od.crystal_rects = drops[minidx].crystal_rects

                od.ndetected += 1
                od.ncrystals += drops[minidx].ncrystals

                od.droplet_areas.append(drops[minidx].get_area())  # area list of droplet of so far
                od.droplet_wdths.append(drops[minidx].droplet_rect.w)  # area list of droplet of so far
                od.droplet_hghts.append(drops[minidx].droplet_rect.h)  # area list of droplet of so far

                updated_old_drops.append(od)
                updated_new_drops.append(drops[minidx])

        for od in self.drops:
            if od not in updated_old_drops:
                if od.ndisapper < 1:
                    od.ndisapper = 1
                    updated_old_drops.append(od)
                else:
                    removed_drops.append(od)

        self.drops = updated_old_drops

        for nd in drops:
            if nd not in updated_new_drops:
                self.drops.append(nd)

        return removed_drops

    def check(self):
        pass
