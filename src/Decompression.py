def printColor(color):
    table = {
        0x00: "107", 
        0x01: "47", 
        0x10: "100", 
        0x11: "40"
    }

    if color not in table:
        raise ValueError("Invalid color code. Must be one of 00, 01, 10, or 11.")
    
    print(f"\033[{table[color]}m  \033[0m", end='')

class BitStream:
    def __init__(self, bin_str):
        self.bin_str = bin_str
        self.pointer = 0

    def consume(self, length):
        bits = self.bin_str[self.pointer:self.pointer + length]
        self.pointer += length
        return bits

class Sprite(BitStream):
    def __init__(self, bin_str):
        super().__init__(bin_str)

        self.sprite_width = int(self.consume(4), 2)
        self.sprite_height = int(self.consume(4), 2)
        self.sprite_size = self.sprite_width * self.sprite_height

        # 0 = Buffer B, 1 = Buffer C
        self.buffer_type = int(self.consume(1), 2)

        # 0 = RLE, 1 = Data
        self.packet_type = int(self.consume(1), 2)

        # "0" = Mode 1, "10" = Mode 2, "11" = Mode 3
        self.decoding_method = "0"

        self.width_px = self.sprite_width * 8
        self.height_px = self.sprite_height * 8
        self.total_px = self.width_px * self.height_px

        empty = ["0"] * self.total_px
        self.Buffer_A = empty.copy()
        self.Buffer_B = empty.copy()
        self.Buffer_C = empty.copy()

    def _index(self, x, y):
        return x + y * self.width_px

    def getBuffer(self, buffer_type):
        return self.Buffer_B if buffer_type == 0 else self.Buffer_C

    def getDataFromBuffer(self, buffer_type, x, y):
        return self.getBuffer(buffer_type)[self._index(x, y)]

    def putDataToBuffer(self, buffer_type, x, y, data):
        buffer = self.getBuffer(buffer_type)

        for bit in data:
            idx = self._index(x, y)
        
            if idx >= self.total_px:
                break
            
            buffer[self._index(x, y)] = bit

            y += 1

            if y >= self.height_px:
                y = 0
                x += 1

                if x >= self.width_px:
                    break

        return x, y

    def decompress(self):
        x = y = 0

        while self._index(x, y) < self.total_px:            
            if self.packet_type == 0:
                x, y = self.decodeRLEPacket(x, y)

            else:
                x, y = self.decodeDataPacket(x, y)

            self.packet_type ^= 1

        self.buffer_type ^= 1

    def decodeRLEPacket(self, x, y):
        buf = self.consume(1)

        while buf[-1] != "0":
            buf += self.consume(1)

        length = int(buf, 2) + int(self.consume(len(buf)), 2) + 1

        return self.putDataToBuffer(self.buffer_type, x, y, "00" * length)

    def decodeDataPacket(self, x, y):
        buf = self.consume(2)

        while buf[-2:] != "00":
            buf += self.consume(2)

        return self.putDataToBuffer(self.buffer_type, x, y, buf[:-2])

    def getEncodingMethod(self):
        self.decoding_method = self.consume(1)

        if self.decoding_method == "1":
            self.decoding_method += self.consume(1)

        self.packet_type = int(self.consume(1), 2)

    def decode(self):
        pri = self.buffer_type
        sec = self.buffer_type ^ 1

        if self.decoding_method != "10":
            bit = 0

            for x in range(self.width_px):
                for y in range(self.height_px):
                    bit ^= int(self.getDataFromBuffer(sec, x, y))
                    self.putDataToBuffer(sec, x, y, str(bit))

        bit = 0

        for x in range(self.width_px):
            for y in range(self.height_px):
                bit ^= int(self.getDataFromBuffer(pri, x, y))
                self.putDataToBuffer(pri, x, y, str(bit))

        if self.decoding_method != "0":
            for x in range(self.width_px):
                for y in range(self.height_px):
                    bit = int(self.getDataFromBuffer(pri, x, y)) ^ int(self.getDataFromBuffer(sec, x, y))
                    self.putDataToBuffer(sec, x, y, str(bit))

        # TODO: Buffer A rendering

    def printStatus(self):
        print(f"Sprite Width: {self.sprite_width} tiles ({self.width_px} px)")
        print(f"Sprite Height: {self.sprite_height} tiles ({self.height_px} px)")
        print(f"Decoding Method: {self.decoding_method}")
        print(f"Final Buffer: {'B' if self.buffer_type == 1 else 'C'}; {self.Buffer_B if self.buffer_type == 1 else self.Buffer_C}\n")

    def render(self):
        pass

def main():
    file_adr = input("Enter the compressed binary file address (*.bin): ")
    
    with open(file_adr, "rb") as f:
        bin_str = ''.join(f'{b:08b}' for b in f.read())

    sprite = Sprite(bin_str)

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