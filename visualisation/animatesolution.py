#!/usr/bin/env python3
import pyglet
from pyglet import shapes
import sys
import re
from abc import ABC, abstractmethod
import argparse



class Heap(ABC):
    def __init__(self, candidate):
        self._heapstate = [None] * 64
        self._freelist = [x for x in range(64)]
        self._candidate = self._translate(candidate)
        self._current = 0
        self.max_allocs = self._maximum_allocs()

    @property
    def freelist(self):
        return self._freelist

    @abstractmethod
    def _translate(self, candidate: list) -> list:
        """Translate a candidate into the kernel-sieve formate"""
        pass

    def calculate_layout_complete(self):
        self._freelist = [x for x in range(64)]
        self._heapstate = [None] * 64
        for line in self._candidate:
            instruction = line.split()[0]
            if instruction == "kmalloc":
                id = line.split()[2]
                self._heapstate[self._freelist.pop(0)] = id
            elif instruction == "kfree":
                id = line.split()[1]
                index = self._heapstate.index(id)
                self._heapstate[index] = None
                self._freelist.insert(0, index)
            else:
                id = instruction
                self._heapstate[self._freelist.pop(0)] = id
        return self._heapstate

    def calculate_layout_step(self) -> tuple[str,int,str]:
        if self._current >= len(self._candidate):
            return "", 0, ""
        line = self._candidate[self._current]
        instruction = line.split()[0]
        if instruction == "kmalloc":
            id = line.split()[2]
            index = self._freelist.pop(0)
            self._heapstate[index] = id
        elif instruction == "kfree":
            id = line.split()[1]
            index = self._heapstate.index(id)
            self._heapstate[index] = None
            self._freelist.insert(0, index)
        else:
            id = instruction
            index = self._freelist.pop(0)
            self._heapstate[index] = id
        self._current += 1
        return instruction, index, id

    def _maximum_allocs(self):
        allocs = 0
        max_allocs = 0
        for line in self._candidate:
            if line.startswith("kmalloc") or line.startswith("fst") or line.startswith("snd"):
                allocs += 1
                if allocs > max_allocs:
                    max_allocs = allocs
            elif line.startswith("kfree"):
                allocs -= 1
        return max_allocs

class HeapRealNoise(Heap):
    def __init__(self, candidate, noise):
        self._noise = noise
        super().__init__(candidate)

    def _translate(self, candidate):
        translated = []
        for line in candidate:
            if line == "sleep(1);":
                continue
            elif line.startswith("int") or line.startswith("fengshui"):
                match = re.search(r"\d+", line)
                if match:
                    id = match.group()
                else:
                    raise RuntimeError(f"line doesn't contain id:\n{line}")
                translated.append(f"kmalloc 256 {id}")
            elif line.startswith("shmctl"):
                match = re.search(r"\d+", line)
                if match:
                    id = match.group()
                else:
                    raise RuntimeError(f"line doesn't contain id:\n{line}")
                translated.append(f"kfree {id}")
            elif line.startswith("ioctl(fd, VULN_ALLOC_OVERFLOW"):
                for i in range(3000, 3000+self._noise):
                    translated.append(f"kmalloc 256 {i}")
                translated.append("fst 256")
                for i in range(3000+self._noise, 3000+2*self._noise):
                    translated.append(f"kmalloc 256 {i}")
            elif line.startswith("ioctl(fd, VULN_ALLOC_TARGET"):
                translated.append("snd 256")
        return translated

class HeapKSieve(Heap):
    def _translate(self, candidate):
        return candidate

# Here it begins
parser = argparse.ArgumentParser(description="Animate a solution!")
parser.add_argument("candidate", type=str, nargs=1, help="The candidate to use")
parser.add_argument("-f", dest="format", metavar="format", type=str, required=False, default="real", help="Choose a format of the solution: real or ksieve")
parser.add_argument("-n", dest="noise", metavar="noise", type=int, required=False, default=2, help="If you choose the 'real' format, you can define here how much noise the 'fst' allocation, i.e. the allocation of the overflowing buffer contains. Example: A value of '2' would add 2 noise allocs before and after the fst alloc")
parser.add_argument("-d", dest="delay", metavar="delay", type=float, default=0.5, required=False, help="Set the delay between allocations in seconds")
args = parser.parse_args()

with open(args.candidate[0]) as f:
    candidate = f.readlines()

if args.format.lower() == "real":
    heap = HeapRealNoise(candidate, args.noise)
elif args.format.lower() == "ksieve":
    heap = HeapKSieve(candidate)
else:
    raise RuntimeError("Invalid format")

window = pyglet.window.Window(1000, 500)
batch_main = pyglet.graphics.Batch()
batch_labels = pyglet.graphics.Batch()

grey = (125, 125, 125)
red = (255, 0, 0)
green = (0, 0x64, 0)
lightgreen = (144, 238, 144)
white = (255, 255, 255)
black = (0, 0, 0, 255)

background = shapes.Rectangle(0,0,window.width,window.height, color=white)

legend_obj = shapes.Rectangle(300, 150, 25, 25, color=grey, batch=batch_main)
legend_obj_label = pyglet.text.Label("Object", font_name="Times New Roman", font_size=15, color=black,x=340, y=155, batch=batch_main)
legend_noise = shapes.Rectangle(300, 100, 25, 25, color=lightgreen, batch=batch_main)
legend_noise_label = pyglet.text.Label("Noise", font_name="Times New Roman", font_size=15, color=black,x=340, y=105, batch=batch_main)
legend_buffer = shapes.Rectangle(500, 150, 25, 25, color=green, batch=batch_main)
legend_buffer_label = pyglet.text.Label("Buffer", font_name="Times New Roman", font_size=15, color=black,x=540, y=155, batch=batch_main)
legend_target = shapes.Rectangle(500, 100, 25, 25, color=red, batch=batch_main)
legend_target_label = pyglet.text.Label("Target", font_name="Times New Roman", font_size=15, color=black,x=540, y=105, batch=batch_main)

@window.event
def on_draw():
    window.clear()
    background.draw()
    batch_main.draw()
    batch_labels.draw()

start = window.width / 2 - (50 * heap.max_allocs / 2)
rec_heap = [shapes.BorderedRectangle(start + 50 * i, window.height/2, 50, 50, color=white, batch=batch_main) for i in range(heap.max_allocs)]
label_freelist = [pyglet.text.Label(f"{i+1}", font_name="Times New Roman", font_size=15, color=black,  x=start+ 20 + 50 * i, y=window.height/2+20, batch=batch_labels) for i in range(heap.max_allocs)]

def update(_):
    instruction, index, id = heap.calculate_layout_step()
    if instruction:
        print(f"[*] {instruction} at {index}")
        if instruction == "kmalloc":
            if int(id) >= 3000:
                color = lightgreen
            else:
                color = grey
            rec_heap[index].color = color
            label_freelist[index].text = ""
        elif instruction == "fst":
            color = green
            rec_heap[index].color = color
            label_freelist[index].text = ""
        elif instruction == "snd":
            color = red
            rec_heap[index].color = color
            label_freelist[index].text = ""
        elif instruction == "kfree":
            rec_heap[index].color = white
    update_freelist_labels()

def update_freelist_labels():
    for index, block in enumerate(heap.freelist):
        if block >= len(label_freelist):
            break
        label_freelist[block].text= f"{index+1}"



pyglet.clock.schedule_interval(update, args.delay)

pyglet.app.run()

