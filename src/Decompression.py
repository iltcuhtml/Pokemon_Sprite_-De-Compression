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

        self.Buffer_A = bytearray(self.total_px)
        self.Buffer_B = bytearray(self.total_px)
        self.Buffer_C = bytearray(self.total_px)

    def getBuffer(self, t):
        return self.Buffer_B if t == 0 else self.Buffer_C

    def putData(self, buffer, idx, data):
        h = self.height_px
        w = self.width_px

        x = idx // h
        y = idx % h

        for bit in data:
            if x >= w:
                break

            buffer[x * h + y] = bit

            y += 1

            if y == h:
                y = 0
                x += 1

        return x * h + y

    def decodeRLEPacket(self, buffer, idx):
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
        return self.putData(buffer, idx, bytearray(length * 2))

    def decodeDataPacket(self, buffer, idx):
        out = bytearray()

        while True:
            v = self.consume(2)

            if v == 0:
                break

            out.append((v >> 1) & 1)
            out.append(v & 1)

        return self.putData(buffer, idx, out)

    def decompress(self):
        idx = 0

        buffer = self.getBuffer(self.buffer_type)
        packet = self.packet_type

        while idx < self.total_px:
            if packet == 0:
                idx = self.decodeRLEPacket(buffer, idx)

            else:
                idx = self.decodeDataPacket(buffer, idx)

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

        if self.decoding_method != 0b10:
            for x in range(w):
                base = x * h
                bit = 0

                for y in range(h):
                    i = base + y
                    bit ^= sec[i]
                    sec[i] = bit

        for x in range(w):
            base = x * h
            bit = 0

            for y in range(h):
                i = base + y
                bit ^= pri[i]
                pri[i] = bit

        if self.decoding_method != 0b0:
            for i in range(self.total_px):
                sec[i] ^= pri[i]

        # TODO: Buffer A rendering

    def printStatus(self):
        print(f"Sprite Width  : {self.sprite_width} tiles ({self.width_px} px)")
        print(f"Sprite Height : {self.sprite_height} tiles ({self.height_px} px)")
        print(f"Decoding Mode : {self.decoding_method}")
        print(f"Final Buffer  : {'B' if self.buffer_type == 0 else 'C'}")
        print(f"Pointer       : {self.pointer} / {self.length}\n")

    def render(self):
        pass

def main():
    file_adr = input("Enter the compressed binary file address (*.bin): ")
    
    with open(file_adr, "rb") as f:
        data = f.read()

    sprite = Sprite(data)

    sprite.decompress()
    sprite.printStatus()

    sprite.getEncodingMethod()
    sprite.printStatus()

    sprite.decompress()
    sprite.printStatus()

    sprite.decode()
    sprite.printStatus()

if __name__ == "__main__":
    main()