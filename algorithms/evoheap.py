from deap import base, creator, tools
import random as rnd
import os, sys
from pprint import pprint
from abc import ABC, abstractmethod
from argparse import ArgumentParser

TYPE_MASK = 0xFF000000000000000000000000000000
TYPE_SHIFT = 120
REP_MASK = 0x00FFFF00000000000000000000000000
REP_SHIFT = 104
SIZE_GROUP_MASK = 0x000000FF000000000000000000000000
SIZE_GROUP_SHIFT = 96
SUB_GROUP_MASK = 0x00000000FF0000000000000000000000
SUB_GROUP_SHIFT = 88
SELECTOR_MASK = 0x0000000000FFFFFF0000000000000000
SELECTOR_SHIFT = 64
ID_MASK = 0x0000000000000000FFFFFFFFFFFFFFFF
ID_SHIFT = 0

ALLOC_T = 0x00
FREE_T = 0x01
FST_T = 0x02
SND_T = 0x03
ALLOC_LOOP_T = 0x04

MAX_ALLOC_ID = 2**64 - 1
WRONG_ORDER = 2**64 - 1
MAX_FITNESS = 2**64


class EvoHeap(ABC):
    def __init__(
        self,
        types,
        groups,
        pmutate=0.9,
        pmate=0.1,
        max_mutations=5,
        max_init_length=15,
        alloc_free_ratio=0.9,
        alloc_loop_enabled=False,
        spray_min=5,
        spray_max=15,
        pmutate_classic=0.7,
        pmutate_spray=0.1,
        pmutate_hole_spray=0.1,
        pmutate_shorten=0.1,
        elitism_frac=0.5,
        lamb=200,
        mu=200,
        target_dist=-96,
        max_allocs=None,
        fst_allocs=None,
        snd_allocs=None,
        distances=[],
        population=[],
    ):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        self._toolbox = base.Toolbox()

        # self._toolbox.register("individual", tools.initRepeat, creator.Individual, self._create_directive, 10)
        self._toolbox.register("individual", self._create_individual)
        self._toolbox.register(
            "population", tools.initRepeat, list, self._toolbox.individual
        )
        self._toolbox.register("evaluate", self._evaluate)
        self._toolbox.register("mutate", self._mutate)
        self._toolbox.register("select", self._select)
        self._toolbox.register("mate", self._mate)
        self._types = types  # Types that are available (At least alloc, free, fst, snd)
        self._groups = groups  # Dictionary that describes the different primitives available to the programm, divided in groups/subgroups. Also contain group probabilities
        self._pmutate = pmutate  # Mutation Probability
        self._pmate = pmate  # Crossover probability
        self._max_mutations = (
            max_mutations  # Maximum number of mutations per individual
        )
        self._max_init_length = (
            max_init_length  # Maximum length of an individual when it is first created
        )
        self._population = [
            creator.Individual(ind) for ind in population
        ]  # The population. Can either be empty, in which case it will be generated, or can be filled from previous generation
        self._alloc_free_ratio = (
            alloc_free_ratio  # Ratio of allocs/free on initialisation of population
        )
        self._alloc_loop_enabled = alloc_loop_enabled  # Decide if the "allocate in loop" type is available. For now it will be disabled, as defragmenting already happened. Could maybe be a default start when starting without defragement, but seems unlikely
        self._spray_min = spray_min
        self._spray_max = spray_max
        self._pmutate_classic = pmutate_classic
        self._pmutate_spray = pmutate_spray
        self._pmutate_hole_spray = pmutate_hole_spray
        self._pmutate_shorten = pmutate_shorten
        self._e = elitism_frac
        self._mu = mu
        self._lambda = lamb
        self._distances = distances
        self._target_dist = target_dist
        # Maximum number of allocs that should be present at the same time
        self._max_allocs = max_allocs
        # number of allocs fst performs
        self._fst_allocs = fst_allocs
        # number of allocs snd performs
        self._snd_allocs = snd_allocs

    def _set_attribute(self, dir, value, mask):
        """Set an attribute of a directive"""
        shift = (mask & ~(mask - 1)).bit_length() - 1
        dir &= ~mask
        dir |= value << shift
        return dir

    def _get_attribute(self, dir, mask):
        """Get an attribute of a directive"""
        shift = (mask & ~(mask - 1)).bit_length() - 1
        tmp = dir & mask
        return tmp >> shift

    def _get_freeable_ids(self, ind, position):
        """Get all ids that can be freed on a specified directive index. Will also discard those IDs which will already be freed later"""
        assert position < len(ind)
        ids = []
        for i, dir in enumerate(ind):
            if self._get_attribute(dir, TYPE_MASK) == ALLOC_T and i < position:
                ids.append(self._get_attribute(dir, ID_MASK))
            elif (
                self._get_attribute(dir, TYPE_MASK) == FREE_T
                and self._get_attribute(dir, ID_MASK) in ids
            ):
                ids.remove(self._get_attribute(dir, ID_MASK))
        return ids

    def _mutate(self, ind):
        """Main Mutation function. Will probabilistically select mutation methods and apply them to ind."""
        for i in range(self._max_mutations):
            r = rnd.random()
            if r < self._pmutate_classic:
                # print("Mutate Classic")
                ind = self._mutate_classic(ind)
            elif r < self._pmutate_classic + self._pmutate_spray:
                # print("Mutate Spray")
                ind = self._mutate_spray(ind)
            elif (
                r
                < self._pmutate_classic + self._pmutate_spray + self._pmutate_hole_spray
            ):
                # print("Mutate hole_spray")
                ind = self._mutate_hole_spray(ind)
            else:
                # print("Mutate Shorten")
                ind = self._mutate_shorten(ind)
            if rnd.random() >= self._pmutate:
                break
        return ind

    def _mutate_classic(self, ind):
        """Mutate an individual. Will mutate one or more directives, either changing their type or their behaviour"""
        if len(ind) == 0:  # If the individual is empty, create a random new one
            return self._create_individual()
        elif len(ind) == 1:
            directives = [0]
        else:
            n_mutations = rnd.randrange(1, len(ind))
            directives = rnd.sample(range(len(ind)), n_mutations)
        for dir in directives:
            if self._get_attribute(ind[dir], TYPE_MASK) == ALLOC_T:
                # Case 1: Allocation selected
                if rnd.random() < 0.5:
                    # Case 1.1: Allocation with different fragment id
                    new_alloc = self._get_random_alloc()
                    old_id = self._get_attribute(ind[dir], ID_MASK)
                    new_alloc = self._set_attribute(new_alloc, old_id, ID_MASK)
                    ind[dir] = new_alloc
                else:
                    # Case 1.2: Allocation becomes free
                    freeable_ids = self._get_freeable_ids(ind, dir)
                    if freeable_ids:
                        id = rnd.choice(freeable_ids)
                        new_free = self._set_attribute(0, FREE_T, TYPE_MASK)
                        new_free = self._set_attribute(new_free, id, ID_MASK)
                        ind[dir] = new_free
            elif self._get_attribute(ind[dir], TYPE_MASK) == FREE_T:
                # Case 2: Free selected
                if rnd.random() < 0.5:
                    # Case 2.1: Free different id
                    freeable_ids = self._get_freeable_ids(ind, dir)
                    if freeable_ids:
                        id = rnd.choice(freeable_ids)
                        new_free = self._set_attribute(ind[dir], id, ID_MASK)
                        ind[dir] = new_free
                else:
                    # Case 2.2: Free becomes alloc
                    new_alloc = self._get_random_alloc()
                    ind[dir] = new_alloc
        return ind

    def _mutate_spray(self, ind):
        """Mutate an individual. Will add a random sequence of allocations at a random offset"""
        length = rnd.randint(self._spray_min, self._spray_max)
        if len(ind) <= 2:
            location = 0
        else:
            location = rnd.randrange(
                0, len(ind) - 1
            )  # Substract 1, as the last one is alway snd
        alloc_primitive = self._get_random_alloc()
        for _ in range(length):
            alloc_primitive = self._set_attribute(
                alloc_primitive, rnd.randint(0, MAX_ALLOC_ID), ID_MASK
            )
            ind.insert(location, alloc_primitive)
        return ind

    def _mutate_hole_spray(self, ind):
        """Mutate an individual. Will add a random sequence of allocations and then free every second of it"""
        length = rnd.randint(self._spray_min, self._spray_max)
        if len(ind) <= 2:
            location = 0
        else:
            location = rnd.randrange(
                0, len(ind) - 1
            )  # Substract 1, as the last one is alway snd
        alloc_primitive = self._get_random_alloc()
        ids = []
        for _ in range(length):
            alloc_id = rnd.randint(0, MAX_ALLOC_ID)
            ids.append(alloc_id)
            alloc_primitive = self._set_attribute(alloc_primitive, alloc_id, ID_MASK)
            ind.insert(location, alloc_primitive)
        free_primitive = self._set_attribute(0, FREE_T, TYPE_MASK)
        for free_id in ids[::2]:
            free_primitive = self._set_attribute(free_primitive, free_id, ID_MASK)
            ind.insert(location + length, free_primitive)
        return ind

    def _mutate_allocation_nudge(self, ind):
        """Shorter version of _mutate_spray. Placeholder only, as it is probably not applicable in this case, or only when the elements in the target cache are really small"""
        pass

    def _mutate_free_nudge(self, ind):
        """Shorter version of _mutate_hole spray. Placeholder only, as it is probably not applicable in this case, or only when the elements in the target cache are really small"""
        pass

    def _mutate_shorten(self, ind):
        """Mutate an individual. Will remove a randomly selected contiguous section"""
        if len(ind) > 2:
            idx_start = rnd.randrange(0, len(ind) - 2)
            idx_end = rnd.randrange(idx_start, len(ind) - 1)
            ind = ind[0:idx_start] + ind[idx_end:]
        return ind

    def _mate(self, ind1, ind2):
        """Two-point crossover for two individuals"""
        if len(ind1) <= 3 or len(ind2) <= 3:
            return ind1, ind2
        idx_start_1 = rnd.randrange(0, len(ind1) - 1)
        idx_end_1 = rnd.randrange(idx_start_1, len(ind1))
        idx_start_2 = rnd.randrange(0, len(ind2) - 1)
        idx_end_2 = rnd.randrange(idx_start_2, len(ind2))

        cutout_1 = ind1[idx_start_1:idx_end_1]
        cutout_2 = ind2[idx_start_2:idx_end_2]

        ind1 = ind1[:idx_start_1] + cutout_2 + ind2[idx_end_1:]
        ind2 = ind2[:idx_start_2] + cutout_1 + ind2[idx_end_2:]
        return ind1, ind2

    def _select(self, pop):
        noerr = []
        orderok = []
        for i in range(len(pop)):
            if pop[i].fitness.values[0] != MAX_FITNESS:
                noerr.append(pop[i])
                if pop[i].fitness.values[0] != WRONG_ORDER:
                    orderok.append(pop[i])
        if len(orderok) > 0:
            pop = orderok
        elif len(noerr) > 0:
            pop = noerr
        offspring_best = tools.selBest(pop, int(self._mu * self._e))
        offspring_tournament = tools.selDoubleTournament(
            pop,
            int(self._mu * (1 - self._e)),
            fitness_size=5,
            parsimony_size=1.4,
            fitness_first=True,
        )
        return offspring_best + offspring_tournament

    def _create_directive(self):
        """Randomly creates a directive"""
        type = rnd.choice(self._types)
        rep = rnd.randint(
            1, 0xFFFF
        )  # Should probably be bounded to maximum elements in cache but lets see
        size_group = rnd.choice(list(self._groups.keys()))
        sub_group = rnd.choice(list(self._groups[size_group].keys()))
        selector = rnd.choice(self._groups[size_group][sub_group])
        alloc_id = rnd.randint(0, MAX_ALLOC_ID)
        ind = type << TYPE_SHIFT
        ind += rep << REP_SHIFT
        ind += size_group << SIZE_GROUP_SHIFT
        ind += sub_group << SUB_GROUP_SHIFT
        ind += selector << SELECTOR_SHIFT
        ind += alloc_id
        return ind

    def _get_random_alloc(self):
        """Returns a random allocation directive which is drawn to the distribution given by the probs of the groups"""
        group_probs = self._groups["probs"]
        assert len(group_probs) == len(self._groups.keys()) - 1
        group_keys = list(self._groups.keys())
        group_keys.remove("probs")
        sel_group_id = rnd.choices(group_keys, group_probs, k=1)[0]
        sel_group = self._groups[sel_group_id]
        subgroup_probs = sel_group["probs"]
        assert len(subgroup_probs) == len(sel_group.keys()) - 1
        sel_group_keys = list(sel_group.keys())
        sel_group_keys.remove("probs")
        sel_subgroup_id = rnd.choices(sel_group_keys, subgroup_probs, k=1)[0]
        sel_id = rnd.choice(self._groups[sel_group_id][sel_subgroup_id])

        assert (
            self._alloc_loop_enabled == False
        ), "Allocation loops are currently not supported"
        dir = self._set_attribute(0, ALLOC_T, TYPE_MASK)
        dir = self._set_attribute(dir, sel_group_id, SIZE_GROUP_MASK)
        dir = self._set_attribute(dir, sel_subgroup_id, SUB_GROUP_MASK)
        dir = self._set_attribute(dir, sel_id, SELECTOR_SHIFT)
        dir += rnd.randint(0, MAX_ALLOC_ID)
        return dir

    def _get_random_free(self, ind):
        """Returns a directive which frees an allocation from ind"""
        freeable = self._get_freeable_ids(ind, len(ind) - 1)
        if not freeable:
            return self._get_random_alloc()
        id = rnd.choice(freeable)
        dir = self._set_attribute(0, FREE_T, TYPE_MASK)
        dir += id
        return dir

    def _create_individual(self, preset_ind=None):
        """Randomly creates a (valid) Individual OR return an indiviadual with given list"""
        if preset_ind:
            return creator.Individual(preset_ind)
        ind = []
        len = rnd.randint(1, self._max_init_length)
        fstIdx = rnd.randint(0, len - 1)
        for i in range(len):
            if i == fstIdx:
                ind.append(self._set_attribute(0, FST_T, TYPE_MASK))
            elif rnd.random() <= self._alloc_free_ratio:
                ind.append(self._get_random_alloc())
            else:
                ind.append(self._get_random_free(ind))
        ind.append(self._set_attribute(0, SND_T, TYPE_MASK))
        return creator.Individual(ind)

    def _evaluate(self, ind):
        """Returns the fitness given the distance of allocations"""
        distance = self._distances[self._population.index(ind)]
        if type(distance) == int:
            # change this for natural (>) or reverse (<)
            if distance > 0:
                # if(distance < 0):
                return 2**64 - 1
            else:
                return abs(distance)
        else:
            return 2**64

    def init(self, n=200):
        """Randomly generate population"""
        self._population = self._toolbox.population(n=n)
        return self._population

    def _check_length_restriction(self, ind):
        """
        Check if individual allocates at most as many objects at the same time
        as self._max_allocs defines (Alloc in loop excluded, as its not implemented)
        """
        if self._max_allocs is None:
            return True
        allocs = 0
        for dir in ind:
            type = self._get_attribute(dir, TYPE_MASK)
            if type == ALLOC_T:
                allocs += 1
            elif type == FST_T:
                allocs += 1 if self._fst_allocs is None else self._fst_allocs
            elif type == SND_T:
                allocs += 1 if self._snd_allocs is None else self._snd_allocs
            elif type == FREE_T:
                allocs -= 1
            if allocs > self._max_allocs:
                return False
        return True

    def get_children(self):
        children = []
        i = 0
        while i < self._lambda:
            # print(f"[~] Round {i}")
            parent_A = rnd.choice(self._population)
            r = rnd.random()
            if r < self._pmutate:
                # print("Mutation")
                new = self._toolbox.mutate(parent_A)
                if self._check_length_restriction(new):
                    children.append(new)
                    i += 1
            elif r < self._pmutate + self._pmate:
                # print("Crossover")
                parent_B = rnd.choice(self._population)
                new_A, new_B = self._toolbox.mate(parent_A, parent_B)
                if self._check_length_restriction(
                    new_A
                ) and self._check_length_restriction(new_B):
                    children.append(new_A)
                    children.append(new_B)
                    i += 2
            else:
                new = parent_A
                children.append(new)
                i += 1
        return children

    def do_evo_step(self):
        self.read_pop()
        if len(self._population) == 0:
            self.init(n=400)
            self.write_pop()
            return self._population
        else:
            fitnesses = list(map(self._toolbox.evaluate, self._population))
            for ind, fit in zip(self._population, fitnesses):
                ind.fitness.values = [fit]
                if fit == abs(self._target_dist):
                    print("[!] Found solution!")
                    print(self.translate_to_text(ind))
                    print(f"Fitness: {fit}")
                    sys.exit(1337)
            print(f"[~] Generation step: Best fit: {min(fitnesses)}")
            survivors = self._toolbox.select(self._population)

            survivors = list(map(self._toolbox.clone, survivors))
            children = self.get_children()
            self._population = children + survivors
            self.write_pop()
            return self._population

    @abstractmethod
    def translate_to_text(self, ind):
        """Translate an individual to text file input for client"""
        pass

    def read_pop(self):
        files = os.listdir(RAW)
        if files:
            pop = []
            distances = []
            for f in files:
                with open(os.path.join(RAW, f), "r") as fd:
                    pop.append([int(dir, 16) for dir in fd.readlines()])
                with open(os.path.join(RES, f), "r") as fd:
                    dist_raw = fd.read()
                    if not dist_raw.startswith("error"):
                        distances.append(int(dist_raw))
                    else:
                        distances.append(dist_raw)

            self._population = [creator.Individual(ind) for ind in pop]
            self._distances = distances
            return pop, distances
        else:
            return [], []

    def write_pop(self):
        pop = self._population
        for i in range(len(pop)):
            with open(os.path.join(RAW, str(i)), "w") as fd:
                fd.write("\n".join([hex(dir) for dir in pop[i]]))
            with open(os.path.join(INS, str(i)), "w") as fd:
                text = self.translate_to_text(pop[i])
                fd.write(text)
                # if text == "\n": # When text is empty, trigger an error with a single alloc
                #    fd.write("kmalloc 96 0")
                # else:
                #    fd.write(text)
        return

    def run(self):
        """
        simple = self._toolbox.individual([1,2,3,4])
        pprint(type(simple))
        """

        self.init()
        children = self.get_children()
        print(type(children[0]))
        # for c in children:
        #    pprint([hex(i) for i in c])
        return
        one_ind = pop[0]
        two_ind = pop[1]
        pprint([hex(d) for d in one_ind])
        pprint([hex(d) for d in two_ind])
        one_ind, two_ind = self._toolbox.mate(one_ind, two_ind)
        pprint([hex(d) for d in one_ind])
        pprint([hex(d) for d in two_ind])
        # one_ind = self._mutate(one_ind)
        # pprint([hex(d) for d in  one_ind ])
        # one_ind = self._mutate(one_ind)
        # pprint([hex(d) for d in  one_ind ])


