#!/usr/bin/env python3

import random as rnd
from abc import ABC, abstractmethod


class RandomSearchBase(ABC):
    def __init__(self, alloc_size, m=100, r=0.98, g=1000, max_id=2047):
        self._m = m
        self._r = r
        self._g = g
        self._alloc_size = alloc_size
        self._in_use_ids = []
        self._max_id = max_id
        self._candidate_counter = 0

    @property
    def alloc_size(self):
        """Size of allocations"""
        return self._alloc_size

    @alloc_size.setter
    def alloc_size(self, alloc_size):
        self._alloc_size = alloc_size

    @property
    def fst_sequence(self):
        """sequence for the first allocation"""
        return f"fst {self._alloc_size}"

    @property
    def snd_sequence(self):
        """sequence for the second allocation"""
        return f"snd {self._alloc_size}"

    @property
    def m(self):
        """maximum candidate size"""
        return self._m

    @m.setter
    def m(self):
        self._m = m

    @property
    def r(self):
        """allocation-free ratio (0<r<=1)"""
        return self._r

    @r.setter
    def r(self):
        self._r = r

    @property
    def g(self):
        """number of candidates to generate"""
        return self._g

    @g.setter
    def g(self):
        self._g = g

    @abstractmethod
    def append_alloc_seq(self, cand):
        """Add an allocation sequence, consisting of one or multiple instructions"""
        pass

    @abstractmethod
    def append_free_seq(self, cand):
        """Add a free sequence, consisting of one or multiple instructions"""
        pass

    def _remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix) :]
        return text  # or whatever

    def construct_candidate(self):
        """Construct a candidate"""
        # print(f"[~] Constructing candidate {self._candidate_counter}")
        self._candidate_counter += 1
        cand = ""
        len = rnd.randint(1, self._m)
        fstIdx = rnd.randint(0, len - 1)
        for i in range(len):
            if i == fstIdx:
                cand = "\n".join([cand, self.fst_sequence])
            elif rnd.random() <= self._r:
                cand = self.append_alloc_seq(cand)
            else:
                cand = self.append_free_seq(cand)
        cand = "\n".join([cand, self.snd_sequence])
        self._in_use_ids = []
        return self._remove_prefix(cand, "\n") + "\n"

    def create_batch(self):
        """Create a list of g candidates"""
        return [self.construct_candidate() for _ in range(self._g)]


class RandomSearchSimple(RandomSearchBase):
    def append_free_seq(self, cand):
        """Frees a random object. If none present, allocate"""
        if not self._in_use_ids:
            # redirect to alloc, as there is nothing to free
            return self.append_alloc_seq(cand)
        free_id = rnd.choice(self._in_use_ids)
        cand = "\n".join([cand, f"kfree {free_id}"])
        self._in_use_ids.remove(free_id)
        return cand

    def append_alloc_seq(self, cand):
        """Allocates a new object"""
        if len(self._in_use_ids) == self._max_id:
            # We cannot allocate more objects, so we simply do nothing
            return cand
        ids = [x for x in range(self._max_id) if x not in self._in_use_ids]
        alloc_id = rnd.choice(ids)
        cand = "\n".join([cand, f"kmalloc {self._alloc_size} {alloc_id}"])
        self._in_use_ids.append(alloc_id)
        return cand


class RandomSearchNoise(RandomSearchSimple):
    def __init__(self, alloc_size, m=100, r=0.98, g=1000, max_id=2047, noise=1):
        super().__init__(alloc_size, m, r, g, max_id)
        self._noise = noise

    @property
    def fst_sequence(self):
        """sequence for the first allocation"""
        fst = ""
        for _ in range(self._noise):
            ids = [x for x in range(self._max_id) if x not in self._in_use_ids]
            alloc_id = rnd.choice(ids)
            fst = "\n".join([fst, f"kmalloc {self._alloc_size} {alloc_id}"])
            self._in_use_ids.append(alloc_id)
        fst = "\n".join([fst, f"fst {self._alloc_size}"])
        for _ in range(self._noise):
            ids = [x for x in range(self._max_id) if x not in self._in_use_ids]
            alloc_id = rnd.choice(ids)
            fst = "\n".join([fst, f"kmalloc {self._alloc_size} {alloc_id}"])
            self._in_use_ids.append(alloc_id)
        return self._remove_prefix(fst, "\n")


class RandomSearchNoiseCantBeFreed(RandomSearchSimple):
    def __init__(self, alloc_size, m=100, r=0.98, g=1000, max_id=2000, noise=1):
        super().__init__(alloc_size, m, r, g, max_id)
        self._noise = noise

    def append_free_seq(self, cand):
        """Frees a random object. If none present, allocate"""
        freeable_ids = list(filter(lambda id: id < self._max_id, self._in_use_ids))
        if not freeable_ids:
            # redirect to alloc, as there is nothing to free
            return self.append_alloc_seq(cand)
        free_id = rnd.choice(freeable_ids)
        cand = "\n".join([cand, f"kfree {free_id}"])
        self._in_use_ids.remove(free_id)
        return cand

    @property
    def fst_sequence(self):
        """sequence for the first allocation"""
        fst = ""
        for _ in range(self._noise):
            ids = [x for x in range(self._max_id, 2048) if x not in self._in_use_ids]
            alloc_id = rnd.choice(ids)
            fst = "\n".join([fst, f"kmalloc {self._alloc_size} {alloc_id}"])
            self._in_use_ids.append(alloc_id)
        fst = "\n".join([fst, f"fst {self._alloc_size}"])
        for _ in range(self._noise):
            ids = [x for x in range(self._max_id, 2048) if x not in self._in_use_ids]
            alloc_id = rnd.choice(ids)
            fst = "\n".join([fst, f"kmalloc {self._alloc_size} {alloc_id}"])
            self._in_use_ids.append(alloc_id)
        return self._remove_prefix(fst, "\n")


if __name__ == "__main__":
    # sample_size = 50
    max_cand_size = 15
    sample_size = 200
    # Searcher = RandomSearchSimple(1024, r=0.98,g=sample_size, m=max_cand_size)
    Searcher = RandomSearchNoiseCantBeFreed(
        256, r=0.5, g=sample_size, m=max_cand_size, noise=3
    )
    candidates = Searcher.create_batch()
    for i in range(sample_size):
        with open(f"./ins/{i}", "w") as f:
            f.write(candidates[i])
