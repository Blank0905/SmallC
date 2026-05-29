import struct

class MemoryError(Exception):
    pass

class Memory:
    """
    Small-C 記憶體模擬器
    - 使用 bytearray 模擬線性記憶體空間。
    - 全域變數（Global）從記憶體起點往上長。
    - 區域變數（Stack）從記憶體終點往下長。
    - 支援 32-bit int (4 bytes) 與 8-bit char (1 byte) 的讀寫。
    - 指標本質上就是 32-bit int，儲存著這個 bytearray 的 index。
    """
    
    def __init__(self, size_bytes=65536):
        self.size = size_bytes
        self.memory = bytearray(size_bytes) #宣告一個65536byte的array
         
        self.heap_ptr = 4           # 全域指標，從 4 開始往上長（保留位址 0 給 NULL）
        self.stack_ptr = size_bytes # 堆疊指標，從尾巴往下長
        self.fp_stack = []          # 紀錄函式呼叫的 Frame Pointer (FP)

    def reset(self):
        """重置記憶體（用於 REPL 的 NEW 指令）"""
        self.memory = bytearray(self.size)
        self.heap_ptr = 4           # 同 __init__：保留位址 0 給 NULL
        self.stack_ptr = self.size
        self.fp_stack = []

    # === 記憶體配置 ===

    def alloc_global(self, size):
        """配置全域記憶體空間，回傳起始位址"""
        addr = self.heap_ptr
        self.heap_ptr += size
        self._check_collision()
        return addr
        
    def alloc_local(self, size):
        """配置區域記憶體空間（Stack），回傳起始位址"""
        self.stack_ptr -= size
        self._check_collision()
        return self.stack_ptr
        
    def _check_collision(self):
        if self.heap_ptr > self.stack_ptr:
            raise MemoryError("Out of Memory: Heap and Stack collision!")

    # === 函式堆疊框架 (Frame) 管理 ===

    def push_frame(self):
        """進入函式時，將目前的 stack_ptr 記下來當作這個函式的基底"""
        self.fp_stack.append(self.stack_ptr)
        
    def pop_frame(self):
        """離開函式時，將 stack_ptr 恢復到進入時的狀態，相當於釋放所有區域變數"""
        if not self.fp_stack:
            raise MemoryError("Call stack underflow!")
        self.stack_ptr = self.fp_stack.pop()

    # === 讀寫操作 ===

    def read_int(self, addr):
        """讀取 4 bytes 的有號整數 (Little Endian)"""
        if addr < 0 or addr + 4 > self.size:
            raise MemoryError(f"Segmentation fault at address {addr}")
        # 將 4 個 byte 組合回整數，明確認定為「小端序」與「有號整數」
        raw_bytes = self.memory[addr:addr+4]
        return int.from_bytes(raw_bytes, byteorder='little', signed=True)
        
    def write_int(self, addr, value):
        """寫入 4 bytes 的有號整數 (Little Endian)"""
        if addr < 0 or addr + 4 > self.size:
            raise MemoryError(f"Segmentation fault at address {addr}")
        # 處理 Python 的大整數溢位，確保範圍在 32-bit signed int 內
        value = (value + 2**31) % 2**32 - 2**31
        # 將整數拆成 4 個 byte
        self.memory[addr:addr+4] = value.to_bytes(4, byteorder='little', signed=True)
        
    def read_char(self, addr):
        """讀取 1 byte 的有號字元"""
        if addr < 0 or addr + 1 > self.size:
            raise MemoryError(f"Segmentation fault at address {addr}")
        raw_bytes = self.memory[addr:addr+1]
        return int.from_bytes(raw_bytes, byteorder='little', signed=True)
        
    def write_char(self, addr, value):
        """寫入 1 byte 的有號字元"""
        if addr < 0 or addr + 1 > self.size:
            raise MemoryError(f"Segmentation fault at address {addr}")
        # 確保值在 -128 ~ 127 之間
        if isinstance(value, str):
            value = ord(value[0])
        value = (value + 128) % 256 - 128
        # 將整數拆成 1 個 byte
        self.memory[addr:addr+1] = value.to_bytes(1, byteorder='little', signed=True)

    def read_string(self, addr):
        """從指定位址讀取 C 字串，直到遇到 \0"""
        curr = addr
        raw_bytes = bytearray()
        while True:
            c = self.read_char(curr)
            if c == 0:
                break
            raw_bytes.append(c if c >= 0 else c + 256)
            curr += 1
        return raw_bytes.decode('utf-8', errors='replace')