class EvoHeapNoNoise(EvoHeap):
    def translate_to_text(self, ind):
        MAX_ID = 2047
        candidate = []
        in_use_ids = []
        id_mapping = dict()
        for dir in ind:
            type = self._get_attribute(dir, TYPE_MASK)
            if type == ALLOC_T:
                ids = [x for x in range(MAX_ID) if x not in in_use_ids]
                alloc_id = rnd.choice(ids)
                candidate.append(f"kmalloc 96 {alloc_id}")
                algo_id = self._get_attribute(dir, ID_MASK)
                id_mapping[algo_id] = alloc_id
                in_use_ids.append(alloc_id)
            elif type == FREE_T:
                algo_id = self._get_attribute(dir, ID_MASK)
                if algo_id in id_mapping:
                    candidate.append(f"kfree {id_mapping[algo_id]}")
                    in_use_ids.remove(id_mapping[algo_id])
                    id_mapping.pop(algo_id)
            elif type == FST_T:
                candidate.append("fst 96")
            elif type == SND_T:
                candidate.append("snd 96")
            else:
                print("Invalid type in individual, moving on...")
        return "\n".join(candidate) + "\n"


class EvoHeapWithNoise(EvoHeap):
    def __init__(self, noise=3, **kwargs):
        super().__init__(**kwargs)
        self._noise = noise

    def translate_to_text(self, ind):
        MAX_ID_NORMAL = 1800
        MAX_ID_TOTAL = 2047
        candidate = []
        in_use_ids = []
        id_mapping = dict()
        for dir in ind:
            type = self._get_attribute(dir, TYPE_MASK)
            if type == ALLOC_T:
                ids = [x for x in range(MAX_ID_NORMAL) if x not in in_use_ids]
                alloc_id = rnd.choice(ids)
                candidate.append(f"kmalloc 256 {alloc_id}")
                algo_id = self._get_attribute(dir, ID_MASK)
                id_mapping[algo_id] = alloc_id
                in_use_ids.append(alloc_id)
            elif type == FREE_T:
                algo_id = self._get_attribute(dir, ID_MASK)
                if algo_id in id_mapping:
                    candidate.append(f"kfree {id_mapping[algo_id]}")
                    in_use_ids.remove(id_mapping[algo_id])
                    id_mapping.pop(algo_id)
            elif type == FST_T:
                selected_ids = []
                for _ in range(self._noise * 2):
                    ids = [
                        x for x in range(MAX_ID_NORMAL, MAX_ID_TOTAL) if x not in in_use_ids
                    ]
                    id = rnd.choice(ids)
                    selected_ids.append(id)
                    in_use_ids.append(id)
                candidate.append(
                    "\n".join(
                        [f"kmalloc 256 {selected_ids[i]}" for i in range(self._noise)]
                    )
                    + "\nfst 256\n"
                    + "\n".join(
                        [
                            f"kmalloc 256 {selected_ids[i]}"
                            for i in range(self._noise, 2 * self._noise)
                        ]
                    )
                )
            elif type == SND_T:
                candidate.append("snd 256")
            else:
                print("Invalid type in individual, moving on...")
        return "\n".join(candidate) + "\n"


