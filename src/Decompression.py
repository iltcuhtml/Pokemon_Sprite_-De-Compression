def printColor(color):
    table = {
        0x00: "107", 
        0x01: "47", 
        0x10: "100", 
        0x11: "40"
    }

    if color not in table:
        raise ValueError("Invalid color code.")
    
    print(f"\033[{table[color]}m  \033[0m", end='')

class BitStream:
    def __init__(self, data: bytes):
        self.data = int.from_bytes(data, "big")
        self.length = len(data) * 8
        self.pointer = 0

    def consume(self, n):
        shift = self.length - self.pointer - n
        value = (self.data >> shift) & ((1 << n) - 1)
        self.pointer += n
        return value

class Sprite(BitStream):
    def __init__(self, data: bytes):
        super().__init__(data)

        self.sprite_width = self.consume(4)
        self.sprite_height = self.consume(4)
        
        self.width_px = self.sprite_width * 8
        self.height_px = self.sprite_height * 8
        self.total_px = self.width_px * self.height_px

        # 0 = Buffer B, 1 = Buffer C
        self.buffer_type = self.consume(1)

        # 0 = RLE, 1 = Data
        self.packet_type = self.consume(1)

        # 0b0 = Mode 1, 0b10 = Mode 2, 0b11 = Mode 3
        self.decoding_method = 0

        self.Buffer_A = bytearray(7 * 7 * 8 * 8)
        self.Buffer_B = bytearray(7 * 7 * 8 * 8)
        self.Buffer_C = bytearray(7 * 7 * 8 * 8)

        self.Sprite = bytearray(7 * 7 * 8 * 2)

    def getBuffer(self, t):
        return self.Buffer_B if t == 0 else self.Buffer_C

    def putData(self, buffer, x, y, data):
        h = self.height_px
        w = self.width_px

        for bit in data:
            if x >= w:
                break

            buffer[x + y * w] = bit

            y += 1

            if y == h:
                y = 0
                x += 1

        return x, y

    def decodeRLEPacket(self, buffer, x, y):
        buf = 0
        bits = 0

        while True:
            b = self.consume(1)
            buf = (buf << 1) | b
            bits += 1

            if b == 0:
                break

        length = buf + self.consume(bits) + 1

        # RLE = "00" * length
        return self.putData(buffer, x, y, bytearray(length * 2))

    def decodeDataPacket(self, buffer, x, y):
        out = bytearray()

        while True:
            v = self.consume(2)

            if v == 0:
                break

            out.append((v >> 1) & 1)
            out.append(v & 1)

        return self.putData(buffer, x, y, out)

    def decompress(self):
        x = y = 0

        buffer = self.getBuffer(self.buffer_type)
        packet = self.packet_type

        while x < self.width_px:
            if packet == 0:
                x, y = self.decodeRLEPacket(buffer, x, y)

            else:
                x, y = self.decodeDataPacket(buffer, x, y)

            packet ^= 1

        self.packet_type = packet
        self.buffer_type ^= 1

    def getEncodingMethod(self):
        self.decoding_method = self.consume(1)

        if self.decoding_method == 1:
            self.decoding_method = (self.decoding_method << 1) | self.consume(1)

        self.packet_type = self.consume(1)

    def decode(self):
        pri = self.getBuffer(self.buffer_type)
        sec = self.getBuffer(self.buffer_type ^ 1)

        h = self.height_px
        w = self.width_px

        x_offset = int(4 - self.sprite_width / 2) * 8
        y_offset = (7 - self.sprite_height) * 8

        if self.decoding_method != 0b10:
            for x in range(w):
                bit = 0

                for y in range(h):
                    bit ^= sec[x + y * w]
                    sec[x + y * w] = bit

        for x in range(w):
            bit = 0

            for y in range(h):
                bit ^= pri[x + y * w]
                pri[x + y * w] = bit

        if self.decoding_method != 0b0:
            for i in range(self.total_px):
                sec[i] ^= pri[i]
        
        for ty in range(h):
            for tx in range(self.sprite_width):
                src = tx * 8 + ty * w
                dst = (tx * 8 + x_offset) + (ty + y_offset) * w

                self.Buffer_A[dst:dst + 8] = self.Buffer_B[src:src + 8]

        self.Buffer_B = bytearray(7 * 7 * 8 * 8)

        for ty in range(h):
            for tx in range(self.sprite_width):
                src = tx * 8 + ty * w
                dst = (tx * 8 + x_offset) + (ty + y_offset) * w

                self.Buffer_B[dst:dst + 8] = self.Buffer_C[src:src + 8]
        
        for y in range(h):
            out = (y * w) * 2

            for y in range(self.sprite_width):
                base = x * 8 + y * w

                b0 = (
                    (self.Buffer_A[base + 0] << 7) |
                    (self.Buffer_A[base + 1] << 6) |
                    (self.Buffer_A[base + 2] << 5) |
                    (self.Buffer_A[base + 3] << 4) |
                    (self.Buffer_A[base + 4] << 3) |
                    (self.Buffer_A[base + 5] << 2) |
                    (self.Buffer_A[base + 6] << 1) |
                    (self.Buffer_A[base + 7])
                )

                b1 = (
                    (self.Buffer_B[base + 0] << 7) |
                    (self.Buffer_B[base + 1] << 6) |
                    (self.Buffer_B[base + 2] << 5) |
                    (self.Buffer_B[base + 3] << 4) |
                    (self.Buffer_B[base + 4] << 3) |
                    (self.Buffer_B[base + 5] << 2) |
                    (self.Buffer_B[base + 6] << 1) |
                    (self.Buffer_B[base + 7])
                )

                self.Sprite[y * w * 2]     = b0
                self.Sprite[y * w * 2 + 1] = b1

                out += 2

    def render(self):
        pass

def main():
    file_adr = input("Enter the compressed binary file address (*.bin): ")
    
    with open(file_adr, "rb") as f:
        data = f.read()

    sprite = Sprite(data)

    sprite.decompress()
    printColor(0x00)
    sprite.getEncodingMethod()
    printColor(0x01)
    sprite.decompress()
    printColor(0x10)
    sprite.decode()
    printColor(0x11)
    sprite.render()

if __name__ == "__main__":
    main()