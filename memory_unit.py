from __future__ import annotations

import logging
from collections import namedtuple
from enum import Enum

from exceptions import BufferEmptyError

LINE_SIZE = 4
ENTRIES_PER_SET = 4

IO_EXTRA_TICKS = 10
MEM_EXTRA_TICKS = 10
CACHE_EXTRA_TICKS = 1

# Tag value that can't be passed during normal store/fetch
# think of additional emptiness bit in tag part (request adress has this bit extended to and filled with 0)
EMPTY_LINE_TAG = -1


class CacheEntry:
    def __init__(self, tag: int, line: list, is_dirty: bool):
        self.tag = tag
        self.line = line
        self.is_dirty = is_dirty


class CacheSet:
    def __init__(self):
        self.entries = [CacheEntry(EMPTY_LINE_TAG, [0] * LINE_SIZE, False) for i in range(ENTRIES_PER_SET)]
        self.plrum = [False] * ENTRIES_PER_SET


DecodedAddress = namedtuple("DecodedAdr", ["word", "line", "tag"])


class Cache:
    def __init__(self, set_size: int):
        assert set_size > LINE_SIZE * ENTRIES_PER_SET, "Set size is too small"
        assert (set_size & (set_size - 1) == 0), "Set size must be a power of 2"


        set_count = set_size // (LINE_SIZE * ENTRIES_PER_SET)

        self._sets = [CacheSet() for j in range(set_count)]
        self._hits = 0
        self._requests = 0
        self.prefetch_end = (
            0  # In ticks time when background prefetch ends: used to simulate prefetching parallel to execution
        )

    def __decode_adr(self, adr: int) -> DecodedAddress:
        return DecodedAddress(
            adr % LINE_SIZE, (adr // LINE_SIZE) % ENTRIES_PER_SET, (adr // LINE_SIZE // ENTRIES_PER_SET)
        )

    def __get_hit_entries(self, dadr: DecodedAddress) -> list[tuple[CacheEntry, CacheSet]]:
        valid = [(cache_set.entries[dadr.line], cache_set) for cache_set in self._sets]
        return list(filter(lambda lc: lc[0].tag == dadr.tag, valid))

    def __update_prlum(self, chosen_set: CacheSet, dadr: DecodedAddress):
        chosen_set.plrum[dadr.line] = True
        capacity_reached = all(cache_set.plrum[dadr.line] == 1 for cache_set in self._sets)

        if capacity_reached:
            for cache_set in self._sets:
                cache_set.plrum[dadr.line] = False
            chosen_set.plrum[dadr.line] = True  # Yes, that takes less actions than not setting it to 0

    def read(self, adr: int) -> object:
        self._requests += 1
        decoded = self.__decode_adr(adr)
        hit_entries = self.__get_hit_entries(decoded)
        if len(hit_entries) == 0:
            return None

        self._hits += 1
        entry = hit_entries[0][0]
        chosen_set = hit_entries[0][1]

        self.__update_prlum(chosen_set, decoded)
        return entry.line[decoded.word]

    def lookup(self, adr: int):
        # NOTE!: Doesn't get counted in hit rate
        decoded = self.__decode_adr(adr)
        hit_entries = self.__get_hit_entries(decoded)
        if len(hit_entries) != 0:
            logging.debug("%s", f"Cache hit on lookup {adr}")
        else:
            logging.debug("%s", f"Cache miss on lookup {adr}")
        return len(hit_entries) != 0

    def write(self, adr: int, word: int) -> bool:
        self._requests += 1
        decoded = self.__decode_adr(adr)
        hit_entries = self.__get_hit_entries(decoded)
        if len(hit_entries) == 0:
            return False

        self._hits += 1
        entry = hit_entries[0][0]
        chosen_set = hit_entries[0][1]

        entry.line[decoded.word] = word
        entry.is_dirty = True

        self.__update_prlum(chosen_set, decoded)
        return True

    def swap(self, adr: int, words: list) -> CacheEntry:
        decoded = self.__decode_adr(adr)

        valid = [(cache_set.entries[decoded.line], cache_set) for cache_set in self._sets]

        entry_for_swap, cache_set = next(filter(lambda ec: not ec[1].plrum[decoded.line], valid))
        new_entry = CacheEntry(decoded.tag, words, False)
        cache_set.entries[decoded.line] = new_entry
        cache_set.plrum[decoded.line] = False
        return entry_for_swap


class ARLatch(Enum):
    PC = 0
    ALU = 1


class MemoryUnit:
    def __init__(self, io_adr: int, mem_size: int, code, read_buffer: list, cache: Cache):
        self._cache = cache

        self._AR = 0

        self._mem = [0] * mem_size
        for instr in code:
            self._mem[instr["offset"]] = instr

        self._data = 0
        self._IO_ADR = io_adr
        self._write_buffer = []
        self._read_buffer = read_buffer

    def __repr__(self) -> str:
        if isinstance(self._data, dict):
            mem_str = (
                f"{'MEM:': >6} {self._data['opcode'].name} {self._data['operand'] if 'operand' in self._data else ''}"
            )
        else:
            mem_str = f"{'MEM:': >6} {self._data}"
        return f"{'ADR:': >6} {self._AR:5} {mem_str}"

    def __fetch_and_insert(self, adr: int) -> tuple[int, object]:
        ticks = 0

        line_start = adr - adr % LINE_SIZE
        line_words = self._mem[line_start : line_start + LINE_SIZE]

        ticks += MEM_EXTRA_TICKS

        swapped_entry = self._cache.swap(adr, line_words)
        logging.debug(
            "%s",
            f"Cache insert {adr}",
        )
        if swapped_entry.is_dirty:
            swapped_adr = (
                swapped_entry.tag * LINE_SIZE * ENTRIES_PER_SET + ((adr // LINE_SIZE) % ENTRIES_PER_SET) * LINE_SIZE
            )
            logging.debug(
                "%s",
                f"Writing evicted line {swapped_adr} to memory",
            )
            self._mem[swapped_adr : swapped_adr + LINE_SIZE] = swapped_entry.line
            ticks += MEM_EXTRA_TICKS
        return (ticks, line_words[adr % LINE_SIZE])

    def __parallel_prefetch(self, adr: int, start_tick: int):
        logging.debug(
            "%s",
            f"Started PARALLEL FETCHING of {self._AR + LINE_SIZE}:",
        )
        prefetch_ticks = CACHE_EXTRA_TICKS  # Cache lookup ticks
        if not self._cache.lookup(adr):
            fetching_extra_ticks, _ = self.__fetch_and_insert(self._AR + LINE_SIZE)
            prefetch_ticks += fetching_extra_ticks
        self._cache.prefetch_end = start_tick + prefetch_ticks
        logging.debug(
            "%s\n",
            f"planned finish on {self._cache.prefetch_end} tick:",
        )

    def read(self, cur_ticks: int) -> int:
        # Ticks till parallel prefetching ends
        extra_ticks = max(self._cache.prefetch_end - cur_ticks, 0)
        logging.debug("%s", f"Prefetch finishing: {max(self._cache.prefetch_end - cur_ticks, 0)} extra ticks")
        if self._AR == self._IO_ADR:
            if len(self._read_buffer) < 1:
                raise BufferEmptyError()
            self._data = ord(self._read_buffer.pop(0))
            extra_ticks += IO_EXTRA_TICKS - 1  # - 1 since current tick is sort of counted
            logging.debug("%s", f"IO read: {IO_EXTRA_TICKS - 1} extra ticks")
            logging.debug("%s\n", f"In total CPU waited for {extra_ticks} extra ticks")
            return extra_ticks

        word = self._cache.read(self._AR)
        extra_ticks += CACHE_EXTRA_TICKS - 1  # - 1 since current tick is sort of counted
        if word is None:
            logging.debug("%s", f"Cache read {self._AR} miss for {CACHE_EXTRA_TICKS - 1} extra ticks")
            fetching_extra_ticks, fetched_word = self.__fetch_and_insert(self._AR)
            extra_ticks += fetching_extra_ticks
            logging.debug("%s\n", f"Memory store/fetch: {fetching_extra_ticks} extra ticks")
            word = fetched_word

            # Starting parallel prefetching
            self.__parallel_prefetch(self._AR + LINE_SIZE, cur_ticks + extra_ticks)
        else:
            logging.debug("%s", f"Cache read {self._AR} hit for {CACHE_EXTRA_TICKS - 1} extra ticks")

        if isinstance(word, dict) and "word" in word:
            self._data = word["word"]
        else:
            self._data = word
        logging.debug("%s\n", f"In total CPU waited for {extra_ticks} extra ticks")
        return extra_ticks

    def write(self, item, cur_ticks: int) -> int:
        extra_ticks = max(self._cache.prefetch_end - cur_ticks, 0)
        logging.debug("%s", f"Prefetch finishing: {max(self._cache.prefetch_end - cur_ticks, 0)} extra ticks")
        if self._AR == self._IO_ADR:
            self._write_buffer.append(item)
            extra_ticks += IO_EXTRA_TICKS - 1  # - 1 since current tick is counted
            logging.debug("%s", f"IO write: {IO_EXTRA_TICKS - 1} extra ticks")
            logging.debug("%s\n", f"In total CPU waited for {extra_ticks} extra ticks")
            return extra_ticks

        is_written = self._cache.write(self._AR, item)
        extra_ticks += CACHE_EXTRA_TICKS - 1  # - 1 since current tick is counted
        if not is_written:
            logging.debug("%s", f"Cache write {self._AR} miss for {CACHE_EXTRA_TICKS - 1} extra ticks")
            fetching_extra_ticks, _ = self.__fetch_and_insert(self._AR)
            extra_ticks += fetching_extra_ticks
            logging.debug("%s", f"Memory store/fetch: {fetching_extra_ticks} extra ticks")

            self._cache.write(self._AR, item)
            extra_ticks += CACHE_EXTRA_TICKS
            logging.debug("%s\n", f"Cache write into fetched: {CACHE_EXTRA_TICKS} extra ticks")

            # Starting parallel prefetching
            self.__parallel_prefetch(self._AR + LINE_SIZE, cur_ticks + extra_ticks)

        else:
            logging.debug("%s", f"Cache write {self._AR} hit for {CACHE_EXTRA_TICKS - 1} extra ticks")
        logging.debug("%s\n", f"In total CPU waited for {extra_ticks} extra ticks")
        return extra_ticks