class EvoHeapTargetNoiseWithReal(EvoHeap):
    def translate_to_text(self, ind):
        MAX_ID_NORMAL = 1800
        MAX_ID_TOTAL = 2047
        candidate = []
        in_use_ids = []
        once_used_ids = []
        id_mapping = dict()
        for dir in ind:
            type = self._get_attribute(dir, TYPE_MASK)
            if type == ALLOC_T:
                ids = [x for x in range(MAX_ID_NORMAL) if x not in in_use_ids]
                alloc_id = rnd.choice(ids)
                if len(candidate) > 0 and candidate[-1].startswith("shmctl"):
                    candidate.append("sleep(1);")
                if alloc_id in once_used_ids:
                    candidate.append(
                        f"fengshui{alloc_id} = shmget(IPC_PRIVATE, 1024, IPC_CREAT);"
                    )
                else:
                    once_used_ids.append(alloc_id)
                    candidate.append(
                        f"int fengshui{alloc_id} = shmget(IPC_PRIVATE, 1024, IPC_CREAT);"
                    )
                algo_id = self._get_attribute(dir, ID_MASK)
                id_mapping[algo_id] = alloc_id
                in_use_ids.append(alloc_id)
            elif type == FREE_T:
                algo_id = self._get_attribute(dir, ID_MASK)
                if algo_id in id_mapping:
                    candidate.append(
                        f"shmctl(fengshui{id_mapping[algo_id]}, IPC_RMID, NULL);"
                    )
                    in_use_ids.remove(id_mapping[algo_id])
                    id_mapping.pop(algo_id)
            elif type == FST_T:
                if len(candidate) > 0 and candidate[-1].startswith("shmctl"):
                    candidate.append("sleep(1);")
                candidate.append("ioctl(fd, VULN_ALLOC_OVERFLOW);")
            elif type == SND_T:
                if len(candidate) > 0 and candidate[-1].startswith("shmctl"):
                    candidate.append("sleep(1);")
                candidate.append("ioctl(fd, VULN_ALLOC_TARGET);")
            else:
                print("Invalid type in individual, moving on...")
        return "\n".join(candidate) + "\n"


INS = "./ins/"
RES = "./res/"
RAW = "./raw/"
EXEC = "./exec/"


def no_noise():

    groups = dict()
    groups[0x1] = dict()
    groups["probs"] = [1.0]
    groups[0x1][0x1] = [0]
    groups[0x1]["probs"] = [1.0]

    evo = EvoHeapNoNoise(None, groups, alloc_free_ratio=0.5)
    evo.do_evo_step()


def use_slabapi_allocs(noise):

    groups = dict()
    groups[0x1] = dict()
    groups["probs"] = [1.0]
    groups[0x1][0x1] = [0]
    groups[0x1]["probs"] = [1.0]

    evo = EvoHeapWithNoise(
        noise=noise, types=None, groups=groups, alloc_free_ratio=0.5, target_dist=-96
    )
    evo.do_evo_step()


def use_real_allocs():
    groups = dict()
    groups[0x1] = dict()
    groups["probs"] = [1.0]
    groups[0x1][0x1] = [0]
    groups[0x1]["probs"] = [1.0]

    evo = EvoHeapTargetNoiseWithReal(
        None,
        groups,
        alloc_free_ratio=0.5,
        target_dist=-256,
        max_allocs=16,
        fst_allocs=5,
        snd_allocs=1,
    )
    evo.do_evo_step()


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-a",
        dest="allocations",
        metavar="allocations",
        type=str,
        required=True,
        help="Choose between 'ksieve' for slab_api allocations or 'real' for allocations unsing shmget and the vuln kernel module",
    )
    parser.add_argument(
        "-n",
        dest="noise",
        metavar="noise",
        type=int,
        help="The amount of noise allocations to perform. Only relevant if performing allocations with slab_api, otherwise noise depends on the 'vuln' kernel module",
        default=-1,
    )
    args = parser.parse_args()
    if args.allocations == "real":
        use_real_allocs()
    elif args.allocations == "ksieve":
        if args.noise < 0:
            raise RuntimeError("You have to give a non-negative Value for noise!")
        use_slabapi_allocs(args.noise)
    else:
        raise RuntimeError("Invalid value for allocation type!")
    # no_noise()
    """
    types = [ALLOC_T, FREE_T]
    groups = dict()
    groups[0xa] = dict()
    groups["probs"] = [1.]
    groups[0xa][0xb] = [0,1,2]
    groups[0xa][0xc] = [3,4,5]
    groups[0xa]["probs"] = [0.8, 0.2]

    pop = [ [rnd.randint(0, MAX_ALLOC_ID) for _ in range(5)] for x in range(200)]
    pop[199] = [1,1,1,1,1,1,1]
    distances = [-x for x in range(200)]
    evo = EvoHeap(types, groups, population=pop, distances=distances)
    next = evo.do_evo_step()
    #pprint(next)
    pprint(len(next))
    """


if __name__ == "__main__":
    main()
